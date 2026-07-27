"""Testes de integracao da carga: staging, upsert, idempotencia e rollback.

Usa uma competencia sintetica ("1900-01", sk_tempo=190001) e um codigo de
operadora ficticio que nao existem nos dados reais carregados pelo
pipeline, para nao interferir com execucoes reais - e limpa tudo ao final.
"""

from __future__ import annotations

from datetime import date

import pandas as pd
import pytest
from sqlalchemy import text
from src.load.audit import finish_execucao, start_execucao
from src.load.loader import load_beneficiarios, load_operadoras

pytestmark = pytest.mark.integration

_SK_TEMPO_TESTE = 190001
_CD_OPERADORA_TESTE = "TEST01"


@pytest.fixture
def cleanup_synthetic_data(writer_engine):
    yield
    with writer_engine.begin() as conn:
        conn.execute(
            text("DELETE FROM fact.fato_beneficiarios WHERE sk_tempo = :sk"),
            {"sk": _SK_TEMPO_TESTE},
        )
        conn.execute(
            text("DELETE FROM dim.dim_tempo WHERE sk_tempo = :sk"), {"sk": _SK_TEMPO_TESTE}
        )
        conn.execute(
            text("DELETE FROM dim.dim_operadora WHERE cd_operadora_ans = :cod"),
            {"cod": _CD_OPERADORA_TESTE},
        )


@pytest.fixture
def synthetic_operadora_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "cd_operadora_ans": [_CD_OPERADORA_TESTE],
            "nr_cnpj": ["00000000000100"],
            "nm_razao_social": ["OPERADORA DE TESTE DE INTEGRACAO"],
            "nm_fantasia": [pd.NA],
            "modalidade": ["Cooperativa Médica"],
            "nm_municipio_sede": ["Boa Vista"],
            "sg_uf_sede": ["RR"],
            "dt_registro_ans": [date(2020, 1, 1)],
        }
    )


@pytest.fixture
def synthetic_beneficiarios_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "competencia": [date(1900, 1, 1)],
            "cd_operadora_ans": [_CD_OPERADORA_TESTE],
            "cd_municipio_ibge": ["140010"],
            "nm_municipio": ["Boa Vista"],
            "cd_uf": ["RR"],
            "tp_sexo": ["F"],
            "de_faixa_etaria": ["25 a 29 anos"],
            "tipo_vinculo": ["Titular"],
            "segmentacao_plano": ["Ambulatorial"],
            "qt_beneficiario_ativo": [42],
            "qt_beneficiario_aderido": [1],
            "qt_beneficiario_cancelado": [0],
        }
    )


def test_load_beneficiarios_is_idempotent(
    writer_engine, cleanup_synthetic_data, synthetic_operadora_df, synthetic_beneficiarios_df
) -> None:
    load_operadoras(writer_engine, synthetic_operadora_df)

    with writer_engine.begin() as conn:
        id_exec = start_execucao(conn, "teste_integracao", "load", "1900-01")

    first = load_beneficiarios(writer_engine, synthetic_beneficiarios_df, "1900-01", id_exec)
    assert first == {"atualizados": 0, "inseridos": 1}

    second = load_beneficiarios(writer_engine, synthetic_beneficiarios_df, "1900-01", id_exec)
    assert second == {"atualizados": 1, "inseridos": 0}

    with writer_engine.begin() as conn:
        finish_execucao(conn, id_exec, "SUCCESS")
        total = conn.execute(
            text(
                "SELECT SUM(qt_beneficiario_ativo) FROM fact.fato_beneficiarios "
                "WHERE sk_tempo = :sk"
            ),
            {"sk": _SK_TEMPO_TESTE},
        ).scalar_one()
    # Idempotencia: rodar duas vezes NAO deve dobrar a contagem.
    assert total == 42


def test_load_beneficiarios_rolls_back_on_failure(
    writer_engine, cleanup_synthetic_data, synthetic_operadora_df, synthetic_beneficiarios_df
) -> None:
    load_operadoras(writer_engine, synthetic_operadora_df)

    broken_df = synthetic_beneficiarios_df.drop(columns=["qt_beneficiario_ativo"])
    with pytest.raises(Exception):  # noqa: B017 - qualquer erro de carga deve reverter a transacao
        load_beneficiarios(writer_engine, broken_df, "1900-01", id_execucao=1)

    with writer_engine.connect() as conn:
        count = conn.execute(
            text("SELECT COUNT(*) FROM fact.fato_beneficiarios WHERE sk_tempo = :sk"),
            {"sk": _SK_TEMPO_TESTE},
        ).scalar_one()
    assert count == 0
