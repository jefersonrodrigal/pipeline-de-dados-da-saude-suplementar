"""Cria a tabela de auditoria de execucao do pipeline (aud.execucao_pipeline).

Precisa existir antes das fatos, pois elas referenciam id_execucao via FK.

Revision ID: 0003
Revises: 0002
Create Date: 2026-07-27
"""

from __future__ import annotations

from alembic import op

from src.utils.migration_sql import run_ddl_file

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    run_ddl_file(op.get_bind(), "07_aud_execucao_pipeline.sql")


def downgrade() -> None:
    op.get_bind().exec_driver_sql("DROP TABLE IF EXISTS aud.execucao_pipeline")
