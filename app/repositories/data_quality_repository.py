"""Consultas de qualidade de dados e historico de execucao do pipeline."""

from __future__ import annotations

import pandas as pd
from app.repositories.base import DatabaseConnection
from src.config.settings import get_settings

import streamlit as st

_TTL = get_settings().streamlit_cache_ttl_seconds


@st.cache_data(ttl=_TTL, show_spinner="Carregando histórico de execuções...")
def _historico_execucoes(limite: int) -> pd.DataFrame:
    return DatabaseConnection.query(
        "SELECT TOP (:limite) * FROM rpt.vw_qualidade_pipeline ORDER BY dh_inicio DESC",
        {"limite": limite},
    )


@st.cache_data(ttl=_TTL, show_spinner="Carregando regras de qualidade...")
def _regras_mais_violadas(limite: int) -> pd.DataFrame:
    return DatabaseConnection.query(
        """
        SELECT TOP (:limite) nm_regra, ds_regra, severidade,
               SUM(qt_rejeitada) AS total_rejeitados,
               SUM(qt_avaliada) AS total_avaliado
        FROM rpt.vw_qualidade_regras
        GROUP BY nm_regra, ds_regra, severidade
        ORDER BY total_rejeitados DESC
        """,
        {"limite": limite},
    )


@st.cache_data(ttl=_TTL, show_spinner=False)
def _resumo_geral() -> pd.DataFrame:
    return DatabaseConnection.query("""
        SELECT
            SUM(qt_recebida) AS total_recebido,
            SUM(qt_valida) AS total_valido,
            SUM(qt_rejeitada) AS total_rejeitado,
            MAX(dh_fim) AS ultima_atualizacao
        FROM rpt.vw_qualidade_pipeline
        WHERE nm_etapa = 'validate_trusted'
        """)


@st.cache_data(ttl=_TTL, show_spinner=False)
def _ultima_execucao() -> pd.DataFrame:
    return DatabaseConnection.query(
        "SELECT TOP (1) * FROM rpt.vw_qualidade_pipeline WHERE nm_etapa = 'load' ORDER BY dh_inicio DESC"
    )


class DataQualityRepository:
    """Camada de acesso a dados de qualidade/auditoria - somente leitura via `rpt`."""

    @staticmethod
    def historico_execucoes(limite: int = 200) -> pd.DataFrame:
        return _historico_execucoes(limite)

    @staticmethod
    def regras_mais_violadas(limite: int = 10) -> pd.DataFrame:
        return _regras_mais_violadas(limite)

    @staticmethod
    def resumo_geral() -> pd.DataFrame:
        return _resumo_geral()

    @staticmethod
    def ultima_execucao() -> pd.DataFrame:
        return _ultima_execucao()
