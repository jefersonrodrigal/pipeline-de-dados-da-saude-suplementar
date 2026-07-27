"""Etapa 'refresh_views': (re)cria as views analiticas em sql/views/*.sql.

Todas usam `CREATE OR ALTER VIEW`, entao rodar esta etapa varias vezes e
seguro (idempotente) - inclusive apos alterar a definicao de uma view.
"""

from __future__ import annotations

import re
from pathlib import Path

from sqlalchemy import Engine
from src.utils.logging_config import get_logger

logger = get_logger(__name__)

VIEWS_DIR = Path(__file__).resolve().parents[2] / "sql" / "views"
_GO_SPLIT_RE = re.compile(r"^\s*GO\s*$", re.IGNORECASE | re.MULTILINE)


def refresh_views(engine: Engine) -> list[str]:
    applied: list[str] = []
    files = sorted(VIEWS_DIR.glob("*.sql"))
    with engine.begin() as connection:
        for path in files:
            sql_text = path.read_text(encoding="utf-8")
            for batch in _GO_SPLIT_RE.split(sql_text):
                statement = batch.strip()
                if statement:
                    connection.exec_driver_sql(statement)
            applied.append(path.stem)
            logger.info("View atualizada", extra={"arquivo": path.name})
    return applied
