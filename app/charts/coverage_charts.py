"""Graficos da pagina de Cobertura Regional."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
from app.charts.palette import COBERTURA_STATUS, PLOTLY_LAYOUT_DEFAULTS


def distribuicao_classificacao(df: pd.DataFrame) -> go.Figure:
    contagem = (
        df["classificacao_cobertura"]
        .value_counts()
        .reindex(["Cobertura adequada", "Atenção", "Cobertura crítica"])
        .fillna(0)
    )
    fig = go.Figure(
        go.Bar(
            x=contagem.index,
            y=contagem.values,
            marker=dict(color=[COBERTURA_STATUS[c] for c in contagem.index]),
            hovertemplate="%{x}<br>%{y:.0f} municípios<extra></extra>",
        )
    )
    fig.update_layout(
        **PLOTLY_LAYOUT_DEFAULTS,
        showlegend=False,
        yaxis=dict(title="Municípios"),
        xaxis=dict(title=None),
    )
    return fig


def ranking_risco_municipios(df: pd.DataFrame, top_n: int = 20) -> go.Figure:
    valid = df.dropna(subset=["beneficiarios_por_estabelecimento"])
    top = valid.nlargest(top_n, "beneficiarios_por_estabelecimento").sort_values(
        "beneficiarios_por_estabelecimento"
    )
    cores = [COBERTURA_STATUS.get(c, "#898781") for c in top["classificacao_cobertura"]]
    fig = go.Figure(
        go.Bar(
            x=top["beneficiarios_por_estabelecimento"],
            y=top["nm_municipio"] + " / " + top["cd_uf"],
            orientation="h",
            marker=dict(color=cores),
            hovertemplate="%{y}<br>%{x:,.1f} beneficiários por estabelecimento<extra></extra>",
        )
    )
    fig.update_layout(
        **PLOTLY_LAYOUT_DEFAULTS,
        showlegend=False,
        xaxis=dict(title="Beneficiários por estabelecimento"),
        yaxis=dict(title=None),
    )
    return fig
