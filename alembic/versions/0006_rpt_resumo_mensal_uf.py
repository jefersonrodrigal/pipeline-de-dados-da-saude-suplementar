"""Cria rpt.tb_resumo_mensal_uf (tabela agregada da etapa 'aggregate').

Revision ID: 0006
Revises: 0005
Create Date: 2026-07-27
"""

from __future__ import annotations

from alembic import op

from src.utils.migration_sql import run_ddl_file

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    run_ddl_file(op.get_bind(), "13_rpt_resumo_mensal_uf.sql")


def downgrade() -> None:
    op.get_bind().exec_driver_sql("DROP TABLE IF EXISTS rpt.tb_resumo_mensal_uf")
