"""Teste de integracao ponta a ponta do orquestrador (src/main.py): roda
TODAS as 8 etapas contra o SQL Server local, usando um subconjunto pequeno
de UFs (RR, AC - ja armazenadas em cache local pelo mecanismo de
deduplicacao de download, entao este teste nao depende de rede) para
manter o teste rapido, mas exercitando o codigo real de producao.
"""

from __future__ import annotations

import pytest
from src.config.settings import get_settings

pytestmark = pytest.mark.integration


@pytest.fixture
def small_uf_scope(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("ANS_BENEFICIARIOS_UFS", "RR,AC")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_full_pipeline_all_stages_succeed(small_uf_scope, writer_engine) -> None:
    from src.main import run

    exit_code = run(stage="all", reference_period="2024-12", source="all", force=False)
    assert exit_code == 0


def test_pipeline_stage_can_run_in_isolation(small_uf_scope, writer_engine) -> None:
    from src.main import run

    assert run(stage="refresh_views", reference_period="2024-12", source="all", force=False) == 0
