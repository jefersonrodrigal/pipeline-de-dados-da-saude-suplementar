"""Camada de qualidade de dados - implementacao propria (sem Great
Expectations).

Justificativa (ver docs/business_rules.md, secao "Qualidade de dados"):
avaliamos usar Great Expectations e decidimos por uma camada propria porque,
para o volume e a natureza deste projeto (algumas dezenas de regras simples
sobre poucos datasets tabulares), o GE traz uma arvore de dependencias
desproporcional (Jupyter/Notebook, scipy, marshmallow, ruamel.yaml, entre
~80 pacotes transitivos - confirmado com `pip install --dry-run` durante o
planejamento) so para expressar checagens que uma funcao Python de poucas
linhas ja resolve com total controle sobre severidade, mensagens em
portugues e integracao direta com as tabelas de auditoria do SQL Server.

Cada `Rule` recebe o DataFrame e devolve uma mascara booleana com as linhas
que VIOLAM a regra. Regras ERROR fazem a linha ser rejeitada (removida do
dataset aceito e registrada em rej.registros_rejeitados); regras WARNING
apenas contam/alertam e a linha permanece no dataset (tipicamente porque
havera uma chave substituta "sentinela" para tratar o caso, ex.: operadora
nao cadastrada -> sk_operadora = -1).
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum

import pandas as pd
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class Severity(StrEnum):
    ERROR = "ERROR"
    WARNING = "WARNING"


@dataclass(frozen=True)
class Rule:
    name: str
    description: str
    severity: Severity
    check: Callable[[pd.DataFrame], pd.Series]  # True = linha viola a regra


@dataclass
class RuleResult:
    rule: Rule
    evaluated: int
    violated: int

    @property
    def accepted(self) -> int:
        return self.evaluated - self.violated


@dataclass
class ValidationOutcome:
    accepted_df: pd.DataFrame
    rejected_records: list[dict]
    rule_results: list[RuleResult]

    @property
    def total_evaluated(self) -> int:
        return len(self.accepted_df) + len({r["_row_index"] for r in self.rejected_records})

    @property
    def total_rejected(self) -> int:
        return len({r["_row_index"] for r in self.rejected_records})


def run_validation(df: pd.DataFrame, rules: list[Rule], dataset_name: str) -> ValidationOutcome:
    working = df.reset_index(drop=True).copy()
    rejected_indices: set[int] = set()
    rejected_records: list[dict] = []
    rule_results: list[RuleResult] = []

    for rule in rules:
        mask = rule.check(working)
        mask = mask.reindex(working.index, fill_value=False)
        violated_count = int(mask.sum())
        rule_results.append(RuleResult(rule=rule, evaluated=len(working), violated=violated_count))

        if violated_count:
            logger.info(
                "Regra de qualidade avaliada",
                extra={
                    "dataset": dataset_name,
                    "regra": rule.name,
                    "severidade": rule.severity.value,
                    "violacoes": violated_count,
                },
            )
        if rule.severity == Severity.ERROR and violated_count:
            for idx in working.index[mask]:
                if idx in rejected_indices:
                    continue
                rejected_indices.add(idx)
                rejected_records.append(
                    {
                        "_row_index": idx,
                        "regra_violada": rule.name,
                        "motivo": rule.description,
                        "registro": working.loc[idx].to_dict(),
                    }
                )

    accepted_df = working.drop(index=list(rejected_indices)).reset_index(drop=True)
    return ValidationOutcome(
        accepted_df=accepted_df, rejected_records=rejected_records, rule_results=rule_results
    )
