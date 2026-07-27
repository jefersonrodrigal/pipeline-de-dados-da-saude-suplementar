"""Transformacao (Raw -> Trusted) do cadastro de operadoras ativas da ANS.

Decisao de minimizacao LGPD (ver docs/security.md): o CSV de origem inclui
dados de pessoa fisica do representante legal da operadora (Representante,
Cargo_Representante) e contatos (Telefone, Fax, Endereco_eletronico, DDD).
Nenhum desses campos e necessario para os indicadores do projeto
(distribuicao geografica/beneficiarios por operadora), entao sao
descartados aqui - nunca chegam a Trusted, Analytics ou ao Streamlit.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from src.transform.region_mapping import VALID_UFS
from src.utils.logging_config import get_logger

logger = get_logger(__name__)

_KEEP_RENAME = {
    "REGISTRO_OPERADORA": "cd_operadora_ans",
    "CNPJ": "nr_cnpj",
    "Razao_Social": "nm_razao_social",
    "Nome_Fantasia": "nm_fantasia",
    "Modalidade": "modalidade",
    "Cidade": "nm_municipio_sede",
    "UF": "sg_uf_sede",
    "Data_Registro_ANS": "dt_registro_ans",
}


def _latest_snapshot_dir(raw_dir: Path) -> Path:
    base = raw_dir / "ans_operadoras"
    candidates = sorted((p for p in base.glob("*") if p.is_dir()), reverse=True)
    if not candidates:
        raise FileNotFoundError(
            f"Nenhum snapshot de operadoras encontrado em {base}. "
            f"Rode a etapa 'extract' antes de transformar."
        )
    return candidates[0]


def transform_ans_operadoras(raw_dir: Path) -> tuple[pd.DataFrame, dict[str, int | str]]:
    snapshot_dir = _latest_snapshot_dir(raw_dir)
    csv_path = snapshot_dir / "Relatorio_cadop.csv"

    raw_df = pd.read_csv(csv_path, sep=";", encoding="utf-8", dtype=str, quotechar='"')
    records_read = len(raw_df)

    missing = [col for col in _KEEP_RENAME if col not in raw_df.columns]
    if missing:
        raise ValueError(
            f"Layout inesperado no cadastro de operadoras: colunas ausentes {missing}."
        )

    df = raw_df[list(_KEEP_RENAME.keys())].rename(columns=_KEEP_RENAME)

    for col in (
        "cd_operadora_ans",
        "nr_cnpj",
        "nm_razao_social",
        "nm_fantasia",
        "modalidade",
        "nm_municipio_sede",
    ):
        df[col] = df[col].astype("string").str.strip()

    df["sg_uf_sede"] = df["sg_uf_sede"].astype("string").str.strip().str.upper()
    df.loc[~df["sg_uf_sede"].isin(VALID_UFS), "sg_uf_sede"] = pd.NA

    df["dt_registro_ans"] = pd.to_datetime(df["dt_registro_ans"], errors="coerce").dt.date

    duplicates_found = int(df.duplicated(subset=["cd_operadora_ans"], keep="first").sum())
    df = df.drop_duplicates(subset=["cd_operadora_ans"], keep="first").reset_index(drop=True)

    empty_razao_social = int(
        df["nm_razao_social"].isna().sum() + (df["nm_razao_social"] == "").sum()
    )

    stats: dict[str, int | str] = {
        "registros_lidos": records_read,
        "operadoras_duplicadas_removidas": duplicates_found,
        "razao_social_ausente": empty_razao_social,
        "registros_finais": len(df),
        "snapshot_usado": snapshot_dir.name,
    }
    logger.info("Transformacao de operadoras concluida", extra=stats)
    return df, stats
