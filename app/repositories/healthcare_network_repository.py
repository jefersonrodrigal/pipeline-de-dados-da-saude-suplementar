"""Consultas de rede assistencial (estabelecimentos, cobertura regional)."""

from __future__ import annotations

import pandas as pd
from app.repositories.base import DatabaseConnection
from src.config.settings import get_settings

import streamlit as st

_TTL = get_settings().streamlit_cache_ttl_seconds


@st.cache_data(ttl=_TTL, show_spinner="Carregando estabelecimentos por município...")
def _por_municipio(sk_tempo: int, cd_uf: str | None) -> pd.DataFrame:
    sql = "SELECT * FROM rpt.vw_estabelecimentos_por_municipio WHERE sk_tempo = :sk"
    params: dict = {"sk": sk_tempo}
    if cd_uf:
        sql += " AND cd_uf = :uf"
        params["uf"] = cd_uf
    sql += " ORDER BY qt_estabelecimentos DESC"
    return DatabaseConnection.query(sql, params)


@st.cache_data(ttl=_TTL, show_spinner="Carregando estabelecimentos por tipo...")
def _por_tipo(sk_tempo: int) -> pd.DataFrame:
    return DatabaseConnection.query(
        "SELECT * FROM rpt.vw_estabelecimentos_por_tipo WHERE sk_tempo = :sk ORDER BY qt_estabelecimentos DESC",
        {"sk": sk_tempo},
    )


@st.cache_data(ttl=_TTL, show_spinner="Calculando razão beneficiários/estabelecimento...")
def _razao_beneficiarios_estabelecimento(sk_tempo: int, cd_uf: str | None) -> pd.DataFrame:
    sql = "SELECT * FROM rpt.vw_razao_beneficiarios_estabelecimento WHERE sk_tempo = :sk"
    params: dict = {"sk": sk_tempo}
    if cd_uf:
        sql += " AND cd_uf = :uf"
        params["uf"] = cd_uf
    return DatabaseConnection.query(sql, params)


@st.cache_data(ttl=_TTL, show_spinner="Calculando cobertura regional...")
def _cobertura_regional(sk_tempo: int, cd_uf: str | None) -> pd.DataFrame:
    sql = "SELECT * FROM rpt.vw_cobertura_regional WHERE sk_tempo = :sk"
    params: dict = {"sk": sk_tempo}
    if cd_uf:
        sql += " AND cd_uf = :uf"
        params["uf"] = cd_uf
    return DatabaseConnection.query(sql, params)


class HealthcareNetworkRepository:
    """Camada de acesso a dados de rede assistencial - somente leitura via `rpt`."""

    @staticmethod
    def por_municipio(sk_tempo: int, cd_uf: str | None = None) -> pd.DataFrame:
        return _por_municipio(sk_tempo, cd_uf)

    @staticmethod
    def por_tipo(sk_tempo: int) -> pd.DataFrame:
        return _por_tipo(sk_tempo)

    @staticmethod
    def razao_beneficiarios_estabelecimento(
        sk_tempo: int, cd_uf: str | None = None
    ) -> pd.DataFrame:
        return _razao_beneficiarios_estabelecimento(sk_tempo, cd_uf)

    @staticmethod
    def cobertura_regional(sk_tempo: int, cd_uf: str | None = None) -> pd.DataFrame:
        return _cobertura_regional(sk_tempo, cd_uf)
