"""Extracao do cadastro de operadoras ativas da ANS.

Fonte real (confirmada manualmente):
    https://dadosabertos.ans.gov.br/FTP/PDA/operadoras_de_plano_de_saude_ativas/Relatorio_cadop.csv

Diferente dos beneficiarios, este e um snapshot UNICO (sobrescrito pela ANS a
cada atualizacao, sem particionamento por competencia). Guardamos uma copia
por data de extracao em data/raw/ans_operadoras/{AAAA-MM-DD}/ para manter
historico de versoes cruas, mesmo a fonte nao versionando.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

from src.extract.http_client import DownloadError, download_to_file
from src.extract.manifest import build_extracted_file, is_duplicate_download, write_manifest
from src.models.pipeline import ExtractedFile, StageResult, StageStatus
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


def extract_ans_operadoras(
    operadoras_url: str,
    raw_dir: Path,
    reference_period: str,
    force: bool = False,
    extraction_date: date | None = None,
) -> tuple[StageResult, list[ExtractedFile]]:
    result = StageResult.start("extract_ans_operadoras")
    extraction_date = extraction_date or date.today()
    target_dir = raw_dir / "ans_operadoras" / extraction_date.isoformat()
    destination = target_dir / "Relatorio_cadop.csv"

    result.records_processed = 1
    try:
        if not force and is_duplicate_download(destination, operadoras_url):
            logger.info(
                "Cadastro de operadoras ja baixado hoje, pulando", extra={"url": operadoras_url}
            )
            extracted = build_extracted_file(
                destination,
                "ans_operadoras",
                operadoras_url,
                reference_period,
                skipped_duplicate=True,
            )
        else:
            download_to_file(operadoras_url, destination)
            extracted = build_extracted_file(
                destination, "ans_operadoras", operadoras_url, reference_period
            )
            write_manifest(extracted)
        result.records_accepted = 1
        result.finish(StageStatus.SUCCESS)
        return result, [extracted]
    except DownloadError as exc:
        logger.error("Falha ao extrair cadastro de operadoras", extra={"erro": str(exc)})
        result.records_rejected = 1
        result.errors.append(str(exc))
        result.finish(StageStatus.FAILED)
        return result, []
