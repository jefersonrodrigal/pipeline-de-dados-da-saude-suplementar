# Staging

O DDL das tabelas de staging (`stg.beneficiarios`, `stg.operadoras`,
`stg.estabelecimentos`) vive em `sql/ddl/12_staging_tables.sql`, junto com as demais
tabelas do banco (fonte única de verdade, aplicada tanto via `sqlcmd` quanto via
Alembic — ver `alembic/versions/0005_rejected_and_staging.py`).

Esta pasta existe para deixar explícita a etapa de staging na estrutura do projeto
(seção 19 do briefing). A lógica de **uso** da staging (truncar, carregar em lote,
fazer upsert/MERGE contra dim/fact e depois limpar) está em `src/load/staging.py`,
`src/load/loader.py` e `src/load/facts.py` — ver `docs/architecture.md`, seção "Carga".
