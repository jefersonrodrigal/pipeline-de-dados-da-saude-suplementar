"""Upsert das dimensoes (dim.dim_tempo, dim_localidade, dim_operadora,
dim_tipo_estabelecimento, dim_estabelecimento).

dim_tempo e dim_localidade sao Tipo 1 (sem historico - a granularidade
mensal e o codigo de municipio nao "mudam de significado" ao longo do
tempo). dim_operadora e dim_estabelecimento sao Tipo 2 (SCD), implementadas
com MERGE T-SQL - ver a nota de limitacoes do MERGE em
docs/business_rules.md antes de alterar esta logica.
"""

from __future__ import annotations

from datetime import date

import pandas as pd
from sqlalchemy import text
from sqlalchemy.engine import Connection
from src.transform.region_mapping import uf_name, uf_region

_MESES_PT = [
    "",
    "Janeiro",
    "Fevereiro",
    "Março",
    "Abril",
    "Maio",
    "Junho",
    "Julho",
    "Agosto",
    "Setembro",
    "Outubro",
    "Novembro",
    "Dezembro",
]


def ensure_dim_tempo(connection: Connection, reference_period: str) -> int:
    year, month = (int(p) for p in reference_period.split("-"))
    sk_tempo = year * 100 + month
    exists = connection.execute(
        text("SELECT 1 FROM dim.dim_tempo WHERE sk_tempo = :sk"), {"sk": sk_tempo}
    ).first()
    if exists:
        return sk_tempo

    competencia = date(year, month, 1)
    trimestre = (month - 1) // 3 + 1
    semestre = 1 if month <= 6 else 2
    connection.execute(
        text("""
            INSERT INTO dim.dim_tempo
                (sk_tempo, competencia, ano, mes, nome_mes, trimestre, semestre, ano_mes_extenso)
            VALUES
                (:sk, :competencia, :ano, :mes, :nome_mes, :trimestre, :semestre, :extenso)
            """),
        {
            "sk": sk_tempo,
            "competencia": competencia,
            "ano": year,
            "mes": month,
            "nome_mes": _MESES_PT[month],
            "trimestre": trimestre,
            "semestre": semestre,
            "extenso": f"{_MESES_PT[month]}/{year}",
        },
    )
    return sk_tempo


def upsert_localidades(
    connection: Connection, localidades: pd.DataFrame
) -> dict[tuple[str, str], int]:
    """`localidades` precisa ter as colunas cd_municipio_ibge, nm_municipio, cd_uf (unicas)."""
    mapping: dict[tuple[str, str], int] = {}
    unique = localidades.drop_duplicates(subset=["cd_municipio_ibge", "cd_uf"])

    for row in unique.itertuples(index=False):
        cd_municipio = row.cd_municipio_ibge
        cd_uf = row.cd_uf
        if cd_uf == "XX" or not cd_municipio:
            mapping[(cd_municipio, cd_uf)] = -1
            continue

        existing = connection.execute(
            text(
                "SELECT sk_localidade FROM dim.dim_localidade "
                "WHERE cd_municipio_ibge = :cod AND cd_uf = :uf"
            ),
            {"cod": cd_municipio, "uf": cd_uf},
        ).first()
        if existing:
            mapping[(cd_municipio, cd_uf)] = existing[0]
            continue

        result = connection.execute(
            text("""
                INSERT INTO dim.dim_localidade (cd_municipio_ibge, nm_municipio, cd_uf, nm_uf, regiao)
                OUTPUT inserted.sk_localidade
                VALUES (:cod, :nome, :uf, :nome_uf, :regiao)
                """),
            {
                "cod": cd_municipio,
                "nome": row.nm_municipio,
                "uf": cd_uf,
                "nome_uf": uf_name(cd_uf),
                "regiao": uf_region(cd_uf),
            },
        )
        mapping[(cd_municipio, cd_uf)] = result.scalar_one()

    return mapping


def upsert_operadoras(connection: Connection) -> None:
    """SCD2 via UPDATE + INSERT explicitos (nao MERGE - ver docs/business_rules.md
    sobre por que o pipeline prioriza a estrategia explicita e onde o MERGE
    do SQL Server e usado/avaliado no projeto - fact_rede_assistencial, em
    src/load/facts.py). Le a partir de stg.operadoras, que o chamador ja
    deve ter carregado antes de invocar esta funcao.
    """
    today = date.today().isoformat()

    # 1) Fecha vigencias de operadoras cujo atributo relevante mudou.
    connection.execute(
        text("""
            UPDATE dst
            SET dst.dt_fim_vigencia = :hoje, dst.fl_vigente = 0
            FROM dim.dim_operadora dst
            INNER JOIN stg.operadoras src
                ON src.cd_operadora_ans = dst.cd_operadora_ans
            WHERE dst.fl_vigente = 1
              AND (
                    dst.nm_razao_social <> src.nm_razao_social
                 OR ISNULL(dst.modalidade, '') <> ISNULL(src.modalidade, '')
                 OR ISNULL(dst.sg_uf_sede, '') <> ISNULL(src.sg_uf_sede, '')
              )
            """),
        {"hoje": today},
    )

    # 2) Insere versao vigente para operadoras novas OU que tiveram a
    #    vigencia anterior fechada no passo 1.
    connection.execute(
        text("""
            INSERT INTO dim.dim_operadora
                (cd_operadora_ans, nr_cnpj, nm_razao_social, nm_fantasia, modalidade,
                 nm_municipio_sede, sg_uf_sede, dt_registro_ans, dt_inicio_vigencia, fl_vigente)
            SELECT
                src.cd_operadora_ans, src.nr_cnpj, src.nm_razao_social, src.nm_fantasia, src.modalidade,
                src.nm_municipio_sede, src.sg_uf_sede, src.dt_registro_ans, :hoje, 1
            FROM stg.operadoras src
            WHERE NOT EXISTS (
                SELECT 1 FROM dim.dim_operadora dst
                WHERE dst.cd_operadora_ans = src.cd_operadora_ans AND dst.fl_vigente = 1
            )
            """),
        {"hoje": today},
    )


