"""Conversao entre 'AAAA-MM' e o inteiro AAAAMM usado como sk_tempo
(chave substituta "inteligente" de dim.dim_tempo - ver docs/architecture.md).
Compartilhado entre src/main.py e a aplicacao Streamlit para nao duplicar a
regra de conversao.
"""

from __future__ import annotations


def to_sk_tempo(reference_period: str) -> int:
    year, month = (int(p) for p in reference_period.split("-"))
    return year * 100 + month


def from_sk_tempo(sk_tempo: int) -> str:
    year, month = divmod(sk_tempo, 100)
    return f"{year:04d}-{month:02d}"
