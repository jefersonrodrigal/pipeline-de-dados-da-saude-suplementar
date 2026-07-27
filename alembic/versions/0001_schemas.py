"""Cria os schemas de negocio (stg, dim, fact, aud, rej, rpt).

Revision ID: 0001
Revises:
Create Date: 2026-07-27
"""

from __future__ import annotations

from alembic import op

from src.utils.migration_sql import run_ddl_file

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    run_ddl_file(op.get_bind(), "01_create_schemas.sql")


def downgrade() -> None:
    connection = op.get_bind()
    for schema in ("rpt", "rej", "aud", "fact", "dim", "stg"):
        connection.exec_driver_sql(f"DROP SCHEMA IF EXISTS {schema}")
