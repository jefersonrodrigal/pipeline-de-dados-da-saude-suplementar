"""Graficos da pagina de Operadoras."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
from app.charts.palette import CATEGORICAL, PLOTLY_LAYOUT_DEFAULTS


def ranking_operadoras(df: pd.DataFrame, top_n: int = 15) -> go.Figure:
    top = df.nsmallest(top_n, "ranking_operadora").sort_values("qt_beneficiarios_ativos")
    fig = go.Figure(
        go.Bar(
            x=top["qt_beneficiarios_ativos"],
            y=top["nm_razao_social"],
            orientation="h",
            marker=dict(color=CATEGORICAL[0]),
            hovertemplate="%{y}<br>%{x:,.0f} beneficiários (%{customdata:.1f}% do total)<extra></extra>",
            customdata=top["participacao_percentual"],
        )
    )
    fig.update_layout(
        **PLOTLY_LAYOUT_DEFAULTS,
        showlegend=False,
        xaxis=dict(title="Beneficiários ativos"),
        yaxis=dict(title=None),
    )
    return fig


def evolucao_operadora(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure(
        go.Scatter(
            x=df["sk_tempo"].astype(str),
            y=df["qt_beneficiarios_ativos"],
            mode="lines+markers",
            line=dict(color=CATEGORICAL[0], width=2),
            marker=dict(size=8),
            hovertemplate="%{x}<br>%{y:,.0f} beneficiários<extra></extra>",
        )
    )
    fig.update_layout(
        **PLOTLY_LAYOUT_DEFAULTS,
        showlegend=False,
        yaxis=dict(title="Beneficiários ativos"),
        xaxis=dict(title=None),
    )
    return fig


def participacao_por_regiao(df: pd.DataFrame, top_n_por_regiao: int = 1) -> go.Figure:
    """Top N operadoras dentro de cada regiao - pequenos multiplos (barras
    agrupadas por regiao), nunca um dashboard de pizza por regiao."""
    top = df[df["ranking_na_regiao"] <= top_n_por_regiao].copy()
    regioes = sorted(top["regiao"].unique())

    fig = go.Figure()
    for idx, operadora in enumerate(sorted(top["nm_razao_social"].unique())[: len(CATEGORICAL)]):
        subset = top[top["nm_razao_social"] == operadora]
        fig.add_trace(
            go.Bar(
                x=subset["regiao"],
                y=subset["qt_beneficiarios_ativos"],
                name=operadora,
                marker=dict(color=CATEGORICAL[idx % len(CATEGORICAL)]),
                hovertemplate="%{x}<br>" + operadora + ": %{y:,.0f}<extra></extra>",
            )
        )
    fig.update_layout(
        **PLOTLY_LAYOUT_DEFAULTS,
        barmode="group",
        xaxis=dict(title=None, categoryorder="array", categoryarray=regioes),
        yaxis=dict(title="Beneficiários ativos"),
    )
    return fig
