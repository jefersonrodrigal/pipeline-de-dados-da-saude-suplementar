#!/bin/sh
# Entrypoint do container do pipeline. Roda uma unica vez por start do
# container: cria o banco (se nao existir), aplica migrations e configura
# os logins/permissoes de minimo privilegio - so entao executa o comando
# recebido (CMD do Dockerfile ou `docker compose run` customizado).
#
# So chega aqui depois que o docker-compose confirma (via healthcheck) que
# o SQL Server esta pronto para aceitar conexoes - ver depends_on em
# docker-compose.yml.
set -eu

echo "[entrypoint] Criando banco de dados (se necessario)..."
sqlcmd -S "${SQLSERVER_HOST}","${SQLSERVER_PORT}" -U sa -P "${SQLSERVER_SA_PASSWORD}" -C \
    -i sql/ddl/00_create_database.sql

echo "[entrypoint] Aplicando migrations (Alembic)..."
python -m alembic upgrade head

echo "[entrypoint] Criando logins de aplicacao (etl_writer, dashboard_reader)..."
sqlcmd -S "${SQLSERVER_HOST}","${SQLSERVER_PORT}" -U sa -P "${SQLSERVER_SA_PASSWORD}" -C \
    -d "${SQLSERVER_DATABASE}" \
    -v EtlWriterPassword="${SQLSERVER_PASSWORD}" \
    -v DashboardReaderPassword="${SQLSERVER_READONLY_PASSWORD}" \
    -i sql/security/01_create_logins.sql

echo "[entrypoint] Aplicando permissoes (least privilege)..."
sqlcmd -S "${SQLSERVER_HOST}","${SQLSERVER_PORT}" -U sa -P "${SQLSERVER_SA_PASSWORD}" -C \
    -d "${SQLSERVER_DATABASE}" \
    -i sql/security/02_grants.sql

echo "[entrypoint] Setup concluido. Executando: $*"
exec "$@"
