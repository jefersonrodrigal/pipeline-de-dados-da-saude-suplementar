"""Fixtures dos testes de integracao - todos marcados `@pytest.mark.integration`
e pulados automaticamente se nenhum SQL Server estiver acessivel (ver
pyproject.toml para a marker e o Makefile/CI para como rodar so os
unitarios: `pytest -m "not integration"`)."""

from __future__ import annotations

import pytest
from sqlalchemy import Engine, text
from src.config.settings import get_settings
from src.utils.db import get_engine


@pytest.fixture(scope="session")
def writer_engine() -> Engine:
    settings = get_settings()
    engine = get_engine(settings.writer_connection)
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"SQL Server indisponivel para testes de integracao: {exc}")
    return engine


@pytest.fixture(scope="session")
def migration_engine() -> Engine:
    settings = get_settings()
    engine = get_engine(settings.migration_connection)
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"SQL Server (migracao) indisponivel para testes de integracao: {exc}")
    return engine
