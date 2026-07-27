from __future__ import annotations

from pathlib import Path

import pytest
from sqlalchemy import text
from src.services.aggregate import refresh_resumo_mensal_uf
from src.services.export_analytics import export_analytics
from src.services.views import refresh_views

pytestmark = pytest.mark.integration


def test_refresh_views_is_idempotent(migration_engine) -> None:
    first = refresh_views(migration_engine)
    second = refresh_views(migration_engine)
    assert first == second
    assert "01_vw_evolucao_mensal_beneficiarios" in first


def test_refresh_resumo_mensal_uf_is_idempotent(writer_engine) -> None:
    first = refresh_resumo_mensal_uf(writer_engine, 202412)
    second = refresh_resumo_mensal_uf(writer_engine, 202412)
    assert first == second

    with writer_engine.connect() as conn:
        count = conn.execute(
            text("SELECT COUNT(*) FROM rpt.tb_resumo_mensal_uf WHERE sk_tempo = :sk"),
            {"sk": 202412},
        ).scalar_one()
    assert count == first


def test_export_analytics_writes_parquet_files(writer_engine, tmp_path: Path) -> None:
    written = export_analytics(writer_engine, tmp_path, "2024-12")
    assert len(written) == 8
    assert all(p.exists() for p in written)
