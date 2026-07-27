"""Selo de classificacao de cobertura - tratado como indicador exploratorio,
NUNCA como diagnostico (ver docs/business_rules.md)."""

from __future__ import annotations

import streamlit as st

_ICONS = {
    "Cobertura adequada": "🟢",
    "Atenção": "🟡",
    "Cobertura crítica": "🔴",
}


def render_coverage_disclaimer() -> None:
    st.info(
        "A classificação de cobertura abaixo é um **indicador exploratório** "
        "baseado na razão beneficiários/estabelecimento, não um diagnóstico "
        "de saúde pública nem uma avaliação oficial da ANS ou do Ministério "
        "da Saúde. Use como ponto de partida para investigação, não como "
        "conclusão definitiva.",
        icon="ℹ️",
    )


def badge_label(classificacao: str) -> str:
    return f"{_ICONS.get(classificacao, '⚪')} {classificacao}"
