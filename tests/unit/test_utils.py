from __future__ import annotations

import pandas as pd
from src.transform.region_mapping import VALID_UFS, uf_name, uf_region
from src.transform.standardize import count_exact_duplicates, drop_exact_duplicates, to_snake_case
from src.utils.hashing import sha256_bytes, sha256_file
from src.utils.period import from_sk_tempo, to_sk_tempo


def test_to_snake_case_handles_mixed_and_spaced_names() -> None:
    assert to_snake_case("Razao_Social") == "razao_social"
    assert to_snake_case("NM_MUNICIPIO") == "nm_municipio"
    assert to_snake_case("Data Registro ANS") == "data_registro_ans"


def test_duplicate_helpers() -> None:
    df = pd.DataFrame({"a": [1, 1, 2]})
    assert count_exact_duplicates(df) == 1
    assert len(drop_exact_duplicates(df)) == 2


def test_region_mapping_has_all_27_ufs_plus_sentinel() -> None:
    assert len(VALID_UFS) == 28  # 26 estados + DF + "XX"
    assert uf_region("RR") == "Norte"
    assert uf_region("SP") == "Sudeste"
    assert uf_name("DF") == "Distrito Federal"
    assert uf_region("ZZ") == "Não informado"


def test_period_roundtrip() -> None:
    assert to_sk_tempo("2024-12") == 202412
    assert from_sk_tempo(202412) == "2024-12"
    assert from_sk_tempo(to_sk_tempo("2026-01")) == "2026-01"


def test_sha256_bytes_is_deterministic() -> None:
    assert sha256_bytes(b"abc") == sha256_bytes(b"abc")
    assert sha256_bytes(b"abc") != sha256_bytes(b"abd")


def test_sha256_file(tmp_path) -> None:
    path = tmp_path / "arquivo.txt"
    path.write_bytes(b"conteudo de teste")
    assert sha256_file(path) == sha256_bytes(b"conteudo de teste")
