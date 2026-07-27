"""Cards de indicadores (st.metric) reutilizados pelas paginas."""

from __future__ import annotations

from app.services.dashboard_service import ResumoExecutivo
from app.utils.formatting import format_datetime, format_decimal, format_int, format_percent

import streamlit as st


def render_resumo_executivo(resumo: ResumoExecutivo) -> None:
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Beneficiários ativos", format_int(resumo.total_beneficiarios))
    col2.metric("Estabelecimentos de saúde", format_int(resumo.total_estabelecimentos))
    col3.metric("Operadoras com beneficiários", format_int(resumo.total_operadoras))
    col4.metric("Estados cobertos", format_int(resumo.qt_estados_cobertos))

    col5, col6, col7 = st.columns(3)
    col5.metric(
        "Beneficiários por estabelecimento",
        format_decimal(resumo.razao_beneficiarios_por_estabelecimento, 1),
    )
    col6.metric(
        "Variação vs. período anterior",
        format_percent(resumo.variacao_percentual_periodo_anterior),
    )
    col7.metric("Status da última execução", resumo.status_ultima_execucao or "sem dados")

    st.caption(f"Última atualização do pipeline: {format_datetime(resumo.ultima_atualizacao)}")
