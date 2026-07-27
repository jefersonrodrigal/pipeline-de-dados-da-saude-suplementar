"""Fabrica de engines SQLAlchemy para o SQL Server.

Usado tanto pelo pipeline (conexao de escrita, `etl_writer`) quanto pela
aplicacao Streamlit (conexao de leitura, `dashboard_reader`) - ver
app/repositories/base.py, que importa `get_engine` a partir daqui para nao
duplicar a logica de criacao/pool de conexao.
"""

from __future__ import annotations

from functools import lru_cache

from sqlalchemy import Engine, create_engine
from src.config.settings import SqlServerConnection


@lru_cache(maxsize=4)
def get_engine(connection: SqlServerConnection) -> Engine:
    """Cria (e reutiliza) um Engine para a conexao informada.

    `pool_pre_ping` evita reutilizar conexoes mortas apos o SQL Server
    reciclar sessoes ociosas; `fast_executemany` acelera cargas em lote via
    pyodbc.
    """
    return create_engine(
        connection.sqlalchemy_url,
        pool_pre_ping=True,
        pool_recycle=1800,
        fast_executemany=True,
        connect_args={"timeout": connection.timeout_seconds},
    )
