"""Graficos da pagina de Beneficiarios (e usados tambem na Visao Executiva)."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
from app.charts.palette import CATEGORICAL, PLOTLY_LAYOUT_DEFAULTS


def evolucao_mensal_beneficiarios(df: pd.DataFrame) -> go.Figure:
    """Linha unica (uma serie -> sem necessidade de legenda, o titulo ja identifica)."""
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df["ano_mes_extenso"],
            y=df["qt_beneficiarios_ativos"],
            mode="lines+markers",
            line=dict(color=CATEGORICAL[0], width=2),
            marker=dict(size=8, color=CATEGORICAL[0]),
            hovertemplate="%{x}<br>%{y:,.0f} beneficiários<extra></extra>",
            name="Beneficiários ativos",
        )
    )
    fig.update_layout(
        **PLOTLY_LAYOUT_DEFAULTS,
        showlegend=False,
        yaxis=dict(title="Beneficiários ativos", gridcolor="#e1e0d9"),
        xaxis=dict(title=None),
    )
    return fig


def ranking_por_estado(df: pd.DataFrame, top_n: int = 15) -> go.Figure:
    top = df.nsmallest(top_n, "ranking_estado").sort_values("qt_beneficiarios_ativos")
    fig = go.Figure(
        go.Bar(
            x=top["qt_beneficiarios_ativos"],
            y=top["nm_uf"],
            orientation="h",
            marker=dict(color=CATEGORICAL[0]),
            hovertemplate="%{y}<br>%{x:,.0f} beneficiários<extra></extra>",
        )
    )
    fig.update_layout(
        **PLOTLY_LAYOUT_DEFAULTS,
        showlegend=False,
        xaxis=dict(title="Beneficiários ativos"),
        yaxis=dict(title=None),
    )
    return fig


def distribuicao_por_municipio(df: pd.DataFrame, top_n: int = 20) -> go.Figure:
    top = df.nlargest(top_n, "qt_beneficiarios_ativos").sort_values("qt_beneficiarios_ativos")
    fig = go.Figure(
        go.Bar(
            x=top["qt_beneficiarios_ativos"],
            y=top["nm_municipio"] + " / " + top["cd_uf"],
            orientation="h",
            marker=dict(color=CATEGORICAL[0]),
            hovertemplate="%{y}<br>%{x:,.0f} beneficiários<extra></extra>",
        )
    )
    fig.update_layout(
        **PLOTLY_LAYOUT_DEFAULTS,
        showlegend=False,
        xaxis=dict(title="Beneficiários ativos"),
        yaxis=dict(title=None),
    )
    return fig
