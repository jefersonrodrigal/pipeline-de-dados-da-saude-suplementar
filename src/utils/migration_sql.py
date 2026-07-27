"""Executa os scripts DDL de sql/ddl/*.sql a partir de migrations Alembic.

Por que reaproveitar os arquivos .sql em vez de usar `op.create_table(...)`:
o esquema usa recursos especificos do T-SQL (colunas computadas persistidas,
indices filtrados, `SET IDENTITY_INSERT` para linhas sentinela) que nao tem
representacao direta e legivel na API declarativa do Alembic. Os arquivos em
sql/ddl/ sao a fonte unica de verdade - tanto para `alembic upgrade head`
quanto para quem preferir rodar via `sqlcmd` diretamente (ver README).

Os scripts usam `GO` como separador de lote (sintaxe do sqlcmd/SSMS, nao do
T-SQL em si), entao precisamos dividir o texto manualmente antes de executar
via pyodbc/SQLAlchemy.

Nota: este modulo mora em src/utils (nao em alembic/) de proposito - um
modulo chamado `alembic.sql_helpers` colidiria com o pacote `alembic`
instalado (que ja ocupa esse nome no sys.path) e nunca seria encontrado.
"""

from __future__ import annotations

import re
from pathlib import Path

from sqlalchemy.engine import Connection

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SQL_DDL_DIR = PROJECT_ROOT / "sql" / "ddl"
_GO_SPLIT_RE = re.compile(r"^\s*GO\s*$", re.IGNORECASE | re.MULTILINE)


def run_ddl_file(connection: Connection, filename: str) -> None:
    sql_text = (SQL_DDL_DIR / filename).read_text(encoding="utf-8")
    for batch in _GO_SPLIT_RE.split(sql_text):
        statement = batch.strip()
        if statement:
            connection.exec_driver_sql(statement)
    # SET NOCOUNT ON e uma configuracao de sessao: se ficar ligada, o
    # driver ODBC passa a reportar rowcount=-1 para comandos seguintes,
    # o que quebra o proprio controle interno do Alembic sobre a tabela
    # alembic_version (ele espera rowcount=1 ao gravar a revisao aplicada).
    # Resetamos aqui para nao vazar esse estado de sessao para o Alembic.
    connection.exec_driver_sql("SET NOCOUNT OFF")
