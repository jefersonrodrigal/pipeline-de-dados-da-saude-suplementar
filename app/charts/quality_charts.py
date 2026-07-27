"""Graficos da pagina de Qualidade dos Dados."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
from app.charts.palette import CATEGORICAL, PLOTLY_LAYOUT_DEFAULTS, STATUS


def regras_mais_violadas(df: pd.DataFrame) -> go.Figure:
    ordered = df.sort_values("total_rejeitados")
    cores = [
        STATUS["critical"] if s == "ERROR" else STATUS["warning"] for s in ordered["severidade"]
    ]
    fig = go.Figure(
        go.Bar(
            x=ordered["total_rejeitados"],
            y=ordered["nm_regra"],
            orientation="h",
            marker=dict(color=cores),
            hovertemplate="%{y}<br>%{x:,.0f} registros rejeitados<extra></extra>",
        )
    )
    fig.update_layout(
        **PLOTLY_LAYOUT_DEFAULTS,
        showlegend=False,
        xaxis=dict(title="Registros rejeitados"),
        yaxis=dict(title=None),
    )
    return fig


def evolucao_status_execucoes(df: pd.DataFrame) -> go.Figure:
    status_cores = {
        "SUCCESS": STATUS["good"],
        "PARTIAL": STATUS["warning"],
        "FAILED": STATUS["critical"],
        "RUNNING": CATEGORICAL[0],
    }
    ordered = df.sort_values("dh_inicio")
    fig = go.Figure()
    for status, cor in status_cores.items():
        subset = ordered[ordered["status"] == status]
        if subset.empty:
            continue
        fig.add_trace(
            go.Scatter(
                x=subset["dh_inicio"],
                y=subset["duracao_segundos"],
                mode="markers",
                name=status,
                marker=dict(size=10, color=cor),
                hovertemplate="%{x}<br>%{y:.1f}s<extra></extra>",
            )
        )
    fig.update_layout(
        **PLOTLY_LAYOUT_DEFAULTS,
        yaxis=dict(title="Duração (segundos)"),
        xaxis=dict(title=None),
    )
    return fig


def percentual_aprovacao_por_execucao(df: pd.DataFrame) -> go.Figure:
    ordered = df.sort_values("dh_inicio")
    fig = go.Figure(
        go.Bar(
            x=ordered["dh_inicio"],
            y=ordered["percentual_aprovacao"],
            marker=dict(color=CATEGORICAL[2]),
            hovertemplate="%{x}<br>%{y:.1f}%% aprovados<extra></extra>",
        )
    )
    fig.update_layout(
        **PLOTLY_LAYOUT_DEFAULTS,
        showlegend=False,
        yaxis=dict(title="% aprovação", range=[0, 100]),
        xaxis=dict(title=None),
    )
    return fig
