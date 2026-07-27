"""Persistencia da camada Trusted em Parquet, particionada por competencia."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


def write_trusted_parquet(
    df: pd.DataFrame, trusted_dir: Path, dataset: str, reference_period: str
) -> Path:
    partition = reference_period.replace("-", "")
    target_dir = trusted_dir / dataset / partition
    target_dir.mkdir(parents=True, exist_ok=True)
    path = target_dir / "part.parquet"
    df.to_parquet(path, index=False)
    return path


def read_trusted_parquet(trusted_dir: Path, dataset: str, reference_period: str) -> pd.DataFrame:
    partition = reference_period.replace("-", "")
    path = trusted_dir / dataset / partition / "part.parquet"
    if not path.exists():
        raise FileNotFoundError(
            f"Parquet Trusted nao encontrado em {path}. Rode a etapa 'transform' antes."
        )
    return pd.read_parquet(path)
