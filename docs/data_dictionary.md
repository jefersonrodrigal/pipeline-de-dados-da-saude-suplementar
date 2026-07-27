# Dicionário de Dados

## 1. Fontes públicas

### 1.1 ANS — Beneficiários (dados consolidados)

| | |
|---|---|
| Conjunto de dados | Informações Consolidadas de Beneficiários |
| Órgão | Agência Nacional de Saúde Suplementar (ANS) |
| URL confirmada | `https://dadosabertos.ans.gov.br/FTP/PDA/informacoes_consolidadas_de_beneficiarios-024/{AAAAMM}/pda-024-icb-{UF}-{AAAA}_{MM}.zip` |
| Período disponível | Pelo menos 2021-05 até o mês corrente (confirmado navegando o índice do FTP) |
| Granularidade | Contagem agregada por operadora × município × sexo × faixa etária × tipo de plano × vínculo — **não é microdado de pessoa física** |
| Formato | ZIP contendo 1 CSV `;`-delimitado, UTF-8, por UF/competência |
| Frequência de atualização | Mensal |
| Colunas de origem (confirmadas baixando um arquivo real) | `ID_CMPT_MOVEL, CD_OPERADORA, NM_RAZAO_SOCIAL, NR_CNPJ, MODALIDADE_OPERADORA, SG_UF, CD_MUNICIPIO, NM_MUNICIPIO, TP_SEXO, DE_FAIXA_ETARIA, DE_FAIXA_ETARIA_REAJ, CD_PLANO, TP_VIGENCIA_PLANO, DE_CONTRATACAO_PLANO, DE_SEGMENTACAO_PLANO, DE_ABRG_GEOGRAFICA_PLANO, COBERTURA_ASSIST_PLAN, TIPO_VINCULO, QT_BENEFICIARIO_ATIVO, QT_BENEFICIARIO_ADERIDO, QT_BENEFICIARIO_CANCELADO, DT_CARGA` |
| Limitações | Arquivo por UF (SP ~130MB/mês); grão mais fino que a fato modelada (ver `docs/architecture.md`); `CD_MUNICIPIO` tem 6 dígitos (IBGE sem dígito verificador). |

### 1.2 ANS — Operadoras Ativas

| | |
|---|---|
| Conjunto de dados | Cadastro de Operadoras Ativas |
| URL confirmada | `https://dadosabertos.ans.gov.br/FTP/PDA/operadoras_de_plano_de_saude_ativas/Relatorio_cadop.csv` |
| Período | Snapshot único, sem histórico por competência (sobrescrito pela ANS a cada atualização) |
| Formato | CSV `;`-delimitado, UTF-8 |
| Colunas de origem | `REGISTRO_OPERADORA, CNPJ, Razao_Social, Nome_Fantasia, Modalidade, Logradouro, Numero, Complemento, Bairro, Cidade, UF, CEP, DDD, Telefone, Fax, Endereco_eletronico, Representante, Cargo_Representante, Regiao_de_Comercializacao, Data_Registro_ANS` |
| Minimização LGPD | `Representante, Cargo_Representante, Telefone, Fax, Endereco_eletronico, DDD` são **descartados** na Trusted (dados de contato/pessoa física do representante legal) — ver `docs/security.md`. |

### 1.3 CNES — Estabelecimentos de Saúde

| | |
|---|---|
| Órgão | DATASUS / Ministério da Saúde |
| URL | **Não existe URL estável** — o portal (`cnes.datasus.gov.br/pages/downloads/arquivosBaseDados.jsp`) exige seleção dinâmica de UF/competência via formulário/servlet. |
| Solução adotada | Fonte configurável: `CNES_DOWNLOAD_URL` no `.env`, OU depósito manual em `data/raw/cnes/incoming/` (ver README nessa pasta). |
| Dado usado nesta demonstração | `exemplo_estabelecimentos_FICTICIO.csv` — **dados 100% fictícios** (nomes/códigos inventados), incluído apenas para permitir rodar o pipeline de ponta a ponta. **Substitua pelo export real do CNES para qualquer análise de negócio.** |
| Mapeamento de colunas | `src/transform/cnes_column_mapping.py` — baseado nas convenções de nome de campo publicamente documentadas pelo DATASUS (`CO_CNES`, `NO_FANTASIA`, `TP_UNIDADE`, `CO_MUNICIPIO`, etc.), **ajustável** conforme o layout do arquivo real baixado. |

## 2. Camada Trusted (Parquet)

| Dataset | Caminho | Colunas |
|---|---|---|
| `beneficiarios` | `data/trusted/beneficiarios/{AAAAMM}/part.parquet` | `competencia, cd_operadora_ans, cd_municipio_ibge, nm_municipio, cd_uf, tp_sexo, de_faixa_etaria, tipo_vinculo, segmentacao_plano, qt_beneficiario_ativo, qt_beneficiario_aderido, qt_beneficiario_cancelado` |
| `operadoras` | `data/trusted/operadoras/{AAAAMM}/part.parquet` | `cd_operadora_ans, nr_cnpj, nm_razao_social, nm_fantasia, modalidade, nm_municipio_sede, sg_uf_sede, dt_registro_ans` |
| `estabelecimentos` | `data/trusted/estabelecimentos/{AAAAMM}/part.parquet` | `cd_cnes, nm_estabelecimento, cd_tipo_estabelecimento, ds_tipo_estabelecimento, cd_municipio_ibge, nm_municipio, cd_uf, periodo_referencia` |

