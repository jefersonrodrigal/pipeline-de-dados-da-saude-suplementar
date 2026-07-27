"""Orquestrador do pipeline de dados da saude suplementar.

Uso:
    python -m src.main --stage all --reference-period 2024-12 --source ans
    python -m src.main --stage extract
    python -m src.main --stage transform --source cnes
    python -m src.main --stage load --force

Cada etapa e independente, idempotente e registra uma linha em
aud.execucao_pipeline (inicio/fim/status/contadores). A execucao para
imediatamente se uma etapa critica falhar (status FAILED); PARTIAL nao
interrompe o `--stage all`.
"""

from __future__ import annotations

import argparse
import sys
import zipfile
from collections.abc import Callable
from pathlib import Path

from sqlalchemy import Engine
from src.config.settings import Settings, get_settings
from src.extract.ans_beneficiarios import extract_ans_beneficiarios
from src.extract.ans_operadoras import extract_ans_operadoras
from src.extract.cnes_estabelecimentos import extract_cnes_estabelecimentos
from src.load.audit import (
    finish_execucao,
    start_execucao,
    write_quality_results,
    write_rejected_records,
)
from src.load.loader import load_beneficiarios, load_operadoras, load_rede_assistencial
from src.models.pipeline import StageStatus
from src.quality.engine import run_validation
from src.quality.rejected_writer import write_rejected_records as write_rejected_files
from src.quality.validators import beneficiarios_rules, estabelecimentos_rules, operadoras_rules
from src.services.aggregate import refresh_resumo_mensal_uf
from src.services.export_analytics import export_analytics as export_analytics_service
from src.services.views import refresh_views as refresh_views_service
from src.transform.ans_beneficiarios import transform_ans_beneficiarios
from src.transform.ans_operadoras import transform_ans_operadoras
from src.transform.cnes_estabelecimentos import transform_cnes_estabelecimentos
from src.transform.writer import read_trusted_parquet, write_trusted_parquet
from src.utils.db import get_engine
from src.utils.logging_config import configure_logging, get_logger
from src.utils.period import to_sk_tempo

logger = get_logger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
STAGES = [
    "extract",
    "validate_raw",
    "transform",
    "validate_trusted",
    "load",
    "aggregate",
    "refresh_views",
    "export_analytics",
]
SOURCES = ["ans", "cnes", "all"]


def stage_extract(
    settings: Settings, engine: Engine, reference_period: str, source: str, force: bool
) -> bool:
    ok = True
    if source in ("ans", "all"):
        for label, fn in (
            (
                "ans_beneficiarios",
                lambda: extract_ans_beneficiarios(
                    settings.ans, settings.data_raw_dir, reference_period, force
                ),
            ),
            (
                "ans_operadoras",
                lambda: extract_ans_operadoras(
                    settings.ans.operadoras_url, settings.data_raw_dir, reference_period, force
                ),
            ),
        ):
            with engine.begin() as conn:
                id_exec = start_execucao(
                    conn, settings.pipeline_name, "extract", reference_period, label
                )
            result, _files = fn()
            with engine.begin() as conn:
                finish_execucao(
                    conn,
                    id_exec,
                    result.status.value,
                    qt_recebida=result.records_processed,
                    qt_valida=result.records_accepted,
                    qt_rejeitada=result.records_rejected,
                    mensagem_erro="; ".join(result.errors) or None,
                )
            logger.info("Extract concluido", extra={"fonte": label, "status": result.status.value})
            ok = ok and result.status != StageStatus.FAILED

    if source in ("cnes", "all"):
        with engine.begin() as conn:
            id_exec = start_execucao(
                conn, settings.pipeline_name, "extract", reference_period, "cnes"
            )
        result, _files = extract_cnes_estabelecimentos(
            settings.cnes, settings.data_raw_dir, reference_period, PROJECT_ROOT, force
        )
        with engine.begin() as conn:
            finish_execucao(
                conn,
                id_exec,
                result.status.value,
                qt_recebida=result.records_processed,
                qt_valida=result.records_accepted,
                qt_rejeitada=result.records_rejected,
                mensagem_erro="; ".join(result.errors) or None,
            )
        logger.info("Extract concluido", extra={"fonte": "cnes", "status": result.status.value})
        ok = ok and result.status != StageStatus.FAILED
    return ok


