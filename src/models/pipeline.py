"""Tipos de dominio compartilhados entre as etapas do pipeline.

Cada etapa (extract, validate_raw, transform, validate_trusted, load,
aggregate, refresh_views, export_analytics) retorna um `StageResult`, o que
padroniza como `src/main.py` decide se deve seguir para a proxima etapa,
registrar sucesso/falha em `aud.execucao_pipeline` e reportar contadores.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path


class StageStatus(StrEnum):
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    PARTIAL = "PARTIAL"


@dataclass
class StageResult:
    stage: str
    status: StageStatus
    started_at: datetime
    finished_at: datetime | None = None
    records_processed: int = 0
    records_accepted: int = 0
    records_rejected: int = 0
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    metadata: dict[str, str] = field(default_factory=dict)

    @classmethod
    def start(cls, stage: str) -> StageResult:
        return cls(stage=stage, status=StageStatus.RUNNING, started_at=datetime.now(UTC))

    def finish(self, status: StageStatus) -> StageResult:
        self.status = status
        self.finished_at = datetime.now(UTC)
        return self

    @property
    def duration_seconds(self) -> float:
        end = self.finished_at or datetime.now(UTC)
        return (end - self.started_at).total_seconds()

    @property
    def ok(self) -> bool:
        return self.status in (StageStatus.SUCCESS, StageStatus.PARTIAL)


@dataclass
class ExtractedFile:
    """Metadados de um arquivo baixado para a camada Raw."""

    path: Path
    source_name: str  # ex.: "ans_beneficiarios", "ans_operadoras", "cnes"
    source_url: str
    sha256: str
    size_bytes: int
    extracted_at: datetime
    reference_period: str  # AAAA-MM
    skipped_duplicate: bool = False

    def to_manifest_dict(self) -> dict:
        return {
            "path": str(self.path),
            "source_name": self.source_name,
            "source_url": self.source_url,
            "sha256": self.sha256,
            "size_bytes": self.size_bytes,
            "extracted_at": self.extracted_at.isoformat(),
            "reference_period": self.reference_period,
        }


def elapsed_since(started_epoch: float) -> float:
    return round(time.monotonic() - started_epoch, 3)
