"""Pagina: Visao Executiva."""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.charts.beneficiary_charts import (  # noqa: E402
    evolucao_mensal_beneficiarios,
    ranking_por_estado,
)
from app.components.filters import select_periodo  # noqa: E402
from app.components.kpi_cards import render_resumo_executivo  # noqa: E402
from app.repositories.base import DatabaseUnavailableError  # noqa: E402
from app.repositories.beneficiary_repository import BeneficiaryRepository  # noqa: E402
from app.services.dashboard_service import DashboardService  # noqa: E402

st.set_page_config(page_title="Visão Executiva", page_icon="🏥", layout="wide")
st.title("Visão Executiva")
st.caption("Indicadores gerais da rede de saúde suplementar e evolução temporal.")

sk_tempo = select_periodo()
if sk_tempo is None:
    st.stop()

try:
    with st.spinner("Calculando indicadores..."):
        resumo = DashboardService.resumo_executivo(sk_tempo)
        evolucao = BeneficiaryRepository.evolucao_mensal()
        por_estado = BeneficiaryRepository.por_estado(sk_tempo)
except DatabaseUnavailableError as exc:
    st.error(str(exc), icon="🚫")
    st.stop()

render_resumo_executivo(resumo)

st.divider()
col_evolucao, col_ranking = st.columns(2)
with col_evolucao:
    st.subheader("Evolução mensal de beneficiários")
    if evolucao.empty:
        st.info("Sem dados suficientes para exibir a evolução temporal.")
    else:
        st.plotly_chart(evolucao_mensal_beneficiarios(evolucao), width="stretch")

with col_ranking:
    st.subheader("Ranking de estados")
    if por_estado.empty:
        st.info("Sem beneficiários carregados para esta competência.")
    else:
        st.plotly_chart(ranking_por_estado(por_estado), width="stretch")

st.caption(
    "Mapa geográfico não incluído nesta versão: os dados de beneficiários da "
    "ANS não trazem coordenadas geográficas, e georreferenciar ~5.500 "
    "municípios de forma confiável exigiria uma base IBGE adicional fora do "
    "escopo deste projeto. O ranking por estado acima cumpre o mesmo papel "
    "analítico de localizar concentração geográfica."
)
