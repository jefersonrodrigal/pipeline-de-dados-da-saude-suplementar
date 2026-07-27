"""Paleta de cores validada (colorblind-safe) usada em todos os graficos.

Valores vindos da skill de dataviz do projeto (ver conversa de
desenvolvimento) - ordem categorica fixa, ramp sequencial de um unico matiz
para magnitude, par divergente azul<->vermelho para variacao percentual, e
paleta de status reservada (nunca usada para series). Nao gerar cores
"na hora" nem ciclar o categorico - sempre usar estas constantes na ordem
definida.
"""

from __future__ import annotations

# Ordem fixa - nunca reordenar por rank/valor, apenas por identidade da serie.
CATEGORICAL = [
    "#2a78d6",  # 1 blue
    "#eb6834",  # 2 orange
    "#1baf7a",  # 3 aqua
    "#eda100",  # 4 yellow
    "#e87ba4",  # 5 magenta
    "#008300",  # 6 green
    "#4a3aa7",  # 7 violet
    "#e34948",  # 8 red
]

# Sequencial (magnitude) - azul, claro -> escuro.
SEQUENTIAL_BLUE = ["#cde2fb", "#9ec5f4", "#5598e7", "#2a78d6", "#184f95", "#0d366b"]

# Divergente (polaridade) - azul <-> vermelho, ponto neutro cinza.
DIVERGING_NEGATIVE = "#e34948"
DIVERGING_NEUTRAL = "#f0efec"
DIVERGING_POSITIVE = "#2a78d6"

# Status (fixo - nunca reaproveitado como serie categorica).
STATUS = {
    "good": "#0ca30c",
    "warning": "#fab219",
    "serious": "#ec835a",
    "critical": "#d03b3b",
}

# Mapeamento das classificacoes exploratorias de cobertura (ver
# rpt.vw_cobertura_regional) para o status palette.
COBERTURA_STATUS = {
    "Cobertura adequada": STATUS["good"],
    "Atenção": STATUS["warning"],
    "Cobertura crítica": STATUS["critical"],
}

MUTED_TEXT = "#898781"
GRIDLINE = "#e1e0d9"

PLOTLY_LAYOUT_DEFAULTS = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="system-ui, -apple-system, Segoe UI, sans-serif"),
    margin=dict(l=10, r=10, t=40, b=10),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
)
