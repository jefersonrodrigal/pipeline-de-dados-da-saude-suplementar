"""Configuracao centralizada da aplicacao.

Todas as variaveis sensiveis (credenciais de banco, URLs de origem) vem de
variaveis de ambiente / arquivo .env - nunca de valores fixos no codigo.
Este modulo e o unico ponto que le `os.environ`; o resto do projeto (pipeline
e Streamlit) sempre recebe um objeto `Settings` ja resolvido.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from urllib.parse import quote_plus

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _load_env() -> None:
    env_path = PROJECT_ROOT / ".env"
    if env_path.exists():
        load_dotenv(env_path, override=False)


def _get(name: str, default: str | None = None, *, required: bool = False) -> str:
    value = os.environ.get(name, default)
    if required and not value:
        raise RuntimeError(
            f"Variavel de ambiente obrigatoria ausente: {name}. "
            f"Verifique seu arquivo .env (veja .env.example)."
        )
    return value or ""


def _get_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    return int(raw) if raw else default


def _get_list(name: str, default: str) -> list[str]:
    raw = os.environ.get(name, default)
    return [item.strip() for item in raw.split(",") if item.strip()]


@dataclass(frozen=True)
class SqlServerConnection:
    """Parametros de conexao para um unico usuario/role do SQL Server."""

    host: str
    port: int
    database: str
    user: str
    password: str
    driver: str
    trust_certificate: bool
    encrypt: bool
    timeout_seconds: int

    @property
    def sqlalchemy_url(self) -> str:
        driver_quoted = quote_plus(self.driver)
        trust = "yes" if self.trust_certificate else "no"
        encrypt = "yes" if self.encrypt else "no"
        password_quoted = quote_plus(self.password)
        user_quoted = quote_plus(self.user)
        return (
            f"mssql+pyodbc://{user_quoted}:{password_quoted}@{self.host}:{self.port}"
            f"/{self.database}?driver={driver_quoted}"
            f"&TrustServerCertificate={trust}&Encrypt={encrypt}"
        )

    @property
    def odbc_connection_string(self) -> str:
        trust = "yes" if self.trust_certificate else "no"
        encrypt = "yes" if self.encrypt else "no"
        return (
            f"DRIVER={{{self.driver}}};SERVER={self.host},{self.port};"
            f"DATABASE={self.database};UID={self.user};PWD={self.password};"
            f"TrustServerCertificate={trust};Encrypt={encrypt}"
        )


@dataclass(frozen=True)
class MigrationConnection:
    """Conexao usada SOMENTE por Alembic/scripts DDL administrativos.

    Deliberadamente separada de `SqlServerConnection`: `etl_writer` e
    `dashboard_reader` tem permissao apenas de DML (SELECT/INSERT/UPDATE/
    DELETE) nos schemas de negocio, nunca DDL (CREATE/ALTER TABLE). Rodar
    migrations exige um principal com privilegios de schema (sysadmin local
    via Windows Auth em desenvolvimento, ou `sa`/login dedicado via SQL Auth
    em Docker) - ver docs/security.md.
    """

    host: str
    port: int
    database: str
    driver: str
    trust_certificate: bool
    encrypt: bool
    auth_mode: str  # "trusted" (Windows Auth) ou "sql" (usuario/senha)
    user: str = ""
    password: str = ""
    timeout_seconds: int = 30

    @property
    def sqlalchemy_url(self) -> str:
        driver_quoted = quote_plus(self.driver)
        trust = "yes" if self.trust_certificate else "no"
        encrypt = "yes" if self.encrypt else "no"
        base = f"mssql+pyodbc://@{self.host}:{self.port}/{self.database}?driver={driver_quoted}"
        if self.auth_mode == "trusted":
            return (
                base + f"&trusted_connection=yes&TrustServerCertificate={trust}&Encrypt={encrypt}"
            )
        user_quoted = quote_plus(self.user)
        password_quoted = quote_plus(self.password)
        return (
            f"mssql+pyodbc://{user_quoted}:{password_quoted}@{self.host}:{self.port}"
            f"/{self.database}?driver={driver_quoted}"
            f"&TrustServerCertificate={trust}&Encrypt={encrypt}"
        )


@dataclass(frozen=True)
class AnsSettings:
    beneficiarios_base_url: str
    beneficiarios_ufs: list[str]
    operadoras_url: str


@dataclass(frozen=True)
class CnesSettings:
    download_url: str
    manual_input_dir: Path


@dataclass(frozen=True)
class Settings:
    app_env: str
    log_level: str
    log_format: str
    pipeline_name: str
    default_reference_period: str
    sql_query_row_limit: int

    writer_connection: SqlServerConnection
    reader_connection: SqlServerConnection
    migration_connection: MigrationConnection

    ans: AnsSettings
    cnes: CnesSettings

    data_raw_dir: Path
    data_trusted_dir: Path
    data_analytics_dir: Path
    data_rejected_dir: Path

    streamlit_port: int = field(default=8501)
    streamlit_cache_ttl_seconds: int = field(default=300)

    def resolved_path(self, relative_or_absolute: Path) -> Path:
        if relative_or_absolute.is_absolute():
            return relative_or_absolute
        return PROJECT_ROOT / relative_or_absolute


def _build_connection(prefix_user: str, prefix_password: str) -> SqlServerConnection:
    return SqlServerConnection(
        host=_get("SQLSERVER_HOST", "localhost"),
        port=_get_int("SQLSERVER_PORT", 1433),
        database=_get("SQLSERVER_DATABASE", "saude_suplementar"),
        user=_get(prefix_user, required=True),
        password=_get(prefix_password, required=True),
        driver=_get("SQLSERVER_DRIVER", "ODBC Driver 18 for SQL Server"),
        trust_certificate=_get("SQLSERVER_TRUST_CERTIFICATE", "yes").lower() == "yes",
        encrypt=_get("SQLSERVER_ENCRYPT", "yes").lower() == "yes",
        timeout_seconds=_get_int("SQLSERVER_TIMEOUT_SECONDS", 30),
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Retorna a configuracao resolvida (com cache de processo)."""
    _load_env()

    writer_connection = _build_connection("SQLSERVER_USER", "SQLSERVER_PASSWORD")
    reader_connection = _build_connection("SQLSERVER_READONLY_USER", "SQLSERVER_READONLY_PASSWORD")
    migration_connection = MigrationConnection(
        host=_get("SQLSERVER_HOST", "localhost"),
        port=_get_int("SQLSERVER_PORT", 1433),
        database=_get("SQLSERVER_DATABASE", "saude_suplementar"),
        driver=_get("SQLSERVER_DRIVER", "ODBC Driver 18 for SQL Server"),
        trust_certificate=_get("SQLSERVER_TRUST_CERTIFICATE", "yes").lower() == "yes",
        encrypt=_get("SQLSERVER_ENCRYPT", "yes").lower() == "yes",
        auth_mode=_get("SQLSERVER_MIGRATION_AUTH", "trusted"),
        user=_get("SQLSERVER_MIGRATION_USER", "sa"),
        password=_get("SQLSERVER_MIGRATION_PASSWORD", ""),
    )

    ans = AnsSettings(
        beneficiarios_base_url=_get(
            "ANS_BENEFICIARIOS_BASE_URL",
            "https://dadosabertos.ans.gov.br/FTP/PDA/informacoes_consolidadas_de_beneficiarios-024",
        ),
        beneficiarios_ufs=_get_list(
            "ANS_BENEFICIARIOS_UFS",
            "AC,AL,AM,AP,BA,CE,DF,ES,GO,MA,MG,MS,MT,PA,PB,PE,PI,PR,RJ,RN,RO,RR,RS,SC,SE,SP,TO,XX",
        ),
        operadoras_url=_get(
            "ANS_OPERADORAS_URL",
            "https://dadosabertos.ans.gov.br/FTP/PDA/operadoras_de_plano_de_saude_ativas/Relatorio_cadop.csv",
        ),
    )
    cnes = CnesSettings(
        download_url=_get("CNES_DOWNLOAD_URL", ""),
        manual_input_dir=Path(_get("CNES_MANUAL_INPUT_DIR", "data/raw/cnes/incoming")),
    )

    return Settings(
        app_env=_get("APP_ENV", "local"),
        log_level=_get("LOG_LEVEL", "INFO"),
        log_format=_get("LOG_FORMAT", "json"),
        pipeline_name=_get("PIPELINE_NAME", "pipeline_saude_suplementar"),
        default_reference_period=_get("DEFAULT_REFERENCE_PERIOD", "2024-12"),
        sql_query_row_limit=_get_int("SQL_QUERY_ROW_LIMIT", 200_000),
        writer_connection=writer_connection,
        reader_connection=reader_connection,
        migration_connection=migration_connection,
        ans=ans,
        cnes=cnes,
        data_raw_dir=Path(_get("DATA_RAW_DIR", "data/raw")),
        data_trusted_dir=Path(_get("DATA_TRUSTED_DIR", "data/trusted")),
        data_analytics_dir=Path(_get("DATA_ANALYTICS_DIR", "data/analytics")),
        data_rejected_dir=Path(_get("DATA_REJECTED_DIR", "data/rejected")),
        streamlit_port=_get_int("STREAMLIT_SERVER_PORT", 8501),
        streamlit_cache_ttl_seconds=_get_int("STREAMLIT_CACHE_TTL_SECONDS", 300),
    )
