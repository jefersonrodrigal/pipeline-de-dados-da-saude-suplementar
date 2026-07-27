"""Testes da aplicacao Streamlit com `streamlit.testing.v1.AppTest` - executam
o script de cada pagina de ponta a ponta (server-side) e verificam ausencia
de excecoes no carregamento, presenca de indicadores e ausencia de
credenciais na interface. Dependem do SQL Server local estar acessivel
(mesma base usada pelo pipeline) - pulados automaticamente se nao estiver.
"""

from __future__ import annotations

import pytest
from src.config.settings import get_settings
from src.utils.db import get_engine
from streamlit.testing.v1 import AppTest

pytestmark = pytest.mark.integration


@pytest.fixture(scope="module", autouse=True)
def _skip_if_db_unavailable():
    settings = get_settings()
    engine = get_engine(settings.reader_connection)
    try:
        with engine.connect():
            pass
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"SQL Server indisponivel para testes de Streamlit: {exc}")


_PAGES = [
    "app/streamlit_app.py",
    "app/pages/01_visao_executiva.py",
    "app/pages/02_beneficiarios.py",
    "app/pages/03_rede_assistencial.py",
    "app/pages/04_cobertura_regional.py",
    "app/pages/05_operadoras.py",
    "app/pages/06_qualidade_dados.py",
    "app/pages/07_exploracao.py",
]


@pytest.mark.parametrize("page_path", _PAGES)
def test_page_runs_without_exceptions(page_path: str) -> None:
    at = AppTest.from_file(page_path, default_timeout=30)
    at.run()
    assert not at.exception, f"{page_path} lancou excecao: {[e.value for e in at.exception]}"


@pytest.mark.parametrize("page_path", _PAGES)
def test_page_never_renders_raw_credentials(page_path: str) -> None:
    at = AppTest.from_file(page_path, default_timeout=30)
    at.run()
    settings = get_settings()
    rendered_text = "\n".join(
        [md.value for md in at.markdown]
        + [t.value for t in at.text]
        + [c.value for c in at.caption]
    )
    assert settings.writer_connection.password not in rendered_text
    assert settings.reader_connection.password not in rendered_text


def test_visao_executiva_shows_kpi_metrics() -> None:
    at = AppTest.from_file("app/pages/01_visao_executiva.py", default_timeout=30)
    at.run()
    assert not at.exception
    assert len(at.metric) >= 4  # pelo menos os 4 cards principais
