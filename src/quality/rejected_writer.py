"""Persistencia de registros rejeitados em arquivo (data/rejected/).

A gravacao na tabela rej.registros_rejeitados do SQL Server acontece na
etapa de carga (src/load/loader.py) - este modulo cuida apenas da copia em
arquivo exigida pela especificacao (auditoria fora do banco, reprocessamento
offline).
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path


def write_rejected_records(
    rejected_records: list[dict],
    rejected_dir: Path,
    dataset_name: str,
    id_execucao: int,
    reference_period: str,
) -> Path | None:
    if not rejected_records:
        return None

    partition = reference_period.replace("-", "")
    target_dir = rejected_dir / dataset_name / partition
    target_dir.mkdir(parents=True, exist_ok=True)
    path = target_dir / f"rejeitados_execucao_{id_execucao}.jsonl"

    with path.open("w", encoding="utf-8") as fh:
        for record in rejected_records:
            payload = {
                "id_execucao": id_execucao,
                "dataset": dataset_name,
                "regra_violada": record["regra_violada"],
                "motivo": record["motivo"],
                "registro": record["registro"],
                "rejeitado_em": datetime.now(UTC).isoformat(),
            }
            fh.write(json.dumps(payload, ensure_ascii=False, default=str) + "\n")

    return path
