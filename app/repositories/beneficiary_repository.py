"""Consultas de beneficiarios (rpt.vw_evolucao_mensal_beneficiarios,
rpt.vw_beneficiarios_por_estado, rpt.vw_beneficiarios_por_municipio,
rpt.vw_ranking_operadoras)."""

from __future__ import annotations

import pandas as pd
from app.repositories.base import DatabaseConnection
from src.config.settings import get_settings

import streamlit as st

_TTL = get_settings().streamlit_cache_ttl_seconds


@st.cache_data(ttl=_TTL, show_spinner="Carregando evolução de beneficiários...")
def _evolucao_mensal() -> pd.DataFrame:
    return DatabaseConnection.query(
        "SELECT * FROM rpt.vw_evolucao_mensal_beneficiarios ORDER BY sk_tempo"
    )


@st.cache_data(ttl=_TTL, show_spinner="Carregando beneficiários por estado...")
def _por_estado(sk_tempo: int) -> pd.DataFrame:
    return DatabaseConnection.query(
        "SELECT * FROM rpt.vw_beneficiarios_por_estado WHERE sk_tempo = :sk ORDER BY ranking_estado",
        {"sk": sk_tempo},
    )


@st.cache_data(ttl=_TTL, show_spinner="Carregando beneficiários por município...")
def _por_municipio(sk_tempo: int, cd_uf: str | None) -> pd.DataFrame:
    sql = "SELECT * FROM rpt.vw_beneficiarios_por_municipio WHERE sk_tempo = :sk"
    params: dict = {"sk": sk_tempo}
    if cd_uf:
        sql += " AND cd_uf = :uf"
        params["uf"] = cd_uf
    sql += " ORDER BY qt_beneficiarios_ativos DESC"
    return DatabaseConnection.query(sql, params)


@st.cache_data(ttl=_TTL, show_spinner="Carregando distribuição por operadora...")
def _por_operadora(sk_tempo: int) -> pd.DataFrame:
    return DatabaseConnection.query(
        "SELECT * FROM rpt.vw_ranking_operadoras WHERE sk_tempo = :sk ORDER BY ranking_operadora",
        {"sk": sk_tempo},
    )


@st.cache_data(ttl=_TTL, show_spinner=False)
def _periodos_disponiveis() -> pd.DataFrame:
    return DatabaseConnection.query(
        "SELECT DISTINCT sk_tempo, ano_mes_extenso FROM rpt.vw_evolucao_mensal_beneficiarios ORDER BY sk_tempo DESC"
    )


@st.cache_data(ttl=_TTL, show_spinner=False)
def _estados_disponiveis() -> pd.DataFrame:
    return DatabaseConnection.query(
        "SELECT DISTINCT cd_uf, nm_uf FROM rpt.vw_beneficiarios_por_estado ORDER BY nm_uf"
    )


class BeneficiaryRepository:
    """Camada de acesso a dados de beneficiarios - somente leitura via `rpt`."""

    @staticmethod
    def evolucao_mensal() -> pd.DataFrame:
        return _evolucao_mensal()

    @staticmethod
    def por_estado(sk_tempo: int) -> pd.DataFrame:
        return _por_estado(sk_tempo)

    @staticmethod
    def por_municipio(sk_tempo: int, cd_uf: str | None = None) -> pd.DataFrame:
        return _por_municipio(sk_tempo, cd_uf)

    @staticmethod
    def por_operadora(sk_tempo: int) -> pd.DataFrame:
        return _por_operadora(sk_tempo)

    @staticmethod
    def periodos_disponiveis() -> pd.DataFrame:
        return _periodos_disponiveis()

    @staticmethod
    def estados_disponiveis() -> pd.DataFrame:
        return _estados_disponiveis()
