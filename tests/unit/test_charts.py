from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
from app.charts.beneficiary_charts import evolucao_mensal_beneficiarios, ranking_por_estado
from app.charts.coverage_charts import distribuicao_classificacao
from app.charts.quality_charts import regras_mais_violadas


def test_evolucao_mensal_returns_figure_with_one_series() -> None:
    df = pd.DataFrame(
        {
            "ano_mes_extenso": ["Novembro/2024", "Dezembro/2024"],
            "qt_beneficiarios_ativos": [100, 120],
        }
    )
    fig = evolucao_mensal_beneficiarios(df)
    assert isinstance(fig, go.Figure)
    assert len(fig.data) == 1
    assert list(fig.data[0].y) == [100, 120]


def test_ranking_por_estado_limits_to_top_n() -> None:
    df = pd.DataFrame(
        {
            "nm_uf": [f"Estado {i}" for i in range(20)],
            "qt_beneficiarios_ativos": list(range(20)),
            "ranking_estado": list(range(1, 21)),
        }
    )
    fig = ranking_por_estado(df, top_n=5)
    assert len(fig.data[0].x) == 5


def test_distribuicao_classificacao_uses_status_colors() -> None:
    df = pd.DataFrame(
        {
            "classificacao_cobertura": [
                "Cobertura adequada",
                "Cobertura crítica",
                "Cobertura crítica",
            ]
        }
    )
    fig = distribuicao_classificacao(df)
    assert isinstance(fig, go.Figure)
    assert sum(fig.data[0].y) == 3


def test_regras_mais_violadas_colors_by_severity() -> None:
    df = pd.DataFrame(
        {
            "nm_regra": ["a", "b"],
            "severidade": ["ERROR", "WARNING"],
            "total_rejeitados": [10, 5],
        }
    )
    fig = regras_mais_violadas(df)
    assert isinstance(fig, go.Figure)
    assert len(fig.data[0].marker.color) == 2
