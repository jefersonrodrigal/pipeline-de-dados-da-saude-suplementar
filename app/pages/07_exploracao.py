"""Pagina: Exploracao dos Dados.

Tabela livre sobre as views analiticas, com selecao de dataset, filtros
dinamicos, ordenacao, escolha de colunas, resumo estatistico e download em
CSV. O nome da view vem de uma lista fixa (nao de texto livre do usuario),
entao nao ha risco de injecao de SQL mesmo montando a consulta com o nome
do dataset.
"""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.repositories.base import DatabaseConnection, DatabaseUnavailableError  # noqa: E402
from src.config.settings import get_settings  # noqa: E402

st.set_page_config(page_title="Exploração dos Dados", page_icon="🏥", layout="wide")
st.title("Exploração dos Dados")
st.caption("Navegue livremente pelas views analíticas do Data Warehouse.")

_DATASETS = {
    "Evolução mensal de beneficiários": "vw_evolucao_mensal_beneficiarios",
    "Beneficiários por estado": "vw_beneficiarios_por_estado",
    "Beneficiários por município": "vw_beneficiarios_por_municipio",
    "Estabelecimentos por município": "vw_estabelecimentos_por_municipio",
    "Estabelecimentos por tipo": "vw_estabelecimentos_por_tipo",
    "Razão beneficiários/estabelecimento": "vw_razao_beneficiarios_estabelecimento",
    "Ranking de operadoras": "vw_ranking_operadoras",
    "Cobertura regional": "vw_cobertura_regional",
    "Variação percentual entre períodos": "vw_variacao_percentual_periodos",
    "Qualidade do pipeline": "vw_qualidade_pipeline",
    "Regras de qualidade": "vw_qualidade_regras",
    "Operadoras por região": "vw_operadoras_por_regiao",
}

MAX_LINHAS = 5_000  # limite de exibicao, independente do SQL_QUERY_ROW_LIMIT do banco

label = st.selectbox("Selecione o conjunto de dados", options=list(_DATASETS.keys()))
view_name = _DATASETS[label]

try:
    settings = get_settings()
    df = DatabaseConnection.query(
        f"SELECT * FROM rpt.{view_name}", row_limit=min(MAX_LINHAS, settings.sql_query_row_limit)
    )
except DatabaseUnavailableError as exc:
    st.error(str(exc), icon="🚫")
    st.stop()

if df.empty:
    st.info("Este conjunto de dados ainda não possui registros carregados.")
    st.stop()

st.caption(
    f"{len(df):,} linha(s) exibida(s) (limite de exibição: {MAX_LINHAS:,}).".replace(",", ".")
)

with st.expander("Filtros dinâmicos", expanded=False):
    colunas_filtraveis = [
        c for c in df.columns if df[c].dtype == object or str(df[c].dtype) == "string"
    ]
    filtros_ativos: dict[str, list] = {}
    for coluna in colunas_filtraveis[:5]:
        valores_unicos = sorted(df[coluna].dropna().unique().tolist())
        if 1 < len(valores_unicos) <= 200:
            selecionados = st.multiselect(
                f"{coluna}", options=valores_unicos, key=f"filtro_{coluna}"
            )
            if selecionados:
                filtros_ativos[coluna] = selecionados

for coluna, valores in filtros_ativos.items():
    df = df[df[coluna].isin(valores)]

colunas_selecionadas = st.multiselect(
    "Colunas exibidas", options=list(df.columns), default=list(df.columns)
)
coluna_ordenacao = st.selectbox("Ordenar por", options=colunas_selecionadas or list(df.columns))
ordem_crescente = st.checkbox("Ordem crescente", value=False)

df_exibido = df[colunas_selecionadas] if colunas_selecionadas else df
if coluna_ordenacao in df_exibido.columns:
    df_exibido = df_exibido.sort_values(coluna_ordenacao, ascending=ordem_crescente)

st.dataframe(df_exibido, width="stretch", hide_index=True)

st.download_button(
    "⬇️ Baixar CSV (dados filtrados)",
    data=df_exibido.to_csv(index=False).encode("utf-8-sig"),
    file_name=f"{view_name}.csv",
    mime="text/csv",
)

with st.expander("Resumo estatístico"):
    # .astype(str): describe(include="all") mistura tipos na mesma coluna
    # (contagens numericas e valores categoricos como "top"/"freq"), o que
    # quebra a conversao para Arrow usada pelo st.dataframe.
    st.dataframe(df_exibido.describe(include="all").transpose().astype(str), width="stretch")
