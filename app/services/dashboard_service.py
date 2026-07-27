"""Servico de agregacao para a pagina 'Visao Executiva' - combina varios
repositorios em um unico conjunto de indicadores (KPIs), evitando que a
pagina Streamlit concentre logica de negocio (ver secao 14 do briefing:
"evitando concentrar regras de negocio na camada de visualizacao")."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
from app.repositories.base import DatabaseConnection
from app.repositories.beneficiary_repository import BeneficiaryRepository
from app.repositories.data_quality_repository import DataQualityRepository
from app.repositories.operator_repository import OperatorRepository
from src.config.settings import get_settings

import streamlit as st

_TTL = get_settings().streamlit_cache_ttl_seconds


@dataclass(frozen=True)
class ResumoExecutivo:
    total_beneficiarios: int
    total_estabelecimentos: int
    total_operadoras: int
    qt_estados_cobertos: int
    razao_beneficiarios_por_estabelecimento: float | None
    variacao_percentual_periodo_anterior: float | None
    ultima_atualizacao: pd.Timestamp | None
    status_ultima_execucao: str | None


@st.cache_data(ttl=_TTL, show_spinner=False)
def _resumo_mensal_uf(sk_tempo: int) -> pd.DataFrame:
    return DatabaseConnection.query(
        "SELECT * FROM rpt.tb_resumo_mensal_uf WHERE sk_tempo = :sk", {"sk": sk_tempo}
    )


class DashboardService:
    """Orquestra repositorios para produzir os indicadores da Visao Executiva."""

    @staticmethod
    def resumo_executivo(sk_tempo: int) -> ResumoExecutivo:
        resumo_uf = _resumo_mensal_uf(sk_tempo)
        operadoras = OperatorRepository.ranking(sk_tempo)
        evolucao = BeneficiaryRepository.evolucao_mensal()
        ultima_execucao = DataQualityRepository.ultima_execucao()

        total_beneficiarios = (
            int(resumo_uf["qt_beneficiarios_ativos"].sum()) if not resumo_uf.empty else 0
        )
        total_estabelecimentos = (
            int(resumo_uf["qt_estabelecimentos"].sum()) if not resumo_uf.empty else 0
        )
        razao = (
            round(total_beneficiarios / total_estabelecimentos, 2)
            if total_estabelecimentos
            else None
        )

        variacao = None
        linha_periodo = evolucao.loc[evolucao["sk_tempo"] == sk_tempo]
        if not linha_periodo.empty and pd.notna(linha_periodo.iloc[0]["variacao_percentual"]):
            variacao = float(linha_periodo.iloc[0]["variacao_percentual"])

        ultima_atualizacao = None
        status_execucao = None
        if not ultima_execucao.empty:
            ultima_atualizacao = ultima_execucao.iloc[0]["dh_fim"]
            status_execucao = ultima_execucao.iloc[0]["status"]

        return ResumoExecutivo(
            total_beneficiarios=total_beneficiarios,
            total_estabelecimentos=total_estabelecimentos,
            total_operadoras=(
                int(operadoras["cd_operadora_ans"].nunique()) if not operadoras.empty else 0
            ),
            qt_estados_cobertos=int(resumo_uf["cd_uf"].nunique()) if not resumo_uf.empty else 0,
            razao_beneficiarios_por_estabelecimento=razao,
            variacao_percentual_periodo_anterior=variacao,
            ultima_atualizacao=ultima_atualizacao,
            status_ultima_execucao=status_execucao,
        )

    @staticmethod
    def resumo_por_uf(sk_tempo: int) -> pd.DataFrame:
        return _resumo_mensal_uf(sk_tempo)
