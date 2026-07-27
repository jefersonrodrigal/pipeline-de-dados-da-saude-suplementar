"""Pagina: Cobertura Regional."""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.charts.coverage_charts import (  # noqa: E402
    distribuicao_classificacao,
    ranking_risco_municipios,
)
from app.components.filters import (  # noqa: E402
    active_filters_caption,
    select_estado,
    select_periodo,
)
from app.components.status_badges import badge_label, render_coverage_disclaimer  # noqa: E402
from app.repositories.base import DatabaseUnavailableError  # noqa: E402
from app.repositories.beneficiary_repository import BeneficiaryRepository  # noqa: E402
from app.repositories.healthcare_network_repository import HealthcareNetworkRepository  # noqa: E402

st.set_page_config(page_title="Cobertura Regional", page_icon="🏥", layout="wide")
st.title("Cobertura Regional")
st.caption("Índice exploratório de cobertura assistencial por município.")
render_coverage_disclaimer()

with st.sidebar:
    st.header("Filtros")
    sk_tempo = select_periodo()
    cd_uf = select_estado()

if sk_tempo is None:
    st.stop()

estados = BeneficiaryRepository.estados_disponiveis()
uf_label = None
if cd_uf:
    match = estados.loc[estados["cd_uf"] == cd_uf, "nm_uf"]
    uf_label = match.iloc[0] if not match.empty else cd_uf
active_filters_caption(str(sk_tempo), uf_label)

try:
    cobertura = HealthcareNetworkRepository.cobertura_regional(sk_tempo, cd_uf)
except DatabaseUnavailableError as exc:
    st.error(str(exc), icon="🚫")
    st.stop()

if cobertura.empty:
    st.info("Sem dados de cobertura para os filtros selecionados.")
    st.stop()

st.subheader("Distribuição das classificações")
st.plotly_chart(distribuicao_classificacao(cobertura), width="stretch")

st.subheader("Municípios com maior razão beneficiários/estabelecimento")
st.plotly_chart(ranking_risco_municipios(cobertura), width="stretch")

st.subheader("Detalhamento por município")
tabela = cobertura[
    [
        "nm_municipio",
        "nm_uf",
        "regiao",
        "qt_beneficiarios_ativos",
        "qt_estabelecimentos",
        "beneficiarios_por_estabelecimento",
        "classificacao_cobertura",
    ]
].copy()
tabela["classificacao_cobertura"] = tabela["classificacao_cobertura"].map(badge_label)
st.dataframe(
    tabela.rename(
        columns={
            "nm_municipio": "Município",
            "nm_uf": "UF",
            "regiao": "Região",
            "qt_beneficiarios_ativos": "Beneficiários",
            "qt_estabelecimentos": "Estabelecimentos",
            "beneficiarios_por_estabelecimento": "Benef./Estab.",
            "classificacao_cobertura": "Classificação",
        }
    ),
    width="stretch",
    hide_index=True,
)
