"""Extracao dos estabelecimentos de saude (CNES/DATASUS).

Diferente da ANS, o CNES NAO possui uma URL estavel de download direto: o
portal (https://cnes.datasus.gov.br/pages/downloads/arquivosBaseDados.jsp)
exige selecao dinamica de UF/competencia via formulario/servlet, que nao
pode ser reproduzida de forma confiavel aqui (nao inventamos endpoints).

Por isso esta fonte e CONFIGURAVEL, com duas opcoes, nesta ordem de
prioridade:

    1. CNES_DOWNLOAD_URL no .env: se voce encontrar/gerar uma URL valida
       (ex.: copiando o link de download apos selecionar UF/competencia no
       portal), o pipeline baixa normalmente.
    2. Deposito manual: coloque o(s) arquivo(s) baixados manualmente em
       CNES_MANUAL_INPUT_DIR (default: data/raw/cnes/incoming/) e rode o
       pipeline - os arquivos encontrados la sao registrados na camada Raw
       (copiados com hash e manifesto) exatamente como um download.

Se nenhuma das duas opcoes estiver disponivel, a extracao falha com uma
mensagem explicando exatamente o que fazer (nunca falha silenciosamente).
"""

from __future__ import annotations

import shutil
from pathlib import Path

from src.config.settings import CnesSettings
from src.extract.http_client import DownloadError, download_to_file
from src.extract.manifest import build_extracted_file, is_duplicate_download, write_manifest
from src.models.pipeline import ExtractedFile, StageResult, StageStatus
from src.utils.logging_config import get_logger

logger = get_logger(__name__)

_ACCEPTED_SUFFIXES = {".csv", ".txt", ".zip", ".dbc"}


def extract_cnes_estabelecimentos(
    cnes_settings: CnesSettings,
    raw_dir: Path,
    reference_period: str,
    project_root: Path,
    force: bool = False,
) -> tuple[StageResult, list[ExtractedFile]]:
    result = StageResult.start("extract_cnes_estabelecimentos")
    target_dir = raw_dir / "cnes" / reference_period.replace("-", "")
    extracted_files: list[ExtractedFile] = []

    if cnes_settings.download_url:
        destination = target_dir / Path(cnes_settings.download_url).name
        result.records_processed = 1
        try:
            if not force and is_duplicate_download(destination, cnes_settings.download_url):
                extracted = build_extracted_file(
                    destination,
                    "cnes",
                    cnes_settings.download_url,
                    reference_period,
                    skipped_duplicate=True,
                )
            else:
                download_to_file(cnes_settings.download_url, destination)
                extracted = build_extracted_file(
                    destination, "cnes", cnes_settings.download_url, reference_period
                )
                write_manifest(extracted)
            extracted_files.append(extracted)
            result.records_accepted = 1
            result.finish(StageStatus.SUCCESS)
            return result, extracted_files
        except DownloadError as exc:
            result.records_rejected = 1
            result.errors.append(str(exc))
            result.finish(StageStatus.FAILED)
            return result, []

    manual_dir = project_root / cnes_settings.manual_input_dir
    manual_files = sorted(
        p for p in manual_dir.glob("*") if p.is_file() and p.suffix.lower() in _ACCEPTED_SUFFIXES
    )

    if not manual_files:
        message = (
            "Nenhuma fonte de dados do CNES configurada. O portal do CNES "
            "(cnes.datasus.gov.br/pages/downloads/arquivosBaseDados.jsp) exige "
            "selecao manual de UF/competencia, entao nao ha URL fixa para "
            f"baixar automaticamente. Configure CNES_DOWNLOAD_URL no .env, OU "
            f"copie o(s) arquivo(s) baixados manualmente para "
            f"'{manual_dir}' e rode novamente."
        )
        logger.warning(message)
        result.records_processed = 0
        result.errors.append(message)
        result.finish(StageStatus.FAILED)
        return result, []

    for source_file in manual_files:
        destination = target_dir / source_file.name
        result.records_processed += 1
        source_marker = f"manual:{source_file.name}"
        if not force and is_duplicate_download(destination, source_marker):
            extracted = build_extracted_file(
                destination, "cnes", source_marker, reference_period, skipped_duplicate=True
            )
        else:
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_file, destination)
            extracted = build_extracted_file(destination, "cnes", source_marker, reference_period)
            write_manifest(extracted)
        extracted_files.append(extracted)
        result.records_accepted += 1

    result.finish(StageStatus.SUCCESS)
    return result, extracted_files