def stage_validate_raw(
    settings: Settings, engine: Engine, reference_period: str, source: str
) -> bool:
    """Checagem minima da camada Raw: arquivo existe, tem tamanho > 0 e (no
    caso de ZIPs) abre sem erro de integridade - antes de gastar tempo
    transformando um arquivo corrompido."""
    ok = True
    with engine.begin() as conn:
        id_exec = start_execucao(
            conn, settings.pipeline_name, "validate_raw", reference_period, source
        )

    checked = 0
    failures: list[str] = []
    if source in ("ans", "all"):
        yyyymm = reference_period.replace("-", "")
        for zip_path in sorted(
            (settings.data_raw_dir / "ans_beneficiarios" / yyyymm).glob("*.zip")
        ):
            checked += 1
            try:
                if zip_path.stat().st_size == 0:
                    raise ValueError("arquivo vazio")
                with zipfile.ZipFile(zip_path) as zf:
                    if zf.testzip() is not None:
                        raise ValueError("zip corrompido")
            except (OSError, ValueError, zipfile.BadZipFile) as exc:
                failures.append(f"{zip_path.name}: {exc}")

    with engine.begin() as conn:
        status = StageStatus.FAILED if failures else StageStatus.SUCCESS
        finish_execucao(
            conn,
            id_exec,
            status.value,
            qt_recebida=checked,
            qt_valida=checked - len(failures),
            qt_rejeitada=len(failures),
            mensagem_erro="; ".join(failures) or None,
        )
    ok = not failures
    logger.info(
        "Validate_raw concluido", extra={"arquivos_checados": checked, "falhas": len(failures)}
    )
    return ok


def _transform_and_persist(
    settings: Settings, engine: Engine, reference_period: str, dataset: str, transform_fn
) -> bool:
    with engine.begin() as conn:
        id_exec = start_execucao(
            conn, settings.pipeline_name, "transform", reference_period, dataset
        )
    try:
        df, stats = transform_fn()
        write_trusted_parquet(df, settings.data_trusted_dir, dataset, reference_period)
        status = StageStatus.SUCCESS
        error_msg = None
    except (FileNotFoundError, ValueError) as exc:
        df, stats, status, error_msg = None, {}, StageStatus.FAILED, str(exc)

    with engine.begin() as conn:
        finish_execucao(
            conn,
            id_exec,
            status.value,
            qt_recebida=stats.get("registros_lidos"),
            qt_valida=stats.get("registros_finais"),
            mensagem_erro=error_msg,
        )
    logger.info("Transform concluido", extra={"dataset": dataset, "status": status.value, **stats})
    return status != StageStatus.FAILED


def stage_transform(settings: Settings, engine: Engine, reference_period: str, source: str) -> bool:
    ok = True
    if source in ("ans", "all"):
        ok &= _transform_and_persist(
            settings,
            engine,
            reference_period,
            "operadoras",
            lambda: transform_ans_operadoras(settings.data_raw_dir),
        )
        ok &= _transform_and_persist(
            settings,
            engine,
            reference_period,
            "beneficiarios",
            lambda: transform_ans_beneficiarios(settings.data_raw_dir, reference_period),
        )
    if source in ("cnes", "all"):
        ok &= _transform_and_persist(
            settings,
            engine,
            reference_period,
            "estabelecimentos",
            lambda: transform_cnes_estabelecimentos(settings.data_raw_dir, reference_period),
        )
    return ok


def _validate_and_persist(
    settings: Settings,
    engine: Engine,
    reference_period: str,
    dataset: str,
    rules_factory: Callable[[], list],
) -> bool:
    """`rules_factory` e sempre uma funcao SEM argumentos (ver chamadores em
    stage_validate_trusted) - qualquer dependencia externa (ex.: codigos de
    operadoras conhecidos) ja deve estar capturada via closure antes de
    chegar aqui."""
    with engine.begin() as conn:
        id_exec = start_execucao(
            conn, settings.pipeline_name, "validate_trusted", reference_period, dataset
        )
    try:
        df = read_trusted_parquet(settings.data_trusted_dir, dataset, reference_period)
    except FileNotFoundError as exc:
        with engine.begin() as conn:
            finish_execucao(conn, id_exec, StageStatus.FAILED.value, mensagem_erro=str(exc))
        return False

    outcome = run_validation(df, rules_factory(), dataset)
    write_trusted_parquet(outcome.accepted_df, settings.data_trusted_dir, dataset, reference_period)
    write_rejected_files(
        outcome.rejected_records, settings.data_rejected_dir, dataset, id_exec, reference_period
    )

    with engine.begin() as conn:
        write_quality_results(conn, id_exec, "validate_trusted", outcome.rule_results)
        write_rejected_records(conn, id_exec, dataset, outcome.rejected_records)
        status = StageStatus.SUCCESS if outcome.accepted_df.shape[0] else StageStatus.FAILED
        finish_execucao(
            conn,
            id_exec,
            status.value,
            qt_recebida=len(df),
            qt_valida=len(outcome.accepted_df),
            qt_rejeitada=len(outcome.rejected_records),
        )
    logger.info(
        "Validate_trusted concluido",
        extra={
            "dataset": dataset,
            "aceitos": len(outcome.accepted_df),
            "rejeitados": len(outcome.rejected_records),
        },
    )
    return True


