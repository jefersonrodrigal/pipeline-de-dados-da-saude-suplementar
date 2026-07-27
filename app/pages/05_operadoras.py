"""Pagina: Operadoras."""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.charts.operator_charts import (  # noqa: E402
    evolucao_operadora,
    participacao_por_regiao,
    ranking_operadoras,
)
from app.components.filters import select_periodo  # noqa: E402
from app.repositories.base import DatabaseUnavailableError  # noqa: E402
from app.repositories.operator_repository import OperatorRepository  # noqa: E402

st.set_page_config(page_title="Operadoras", page_icon="🏥", layout="wide")
st.title("Operadoras")
st.caption("Ranking, evolução e participação regional das operadoras de planos de saúde.")

with st.sidebar:
    st.header("Filtros")
    sk_tempo = select_periodo()

if sk_tempo is None:
    st.stop()

try:
    ranking = OperatorRepository.ranking(sk_tempo)
    participacao_regiao = OperatorRepository.participacao_por_regiao(sk_tempo)
except DatabaseUnavailableError as exc:
    st.error(str(exc), icon="🚫")
    st.stop()

if ranking.empty:
    st.info("Nenhuma operadora com beneficiários nesta competência.")
    st.stop()

st.subheader("Ranking de operadoras")
st.plotly_chart(ranking_operadoras(ranking), width="stretch")

st.subheader("Concentração de mercado")
top5_participacao = ranking.nsmallest(5, "ranking_operadora")["participacao_percentual"].sum()
col1, col2 = st.columns(2)
col1.metric("Participação das 5 maiores operadoras", f"{top5_participacao:.1f}%")
col2.metric("Total de operadoras com beneficiários", f"{ranking['cd_operadora_ans'].nunique()}")

st.subheader("Participação por região (operadora líder)")
if participacao_regiao.empty:
    st.info("Sem dados de participação regional.")
else:
    st.plotly_chart(participacao_por_regiao(participacao_regiao), width="stretch")

st.subheader("Evolução de uma operadora específica")
opcoes = dict(zip(ranking["cd_operadora_ans"], ranking["nm_razao_social"], strict=True))
cd_operadora = st.selectbox(
    "Selecione a operadora", options=list(opcoes.keys()), format_func=lambda c: opcoes.get(c, c)
)
if cd_operadora:
    evolucao_df = OperatorRepository.evolucao(cd_operadora)
    if evolucao_df.empty:
        st.info("Sem histórico suficiente para esta operadora.")
    else:
        st.plotly_chart(evolucao_operadora(evolucao_df), width="stretch")
