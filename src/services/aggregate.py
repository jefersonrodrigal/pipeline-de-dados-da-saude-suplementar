"""Etapa 'aggregate': materializa rpt.tb_resumo_mensal_uf para a competencia
corrente. Roda ANTES de 'refresh_views' (ver src/main.py), entao consulta
fact/dim diretamente - nao pode depender das views de rpt.
"""

from __future__ import annotations

from sqlalchemy import Engine, text
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


def refresh_resumo_mensal_uf(engine: Engine, sk_tempo: int) -> int:
    with engine.begin() as connection:
        connection.execute(
            text("DELETE FROM rpt.tb_resumo_mensal_uf WHERE sk_tempo = :sk"), {"sk": sk_tempo}
        )
        result = connection.execute(
            text("""
                INSERT INTO rpt.tb_resumo_mensal_uf
                    (sk_tempo, cd_uf, nm_uf, regiao, qt_beneficiarios_ativos,
                     qt_estabelecimentos, razao_beneficiarios_por_estabelecimento)
                SELECT
                    :sk AS sk_tempo,
                    l.cd_uf,
                    MAX(l.nm_uf) AS nm_uf,
                    MAX(l.regiao) AS regiao,
                    ISNULL(SUM(b.qt_beneficiario_ativo), 0) AS qt_beneficiarios_ativos,
                    ISNULL(MAX(r.qt_estabelecimentos), 0) AS qt_estabelecimentos,
                    CASE WHEN ISNULL(MAX(r.qt_estabelecimentos), 0) = 0 THEN NULL
                         ELSE CAST(ISNULL(SUM(b.qt_beneficiario_ativo), 0) AS DECIMAL(14, 2)) / MAX(r.qt_estabelecimentos)
                    END AS razao
                FROM dim.dim_localidade l
                LEFT JOIN fact.fato_beneficiarios b
                    ON b.sk_localidade = l.sk_localidade AND b.sk_tempo = :sk
                LEFT JOIN (
                    SELECT sk_localidade, SUM(qt_estabelecimento) AS qt_estabelecimentos
                    FROM fact.fato_rede_assistencial
                    WHERE sk_tempo = :sk
                    GROUP BY sk_localidade
                ) r ON r.sk_localidade = l.sk_localidade
                WHERE l.sk_localidade <> -1
                GROUP BY l.cd_uf
                HAVING ISNULL(SUM(b.qt_beneficiario_ativo), 0) > 0 OR ISNULL(MAX(r.qt_estabelecimentos), 0) > 0
                """),
            {"sk": sk_tempo},
        )
        rows = result.rowcount
    logger.info(
        "Agregacao rpt.tb_resumo_mensal_uf atualizada", extra={"sk_tempo": sk_tempo, "linhas": rows}
    )
    return rows
