from __future__ import annotations

from pathlib import Path

from src.extract.manifest import build_extracted_file, is_duplicate_download, write_manifest


def test_first_download_is_not_a_duplicate(tmp_path: Path) -> None:
    target = tmp_path / "arquivo.zip"
    assert is_duplicate_download(target, "https://exemplo.com/arquivo.zip") is False


def test_same_url_is_detected_as_duplicate(tmp_path: Path) -> None:
    target = tmp_path / "arquivo.zip"
    target.write_bytes(b"conteudo")
    extracted = build_extracted_file(
        target, "fonte_teste", "https://exemplo.com/arquivo.zip", "2024-12"
    )
    write_manifest(extracted)

    assert is_duplicate_download(target, "https://exemplo.com/arquivo.zip") is True


def test_different_url_is_not_a_duplicate(tmp_path: Path) -> None:
    target = tmp_path / "arquivo.zip"
    target.write_bytes(b"conteudo")
    extracted = build_extracted_file(
        target, "fonte_teste", "https://exemplo.com/arquivo.zip", "2024-12"
    )
    write_manifest(extracted)

    assert is_duplicate_download(target, "https://exemplo.com/outro-arquivo.zip") is False
