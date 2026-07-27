"""Testa a traducao de falhas de conexao em DatabaseUnavailableError -
cenario de 'banco indisponivel' exigido pela secao 21/22 do briefing."""

from __future__ import annotations

import pytest
from app.repositories import base
from sqlalchemy.exc import OperationalError


class _FakeEngine:
    def connect(self):
        raise OperationalError("SELECT 1", {}, Exception("conexao recusada"))


def test_run_query_raises_friendly_error_when_db_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(base, "get_reader_engine", lambda: _FakeEngine())

    with pytest.raises(base.DatabaseUnavailableError):
        base.run_query("SELECT 1")


def test_run_query_truncates_to_row_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    import pandas as pd

    big_df = pd.DataFrame({"valor": range(10)})
    monkeypatch.setattr(base.pd, "read_sql", lambda *a, **k: big_df)

    class _OkConn:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    class _OkEngine:
        def connect(self):
            return _OkConn()

    monkeypatch.setattr(base, "get_reader_engine", lambda: _OkEngine())
    result = base.run_query("SELECT * FROM tabela", row_limit=3)
    assert len(result) == 3
