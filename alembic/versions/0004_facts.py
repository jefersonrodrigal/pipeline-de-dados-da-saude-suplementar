"""Cria as tabelas fato: fato_beneficiarios, fato_rede_assistencial,
fato_qualidade_dados.

Revision ID: 0004
Revises: 0003
Create Date: 2026-07-27
"""

from __future__ import annotations

from alembic import op

from src.utils.migration_sql import run_ddl_file

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None

_FILES = (
    "08_fact_beneficiarios.sql",
    "09_fact_rede_assistencial.sql",
    "10_fact_qualidade_dados.sql",
)


def upgrade() -> None:
    connection = op.get_bind()
    for filename in _FILES:
        run_ddl_file(connection, filename)


def downgrade() -> None:
    connection = op.get_bind()
    for table in (
        "fact.fato_qualidade_dados",
        "fact.fato_rede_assistencial",
        "fact.fato_beneficiarios",
    ):
        connection.exec_driver_sql(f"DROP TABLE IF EXISTS {table}")
