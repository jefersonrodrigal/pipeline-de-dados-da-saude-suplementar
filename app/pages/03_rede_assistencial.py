"""Pagina: Rede Assistencial."""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.charts.network_charts import (  # noqa: E402
    estabelecimentos_por_estado,
    estabelecimentos_por_tipo,
    razao_beneficiarios_estabelecimento,
)
from app.components.filters import (  # noqa: E402
    active_filters_caption,
    select_estado,
    select_periodo,
)
from app.repositories.base import DatabaseUnavailableError  # noqa: E402
from app.repositories.beneficiary_repository import BeneficiaryRepository  # noqa: E402
from app.repositories.healthcare_network_repository import HealthcareNetworkRepository  # noqa: E402
from app.utils.formatting import format_int

st.set_page_config(page_title="Rede Assistencial", page_icon="🏥", layout="wide")
st.title("Rede Assistencial")
st.caption("Distribuição dos estabelecimentos de saúde por tipo, estado e município.")

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
    por_municipio = HealthcareNetworkRepository.por_municipio(sk_tempo, cd_uf)
    por_tipo = HealthcareNetworkRepository.por_tipo(sk_tempo)
    razao = HealthcareNetworkRepository.razao_beneficiarios_estabelecimento(sk_tempo, cd_uf)
except DatabaseUnavailableError as exc:
    st.error(str(exc), icon="🚫")
    st.stop()

if por_municipio.empty and por_tipo.empty:
    st.info(
        "Nenhum estabelecimento carregado ainda. Este projeto inclui um "
        "arquivo de demonstração fictício para o CNES - rode "
        "`python -m src.main --stage all --source cnes` para carregá-lo, "
        "ou substitua por um export real (ver data/raw/cnes/incoming/README.md)."
    )
    st.stop()

col1, col2 = st.columns(2)
col1.metric(
    "Total de estabelecimentos (filtro atual)",
    format_int(por_municipio["qt_estabelecimentos"].sum()),
)
col2.metric(
    "Municípios com rede cadastrada", format_int(por_municipio["cd_municipio_ibge"].nunique())
)

tab_tipo, tab_geografia, tab_razao = st.tabs(
    ["Por tipo", "Por estado/município", "Razão beneficiários/estabelecimento"]
)

with tab_tipo:
    if por_tipo.empty:
        st.info("Sem estabelecimentos classificados por tipo.")
    else:
        st.plotly_chart(estabelecimentos_por_tipo(por_tipo), width="stretch")

with tab_geografia:
    if por_municipio.empty:
        st.info("Sem estabelecimentos para os filtros selecionados.")
    else:
        if cd_uf is None:
            st.plotly_chart(estabelecimentos_por_estado(por_municipio), width="stretch")
        st.dataframe(
            por_municipio[["nm_municipio", "nm_uf", "regiao", "qt_estabelecimentos"]],
            width="stretch",
            hide_index=True,
        )

with tab_razao:
    if razao.empty:
        st.info("Sem dados para calcular a razão beneficiários/estabelecimento.")
    else:
        st.plotly_chart(razao_beneficiarios_estabelecimento(razao), width="stretch")
        sem_cobertura = razao[razao["qt_estabelecimentos"] == 0]
        if not sem_cobertura.empty:
            st.warning(
                f"{len(sem_cobertura)} município(s) com beneficiários mas ZERO "
                f"estabelecimentos cadastrados na competência selecionada - "
                f"possível lacuna de atendimento (ver página Cobertura Regional)."
            )
