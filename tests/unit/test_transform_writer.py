from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest
from src.transform.writer import read_trusted_parquet, write_trusted_parquet


def test_write_and_read_roundtrip(tmp_path: Path) -> None:
    df = pd.DataFrame({"a": [1, 2], "b": ["x", "y"]})
    path = write_trusted_parquet(df, tmp_path, "beneficiarios", "2024-12")

    assert path.exists()
    loaded = read_trusted_parquet(tmp_path, "beneficiarios", "2024-12")
    pd.testing.assert_frame_equal(df, loaded)


def test_read_raises_when_missing(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        read_trusted_parquet(tmp_path, "beneficiarios", "1900-01")
