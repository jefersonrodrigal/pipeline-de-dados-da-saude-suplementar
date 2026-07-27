"""Manifesto de download da camada Raw.

Cada arquivo baixado ganha um sidecar `<arquivo>.manifest.json` com a URL de
origem, hash SHA-256, tamanho, data/hora de extracao e periodo de
referencia. Antes de baixar, verificamos se ja existe um manifesto para o
mesmo destino com a mesma URL - se sim (e o arquivo de dados ainda existir
em disco), o download e pulado, o que evita baixar novamente varios
megabytes de um arquivo que nao mudou. Use `force=True` para ignorar isso.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from src.models.pipeline import ExtractedFile
from src.utils.hashing import sha256_file
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


def manifest_path(data_path: Path) -> Path:
    return data_path.with_suffix(data_path.suffix + ".manifest.json")


def read_manifest(data_path: Path) -> dict | None:
    path = manifest_path(data_path)
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def is_duplicate_download(data_path: Path, source_url: str) -> bool:
    if not data_path.exists():
        return False
    existing = read_manifest(data_path)
    return bool(existing and existing.get("source_url") == source_url)


def write_manifest(extracted: ExtractedFile) -> Path:
    path = manifest_path(extracted.path)
    payload = extracted.to_manifest_dict()
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def build_extracted_file(
    path: Path,
    source_name: str,
    source_url: str,
    reference_period: str,
    skipped_duplicate: bool = False,
) -> ExtractedFile:
    return ExtractedFile(
        path=path,
        source_name=source_name,
        source_url=source_url,
        sha256=sha256_file(path),
        size_bytes=path.stat().st_size,
        extracted_at=datetime.now(UTC),
        reference_period=reference_period,
        skipped_duplicate=skipped_duplicate,
    )
