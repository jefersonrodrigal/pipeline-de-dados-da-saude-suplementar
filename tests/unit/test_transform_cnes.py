from __future__ import annotations

from pathlib import Path

import pytest
from src.transform.cnes_estabelecimentos import transform_cnes_estabelecimentos


def test_transform_maps_known_columns(cnes_raw: Path) -> None:
    df, stats = transform_cnes_estabelecimentos(cnes_raw, "2024-12")
    assert stats["registros_finais"] == 3
    assert set(df.columns) >= {
        "cd_cnes",
        "nm_estabelecimento",
        "cd_tipo_estabelecimento",
        "cd_municipio_ibge",
    }


def test_transform_raises_on_unrecognized_layout(tmp_path: Path) -> None:
    target_dir = tmp_path / "raw" / "cnes" / "202412"
    target_dir.mkdir(parents=True)
    (target_dir / "layout_desconhecido.csv").write_text(
        "COLUNA_X;COLUNA_Y\n1;2\n", encoding="utf-8"
    )

    with pytest.raises(ValueError, match="Layout do CNES nao reconhecido"):
        transform_cnes_estabelecimentos(tmp_path / "raw", "2024-12")


def test_transform_deduplicates_by_cnes_code(cnes_raw: Path) -> None:
    # Adiciona um arquivo com um CNES repetido.
    extra_dir = cnes_raw / "cnes" / "202412"
    header = "CO_CNES;NO_FANTASIA;TP_UNIDADE;DS_TP_UNIDADE;CO_MUNICIPIO;NO_MUNICIPIO;CO_UF"
    row = "1000001;Hospital Teste Duplicado;05;Hospital Geral;140010;Boa Vista;RR"
    (extra_dir / "duplicado.csv").write_text("\n".join([header, row]), encoding="utf-8")

    df, stats = transform_cnes_estabelecimentos(cnes_raw, "2024-12")
    assert stats["estabelecimentos_duplicados_removidos"] == 1
    assert df["cd_cnes"].is_unique
