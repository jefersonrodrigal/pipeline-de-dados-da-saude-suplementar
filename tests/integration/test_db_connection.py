from __future__ import annotations

import pytest
from sqlalchemy import text

pytestmark = pytest.mark.integration


def test_writer_can_connect_and_identifies_as_etl_writer(writer_engine) -> None:
    with writer_engine.connect() as conn:
        login = conn.execute(text("SELECT SUSER_SNAME()")).scalar_one()
    assert login == "etl_writer"


def test_writer_cannot_create_tables(writer_engine) -> None:
    """etl_writer e deliberadamente proibido de rodar DDL (least privilege) -
    ver docs/security.md."""
    with pytest.raises(Exception, match="(?i)permiss|denied"), writer_engine.begin() as conn:
        conn.exec_driver_sql("CREATE TABLE stg.__deve_falhar (id INT)")


def test_migration_connection_has_sysadmin_or_ddl_rights(migration_engine) -> None:
    with migration_engine.connect() as conn:
        conn.execute(text("SELECT TOP 1 * FROM sys.tables"))
