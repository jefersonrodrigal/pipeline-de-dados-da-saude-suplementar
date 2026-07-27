"""Carga das tabelas de staging (stg.*) a partir de DataFrames pandas.

Staging e sempre TRUNCATE + INSERT completo do lote da execucao corrente -
nunca acumula historico (ver sql/ddl/12_staging_tables.sql).
"""

from __future__ import annotations

import pandas as pd
from sqlalchemy import text
from sqlalchemy.engine import Connection


def truncate_staging(connection: Connection, table: str) -> None:
    # DELETE, nao TRUNCATE: TRUNCATE TABLE exige permissao ALTER no SQL
    # Server, que o login etl_writer deliberadamente nao tem (least
    # privilege - ver sql/security/02_grants.sql). Para o volume de uma
    # tabela de staging, a diferenca de custo e irrelevante.
    connection.execute(text(f"DELETE FROM stg.{table}"))


def bulk_insert(connection: Connection, df: pd.DataFrame, table: str, chunksize: int = 5000) -> int:
    if df.empty:
        return 0
    df.to_sql(
        table,
        con=connection,
        schema="stg",
        if_exists="append",
        index=False,
        chunksize=chunksize,
        method=None,
    )
    return len(df)
