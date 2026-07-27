# Segurança e LGPD

## 1. Princípio geral

Todos os dados usados neste projeto são **públicos** (ANS, CNES/DATASUS) e já vêm
agregados ou referentes a pessoas jurídicas (operadoras, estabelecimentos), não a
beneficiários individuais identificáveis. Ainda assim, o projeto aplica princípios de
minimização e controle de acesso como se lidasse com dados sensíveis, por boa prática
e porque parte da fonte (cadastro de operadoras) inclui dados de pessoa física do
representante legal.

## 2. Minimização de dados (LGPD, art. 6º, III)

O cadastro de operadoras da ANS (`Relatorio_cadop.csv`) inclui colunas de contato e de
pessoa física do representante legal: `Representante`, `Cargo_Representante`,
`Telefone`, `Fax`, `Endereco_eletronico`, `DDD`. **Nenhuma dessas colunas é necessária**
para os indicadores do projeto (distribuição geográfica, beneficiários por operadora).

Decisão: essas colunas são **descartadas na camada Trusted**
(`src/transform/ans_operadoras.py`) — nunca chegam a Analytics, ao SQL Server ou ao
Streamlit. Ver teste `tests/unit/test_transform_ans_operadoras.py::test_transform_drops_pii_columns`.

## 3. Agregação mínima e risco de reidentificação

Os dados de beneficiários da ANS já chegam agregados (contagens por operadora ×
município × faixa etária × sexo × vínculo), não microdados de pessoa física. O
Streamlit nunca expõe uma linha individual de beneficiário — todas as páginas
consomem agregações (views `rpt.*`). A página "Exploração dos Dados" permite navegar
livremente, mas apenas sobre as **mesmas views agregadas**, nunca sobre uma tabela de
grão individual.

## 4. Controle de acesso (least privilege)

Dois principais de banco de dados, com escopos disjuntos:

| Usuário | Uso | Permissões |
|---|---|---|
| `etl_writer` | Pipeline (extract/transform/load) | `SELECT/INSERT/UPDATE/DELETE` em `stg`, `dim`, `fact`, `aud`, `rej`, `rpt` (a última só para escrever `rpt.tb_resumo_mensal_uf`). **Sem** permissão de DDL (`CREATE`/`ALTER`/`TRUNCATE` — confirmado no teste `test_writer_cannot_create_tables`). |
| `dashboard_reader` | Aplicação Streamlit | `SELECT` **somente** no schema `rpt` (views + `tb_resumo_mensal_uf`). Sem acesso a `dim`/`fact`/`aud`/`rej` — confirmado em `tests/integration/test_views.py::test_dashboard_reader_can_select_from_views_but_not_from_facts`. |

Migrations e scripts DDL rodam sob um terceiro principal (`MigrationConnection` em
`src/config/settings.py`): Windows Authentication localmente (`SQLSERVER_MIGRATION_AUTH=trusted`)
ou `sa` via autenticação SQL em containers Docker (`SQLSERVER_MIGRATION_AUTH=sql`) —
nunca o mesmo usuário que roda a aplicação em produção.

## 5. Gestão de segredos

- Nenhuma credencial é gravada em código ou em scripts versionados. `.env` está no
  `.gitignore`; apenas `.env.example` (com valores fictícios) é versionado.
- Scripts SQL de criação de login (`sql/security/01_create_logins.sql`) recebem a senha
  via variável de scripting do `sqlcmd` (`-v EtlWriterPassword=...`), nunca hardcoded.
- O CI (`.github/workflows/ci.yml`) tem um passo dedicado que falha o build se um
  arquivo `.env` for commitado ou se um padrão de credencial hardcoded for encontrado.
- Mensagens de erro do banco mostradas ao usuário no Streamlit são genéricas
  (`DatabaseUnavailableError`, ver `app/repositories/base.py`) — nunca incluem host,
  driver ou credenciais, mesmo que a exceção original do driver contenha esses dados.

## 6. Timeouts e limites de consulta

- Conexões definem timeout configurável (`SQLSERVER_TIMEOUT_SECONDS`).
- Toda consulta do Streamlit passa por `run_query()` (`app/repositories/base.py`), que
  aplica `SQL_QUERY_ROW_LIMIT` (default 200.000 linhas) e trunca o resultado antes de
  retornar — evita que uma consulta sem filtro derrube a memória da aplicação.
- A página "Exploração dos Dados" aplica um limite adicional, mais conservador
  (`MAX_LINHAS = 5.000`), específico para exibição em tabela.

## 7. Consultas parametrizadas (prevenção de SQL Injection)

Todas as consultas usam `sqlalchemy.text()` com bind parameters nomeados
(`:sk`, `:uf`, etc.) — nunca f-string/concatenação de valores de filtro do usuário
(estado, período, texto de busca) dentro do SQL. A única exceção documentada é o nome
da **view** na página de Exploração, que vem de uma lista fixa em código
(`_DATASETS` em `app/pages/07_exploracao.py`), nunca de texto livre digitado pelo
usuário.

## 8. Auditoria

Toda execução de pipeline é registrada em `aud.execucao_pipeline` (início, fim, status,
contadores de registros recebidos/aceitos/rejeitados, mensagens de erro) e toda regra de
qualidade avaliada é registrada em `fact.fato_qualidade_dados` — permitindo reconstruir
"o que aconteceu e quando" sem depender de logs externos.

## 9. Retenção

Este projeto não implementa política de expurgo automático (fora de escopo para uma
demonstração de portfólio), mas a estrutura já suporta: `rej.registros_rejeitados` e
`aud.execucao_pipeline` têm timestamp em toda linha, permitindo uma rotina de limpeza
por idade a ser adicionada conforme a política de retenção da organização que adotar
este pipeline.

## 10. Downloads realizados pelo usuário

O botão de download em CSV (página "Exploração dos Dados") exporta apenas o resultado
já agregado e filtrado exibido na tela — nunca uma tabela de grão individual — mantendo
a mesma garantia de agregação mínima descrita na seção 3.
