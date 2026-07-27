"""Cria as dimensoes: dim_tempo, dim_localidade, dim_operadora,
dim_tipo_estabelecimento, dim_estabelecimento.

Revision ID: 0002
Revises: 0001
Create Date: 2026-07-27
"""

from __future__ import annotations

from alembic import op

from src.utils.migration_sql import run_ddl_file

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None

_FILES = (
    "02_dim_tempo.sql",
    "03_dim_localidade.sql",
    "04_dim_operadora.sql",
    "05_dim_tipo_estabelecimento.sql",
    "06_dim_estabelecimento.sql",
)


def upgrade() -> None:
    connection = op.get_bind()
    for filename in _FILES:
        run_ddl_file(connection, filename)


def downgrade() -> None:
    connection = op.get_bind()
    for table in (
        "dim.dim_estabelecimento",
        "dim.dim_tipo_estabelecimento",
        "dim.dim_operadora",
        "dim.dim_localidade",
        "dim.dim_tempo",
    ):
        connection.exec_driver_sql(f"DROP TABLE IF EXISTS {table}")
