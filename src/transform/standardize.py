"""Helpers genericos de padronizacao usados por todos os transformadores."""

from __future__ import annotations

import re

import pandas as pd

_SNAKE_RE_1 = re.compile(r"(.)([A-Z][a-z]+)")
_SNAKE_RE_2 = re.compile(r"([a-z0-9])([A-Z])")


def to_snake_case(name: str) -> str:
    name = name.strip()
    name = _SNAKE_RE_1.sub(r"\1_\2", name)
    name = _SNAKE_RE_2.sub(r"\1_\2", name)
    return name.lower().replace(" ", "_").replace("__", "_")


def standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [to_snake_case(c) for c in df.columns]
    return df


def strip_strings(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    df = df.copy()
    for col in columns:
        if col in df.columns:
            df[col] = df[col].astype("string").str.strip()
    return df


def pad_code(series: pd.Series, width: int) -> pd.Series:
    """Preenche com zeros a esquerda (ex.: codigo de municipio truncado)."""
    return series.astype("string").str.strip().str.zfill(width)


def count_exact_duplicates(df: pd.DataFrame) -> int:
    return int(df.duplicated(keep="first").sum())


def drop_exact_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    return df.drop_duplicates(keep="first").reset_index(drop=True)
