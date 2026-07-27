"""Cria rej.registros_rejeitados e as tabelas de staging (stg.*).

Revision ID: 0005
Revises: 0004
Create Date: 2026-07-27
"""

from __future__ import annotations

from alembic import op

from src.utils.migration_sql import run_ddl_file

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None

_FILES = (
    "11_rej_registros_rejeitados.sql",
    "12_staging_tables.sql",
)


def upgrade() -> None:
    connection = op.get_bind()
    for filename in _FILES:
        run_ddl_file(connection, filename)


def downgrade() -> None:
    connection = op.get_bind()
    for table in (
        "stg.estabelecimentos",
        "stg.operadoras",
        "stg.beneficiarios",
        "rej.registros_rejeitados",
    ):
        connection.exec_driver_sql(f"DROP TABLE IF EXISTS {table}")