def stage_validate_trusted(
    settings: Settings, engine: Engine, reference_period: str, source: str
) -> bool:
    ok = True
    known_operadoras: set[str] | None = None
    if source in ("ans", "all"):
        ok &= _validate_and_persist(
            settings, engine, reference_period, "operadoras", operadoras_rules
        )
        try:
            known_operadoras = set(
                read_trusted_parquet(settings.data_trusted_dir, "operadoras", reference_period)[
                    "cd_operadora_ans"
                ]
            )
        except FileNotFoundError:
            known_operadoras = None
        ok &= _validate_and_persist(
            settings,
            engine,
            reference_period,
            "beneficiarios",
            lambda: beneficiarios_rules(known_operadora_codes=known_operadoras),
        )
    if source in ("cnes", "all"):
        ok &= _validate_and_persist(
            settings, engine, reference_period, "estabelecimentos", estabelecimentos_rules
        )
    return ok


def stage_load(settings: Settings, engine: Engine, reference_period: str, source: str) -> bool:
    ok = True
    if source in ("ans", "all"):
        with engine.begin() as conn:
            id_exec = start_execucao(
                conn, settings.pipeline_name, "load", reference_period, "operadoras"
            )
        try:
            op_df = read_trusted_parquet(settings.data_trusted_dir, "operadoras", reference_period)
            counts = load_operadoras(engine, op_df)
            with engine.begin() as conn:
                finish_execucao(
                    conn, id_exec, StageStatus.SUCCESS.value, qt_valida=counts["processados"]
                )
        except (FileNotFoundError, RuntimeError) as exc:
            with engine.begin() as conn:
                finish_execucao(conn, id_exec, StageStatus.FAILED.value, mensagem_erro=str(exc))
            ok = False

    if source in ("cnes", "all"):
        with engine.begin() as conn:
            id_exec = start_execucao(
                conn, settings.pipeline_name, "load", reference_period, "estabelecimentos"
            )
        try:
            est_df = read_trusted_parquet(
                settings.data_trusted_dir, "estabelecimentos", reference_period
            )
            counts = load_rede_assistencial(engine, est_df, reference_period, id_exec)
            with engine.begin() as conn:
                finish_execucao(
                    conn,
                    id_exec,
                    StageStatus.SUCCESS.value,
                    qt_valida=counts["atualizados"] + counts["inseridos"],
                )
        except (FileNotFoundError, RuntimeError) as exc:
            with engine.begin() as conn:
                finish_execucao(conn, id_exec, StageStatus.FAILED.value, mensagem_erro=str(exc))
            ok = False

    if source in ("ans", "all"):
        with engine.begin() as conn:
            id_exec = start_execucao(
                conn, settings.pipeline_name, "load", reference_period, "beneficiarios"
            )
        try:
            ben_df = read_trusted_parquet(
                settings.data_trusted_dir, "beneficiarios", reference_period
            )
            counts = load_beneficiarios(engine, ben_df, reference_period, id_exec)
            with engine.begin() as conn:
                finish_execucao(
                    conn,
                    id_exec,
                    StageStatus.SUCCESS.value,
                    qt_recebida=len(ben_df),
                    qt_valida=counts["atualizados"] + counts["inseridos"],
                )
        except (FileNotFoundError, RuntimeError) as exc:
            with engine.begin() as conn:
                finish_execucao(conn, id_exec, StageStatus.FAILED.value, mensagem_erro=str(exc))
            ok = False
    return ok


