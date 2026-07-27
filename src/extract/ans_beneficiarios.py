"""Extracao dos dados consolidados de beneficiarios da ANS.

Fonte real (confirmada manualmente, ver docs/data_dictionary.md):
    https://dadosabertos.ans.gov.br/FTP/PDA/informacoes_consolidadas_de_beneficiarios-024/{AAAAMM}/pda-024-icb-{UF}-{AAAA}_{MM}.zip

Um arquivo ZIP por UF e por competencia. O conteudo e uma contagem agregada
(QT_BENEFICIARIO_*), nao um microdado de pessoa fisica.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src.config.settings import AnsSettings
from src.extract.http_client import DownloadError, download_to_file
from src.extract.manifest import build_extracted_file, is_duplicate_download, write_manifest
from src.models.pipeline import ExtractedFile, StageResult, StageStatus
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True)
class ReferencePeriod:
    year: int
    month: int

    @classmethod
    def parse(cls, value: str) -> ReferencePeriod:
        """Aceita 'AAAA-MM' (ex.: '2024-12')."""
        year_str, month_str = value.split("-")
        return cls(year=int(year_str), month=int(month_str))

    @property
    def yyyymm(self) -> str:
        return f"{self.year:04d}{self.month:02d}"

    @property
    def as_ans_suffix(self) -> str:
        return f"{self.year:04d}_{self.month:02d}"

    def __str__(self) -> str:
        return f"{self.year:04d}-{self.month:02d}"


def build_url(base_url: str, period: ReferencePeriod, uf: str) -> str:
    return f"{base_url}/{period.yyyymm}/pda-024-icb-{uf}-{period.as_ans_suffix}.zip"


def extract_ans_beneficiarios(
    ans_settings: AnsSettings,
    raw_dir: Path,
    reference_period: str,
    force: bool = False,
) -> tuple[StageResult, list[ExtractedFile]]:
    result = StageResult.start("extract_ans_beneficiarios")
    period = ReferencePeriod.parse(reference_period)
    target_dir = raw_dir / "ans_beneficiarios" / period.yyyymm
    extracted_files: list[ExtractedFile] = []

    for uf in ans_settings.beneficiarios_ufs:
        url = build_url(ans_settings.beneficiarios_base_url, period, uf)
        destination = target_dir / f"pda-024-icb-{uf}-{period.as_ans_suffix}.zip"
        result.records_processed += 1
        try:
            if not force and is_duplicate_download(destination, url):
                logger.info("Download ja existente, pulando", extra={"uf": uf, "url": url})
                extracted = build_extracted_file(
                    destination, "ans_beneficiarios", url, str(period), skipped_duplicate=True
                )
            else:
                download_to_file(url, destination)
                extracted = build_extracted_file(destination, "ans_beneficiarios", url, str(period))
                write_manifest(extracted)
            extracted_files.append(extracted)
            result.records_accepted += 1
        except DownloadError as exc:
            logger.error("Falha ao extrair UF", extra={"uf": uf, "url": url, "erro": str(exc)})
            result.records_rejected += 1
            result.errors.append(f"{uf}: {exc}")

    status = StageStatus.SUCCESS
    if result.records_rejected and result.records_accepted:
        status = StageStatus.PARTIAL
    elif result.records_rejected and not result.records_accepted:
        status = StageStatus.FAILED
    result.finish(status)
    return result, extracted_files
