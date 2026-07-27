"""Graficos da pagina de Rede Assistencial."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
from app.charts.palette import CATEGORICAL, PLOTLY_LAYOUT_DEFAULTS


def estabelecimentos_por_tipo(df: pd.DataFrame) -> go.Figure:
    ordered = df.sort_values("qt_estabelecimentos")
    fig = go.Figure(
        go.Bar(
            x=ordered["qt_estabelecimentos"],
            y=ordered["ds_tipo_estabelecimento"],
            orientation="h",
            marker=dict(color=CATEGORICAL[2]),
            hovertemplate="%{y}<br>%{x:,.0f} estabelecimentos<extra></extra>",
        )
    )
    fig.update_layout(
        **PLOTLY_LAYOUT_DEFAULTS,
        showlegend=False,
        xaxis=dict(title="Estabelecimentos"),
        yaxis=dict(title=None),
    )
    return fig


def razao_beneficiarios_estabelecimento(df: pd.DataFrame, top_n: int = 20) -> go.Figure:
    valid = df.dropna(subset=["beneficiarios_por_estabelecimento"])
    top = valid.nlargest(top_n, "beneficiarios_por_estabelecimento").sort_values(
        "beneficiarios_por_estabelecimento"
    )
    fig = go.Figure(
        go.Bar(
            x=top["beneficiarios_por_estabelecimento"],
            y=top["nm_municipio"] + " / " + top["cd_uf"],
            orientation="h",
            marker=dict(color=CATEGORICAL[1]),
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


def estabelecimentos_por_estado(df: pd.DataFrame, top_n: int = 15) -> go.Figure:
    por_estado = (
        df.groupby(["cd_uf", "nm_uf"], as_index=False)["qt_estabelecimentos"]
        .sum()
        .nlargest(top_n, "qt_estabelecimentos")
        .sort_values("qt_estabelecimentos")
    )
    fig = go.Figure(
        go.Bar(
            x=por_estado["qt_estabelecimentos"],
            y=por_estado["nm_uf"],
            orientation="h",
            marker=dict(color=CATEGORICAL[2]),
            hovertemplate="%{y}<br>%{x:,.0f} estabelecimentos<extra></extra>",
        )
    )
    fig.update_layout(
        **PLOTLY_LAYOUT_DEFAULTS,
        showlegend=False,
        xaxis=dict(title="Estabelecimentos"),
        yaxis=dict(title=None),
    )
    return fig
