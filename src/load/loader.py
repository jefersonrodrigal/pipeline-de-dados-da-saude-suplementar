"""Orquestracao da carga por dataset. Cada funcao roda dentro de UMA
transacao (engine.begin()): se qualquer passo falhar, tudo e revertido -
nao ha risco de deixar staging ou fato em estado parcial.
"""

from __future__ import annotations

import pandas as pd
from sqlalchemy import Engine
from src.load.dimensions import (
    ensure_dim_tempo,
    resolve_operadora_keys,
    upsert_estabelecimentos,
    upsert_localidades,
    upsert_operadoras,
    upsert_tipos_estabelecimento,
)
from src.load.facts import load_fato_beneficiarios, load_fato_rede_assistencial
from src.load.staging import bulk_insert, truncate_staging
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


def load_operadoras(engine: Engine, df: pd.DataFrame) -> dict[str, int]:
    with engine.begin() as connection:
        truncate_staging(connection, "operadoras")
        bulk_insert(connection, df, "operadoras")
        upsert_operadoras(connection)
        truncate_staging(connection, "operadoras")
    logger.info("Carga de operadoras concluida", extra={"registros": len(df)})
    return {"processados": len(df)}


def load_rede_assistencial(
    engine: Engine, df: pd.DataFrame, reference_period: str, id_execucao: int
) -> dict[str, int]:
    with engine.begin() as connection:
        sk_tempo = ensure_dim_tempo(connection, reference_period)
        upsert_localidades(
            connection, df[["cd_municipio_ibge", "nm_municipio", "cd_uf"]].drop_duplicates()
        )
        upsert_tipos_estabelecimento(
            connection, df[["cd_tipo_estabelecimento", "ds_tipo_estabelecimento"]].drop_duplicates()
        )

        truncate_staging(connection, "estabelecimentos")
        bulk_insert(connection, df, "estabelecimentos")
        upsert_estabelecimentos(connection)
        counts = load_fato_rede_assistencial(connection, sk_tempo, id_execucao)
        truncate_staging(connection, "estabelecimentos")

    logger.info("Carga de rede assistencial concluida", extra=counts)
    return counts


def load_beneficiarios(
    engine: Engine, df: pd.DataFrame, reference_period: str, id_execucao: int
) -> dict[str, int]:
    with engine.begin() as connection:
        sk_tempo = ensure_dim_tempo(connection, reference_period)
        localidade_map = upsert_localidades(
            connection, df[["cd_municipio_ibge", "nm_municipio", "cd_uf"]].drop_duplicates()
        )
        operadora_map = resolve_operadora_keys(connection, df["cd_operadora_ans"].unique().tolist())

        staged = df.copy()
        staged["sk_tempo"] = sk_tempo
        staged["sk_operadora"] = (
            staged["cd_operadora_ans"].map(operadora_map).fillna(-1).astype("int64")
        )
        staged["sk_localidade"] = [
            localidade_map.get((cod, uf), -1)
            for cod, uf in zip(staged["cd_municipio_ibge"], staged["cd_uf"], strict=True)
        ]

        # Re-agregar apos resolver chaves substitutas: operadoras distintas
        # sem cadastro (ou municipios "XX") colapsam no mesmo sentinela -1,
        # o que pode reunir, no MESMO grao de chave substituta, linhas que
        # eram distintas no grao de chave natural. Sem este SUM, o INSERT
        # tentaria gravar duas linhas com a mesma chave (uq_fato_beneficiarios_grao)
        # e violaria a constraint - ou, pior, silenciosamente perderia uma delas.
        grain_sk = [
            "sk_tempo",
            "sk_operadora",
            "sk_localidade",
            "tp_sexo",
            "de_faixa_etaria",
            "tipo_vinculo",
            "segmentacao_plano",
        ]
        qty_cols = ["qt_beneficiario_ativo", "qt_beneficiario_aderido", "qt_beneficiario_cancelado"]
        staged = staged.groupby(grain_sk, as_index=False, dropna=False)[qty_cols].sum()
        staged["id_execucao"] = id_execucao

        final_cols = [
            "id_execucao",
            "sk_tempo",
            "sk_operadora",
            "sk_localidade",
            "tp_sexo",
            "de_faixa_etaria",
            "tipo_vinculo",
            "segmentacao_plano",
            "qt_beneficiario_ativo",
            "qt_beneficiario_aderido",
            "qt_beneficiario_cancelado",
        ]
        staged = staged[final_cols]

        truncate_staging(connection, "beneficiarios")
        bulk_insert(connection, staged, "beneficiarios")
        counts = load_fato_beneficiarios(connection, staged_count=len(staged))
        truncate_staging(connection, "beneficiarios")

    logger.info("Carga de beneficiarios concluida", extra=counts)
    return counts