def upsert_tipos_estabelecimento(connection: Connection, tipos: pd.DataFrame) -> dict[str, int]:
    """`tipos` precisa ter cd_tipo_estabelecimento, ds_tipo_estabelecimento (unicas)."""
    mapping: dict[str, int] = {}
    unique = tipos.drop_duplicates(subset=["cd_tipo_estabelecimento"])

    for row in unique.itertuples(index=False):
        codigo = row.cd_tipo_estabelecimento
        if not codigo or pd.isna(codigo):
            mapping[codigo] = -1
            continue
        existing = connection.execute(
            text(
                "SELECT sk_tipo_estabelecimento FROM dim.dim_tipo_estabelecimento WHERE cd_tipo_estabelecimento = :cod"
            ),
            {"cod": codigo},
        ).first()
        if existing:
            mapping[codigo] = existing[0]
            continue
        result = connection.execute(
            text("""
                INSERT INTO dim.dim_tipo_estabelecimento (cd_tipo_estabelecimento, ds_tipo_estabelecimento)
                OUTPUT inserted.sk_tipo_estabelecimento
                VALUES (:cod, :desc)
                """),
            {"cod": codigo, "desc": row.ds_tipo_estabelecimento or f"Tipo {codigo}"},
        )
        mapping[codigo] = result.scalar_one()
    return mapping


def upsert_estabelecimentos(connection: Connection) -> None:
    """SCD2 via UPDATE + INSERT explicitos para dim.dim_estabelecimento -
    mesma logica/racional de `upsert_operadoras`. Le a partir de
    stg.estabelecimentos, que o chamador ja deve ter carregado antes de
    invocar esta funcao."""
    today = date.today().isoformat()

    connection.execute(
        text("""
            UPDATE dst
            SET dst.dt_fim_vigencia = :hoje, dst.fl_vigente = 0
            FROM dim.dim_estabelecimento dst
            INNER JOIN stg.estabelecimentos src ON src.cd_cnes = dst.cd_cnes
            INNER JOIN dim.dim_tipo_estabelecimento tp ON tp.cd_tipo_estabelecimento = src.cd_tipo_estabelecimento
            INNER JOIN dim.dim_localidade loc
                ON loc.cd_municipio_ibge = src.cd_municipio_ibge AND loc.cd_uf = src.cd_uf
            WHERE dst.fl_vigente = 1
              AND (
                    dst.nm_estabelecimento <> src.nm_estabelecimento
                 OR dst.sk_tipo_estabelecimento <> tp.sk_tipo_estabelecimento
                 OR dst.sk_localidade <> loc.sk_localidade
              )
            """),
        {"hoje": today},
    )

    connection.execute(
        text("""
            INSERT INTO dim.dim_estabelecimento
                (cd_cnes, nm_estabelecimento, sk_tipo_estabelecimento, sk_localidade,
                 dt_inicio_vigencia, fl_vigente)
            SELECT
                src.cd_cnes, src.nm_estabelecimento,
                ISNULL(tp.sk_tipo_estabelecimento, -1), ISNULL(loc.sk_localidade, -1),
                :hoje, 1
            FROM stg.estabelecimentos src
            LEFT JOIN dim.dim_tipo_estabelecimento tp ON tp.cd_tipo_estabelecimento = src.cd_tipo_estabelecimento
            LEFT JOIN dim.dim_localidade loc
                ON loc.cd_municipio_ibge = src.cd_municipio_ibge AND loc.cd_uf = src.cd_uf
            WHERE NOT EXISTS (
                SELECT 1 FROM dim.dim_estabelecimento dst
                WHERE dst.cd_cnes = src.cd_cnes AND dst.fl_vigente = 1
            )
            """),
        {"hoje": today},
    )


def resolve_estabelecimento_keys(connection: Connection, codes: list[str]) -> dict[str, int]:
    if not codes:
        return {}
    rows = (
        connection.execute(
            text(
                "SELECT cd_cnes, sk_estabelecimento FROM dim.dim_estabelecimento WHERE fl_vigente = 1"
            )
        )
        .tuples()
        .all()
    )
    mapping: dict[str, int] = dict(rows)
    return {code: mapping.get(code, -1) for code in codes}


def resolve_operadora_keys(connection: Connection, codes: list[str]) -> dict[str, int]:
    """Mapeia cd_operadora_ans -> sk_operadora vigente (fallback -1 = nao cadastrada)."""
    if not codes:
        return {}
    rows = (
        connection.execute(
            text(
                "SELECT cd_operadora_ans, sk_operadora FROM dim.dim_operadora WHERE fl_vigente = 1"
            )
        )
        .tuples()
        .all()
    )
    mapping: dict[str, int] = dict(rows)
    return {code: mapping.get(code, -1) for code in codes}
