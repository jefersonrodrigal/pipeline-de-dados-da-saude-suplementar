"""Logging estruturado (JSON) para todo o pipeline.

Usar `get_logger(__name__)` em vez de `print`. Cada linha de log e um JSON
com timestamp, nivel, logger, mensagem e quaisquer campos extras passados via
`extra={...}` - isso permite filtrar/agregar logs de execucao facilmente
(ex.: grep por "id_execucao").
"""

from __future__ import annotations

import json
import logging
import sys
from datetime import UTC, datetime
from typing import Any

_RESERVED_LOG_RECORD_ATTRS = set(logging.LogRecord("", 0, "", 0, "", None, None).__dict__.keys())


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        extras = {
            key: value
            for key, value in record.__dict__.items()
            if key not in _RESERVED_LOG_RECORD_ATTRS
        }
        if extras:
            payload.update(extras)
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False, default=str)


def configure_logging(level: str = "INFO", fmt: str = "json") -> None:
    root = logging.getLogger()
    root.setLevel(level.upper())
    root.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    if fmt == "json":
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(
            logging.Formatter("%(asctime)s | %(levelname)-8s | %(name)s | %(message)s")
        )
    root.addHandler(handler)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
