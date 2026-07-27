# Pipeline de Dados da Saúde Suplementar

Pipeline de dados completo — extração, tratamento, qualidade, carga em Microsoft SQL
Server e aplicação analítica em Streamlit — construído sobre dados **públicos reais**
da ANS (beneficiários e operadoras) e do CNES/DATASUS (rede de estabelecimentos de
saúde):

> **Analisar a distribuição da rede de saúde e dos beneficiários por região,
> identificando concentração, cobertura, evolução histórica e possíveis lacunas de
> atendimento.**

## Índice

1. [Objetivo](#objetivo)
2. [Arquitetura](#arquitetura)
3. [Tecnologias](#tecnologias)
4. [Fonte dos dados](#fonte-dos-dados)
5. [Estrutura de diretórios](#estrutura-de-diretórios)
6. [Instalação](#instalação)
7. [Configuração (.env)](#configuração-env)
8. [SQL Server local](#sql-server-local)
9. [Migrations](#migrations)
10. [Rodando o pipeline](#rodando-o-pipeline)
11. [Rodando o Streamlit](#rodando-o-streamlit)
12. [Testes](#testes)
13. [Modelo de dados](#modelo-de-dados)
14. [Qualidade de dados](#qualidade-de-dados)
15. [Indicadores](#indicadores)
16. [Segurança e LGPD](#segurança-e-lgpd)
17. [Docker](#docker)
18. [Limitações conhecidas](#limitações-conhecidas)
19. [Melhorias futuras](#melhorias-futuras)
20. [Checklist de entregáveis](#checklist-de-entregáveis)


## Objetivo

Construir, com dados públicos reais, uma solução ponta a ponta que:

- extrai dados da ANS (FTP) e do CNES (fonte configurável);
- armazena os arquivos originais com hash/metadados (Raw);
- padroniza, normaliza e agrega os dados (Trusted);
- valida qualidade com uma camada de regras própria, auditável;
- carrega em um modelo dimensional no SQL Server, com controle de acesso por perfil;
- expõe indicadores em uma aplicação Streamlit multipágina;
- documenta arquitetura, regras de negócio e decisões técnicas.

## Arquitetura

Ver **[docs/architecture.md](docs/architecture.md)** para o diagrama completo (fluxo
Raw → Trusted → Qualidade → SQL Server → Streamlit, modelo dimensional em Mermaid,
decisões de modelagem e a avaliação staging-explícita vs. `MERGE`).

Resumo das camadas:

| Camada | Onde vive | Responsabilidade |
|---|---|---|
| Raw | `data/raw/` | Cópia fiel + hash SHA-256 + metadados de extração, dedupe automático |
| Trusted | `data/trusted/*.parquet` | Padronização, normalização, agregação no grão da fato |
| Analytics/Gold | SQL Server (`dim`, `fact`, `rpt`) | Modelo dimensional, views analíticas, tabela agregada materializada |

## Tecnologias

Python 3.11+ (desenvolvido/testado em 3.14), Pandas, SQLAlchemy + PyODBC + ODBC Driver
18, Alembic, Streamlit, Plotly, Pytest (+ `streamlit.testing.v1.AppTest`), Docker,
Jupyter. Grande Expectations foi avaliado e **não** foi adotado — justificativa em
[docs/business_rules.md](docs/business_rules.md#1-por-que-uma-camada-de-qualidade-própria-em-vez-do-great-expectations).

## Fonte dos dados

Todas as URLs abaixo foram **confirmadas manualmente** durante o desenvolvimento
(arquivos reais foram baixados e inspecionados) — ver detalhes completos, colunas e
limitações em **[docs/data_dictionary.md](docs/data_dictionary.md)**.

| Fonte | Órgão | Como é obtida |
|---|---|---|
| Beneficiários consolidados | ANS | FTP público, ZIP mensal por UF (`ANS_BENEFICIARIOS_BASE_URL` + `ANS_BENEFICIARIOS_UFS` no `.env`) |
| Operadoras ativas | ANS | CSV público, snapshot único (`ANS_OPERADORAS_URL`) |
| Estabelecimentos (CNES) | DATASUS | **Sem URL estável** — configurável via `CNES_DOWNLOAD_URL` ou depósito manual em `data/raw/cnes/incoming/` (inclui um arquivo fictício de demonstração, ver README nessa pasta) |

## Estrutura de diretórios

```
pipeline-saude-suplementar/
├── app/                    # Aplicação Streamlit (multipágina)
├── data/                   # raw/ trusted/ analytics/ rejected/
├── notebooks/              # Análise exploratória (executada, ver notebooks/exploratory_analysis.ipynb)
├── sql/                    # ddl/ views/ queries/ security/ staging/
├── src/                    # config/ extract/ transform/ quality/ load/ services/ models/ utils/ main.py
├── tests/                  # unit/ integration/ streamlit/ fixtures/
├── docs/                   # architecture, data_dictionary, business_rules, security, streamlit_guide
├── alembic/                # Migrations (executam os mesmos scripts de sql/ddl/)
├── .github/workflows/      # CI (lint, type-check, testes unitários e de integração)
├── docker-compose.yml, Dockerfile, Dockerfile.streamlit, Makefile
```

## Instalação

O projeto assume um virtualenv já criado em `.venv/` (Windows). Para (re)instalar as
dependências:

```powershell
make install
# ou, sem make:
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m pip install -e ".[dev]"
```

## Configuração (.env)

Copie `.env.example` para `.env` e preencha com valores reais do seu ambiente — **nunca
use os valores de exemplo em produção**. Variáveis principais:

```env
SQLSERVER_HOST=localhost
SQLSERVER_PORT=1433
SQLSERVER_DATABASE=saude_suplementar
SQLSERVER_USER=etl_writer
SQLSERVER_PASSWORD=<senha-do-etl_writer>
SQLSERVER_READONLY_USER=dashboard_reader
SQLSERVER_READONLY_PASSWORD=<senha-do-dashboard_reader>
SQLSERVER_DRIVER=ODBC Driver 18 for SQL Server
ANS_BENEFICIARIOS_UFS=SP,MG,RJ,RS,CE   # subconjunto para demo rápida; default = todas as 27 + XX
DEFAULT_REFERENCE_PERIOD=2024-12
```

## SQL Server local

Requer uma instância do SQL Server acessível (local, Docker, ou remota) com **autenticação
mista habilitada**. Crie o banco e os schemas:

```powershell
sqlcmd -S localhost -E -C -i sql\ddl\00_create_database.sql
sqlcmd -S localhost -E -C -d saude_suplementar -i sql\ddl\01_create_schemas.sql
```

Crie os logins de aplicação (least privilege — ver [docs/security.md](docs/security.md)):

```powershell
sqlcmd -S localhost -E -C -d saude_suplementar `
    -v EtlWriterPassword="<senha>" -v DashboardReaderPassword="<senha>" `
    -i sql\security\01_create_logins.sql
sqlcmd -S localhost -E -C -d saude_suplementar -i sql\security\02_grants.sql
```

(equivalente a `make db-security`, lendo as senhas de `SQLSERVER_PASSWORD`/`SQLSERVER_READONLY_PASSWORD`)

## Migrations

As tabelas (`dim`, `fact`, `aud`, `rej`, `stg`, `rpt.tb_resumo_mensal_uf`) são criadas via
Alembic, que executa os mesmos scripts de `sql/ddl/` (fonte única de verdade — ver
justificativa em `src/utils/migration_sql.py`):

```powershell
make migrate
# ou: .venv\Scripts\python.exe -m alembic upgrade head
```

## Rodando o pipeline

```powershell
python -m src.main --stage all --reference-period 2024-12 --source all
```

Etapas individuais (todas idempotentes, podem ser re-executadas):

```powershell
python -m src.main --stage extract
python -m src.main --stage transform --source cnes
python -m src.main --stage load --force
python -m src.main --stage refresh_views
```

Ver todas as 8 etapas (extract, validate_raw, transform, validate_trusted, load,
aggregate, refresh_views, export_analytics) em [docs/architecture.md](docs/architecture.md).

## Rodando o Streamlit

```powershell
streamlit run app/streamlit_app.py
```

Acesse `http://localhost:8501`. Descrição de cada página e estratégia de cache em
**[docs/streamlit_guide.md](docs/streamlit_guide.md)**.

## Testes

90 testes automatizados, ~88% de cobertura (`src` + `app`), sem dependência dos arquivos
públicos completos (fixtures fictícias pequenas em `tests/conftest.py`):

```powershell
make test-unit          # ~70 testes, sem SQL Server
make test-integration    # requer SQL Server (mesma base do pipeline)
make coverage
```

Cobrem: leitura/padronização/tipos/nulos (transform), regras de qualidade e motor de
validação, extração com HTTP mockado, manifesto de deduplicação, conexão/migrations/
staging/upsert/MERGE/rollback/idempotência (integração real), views analíticas,
repositórios com banco mockado, filtros e páginas Streamlit (`AppTest`), gráficos, e
cenários de falha/banco indisponível.

## Modelo de dados

Diagrama ER completo, decisões de SCD, chaves e índices em
**[docs/architecture.md](docs/architecture.md)**; dicionário de colunas por tabela em
**[docs/data_dictionary.md](docs/data_dictionary.md)**.

## Qualidade de dados

Motor de regras próprio (justificativa vs. Great Expectations, lista completa de regras
por dataset, e a razão de cada severidade ERROR/WARNING) em
**[docs/business_rules.md](docs/business_rules.md)**.

## Indicadores

Fórmula, origem, granularidade, periodicidade, limitações e interpretação de negócio de
cada indicador em **[docs/data_dictionary.md](docs/data_dictionary.md#5-indicadores--fórmula-origem-e-interpretação)**.

## Segurança e LGPD

Minimização de dados, controle de acesso (least privilege), gestão de segredos,
prevenção de SQL injection e análise de risco de reidentificação em
**[docs/security.md](docs/security.md)**.

## Docker

```bash
docker compose up -d
```

Sobe 3 serviços: `sqlserver` (imagem oficial Microsoft, com healthcheck), `pipeline`
(aguarda o SQL Server saudável, roda migrations + logins/grants + `--stage all` uma
única vez) e `streamlit` (aguarda o pipeline terminar com sucesso, publica em
`http://localhost:8501`). Ver `docker-compose.yml`, `Dockerfile`, `Dockerfile.streamlit`
e `docker/entrypoint-pipeline.sh`.

## Limitações conhecidas

- CNES usa um arquivo fictício de demonstração até que um export real seja depositado
  (ver `data/raw/cnes/incoming/README.md`) — qualquer conclusão sobre cobertura
  assistencial real exige substituí-lo.
- Sem geocodificação (lat/long) — mapas coropléticos exigiriam uma base IBGE adicional,
  fora do escopo definido para o projeto.
- Cadastro de operadoras é um snapshot sem histórico por competência (limitação da
  própria fonte, não do pipeline) — pode gerar o WARNING `operadora_inexistente` em
  competências mais antigas.
- Ambiente Python 3.14 é muito recente; a CI valida contra 3.12 para reduzir risco de
  incompatibilidades dos runners do GitHub Actions (o projeto exige apenas `>=3.11`).

## Melhorias futuras

- Carregar as 27 UFs + múltiplas competências consecutivas para habilitar análises de
  série temporal e correlação com significância estatística real.
- Integrar um export oficial do CNES e validar/ajustar `src/transform/cnes_column_mapping.py`.
- Adicionar uma base de geolocalização (IBGE) para mapas coropléticos na Visão Executiva.
- Política de retenção/expurgo automático para `aud.execucao_pipeline` e `rej.registros_rejeitados`.
- Publicar o Streamlit em Azure Container Apps/App Service (arquitetura já é
  container-ready via `Dockerfile.streamlit`).

## Checklist de entregáveis

- [x] Definição do problema e arquitetura (`docs/architecture.md`)
- [x] Dataset escolhido e documentado com URLs confirmadas (`docs/data_dictionary.md`)
- [x] Modelagem dimensional completa (DDL + Alembic + diagrama Mermaid)
- [x] Pipeline com 8 etapas independentes, idempotentes, auditadas
- [x] Extração real (ANS) + fonte configurável (CNES)
- [x] Transformação, normalização e agregação corretas (com bugs reais encontrados e corrigidos via testes)
- [x] Qualidade de dados própria, com justificativa documentada
- [x] Carga transacional (staging explícita + MERGE avaliado), least privilege
- [x] 12 views analíticas + 12 consultas SQL de exemplo
- [x] Aplicação Streamlit com 7 páginas, cache, filtros, tratamento de falhas
- [x] 90 testes automatizados (~88% cobertura), incluindo Streamlit `AppTest`
- [x] Docker Compose completo (SQL Server + pipeline + Streamlit)
- [x] CI (lint, format, type-check, testes unitários e de integração, scan de segredos)
- [x] Notebook exploratório executado com dados reais
- [x] Documentação completa (arquitetura, dicionário, regras, segurança, guia Streamlit)

## Como rodar

```powershell
# 1. Suba o SQL Server (local ou docker compose up -d sqlserver)
# 2. Aplique migrations e segurança
make migrate
make db-security
# 3. Rode o pipeline (subconjunto rápido de UFs, se quiser velocidade)
python -m src.main --stage all --reference-period 2024-12
# 4. Suba a aplicação
streamlit run app/streamlit_app.py
# 5. Abra http://localhost:8501 e navegue pelas 7 páginas
# 6. Mostre o notebook já executado: notebooks/exploratory_analysis.ipynb
# 7. Rode os testes ao vivo:
make test
```
