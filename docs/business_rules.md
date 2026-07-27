# Regras de Negócio e Qualidade de Dados

## 1. Por que uma camada de qualidade própria em vez do Great Expectations

Avaliamos usar o Great Expectations (GE) antes de implementar `src/quality/`. Durante o
planejamento, rodamos `pip install --dry-run great_expectations` e confirmamos que a
versão compatível (0.18.8) traz **~80 pacotes transitivos**, incluindo Jupyter/Notebook
completo, JupyterLab, `scipy`, `marshmallow`, `ruamel.yaml`, `ipykernel`, entre outros —
uma árvore de dependências desproporcional para validar algumas dezenas de regras sobre
três datasets tabulares.

Decisão: implementar um motor de regras próprio (`src/quality/engine.py`), com:

- `Rule(name, description, severity, check)` — `check` recebe o DataFrame e devolve uma
  máscara booleana das linhas que **violam** a regra;
- regras `ERROR` rejeitam a linha (removida do dataset aceito, gravada em
  `rej.registros_rejeitados` e em arquivo `data/rejected/*.jsonl`);
- regras `WARNING` apenas contam/alertam — a linha permanece no dataset, tipicamente
  porque haverá uma chave substituta sentinela para tratar o caso (ex.: operadora não
  cadastrada → `sk_operadora = -1`).

Vantagens práticas observadas: mensagens em português, integração direta com as tabelas
de auditoria do SQL Server, e testes unitários simples (`tests/unit/test_quality_engine.py`,
`test_quality_validators.py`) sem qualquer dependência extra.

## 2. Regras de qualidade implementadas

### 2.1 Beneficiários (`src/quality/validators.py::beneficiarios_rules`)

| Regra | Severidade | Descrição |
|---|---|---|
| `valores_negativos` | ERROR | Quantidade de beneficiários negativa |
| `volume_implausivel` | ERROR | `qt_beneficiario_ativo` > 500.000 em uma única linha do grão |
| `uf_invalida` | ERROR | UF fora da lista das 27 unidades federativas + `XX` |
| `municipio_ausente` | ERROR | Código de município vazio/nulo |
| `municipio_formato_invalido` | WARNING | Código de município fora do padrão de 6-7 dígitos |
| `periodo_invalido` | ERROR | Competência não pôde ser interpretada |
| `operadora_inexistente` | WARNING | `cd_operadora_ans` não encontrado no cadastro de operadoras ativas (ver nota abaixo) |
| `municipio_uf_inconsistente` | WARNING | Mesmo código de município associado a nomes diferentes no mesmo arquivo |

**Por que `operadora_inexistente` é WARNING, não ERROR**: o cadastro de operadoras é um
snapshot do dia da extração (sem histórico por competência), enquanto o arquivo de
beneficiários é histórico. Uma operadora pode ter sido descredenciada entre a
competência de referência e a data da extração do cadastro — isso não é um erro de
dado, é uma consequência esperada de cruzar uma fonte histórica com uma fonte "viva".
Rejeitar a linha destruiria beneficiários reais; a linha é aceita e associada ao
sentinela `sk_operadora = -1`.

### 2.2 Operadoras (`operadoras_rules`)

`codigo_operadora_ausente` (ERROR), `razao_social_ausente` (ERROR),
`cnpj_formato_invalido` (WARNING — 14 dígitos esperados), `operadora_duplicada` (ERROR).

### 2.3 Estabelecimentos (`estabelecimentos_rules`)

`cnes_ausente` (ERROR), `nome_ausente` (ERROR), `sem_classificacao` (WARNING — sem tipo
informado, mapeado para o sentinela `sk_tipo_estabelecimento = -1`), `cnes_duplicado`
(ERROR), `uf_invalida` (WARNING).

## 3. Estratégia de carga: staging explícita vs. `MERGE`

Ver detalhamento completo em `docs/architecture.md`, seção "Carga". Resumo da decisão:

- **Fato de beneficiários**: staging → `UPDATE` → `INSERT` → validação de contagem →
  commit → limpeza da staging (estratégia explícita, priorizada pela especificação do
  projeto por ser mais previsível/testável).
- **Fato de rede assistencial**: `MERGE` T-SQL, escolhido deliberadamente como o "caso
  avaliado", com grão `(sk_tempo, sk_estabelecimento)` sempre `NOT NULL` (evita a
  armadilha de comparação `NULL x NULL` na cláusula `ON`).

## 4. Dimensões lentamente mutáveis (SCD)

- **Tipo 2** (`dim_operadora`, `dim_estabelecimento`): quando um atributo relevante muda
  (razão social, modalidade, UF sede da operadora; nome, tipo ou localidade do
  estabelecimento), a linha vigente é fechada (`dt_fim_vigencia`, `fl_vigente = 0`) e
  uma nova linha é inserida (`fl_vigente = 1`). Implementado via `UPDATE` + `INSERT`
  explícitos em `src/load/dimensions.py`.
- **Tipo 1** (`dim_tempo`, `dim_localidade`, `dim_tipo_estabelecimento`): sobrescreve,
  sem histórico — não há necessidade de negócio para rastrear mudança de nome de
  município ou de tipo de estabelecimento.

## 5. Classificação exploratória de cobertura regional

A página "Cobertura Regional" e a view `rpt.vw_cobertura_regional` classificam cada
município em três faixas, com base na razão beneficiários/estabelecimento:

| Classificação | Critério |
|---|---|
| Cobertura adequada | `beneficiarios_por_estabelecimento < 2.000` |
| Atenção | `2.000 <= beneficiarios_por_estabelecimento < 5.000` |
| Cobertura crítica | `beneficiarios_por_estabelecimento >= 5.000` OU zero estabelecimentos cadastrados |

**Estes limiares (2.000 e 5.000) são heurísticas definidas para fins de demonstração e
priorização exploratória neste projeto — não são um padrão regulatório da ANS ou do
Ministério da Saúde, nem devem ser lidos como diagnóstico de saúde pública.** A interface
do Streamlit reforça esse disclaimer explicitamente (`app/components/status_badges.py`).

## 6. Normalização de códigos

- **Município**: mantido com o código de 6 dígitos exatamente como a ANS publica (ver
  justificativa em `docs/architecture.md`, item 2).
- **UF**: normalizado para maiúsculas; qualquer valor fora das 27 UFs + `DF` vira o
  sentinela `XX` ("Não identificado / Exterior").
- **Operadora/Estabelecimento**: strings de código são normalizadas (trim), mas nunca
  reformatadas numericamente (evita inventar dígitos).

## 7. Reprocessamento e idempotência

Toda carga (dimensões e fatos) é idempotente: rodar a mesma competência duas vezes
resulta em `UPDATE` das linhas existentes, nunca duplicação — garantido pelas
constraints de grão (`uq_fato_beneficiarios_grao`, `uq_fato_rede_grao`) e testado em
`tests/integration/test_load_facts.py::test_load_beneficiarios_is_idempotent`. Falhas em
qualquer ponto da carga revertem a transação inteira (`tests/integration/test_load_facts.py::test_load_beneficiarios_rolls_back_on_failure`).
