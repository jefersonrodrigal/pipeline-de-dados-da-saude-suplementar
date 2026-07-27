"""Transformacao (Raw -> Trusted) dos dados consolidados de beneficiarios.

Le todos os ZIPs baixados para uma competencia (um por UF), concatena,
padroniza nomes/tipos de colunas e normaliza os codigos de municipio/UF.

Importante sobre o grao: o arquivo de origem da ANS tem grao mais fino que
a fato_beneficiarios (inclui tambem CD_PLANO, DE_CONTRATACAO_PLANO,
DE_ABRG_GEOGRAFICA_PLANO - atributos de plano que decidimos NAO modelar como
dimensao, ver docs/architecture.md). Por isso, linhas de origem diferentes
podem legitimamente colapsar no mesmo grao da fato (mesma operadora,
municipio, sexo, faixa etaria, vinculo e segmentacao, mas planos distintos).
Tratar isso como "duplicata" e remover a linha SUBESTIMARIA beneficiarios;
o correto e agregar (SUM) as quantidades - e o que este modulo faz.

"Duplicidade exata" (para fins de auditoria/qualidade) e medida ANTES dessa
agregacao, comparando a linha bruta completa como veio da fonte.
"""

from __future__ import annotations

import zipfile
from datetime import date
from pathlib import Path

import pandas as pd
from src.transform.region_mapping import VALID_UFS
from src.utils.logging_config import get_logger

logger = get_logger(__name__)

_EXPECTED_COLUMNS = {
    "CD_OPERADORA": "cd_operadora_ans",
    "SG_UF": "cd_uf",
    "CD_MUNICIPIO": "cd_municipio_ibge",
    "NM_MUNICIPIO": "nm_municipio",
    "TP_SEXO": "tp_sexo",
    "DE_FAIXA_ETARIA": "de_faixa_etaria",
    "TIPO_VINCULO": "tipo_vinculo",
    "DE_SEGMENTACAO_PLANO": "segmentacao_plano",
    "QT_BENEFICIARIO_ATIVO": "qt_beneficiario_ativo",
    "QT_BENEFICIARIO_ADERIDO": "qt_beneficiario_aderido",
    "QT_BENEFICIARIO_CANCELADO": "qt_beneficiario_cancelado",
}

_GRAIN_COLUMNS = [
    "competencia",
    "cd_operadora_ans",
    "cd_municipio_ibge",
    "nm_municipio",
    "cd_uf",
    "tp_sexo",
    "de_faixa_etaria",
    "tipo_vinculo",
    "segmentacao_plano",
]
_INT_COLUMNS = ["qt_beneficiario_ativo", "qt_beneficiario_aderido", "qt_beneficiario_cancelado"]


def _read_single_zip(zip_path: Path) -> pd.DataFrame:
    with zipfile.ZipFile(zip_path) as zf:
        members = [n for n in zf.namelist() if n.lower().endswith(".csv")]
        if not members:
            raise ValueError(f"Nenhum CSV encontrado dentro de {zip_path.name}")
        with zf.open(members[0]) as fh:
            # Le TODAS as colunas originais (nao apenas as usadas no grao da
            # fato) - necessario para detectar duplicidade exata na origem
            # antes de qualquer projecao/agregacao.
            df = pd.read_csv(fh, sep=";", encoding="utf-8", dtype=str, quotechar='"')
    return df


def transform_ans_beneficiarios(
    raw_dir: Path, reference_period: str
) -> tuple[pd.DataFrame, dict[str, int]]:
    """Retorna (dataframe padronizado e agregado no grao da fato, estatisticas)."""
    yyyymm = reference_period.replace("-", "")
    source_dir = raw_dir / "ans_beneficiarios" / yyyymm
    zip_files = sorted(source_dir.glob("pda-024-icb-*.zip"))

    if not zip_files:
        raise FileNotFoundError(
            f"Nenhum arquivo de beneficiarios encontrado em {source_dir}. "
            f"Rode a etapa 'extract' para a competencia {reference_period} antes de transformar."
        )

    frames = []
    for zip_path in zip_files:
        try:
            frames.append(_read_single_zip(zip_path))
        except (zipfile.BadZipFile, ValueError) as exc:
            logger.error(
                "Arquivo corrompido/ilegivel, ignorado",
                extra={"arquivo": zip_path.name, "erro": str(exc)},
            )

    if not frames:
        raise ValueError(f"Todos os arquivos de {source_dir} estavam corrompidos ou vazios.")

    raw_df = pd.concat(frames, ignore_index=True)
    records_read = len(raw_df)

    # Duplicidade exata medida E REMOVIDA sobre a linha bruta completa
    # (todas as colunas originais). Sem o drop_duplicates, uma linha
    # duplicada na fonte seria somada duas vezes na agregacao por grao
    # abaixo, inflando artificialmente a contagem de beneficiarios.
    duplicates_found = int(raw_df.duplicated(keep="first").sum())
    raw_df = raw_df.drop_duplicates(keep="first").reset_index(drop=True)

    missing = [col for col in _EXPECTED_COLUMNS if col not in raw_df.columns]
    if missing:
        raise ValueError(
            f"Layout inesperado no arquivo de beneficiarios: colunas ausentes {missing}. "
            f"O layout da ANS pode ter mudado - confira o dicionario de dados."
        )

    df = raw_df.rename(columns=_EXPECTED_COLUMNS)

    year, month = (int(part) for part in reference_period.split("-"))
    df["competencia"] = date(year, month, 1)

    df["cd_operadora_ans"] = df["cd_operadora_ans"].astype("string").str.strip()
    # NAO fazer zfill(7): o codigo de municipio da ANS ja vem com 6 digitos
    # (codigo IBGE sem o digito verificador) - completar com zero a
    # esquerda produziria um codigo diferente e invalido (ex.: "140010"
    # vira erroneamente "0140010" em vez do IBGE real "1400100").
    df["cd_municipio_ibge"] = df["cd_municipio_ibge"].astype("string").str.strip()
    df["nm_municipio"] = df["nm_municipio"].astype("string").str.strip()
    df["cd_uf"] = df["cd_uf"].astype("string").str.strip().str.upper()
    df.loc[~df["cd_uf"].isin(VALID_UFS), "cd_uf"] = "XX"

    df["tp_sexo"] = df["tp_sexo"].astype("string").str.strip().str.upper().replace({"": pd.NA})
    df["de_faixa_etaria"] = df["de_faixa_etaria"].astype("string").str.strip()
    df["tipo_vinculo"] = df["tipo_vinculo"].astype("string").str.strip()
    df["segmentacao_plano"] = df["segmentacao_plano"].astype("string").str.strip()

    for col in _INT_COLUMNS:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype("int64")

    # Agregacao para o grao da fato: soma as quantidades de linhas de origem
    # que diferem apenas por atributos de plano nao modelados (CD_PLANO etc.)
    aggregated = (
        df.groupby(_GRAIN_COLUMNS, as_index=False, dropna=False)[_INT_COLUMNS]
        .sum()
        .reset_index(drop=True)
    )

    stats = {
        "arquivos_lidos": len(frames),
        "arquivos_ignorados": len(zip_files) - len(frames),
        "registros_lidos": records_read,
        "duplicatas_exatas_na_origem": duplicates_found,
        "linhas_agregadas_no_grao_da_fato": records_read - len(aggregated),
        "registros_finais": len(aggregated),
    }
    logger.info("Transformacao de beneficiarios concluida", extra=stats)
    return aggregated, stats
