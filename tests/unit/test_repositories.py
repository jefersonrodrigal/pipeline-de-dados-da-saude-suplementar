"""Testes dos repositorios com DatabaseConnection mockado - nao dependem de
um SQL Server real (ver tests/integration para os testes que dependem)."""

from __future__ import annotations

import pandas as pd
import pytest
from app.repositories import beneficiary_repository, data_quality_repository, operator_repository
from app.repositories.beneficiary_repository import BeneficiaryRepository
from app.repositories.data_quality_repository import DataQualityRepository
from app.repositories.operator_repository import OperatorRepository

import streamlit as st


@pytest.fixture(autouse=True)
def _clear_streamlit_cache():
    st.cache_data.clear()
    yield
    st.cache_data.clear()


def test_beneficiary_repository_evolucao_mensal(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_df = pd.DataFrame({"sk_tempo": [202412], "qt_beneficiarios_ativos": [100]})
    monkeypatch.setattr(
        beneficiary_repository.DatabaseConnection,
        "query",
        staticmethod(lambda sql, params=None, row_limit=None: fake_df),
    )
    result = BeneficiaryRepository.evolucao_mensal()
    pd.testing.assert_frame_equal(result, fake_df)


def test_beneficiary_repository_por_municipio_filters_by_uf(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured = {}

    def fake_query(sql, params=None, row_limit=None):
        captured["sql"] = sql
        captured["params"] = params
        return pd.DataFrame({"cd_uf": ["RR"]})

    monkeypatch.setattr(
        beneficiary_repository.DatabaseConnection, "query", staticmethod(fake_query)
    )
    BeneficiaryRepository.por_municipio(202412, "RR")

    assert "cd_uf = :uf" in captured["sql"]
    assert captured["params"] == {"sk": 202412, "uf": "RR"}


def test_operator_repository_ranking(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_df = pd.DataFrame({"cd_operadora_ans": ["1"], "ranking_operadora": [1]})
    monkeypatch.setattr(
        operator_repository.DatabaseConnection,
        "query",
        staticmethod(lambda sql, params=None, row_limit=None: fake_df),
    )
    result = OperatorRepository.ranking(202412)
    assert list(result["cd_operadora_ans"]) == ["1"]


def test_data_quality_repository_resumo_geral(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_df = pd.DataFrame({"total_recebido": [100], "total_valido": [95], "total_rejeitado": [5]})
    monkeypatch.setattr(
        data_quality_repository.DatabaseConnection,
        "query",
        staticmethod(lambda sql, params=None, row_limit=None: fake_df),
    )
    result = DataQualityRepository.resumo_geral()
    assert result.iloc[0]["total_valido"] == 95