def stage_aggregate(settings: Settings, engine: Engine, reference_period: str) -> bool:
    with engine.begin() as conn:
        id_exec = start_execucao(conn, settings.pipeline_name, "aggregate", reference_period)
    try:
        rows = refresh_resumo_mensal_uf(engine, to_sk_tempo(reference_period))
        with engine.begin() as conn:
            finish_execucao(conn, id_exec, StageStatus.SUCCESS.value, qt_valida=rows)
        return True
    except Exception as exc:  # noqa: BLE001 - queremos registrar qualquer falha de SQL
        with engine.begin() as conn:
            finish_execucao(conn, id_exec, StageStatus.FAILED.value, mensagem_erro=str(exc))
        return False


def stage_refresh_views(
    settings: Settings, writer_engine: Engine, migration_engine: Engine, reference_period: str
) -> bool:
    with writer_engine.begin() as conn:
        id_exec = start_execucao(conn, settings.pipeline_name, "refresh_views", reference_period)
    try:
        applied = refresh_views_service(migration_engine)
        with writer_engine.begin() as conn:
            finish_execucao(conn, id_exec, StageStatus.SUCCESS.value, qt_valida=len(applied))
        return True
    except Exception as exc:  # noqa: BLE001
        with writer_engine.begin() as conn:
            finish_execucao(conn, id_exec, StageStatus.FAILED.value, mensagem_erro=str(exc))
        return False


def stage_export_analytics(settings: Settings, engine: Engine, reference_period: str) -> bool:
    with engine.begin() as conn:
        id_exec = start_execucao(conn, settings.pipeline_name, "export_analytics", reference_period)
    try:
        written = export_analytics_service(engine, settings.data_analytics_dir, reference_period)
        with engine.begin() as conn:
            finish_execucao(conn, id_exec, StageStatus.SUCCESS.value, qt_valida=len(written))
        return True
    except Exception as exc:  # noqa: BLE001
        with engine.begin() as conn:
            finish_execucao(conn, id_exec, StageStatus.FAILED.value, mensagem_erro=str(exc))
        return False


def run(stage: str, reference_period: str, source: str, force: bool) -> int:
    settings = get_settings()
    configure_logging(settings.log_level, settings.log_format)
    writer_engine = get_engine(settings.writer_connection)
    migration_engine = get_engine(settings.migration_connection)

    pipeline: list[tuple[str, Callable[[], bool]]] = [
        (
            "extract",
            lambda: stage_extract(settings, writer_engine, reference_period, source, force),
        ),
        (
            "validate_raw",
            lambda: stage_validate_raw(settings, writer_engine, reference_period, source),
        ),
        ("transform", lambda: stage_transform(settings, writer_engine, reference_period, source)),
        (
            "validate_trusted",
            lambda: stage_validate_trusted(settings, writer_engine, reference_period, source),
        ),
        ("load", lambda: stage_load(settings, writer_engine, reference_period, source)),
        ("aggregate", lambda: stage_aggregate(settings, writer_engine, reference_period)),
        (
            "refresh_views",
            lambda: stage_refresh_views(
                settings, writer_engine, migration_engine, reference_period
            ),
        ),
        (
            "export_analytics",
            lambda: stage_export_analytics(settings, writer_engine, reference_period),
        ),
    ]

    stages_to_run = pipeline if stage == "all" else [item for item in pipeline if item[0] == stage]

    for name, fn in stages_to_run:
        logger.info(
            "Iniciando etapa", extra={"etapa": name, "periodo": reference_period, "fonte": source}
        )
        success = fn()
        if not success:
            logger.error("Etapa falhou, interrompendo pipeline", extra={"etapa": name})
            return 1
        logger.info("Etapa concluida com sucesso", extra={"etapa": name})

    return 0


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Pipeline de dados da saude suplementar")
    parser.add_argument("--stage", choices=["all", *STAGES], default="all")
    parser.add_argument("--reference-period", dest="reference_period", default=None, help="AAAA-MM")
    parser.add_argument("--source", choices=SOURCES, default="all")
    parser.add_argument("--force", action="store_true", default=False)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    reference_period = args.reference_period or get_settings().default_reference_period
    return run(args.stage, reference_period, args.source, args.force)


if __name__ == "__main__":
    sys.exit(main())
