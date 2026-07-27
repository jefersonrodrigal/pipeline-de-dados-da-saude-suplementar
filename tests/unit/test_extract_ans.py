"""Testes de extracao SEM rede: `download_to_file` e mockado, entao nenhum
teste aqui depende de acesso a internet ou dos arquivos publicos completos."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from src.config.settings import AnsSettings
from src.extract.ans_beneficiarios import ReferencePeriod, build_url, extract_ans_beneficiarios
from src.extract.ans_operadoras import extract_ans_operadoras
from src.models.pipeline import StageStatus


def _fake_download(url: str, destination: Path, timeout_seconds: int = 60) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(b"conteudo ficticio de teste")
    return destination


def test_build_url_matches_real_ans_pattern() -> None:
    period = ReferencePeriod.parse("2024-12")
    url = build_url("https://dadosabertos.ans.gov.br/FTP/PDA/base", period, "RR")
    assert url == "https://dadosabertos.ans.gov.br/FTP/PDA/base/202412/pda-024-icb-RR-2024_12.zip"


def test_extract_beneficiarios_downloads_each_uf(tmp_path: Path) -> None:
    settings = AnsSettings(
        beneficiarios_base_url="https://exemplo.com/base",
        beneficiarios_ufs=["RR", "AC"],
        operadoras_url="",
    )
    with patch(
        "src.extract.ans_beneficiarios.download_to_file", side_effect=_fake_download
    ) as mock_download:
        result, files = extract_ans_beneficiarios(settings, tmp_path, "2024-12")

    assert result.status == StageStatus.SUCCESS
    assert result.records_accepted == 2
    assert mock_download.call_count == 2
    assert len(files) == 2


def test_extract_beneficiarios_skips_duplicate_on_second_call(tmp_path: Path) -> None:
    settings = AnsSettings(
        beneficiarios_base_url="https://exemplo.com/base",
        beneficiarios_ufs=["RR"],
        operadoras_url="",
    )
    with patch(
        "src.extract.ans_beneficiarios.download_to_file", side_effect=_fake_download
    ) as mock_download:
        extract_ans_beneficiarios(settings, tmp_path, "2024-12")
        _, files = extract_ans_beneficiarios(settings, tmp_path, "2024-12")

    assert mock_download.call_count == 1  # segunda chamada nao baixa de novo
    assert files[0].skipped_duplicate is True


def test_extract_beneficiarios_force_redownloads(tmp_path: Path) -> None:
    settings = AnsSettings(
        beneficiarios_base_url="https://exemplo.com/base",
        beneficiarios_ufs=["RR"],
        operadoras_url="",
    )
    with patch(
        "src.extract.ans_beneficiarios.download_to_file", side_effect=_fake_download
    ) as mock_download:
        extract_ans_beneficiarios(settings, tmp_path, "2024-12")
        extract_ans_beneficiarios(settings, tmp_path, "2024-12", force=True)

    assert mock_download.call_count == 2


def test_extract_operadoras_reports_failure_status(tmp_path: Path) -> None:
    from src.extract.http_client import DownloadError

    with patch(
        "src.extract.ans_operadoras.download_to_file", side_effect=DownloadError("falha simulada")
    ):
        result, files = extract_ans_operadoras("https://exemplo.com/cadop.csv", tmp_path, "2024-12")

    assert result.status == StageStatus.FAILED
    assert files == []