## 3. Modelo dimensional (SQL Server)

Ver DDL completo comentado em `sql/ddl/*.sql` e o diagrama ER em `docs/architecture.md`. Resumo de cada tabela:

| Schema.Tabela | Grão | Chave natural | Chave substituta |
|---|---|---|---|
| `dim.dim_tempo` | 1 linha/mês | `competencia` | `sk_tempo` (= `AAAAMM`) |
| `dim.dim_localidade` | 1 linha/município | `(cd_municipio_ibge, cd_uf)` | `sk_localidade` (identity) |
| `dim.dim_operadora` | 1 linha/versão vigente da operadora (SCD2) | `cd_operadora_ans` | `sk_operadora` (identity) |
| `dim.dim_tipo_estabelecimento` | 1 linha/tipo | `cd_tipo_estabelecimento` | `sk_tipo_estabelecimento` (identity) |
| `dim.dim_estabelecimento` | 1 linha/versão vigente do estabelecimento (SCD2) | `cd_cnes` | `sk_estabelecimento` (identity) |
| `fact.fato_beneficiarios` | competência × operadora × localidade × sexo × faixa × vínculo × segmentação | (composta, ver `uq_fato_beneficiarios_grao`) | `sk_beneficiarios` (identity) |
| `fact.fato_rede_assistencial` | competência × estabelecimento | `(sk_tempo, sk_estabelecimento)` | `sk_rede_assistencial` (identity) |
| `fact.fato_qualidade_dados` | execução × etapa × regra | — | `id_qualidade` (identity) |
| `aud.execucao_pipeline` | 1 linha/execução de etapa | — | `id_execucao` (identity) |
| `rej.registros_rejeitados` | 1 linha/registro rejeitado | — | `id_rejeicao` (identity) |
| `rpt.tb_resumo_mensal_uf` | competência × UF | `(sk_tempo, cd_uf)` | — (chave composta é PK) |

## 4. Views analíticas (`schema rpt`)

| View | Responde a pergunta de negócio |
|---|---|
| `vw_evolucao_mensal_beneficiarios` | Como evoluiu o total de beneficiários mês a mês? |
| `vw_beneficiarios_por_estado` | Quais estados têm mais beneficiários? |
| `vw_beneficiarios_por_municipio` | Quais municípios têm mais beneficiários? |
| `vw_estabelecimentos_por_municipio` | Quantos estabelecimentos por município? |
| `vw_estabelecimentos_por_tipo` | Quais tipos de estabelecimento são mais comuns? |
| `vw_razao_beneficiarios_estabelecimento` | Qual a relação beneficiários/estabelecimentos? |
| `vw_ranking_operadoras` | Quais operadoras têm mais beneficiários/participação? |
| `vw_cobertura_regional` | Quais regiões têm possível baixa cobertura? |
| `vw_variacao_percentual_periodos` | Qual a variação percentual entre períodos, por UF? |
| `vw_qualidade_pipeline` | Como evolui a qualidade/duração das execuções do pipeline? |
| `vw_qualidade_regras` *(bônus)* | Quais regras de qualidade são mais violadas? |
| `vw_operadoras_por_regiao` *(bônus)* | Quais operadoras lideram em cada região? |

## 5. Indicadores — fórmula, origem e interpretação

| Indicador | Fórmula | Origem | Granularidade | Periodicidade | Limitações | Interpretação de negócio |
|---|---|---|---|---|---|---|
| Total de beneficiários | `SUM(qt_beneficiario_ativo)` | `fact.fato_beneficiarios` | Brasil/UF/Município/Operadora | Mensal | Contagem agregada da ANS, não elimina possíveis vínculos duplicados de uma mesma pessoa em planos diferentes | Tamanho do mercado atendido no recorte |
| Crescimento mensal (%) | `(atual - anterior) / anterior * 100` | `vw_evolucao_mensal_beneficiarios` (via `LAG`) | Nacional/UF | Mensal | Nulo no primeiro mês carregado (sem anterior) | Sinaliza expansão/retração recente |
| Participação de mercado (operadora) | `qt_beneficiarios_operadora / SUM(qt_beneficiarios) * 100` | `vw_ranking_operadoras` | Por competência | Mensal | Não distingue vidas físicas de titulares+dependentes | Concentração de mercado, poder de barganha |
| Beneficiários por estabelecimento | `qt_beneficiarios_ativos / qt_estabelecimentos` | `vw_razao_beneficiarios_estabelecimento` | Município | Mensal | `NULL` quando não há estabelecimentos (ver índice de cobertura) | Proxy de pressão de demanda sobre a rede |
| Índice exploratório de cobertura | Classificação por faixas da razão acima (ver `docs/business_rules.md`) | `vw_cobertura_regional` | Município | Mensal | **Exploratório, não é diagnóstico** — thresholds arbitrários definidos para este projeto | Priorização de investigação, não decisão automática |
| % de registros válidos/rejeitados | `qt_valida / qt_recebida * 100` | `aud.execucao_pipeline` / `vw_qualidade_pipeline` | Por execução/etapa | Por execução | Depende de quais regras estão ativas | Saúde geral do pipeline de dados |
| Duração média do pipeline | `AVG(duracao_segundos)` por etapa | `vw_qualidade_pipeline` | Por etapa | Por execução | Sensível ao volume de UFs carregadas | Planejamento de janelas de execução |
