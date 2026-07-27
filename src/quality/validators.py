"""Conjuntos de regras de qualidade por dataset (Trusted).

Ver src/quality/engine.py para o funcionamento do motor de regras.
"""

from __future__ import annotations

import pandas as pd
from src.quality.engine import Rule, Severity
from src.transform.region_mapping import VALID_UFS


def _required_columns_present(df: pd.DataFrame, required: list[str]) -> list[str]:
    """Checagem de schema (nao por linha) - retorna colunas ausentes."""
    return [c for c in required if c not in df.columns]


def beneficiarios_rules(known_operadora_codes: set[str] | None = None) -> list[Rule]:
    def negative_values(df: pd.DataFrame) -> pd.Series:
        cols = ["qt_beneficiario_ativo", "qt_beneficiario_aderido", "qt_beneficiario_cancelado"]
        return (df[cols] < 0).any(axis=1)

    def implausible_volume(df: pd.DataFrame) -> pd.Series:
        # Limite de plausibilidade: nenhuma linha do grao (operadora x
        # municipio x faixa etaria x ...) deveria ter mais de 500 mil
        # beneficiarios ativos - acima disso e mais provavel um erro de
        # parsing/agregacao do que um dado real.
        return df["qt_beneficiario_ativo"] > 500_000

    def invalid_uf(df: pd.DataFrame) -> pd.Series:
        return ~df["cd_uf"].isin(VALID_UFS)

    def missing_municipio_code(df: pd.DataFrame) -> pd.Series:
        return df["cd_municipio_ibge"].isna() | (
            df["cd_municipio_ibge"].astype("string").str.len() == 0
        )

    def municipio_code_format(df: pd.DataFrame) -> pd.Series:
        codes = df["cd_municipio_ibge"].astype("string")
        return ~codes.str.match(r"^\d{6,7}$", na=False) & (df["cd_uf"] != "XX")

    def invalid_period(df: pd.DataFrame) -> pd.Series:
        return df["competencia"].isna()

    def unknown_operadora(df: pd.DataFrame) -> pd.Series:
        if not known_operadora_codes:
            return pd.Series(False, index=df.index)
        return ~df["cd_operadora_ans"].isin(known_operadora_codes)

    def municipio_uf_inconsistency(df: pd.DataFrame) -> pd.Series:
        # Um mesmo codigo de municipio nao deveria aparecer com nomes de
        # municipio diferentes dentro do mesmo arquivo/competencia.
        valid = df[df["cd_uf"] != "XX"]
        if valid.empty:
            return pd.Series(False, index=df.index)
        distinct_names = valid.groupby("cd_municipio_ibge")["nm_municipio"].transform("nunique")
        mask = pd.Series(False, index=df.index)
        mask.loc[valid.index] = distinct_names > 1
        return mask

    return [
        Rule(
            "valores_negativos",
            "Quantidade de beneficiarios negativa",
            Severity.ERROR,
            negative_values,
        ),
        Rule(
            "volume_implausivel",
            "Quantidade de beneficiarios acima do limite plausivel (500.000)",
            Severity.ERROR,
            implausible_volume,
        ),
        Rule(
            "uf_invalida", "Codigo de UF fora da lista de UFs validas", Severity.ERROR, invalid_uf
        ),
        Rule(
            "municipio_ausente",
            "Codigo de municipio ausente ou vazio",
            Severity.ERROR,
            missing_municipio_code,
        ),
        Rule(
            "municipio_formato_invalido",
            "Codigo de municipio fora do formato esperado (6-7 digitos)",
            Severity.WARNING,
            municipio_code_format,
        ),
        Rule(
            "periodo_invalido",
            "Competencia (periodo de referencia) invalida",
            Severity.ERROR,
            invalid_period,
        ),
        Rule(
            "operadora_inexistente",
            "Codigo de operadora nao encontrado no cadastro ANS",
            Severity.WARNING,
            unknown_operadora,
        ),
        Rule(
            "municipio_uf_inconsistente",
            "Mesmo codigo de municipio associado a nomes diferentes",
            Severity.WARNING,
            municipio_uf_inconsistency,
        ),
    ]


def operadoras_rules() -> list[Rule]:
    def missing_code(df: pd.DataFrame) -> pd.Series:
        return df["cd_operadora_ans"].isna() | (
            df["cd_operadora_ans"].astype("string").str.len() == 0
        )

    def missing_razao_social(df: pd.DataFrame) -> pd.Series:
        return df["nm_razao_social"].isna() | (
            df["nm_razao_social"].astype("string").str.len() == 0
        )

    def invalid_cnpj_format(df: pd.DataFrame) -> pd.Series:
        cnpj = df["nr_cnpj"].astype("string")
        return ~cnpj.str.match(r"^\d{14}$", na=False)

    def duplicated_code(df: pd.DataFrame) -> pd.Series:
        return df.duplicated(subset=["cd_operadora_ans"], keep="first")

    return [
        Rule(
            "codigo_operadora_ausente",
            "Codigo de registro ANS ausente",
            Severity.ERROR,
            missing_code,
        ),
        Rule("razao_social_ausente", "Razao social ausente", Severity.ERROR, missing_razao_social),
        Rule(
            "cnpj_formato_invalido",
            "CNPJ fora do formato esperado (14 digitos)",
            Severity.WARNING,
            invalid_cnpj_format,
        ),
        Rule(
            "operadora_duplicada",
            "Codigo de operadora duplicado no cadastro",
            Severity.ERROR,
            duplicated_code,
        ),
    ]


def estabelecimentos_rules() -> list[Rule]:
    def missing_cnes(df: pd.DataFrame) -> pd.Series:
        return df["cd_cnes"].isna() | (df["cd_cnes"].astype("string").str.len() == 0)

    def missing_nome(df: pd.DataFrame) -> pd.Series:
        return df["nm_estabelecimento"].isna() | (
            df["nm_estabelecimento"].astype("string").str.len() == 0
        )

    def sem_classificacao(df: pd.DataFrame) -> pd.Series:
        tipo = df["cd_tipo_estabelecimento"].astype("string")
        return tipo.isna() | (tipo.str.len() == 0)

    def duplicated_cnes(df: pd.DataFrame) -> pd.Series:
        return df.duplicated(subset=["cd_cnes"], keep="first")

    def invalid_uf(df: pd.DataFrame) -> pd.Series:
        return ~df["cd_uf"].isin(VALID_UFS)

    return [
        Rule("cnes_ausente", "Codigo CNES ausente", Severity.ERROR, missing_cnes),
        Rule("nome_ausente", "Nome do estabelecimento ausente", Severity.ERROR, missing_nome),
        Rule(
            "sem_classificacao",
            "Estabelecimento sem tipo/classificacao informado",
            Severity.WARNING,
            sem_classificacao,
        ),
        Rule("cnes_duplicado", "Codigo CNES duplicado", Severity.ERROR, duplicated_cnes),
        Rule(
            "uf_invalida", "Codigo de UF fora da lista de UFs validas", Severity.WARNING, invalid_uf
        ),
    ]
