"""Etapa 'export_analytics': gera snapshots em Parquet das principais views
analiticas em data/analytics/ - util para o notebook exploratorio e como
fallback caso o SQL Server fique indisponivel (ver docs/architecture.md).
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from sqlalchemy import Engine
from src.utils.logging_config import get_logger

logger = get_logger(__name__)

_EXPORTED_VIEWS = [
    "vw_evolucao_mensal_beneficiarios",
    "vw_beneficiarios_por_estado",
    "vw_beneficiarios_por_municipio",
    "vw_estabelecimentos_por_tipo",
    "vw_razao_beneficiarios_estabelecimento",
    "vw_ranking_operadoras",
    "vw_cobertura_regional",
    "vw_qualidade_pipeline",
]


def export_analytics(engine: Engine, analytics_dir: Path, reference_period: str) -> list[Path]:
    partition = reference_period.replace("-", "")
    target_dir = analytics_dir / partition
    target_dir.mkdir(parents=True, exist_ok=True)

    written: list[Path] = []
    with engine.connect() as connection:
        for view_name in _EXPORTED_VIEWS:
            df = pd.read_sql(f"SELECT * FROM rpt.{view_name}", connection)
            path = target_dir / f"{view_name}.parquet"
            df.to_parquet(path, index=False)
            written.append(path)
            logger.info(
                "Snapshot exportado",
                extra={"view": view_name, "linhas": len(df), "arquivo": str(path)},
            )
    return written
