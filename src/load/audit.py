"""Escrita nas tabelas de auditoria (aud.execucao_pipeline,
fact.fato_qualidade_dados, rej.registros_rejeitados).

`start_execucao`/`finish_execucao` sao usados por src/main.py ao redor de
CADA etapa do pipeline (extract, validate_raw, transform, ...), dando um
`id_execucao` por etapa executada - o que permite consultar, por exemplo,
"quanto tempo levou a etapa transform na ultima execucao" isoladamente.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime

from sqlalchemy import text
from sqlalchemy.engine import Connection
from src.quality.engine import RuleResult


def start_execucao(
    connection: Connection,
    nm_pipeline: str,
    nm_etapa: str,
    periodo_referencia: str | None = None,
    fonte: str | None = None,
    origem_arquivo: str | None = None,
    hash_arquivo: str | None = None,
) -> int:
    result = connection.execute(
        text("""
            INSERT INTO aud.execucao_pipeline
                (nm_pipeline, nm_etapa, dh_inicio, periodo_referencia, fonte,
                 origem_arquivo, hash_arquivo, status)
            OUTPUT inserted.id_execucao
            VALUES (:pipeline, :etapa, :inicio, :periodo, :fonte, :origem, :hash, 'RUNNING')
            """),
        {
            "pipeline": nm_pipeline,
            "etapa": nm_etapa,
            "inicio": datetime.now(UTC),
            "periodo": periodo_referencia,
            "fonte": fonte,
            "origem": origem_arquivo,
            "hash": hash_arquivo,
        },
    )
    return result.scalar_one()


def finish_execucao(
    connection: Connection,
    id_execucao: int,
    status: str,
    qt_recebida: int | None = None,
    qt_valida: int | None = None,
    qt_rejeitada: int | None = None,
    regra_violada: str | None = None,
    mensagem_erro: str | None = None,
) -> None:
    connection.execute(
        text("""
            UPDATE aud.execucao_pipeline
            SET dh_fim = :fim, status = :status, qt_recebida = :recebida,
                qt_valida = :valida, qt_rejeitada = :rejeitada,
                regra_violada = :regra, mensagem_erro = :mensagem
            WHERE id_execucao = :id
            """),
        {
            "fim": datetime.now(UTC),
            "status": status,
            "recebida": qt_recebida,
            "valida": qt_valida,
            "rejeitada": qt_rejeitada,
            "regra": regra_violada,
            "mensagem": mensagem_erro,
            "id": id_execucao,
        },
    )


def write_quality_results(
    connection: Connection, id_execucao: int, nm_etapa: str, rule_results: list[RuleResult]
) -> None:
    if not rule_results:
        return
    connection.execute(
        text("""
            INSERT INTO fact.fato_qualidade_dados
                (id_execucao, nm_etapa, nm_regra, ds_regra, qt_avaliada, qt_aceita, qt_rejeitada, severidade)
            VALUES (:id_execucao, :etapa, :regra, :descricao, :avaliada, :aceita, :rejeitada, :severidade)
            """),
        [
            {
                "id_execucao": id_execucao,
                "etapa": nm_etapa,
                "regra": r.rule.name,
                "descricao": r.rule.description,
                "avaliada": r.evaluated,
                "aceita": r.accepted,
                "rejeitada": r.violated,
                "severidade": r.rule.severity.value,
            }
            for r in rule_results
        ],
    )


def write_rejected_records(
    connection: Connection, id_execucao: int, dataset_name: str, rejected_records: list[dict]
) -> None:
    if not rejected_records:
        return
    connection.execute(
        text("""
            INSERT INTO rej.registros_rejeitados (id_execucao, nm_dataset, regra_violada, motivo, registro_json)
            VALUES (:id_execucao, :dataset, :regra, :motivo, :registro)
            """),
        [
            {
                "id_execucao": id_execucao,
                "dataset": dataset_name,
                "regra": r["regra_violada"],
                "motivo": r["motivo"],
                "registro": json.dumps(r["registro"], ensure_ascii=False, default=str),
            }
            for r in rejected_records
        ],
    )
