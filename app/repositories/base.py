"""Fabrica de conexao + execucao parametrizada de consultas para o Streamlit.

Toda leitura do banco passa por `run_query`, que:
  - usa SEMPRE o usuario `dashboard_reader` (somente leitura, restrito ao
    schema `rpt` - ver sql/security/02_grants.sql), nunca `etl_writer`;
  - usa consultas parametrizadas (bind params via SQLAlchemy `text()`),
    nunca concatenacao de string, prevenindo SQL injection;
  - aplica um limite de linhas (SQL_QUERY_ROW_LIMIT) para nao estourar
    memoria da aplicacao;
  - traduz falhas de conexao em `DatabaseUnavailableError`, uma excecao
    "amigavel" que as paginas capturam para mostrar uma mensagem ao usuario
    em vez de um stack trace.

O engine e cacheado com `st.cache_resource` (mantido vivo entre reruns,
nunca serializado); os RESULTADOS de consulta sao cacheados com
`st.cache_data` diretamente nos modulos de repositorio (nao aqui), pois o
TTL e a chave de cache dependem dos parametros de cada consulta especifica.
"""

from __future__ import annotations

import pandas as pd
from sqlalchemy import Engine, text
from sqlalchemy.exc import DBAPIError, OperationalError
from src.config.settings import get_settings
from src.utils.db import get_engine as _build_engine
from src.utils.logging_config import get_logger

import streamlit as st

logger = get_logger(__name__)


class DatabaseUnavailableError(RuntimeError):
    """Levantada quando o SQL Server nao responde - mensagem segura para o usuario final."""


@st.cache_resource(show_spinner=False)
def get_reader_engine() -> Engine:
    settings = get_settings()
    return _build_engine(settings.reader_connection)


def run_query(sql: str, params: dict | None = None, row_limit: int | None = None) -> pd.DataFrame:
    """Executa `sql` (com bind params) usando a conexao somente leitura.

    Nunca formate `sql` com f-strings a partir de entrada do usuario -
    filtros de UF/municipio/periodo devem sempre vir via `params`.
    """
    settings = get_settings()
    limit = row_limit or settings.sql_query_row_limit
    engine = get_reader_engine()
    try:
        with engine.connect() as connection:
            df = pd.read_sql(text(sql), connection, params=params or {})
    except (OperationalError, DBAPIError) as exc:
        # Nao expor detalhes de infraestrutura (host, driver, credenciais)
        # na mensagem mostrada ao usuario - apenas no log estruturado.
        logger.error("Falha ao consultar o SQL Server", extra={"erro": str(exc)})
        raise DatabaseUnavailableError(
            "Nao foi possivel conectar ao banco de dados agora. Tente novamente em instantes."
        ) from exc

    if len(df) > limit:
        logger.warning(
            "Consulta truncada pelo limite de linhas", extra={"limite": limit, "retornado": len(df)}
        )
        df = df.head(limit)
    return df


class DatabaseConnection:
    """Fachada fina usada pelos repositorios - existe para dar um ponto
    unico de substituicao em testes (mock de `DatabaseConnection.query`)."""

    @staticmethod
    def query(sql: str, params: dict | None = None, row_limit: int | None = None) -> pd.DataFrame:
        return run_query(sql, params=params, row_limit=row_limit)
