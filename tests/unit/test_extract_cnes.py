from __future__ import annotations

from pathlib import Path

from src.config.settings import CnesSettings
from src.extract.cnes_estabelecimentos import extract_cnes_estabelecimentos
from src.models.pipeline import StageStatus


def test_extract_fails_clearly_when_no_source_configured(tmp_path: Path) -> None:
    cnes_settings = CnesSettings(
        download_url="", manual_input_dir=Path("data/raw/cnes/incoming_vazio")
    )
    result, files = extract_cnes_estabelecimentos(cnes_settings, tmp_path, "2024-12", tmp_path)
    assert result.status == StageStatus.FAILED
    assert files == []
    assert "CNES_DOWNLOAD_URL" in result.errors[0]


def test_extract_registers_manual_files(tmp_path: Path) -> None:
    incoming = tmp_path / "incoming"
    incoming.mkdir()
    (incoming / "estabelecimentos.csv").write_text(
        "CO_CNES;NO_FANTASIA\n1;Teste\n", encoding="utf-8"
    )

    cnes_settings = CnesSettings(download_url="", manual_input_dir=Path("incoming"))
    result, files = extract_cnes_estabelecimentos(
        cnes_settings, tmp_path / "raw", "2024-12", tmp_path
    )

    assert result.status == StageStatus.SUCCESS
    assert len(files) == 1
    assert files[0].path.exists()


def test_extract_manual_files_are_deduplicated_on_second_call(tmp_path: Path) -> None:
    incoming = tmp_path / "incoming"
    incoming.mkdir()
    (incoming / "estabelecimentos.csv").write_text(
        "CO_CNES;NO_FANTASIA\n1;Teste\n", encoding="utf-8"
    )
    cnes_settings = CnesSettings(download_url="", manual_input_dir=Path("incoming"))

    extract_cnes_estabelecimentos(cnes_settings, tmp_path / "raw", "2024-12", tmp_path)
    _, files = extract_cnes_estabelecimentos(cnes_settings, tmp_path / "raw", "2024-12", tmp_path)

    assert files[0].skipped_duplicate is True
