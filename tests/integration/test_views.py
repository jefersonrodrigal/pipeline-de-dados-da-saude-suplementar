from __future__ import annotations

import pytest
from sqlalchemy import text

pytestmark = pytest.mark.integration

_EXPECTED_COLUMNS = {
    "vw_evolucao_mensal_beneficiarios": {
        "sk_tempo",
        "qt_beneficiarios_ativos",
        "variacao_percentual",
    },
    "vw_beneficiarios_por_estado": {"cd_uf", "qt_beneficiarios_ativos", "ranking_estado"},
    "vw_cobertura_regional": {"classificacao_cobertura", "beneficiarios_por_estabelecimento"},
    "vw_ranking_operadoras": {"cd_operadora_ans", "participacao_percentual", "ranking_operadora"},
    "vw_qualidade_pipeline": {"id_execucao", "status", "percentual_aprovacao"},
}


@pytest.mark.parametrize("view_name,expected_columns", _EXPECTED_COLUMNS.items())
def test_view_has_expected_columns(writer_engine, view_name, expected_columns) -> None:
    with writer_engine.connect() as conn:
        columns = set(
            conn.execute(
                text(
                    "SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS "
                    "WHERE TABLE_SCHEMA = 'rpt' AND TABLE_NAME = :view"
                ),
                {"view": view_name},
            ).scalars()
        )
    missing = expected_columns - columns
    assert not missing, f"{view_name} sem as colunas esperadas: {missing}"


def test_dashboard_reader_can_select_from_views_but_not_from_facts(writer_engine) -> None:
    """Reforca a fronteira de seguranca (least privilege) tambem no nivel
    de teste automatizado, nao so manualmente (ver docs/security.md)."""
    from src.config.settings import get_settings
    from src.utils.db import get_engine

    reader_engine = get_engine(get_settings().reader_connection)
    with reader_engine.connect() as conn:
        conn.execute(text("SELECT TOP 1 * FROM rpt.vw_beneficiarios_por_estado"))

    with pytest.raises(Exception, match="(?i)permiss|denied"), reader_engine.connect() as conn:
        conn.execute(text("SELECT TOP 1 * FROM fact.fato_beneficiarios"))
