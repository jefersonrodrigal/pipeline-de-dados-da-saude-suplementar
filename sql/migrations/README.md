# Migrations

As migrations executáveis vivem em `alembic/versions/` (convenção do Alembic, a
ferramenta usada pelo projeto — ver `alembic.ini` e `src/utils/migration_sql.py`), não
nesta pasta. `alembic/versions/*.py` executa os scripts DDL de `sql/ddl/*.sql` em ordem,
garantindo que o SQL puro e a migration nunca fiquem dessincronizados.

Esta pasta existe para deixar explícita a etapa na estrutura do projeto (seção 19 do
briefing). Ver `docs/architecture.md` e o README principal, seção "Migrations".
