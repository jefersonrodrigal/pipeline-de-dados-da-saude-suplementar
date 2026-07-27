"""Transformacao (Raw -> Trusted) dos estabelecimentos de saude (CNES).

Le todos os arquivos CSV/TXT depositados em data/raw/cnes/{periodo}/ (ver
src/extract/cnes_estabelecimentos.py) e aplica o mapeamento configuravel de
src/transform/cnes_column_mapping.py. Arquivos .dbc (formato compactado
proprio do DATASUS) NAO sao suportados aqui - precisam ser convertidos para
CSV/TXT antes (ferramenta oficial "TabWin"/"blast.exe"), pois nao ha uma
biblioteca Python confiavel e amplamente mantida para descompacta-los.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from src.transform.cnes_column_mapping import CNES_COLUMN_MAP, REQUIRED_STANDARD_COLUMNS
from src.transform.region_mapping import VALID_UFS
from src.utils.logging_config import get_logger

logger = get_logger(__name__)

_SUPPORTED_SUFFIXES = {".csv", ".txt"}


def _read_any(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, sep=None, engine="python", dtype=str, encoding="utf-8")


def transform_cnes_estabelecimentos(
    raw_dir: Path, reference_period: str
) -> tuple[pd.DataFrame, dict[str, int]]:
    source_dir = raw_dir / "cnes" / reference_period.replace("-", "")
    files = sorted(p for p in source_dir.glob("*") if p.suffix.lower() in _SUPPORTED_SUFFIXES)

    if not files:
        raise FileNotFoundError(
            f"Nenhum arquivo CSV/TXT de estabelecimentos encontrado em {source_dir}. "
            f"Rode a etapa 'extract' (fonte cnes) antes de transformar. Arquivos .dbc "
            f"precisam ser convertidos para CSV antes de serem usados."
        )

    frames = []
    for path in files:
        try:
            frames.append(_read_any(path))
        except (pd.errors.ParserError, UnicodeDecodeError) as exc:
            logger.error(
                "Arquivo CNES ilegivel, ignorado", extra={"arquivo": path.name, "erro": str(exc)}
            )

    if not frames:
        raise ValueError(f"Todos os arquivos de {source_dir} eram ilegiveis.")

    raw_df = pd.concat(frames, ignore_index=True)
    records_read = len(raw_df)

    rename_map = {col: target for col, target in CNES_COLUMN_MAP.items() if col in raw_df.columns}
    df = raw_df.rename(columns=rename_map)

    missing_required = [c for c in REQUIRED_STANDARD_COLUMNS if c not in df.columns]
    if missing_required:
        raise ValueError(
            f"Layout do CNES nao reconhecido: colunas obrigatorias ausentes {missing_required}. "
            f"Ajuste src/transform/cnes_column_mapping.py conforme o dicionario de dados do "
            f"arquivo baixado (colunas disponiveis: {list(raw_df.columns)})."
        )

    df["cd_cnes"] = df["cd_cnes"].astype("string").str.strip()
    df["nm_estabelecimento"] = df["nm_estabelecimento"].astype("string").str.strip()
    # Mantido como veio da fonte (sem zfill): ver nota em
    # src/transform/ans_beneficiarios.py sobre nao inventar digitos.
    df["cd_municipio_ibge"] = df["cd_municipio_ibge"].astype("string").str.strip()

    if "cd_uf" in df.columns:
        df["cd_uf"] = df["cd_uf"].astype("string").str.strip().str.upper()
        df.loc[~df["cd_uf"].isin(VALID_UFS), "cd_uf"] = "XX"
    else:
        df["cd_uf"] = "XX"

    if "nm_municipio" not in df.columns:
        df["nm_municipio"] = "Não informado"
    else:
        df["nm_municipio"] = df["nm_municipio"].astype("string").str.strip()

    if "cd_tipo_estabelecimento" in df.columns:
        df["cd_tipo_estabelecimento"] = df["cd_tipo_estabelecimento"].astype("string").str.strip()
    else:
        df["cd_tipo_estabelecimento"] = pd.NA

    if "ds_tipo_estabelecimento" in df.columns:
        df["ds_tipo_estabelecimento"] = df["ds_tipo_estabelecimento"].astype("string").str.strip()
    else:
        df["ds_tipo_estabelecimento"] = df["cd_tipo_estabelecimento"].apply(
            lambda c: f"Tipo {c}" if pd.notna(c) else pd.NA
        )

    df["periodo_referencia"] = reference_period

    missing_cnes = int(df["cd_cnes"].isna().sum() + (df["cd_cnes"] == "").sum())
    duplicates_found = int(df.duplicated(subset=["cd_cnes"], keep="first").sum())
    df = df.drop_duplicates(subset=["cd_cnes"], keep="first").reset_index(drop=True)

    keep_cols = [
        "cd_cnes",
        "nm_estabelecimento",
        "cd_tipo_estabelecimento",
        "ds_tipo_estabelecimento",
        "cd_municipio_ibge",
        "nm_municipio",
        "cd_uf",
        "periodo_referencia",
    ]
    df = df[keep_cols]

    stats = {
        "arquivos_lidos": len(frames),
        "registros_lidos": records_read,
        "cnes_ausente_ou_vazio": missing_cnes,
        "estabelecimentos_duplicados_removidos": duplicates_found,
        "registros_finais": len(df),
    }
    logger.info("Transformacao de estabelecimentos (CNES) concluida", extra=stats)
    return df, stats
