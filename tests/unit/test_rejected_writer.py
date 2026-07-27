from __future__ import annotations

import json
from pathlib import Path

from src.quality.rejected_writer import write_rejected_records


def test_write_rejected_records_creates_jsonl_file(tmp_path: Path) -> None:
    records = [
        {"regra_violada": "valores_negativos", "motivo": "teste", "registro": {"a": 1}},
        {"regra_violada": "uf_invalida", "motivo": "teste2", "registro": {"a": 2}},
    ]
    path = write_rejected_records(
        records, tmp_path, "beneficiarios", id_execucao=42, reference_period="2024-12"
    )

    assert path is not None
    lines = path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2
    first = json.loads(lines[0])
    assert first["id_execucao"] == 42
    assert first["dataset"] == "beneficiarios"


def test_write_rejected_records_returns_none_when_empty(tmp_path: Path) -> None:
    assert write_rejected_records([], tmp_path, "beneficiarios", 1, "2024-12") is None
