"""Pagina: Beneficiarios."""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.charts.beneficiary_charts import (  # noqa: E402
    distribuicao_por_municipio,
    evolucao_mensal_beneficiarios,
)
from app.components.filters import (  # noqa: E402
    active_filters_caption,
    select_estado,
    select_periodo,
)
from app.repositories.base import DatabaseUnavailableError  # noqa: E402
from app.repositories.beneficiary_repository import BeneficiaryRepository  # noqa: E402
from app.utils.formatting import format_int, format_percent

st.set_page_config(page_title="Beneficiários", page_icon="🏥", layout="wide")
st.title("Beneficiários")
st.caption("Evolução, distribuição geográfica e participação por operadora.")

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
    evolucao = BeneficiaryRepository.evolucao_mensal()
    por_municipio = BeneficiaryRepository.por_municipio(sk_tempo, cd_uf)
    por_operadora = BeneficiaryRepository.por_operadora(sk_tempo)
except DatabaseUnavailableError as exc:
    st.error(str(exc), icon="🚫")
    st.stop()

tab_evolucao, tab_geografia, tab_operadoras = st.tabs(
    ["Evolução mensal", "Distribuição geográfica", "Participação por operadora"]
)

with tab_evolucao:
    if evolucao.empty:
        st.info("Sem dados de evolução disponíveis.")
    else:
        st.plotly_chart(evolucao_mensal_beneficiarios(evolucao), width="stretch")
        linha_atual = evolucao.loc[evolucao["sk_tempo"] == sk_tempo]
        if not linha_atual.empty:
            col1, col2 = st.columns(2)
            col1.metric(
                "Crescimento absoluto (vs. mês anterior)",
                format_int(linha_atual.iloc[0]["variacao_absoluta"]),
            )
            col2.metric(
                "Crescimento percentual", format_percent(linha_atual.iloc[0]["variacao_percentual"])
            )

with tab_geografia:
    if por_municipio.empty:
        st.info("Nenhum beneficiário encontrado para os filtros selecionados.")
    else:
        st.plotly_chart(distribuicao_por_municipio(por_municipio), width="stretch")
        st.dataframe(
            por_municipio[["nm_municipio", "nm_uf", "regiao", "qt_beneficiarios_ativos"]],
            width="stretch",
            hide_index=True,
        )

with tab_operadoras:
    if por_operadora.empty:
        st.info("Nenhuma operadora com beneficiários nesta competência.")
    else:
        st.dataframe(
            por_operadora[
                [
                    "nm_razao_social",
                    "modalidade",
                    "qt_beneficiarios_ativos",
                    "participacao_percentual",
                    "ranking_operadora",
                ]
            ].rename(
                columns={
                    "nm_razao_social": "Operadora",
                    "modalidade": "Modalidade",
                    "qt_beneficiarios_ativos": "Beneficiários",
                    "participacao_percentual": "Participação (%)",
                    "ranking_operadora": "Ranking",
                }
            ),
            width="stretch",
            hide_index=True,
        )
