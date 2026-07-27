"""Consultas de operadoras (ranking, evolucao, participacao por regiao)."""

from __future__ import annotations

import pandas as pd
from app.repositories.base import DatabaseConnection
from src.config.settings import get_settings

import streamlit as st

_TTL = get_settings().streamlit_cache_ttl_seconds


@st.cache_data(ttl=_TTL, show_spinner="Carregando ranking de operadoras...")
def _ranking(sk_tempo: int) -> pd.DataFrame:
    return DatabaseConnection.query(
        "SELECT * FROM rpt.vw_ranking_operadoras WHERE sk_tempo = :sk ORDER BY ranking_operadora",
        {"sk": sk_tempo},
    )


@st.cache_data(ttl=_TTL, show_spinner="Carregando evolução da operadora...")
def _evolucao(cd_operadora_ans: str) -> pd.DataFrame:
    return DatabaseConnection.query(
        """
        SELECT sk_tempo, competencia, qt_beneficiarios_ativos
        FROM rpt.vw_ranking_operadoras
        WHERE cd_operadora_ans = :cod
        ORDER BY sk_tempo
        """,
        {"cod": cd_operadora_ans},
    )


@st.cache_data(ttl=_TTL, show_spinner="Carregando participação por região...")
def _participacao_por_regiao(sk_tempo: int) -> pd.DataFrame:
    return DatabaseConnection.query(
        "SELECT * FROM rpt.vw_operadoras_por_regiao WHERE sk_tempo = :sk ORDER BY regiao, ranking_na_regiao",
        {"sk": sk_tempo},
    )


class OperatorRepository:
    """Camada de acesso a dados de operadoras - somente leitura via `rpt`."""

    @staticmethod
    def ranking(sk_tempo: int) -> pd.DataFrame:
        return _ranking(sk_tempo)

    @staticmethod
    def evolucao(cd_operadora_ans: str) -> pd.DataFrame:
        return _evolucao(cd_operadora_ans)

    @staticmethod
    def participacao_por_regiao(sk_tempo: int) -> pd.DataFrame:
        return _participacao_por_regiao(sk_tempo)
