"""Pagina: Qualidade dos Dados."""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.charts.quality_charts import (  # noqa: E402
    evolucao_status_execucoes,
    percentual_aprovacao_por_execucao,
    regras_mais_violadas,
)
from app.repositories.base import DatabaseUnavailableError  # noqa: E402
from app.repositories.data_quality_repository import DataQualityRepository  # noqa: E402
from app.utils.formatting import format_datetime, format_int, format_percent

st.set_page_config(page_title="Qualidade dos Dados", page_icon="🏥", layout="wide")
st.title("Qualidade dos Dados")
st.caption("Auditoria e histórico de execução do pipeline de dados.")

col_refresh, _ = st.columns([1, 5])
if col_refresh.button(
    "🔄 Atualizar dados", help="Limpa o cache e busca os dados mais recentes do banco"
):
    st.cache_data.clear()
    st.rerun()

try:
    resumo = DataQualityRepository.resumo_geral()
    historico = DataQualityRepository.historico_execucoes()
    regras = DataQualityRepository.regras_mais_violadas()
except DatabaseUnavailableError as exc:
    st.error(str(exc), icon="🚫")
    st.stop()

if not resumo.empty:
    linha = resumo.iloc[0]
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Registros processados", format_int(linha["total_recebido"]))
    col2.metric("Registros aceitos", format_int(linha["total_valido"]))
    col3.metric("Registros rejeitados", format_int(linha["total_rejeitado"]))
    percentual = (
        (linha["total_valido"] / linha["total_recebido"] * 100) if linha["total_recebido"] else None
    )
    col4.metric("% de aprovação", format_percent(percentual))
    st.caption(f"Última atualização considerada: {format_datetime(linha['ultima_atualizacao'])}")

st.divider()
tab_historico, tab_regras = st.tabs(["Histórico de execuções", "Regras mais violadas"])

with tab_historico:
    if historico.empty:
        st.info("Nenhuma execução registrada ainda.")
    else:
        st.plotly_chart(evolucao_status_execucoes(historico), width="stretch")
        st.plotly_chart(
            percentual_aprovacao_por_execucao(historico.dropna(subset=["percentual_aprovacao"])),
            width="stretch",
        )
        st.dataframe(
            historico[
                [
                    "nm_etapa",
                    "fonte",
                    "status",
                    "dh_inicio",
                    "dh_fim",
                    "duracao_segundos",
                    "qt_recebida",
                    "qt_valida",
                    "qt_rejeitada",
                    "periodo_referencia",
                ]
            ].rename(
                columns={
                    "nm_etapa": "Etapa",
                    "fonte": "Fonte",
                    "status": "Status",
                    "dh_inicio": "Início",
                    "dh_fim": "Fim",
                    "duracao_segundos": "Duração (s)",
                    "qt_recebida": "Recebidos",
                    "qt_valida": "Válidos",
                    "qt_rejeitada": "Rejeitados",
                    "periodo_referencia": "Competência",
                }
            ),
            width="stretch",
            hide_index=True,
        )

with tab_regras:
    if regras.empty:
        st.info("Nenhuma regra de qualidade avaliada ainda.")
    else:
        st.plotly_chart(regras_mais_violadas(regras), width="stretch")
        st.dataframe(
            regras.rename(
                columns={
                    "nm_regra": "Regra",
                    "ds_regra": "Descrição",
                    "severidade": "Severidade",
                    "total_rejeitados": "Total rejeitado",
                    "total_avaliado": "Total avaliado",
                }
            ),
            width="stretch",
            hide_index=True,
        )
