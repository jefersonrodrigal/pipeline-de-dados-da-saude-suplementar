from __future__ import annotations

import pytest
from sqlalchemy import text

pytestmark = pytest.mark.integration

_EXPECTED_TABLES = {
    ("dim", "dim_tempo"),
    ("dim", "dim_localidade"),
    ("dim", "dim_operadora"),
    ("dim", "dim_tipo_estabelecimento"),
    ("dim", "dim_estabelecimento"),
    ("fact", "fato_beneficiarios"),
    ("fact", "fato_rede_assistencial"),
    ("fact", "fato_qualidade_dados"),
    ("aud", "execucao_pipeline"),
    ("rej", "registros_rejeitados"),
    ("stg", "beneficiarios"),
    ("stg", "operadoras"),
    ("stg", "estabelecimentos"),
    ("rpt", "tb_resumo_mensal_uf"),
}

_EXPECTED_VIEWS = {
    "vw_evolucao_mensal_beneficiarios",
    "vw_beneficiarios_por_estado",
    "vw_beneficiarios_por_municipio",
    "vw_estabelecimentos_por_municipio",
    "vw_estabelecimentos_por_tipo",
    "vw_razao_beneficiarios_estabelecimento",
    "vw_ranking_operadoras",
    "vw_cobertura_regional",
    "vw_variacao_percentual_periodos",
    "vw_qualidade_pipeline",
}


def test_all_expected_tables_exist(writer_engine) -> None:
    with writer_engine.connect() as conn:
        rows = conn.execute(
            text(
                "SELECT s.name, t.name FROM sys.tables t JOIN sys.schemas s ON t.schema_id = s.schema_id"
            )
        ).all()
    existing = {(schema, table) for schema, table in rows}
    missing = _EXPECTED_TABLES - existing
    assert not missing, f"Tabelas esperadas ausentes: {missing}"


def test_all_10_mandatory_views_exist(writer_engine) -> None:
    with writer_engine.connect() as conn:
        rows = conn.execute(
            text(
                "SELECT v.name FROM sys.views v JOIN sys.schemas s ON v.schema_id = s.schema_id WHERE s.name = 'rpt'"
            )
        ).all()
    existing = {name for (name,) in rows}
    missing = _EXPECTED_VIEWS - existing
    assert not missing, f"Views obrigatorias ausentes: {missing}"


def test_sentinel_rows_exist(writer_engine) -> None:
    with writer_engine.connect() as conn:
        assert (
            conn.execute(
                text("SELECT COUNT(*) FROM dim.dim_localidade WHERE sk_localidade = -1")
            ).scalar_one()
            == 1
        )
        assert (
            conn.execute(
                text("SELECT COUNT(*) FROM dim.dim_operadora WHERE sk_operadora = -1")
            ).scalar_one()
            == 1
        )
        assert (
            conn.execute(
                text(
                    "SELECT COUNT(*) FROM dim.dim_tipo_estabelecimento WHERE sk_tipo_estabelecimento = -1"
                )
            ).scalar_one()
            == 1
        )
        assert (
            conn.execute(
                text("SELECT COUNT(*) FROM dim.dim_estabelecimento WHERE sk_estabelecimento = -1")
            ).scalar_one()
            == 1
        )
