from __future__ import annotations

from pathlib import Path

import pytest
from src.transform.ans_beneficiarios import transform_ans_beneficiarios


def test_transform_detects_and_removes_exact_duplicates(ans_beneficiarios_raw: Path) -> None:
    _, stats = transform_ans_beneficiarios(ans_beneficiarios_raw, "2024-12")
    assert stats["duplicatas_exatas_na_origem"] == 1


def test_transform_aggregates_rows_sharing_the_fact_grain(ans_beneficiarios_raw: Path) -> None:
    df, _ = transform_ans_beneficiarios(ans_beneficiarios_raw, "2024-12")

    # As duas primeiras linhas do fixture (planos 111111111 e 222222222)
    # compartilham o mesmo grao da fato (mesma operadora/municipio/sexo/
    # faixa/vinculo/segmentacao) e devem ser somadas, nao duplicadas.
    boa_vista = df[(df["cd_municipio_ibge"] == "140010") & (df["cd_operadora_ans"] == "000001")]
    assert len(boa_vista) == 1
    assert int(boa_vista.iloc[0]["qt_beneficiario_ativo"]) == 15
    assert int(boa_vista.iloc[0]["qt_beneficiario_aderido"]) == 1

    # A duplicata exata (terceira linha) NAO deve ser somada uma terceira vez.
    assert int(boa_vista.iloc[0]["qt_beneficiario_ativo"]) != 20


def test_transform_normalizes_uf_and_keeps_municipio_code_untouched(
    ans_beneficiarios_raw: Path,
) -> None:
    df, _ = transform_ans_beneficiarios(ans_beneficiarios_raw, "2024-12")
    assert set(df["cd_uf"].unique()) == {"RR"}
    # Codigo de 6 digitos da ANS preservado sem zfill/alteracao (ver
    # comentario em src/transform/ans_beneficiarios.py).
    assert set(df["cd_municipio_ibge"].unique()) == {"140010", "140002"}


def test_transform_raises_when_no_files_found(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        transform_ans_beneficiarios(tmp_path / "raw", "2024-12")
