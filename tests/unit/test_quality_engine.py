from __future__ import annotations

import pandas as pd
from src.quality.engine import Rule, Severity, run_validation


def test_error_rule_rejects_violating_rows() -> None:
    df = pd.DataFrame({"valor": [10, -5, 3, -1]})
    rule = Rule(
        "nao_negativo", "Valor nao pode ser negativo", Severity.ERROR, lambda d: d["valor"] < 0
    )

    outcome = run_validation(df, [rule], "teste")

    assert len(outcome.accepted_df) == 2
    assert list(outcome.accepted_df["valor"]) == [10, 3]
    assert len(outcome.rejected_records) == 2
    assert all(r["regra_violada"] == "nao_negativo" for r in outcome.rejected_records)


def test_warning_rule_does_not_reject_rows() -> None:
    df = pd.DataFrame({"valor": [10, -5]})
    rule = Rule("aviso", "So um aviso", Severity.WARNING, lambda d: d["valor"] < 0)

    outcome = run_validation(df, [rule], "teste")

    assert len(outcome.accepted_df) == 2
    assert outcome.rejected_records == []
    assert outcome.rule_results[0].violated == 1
    assert outcome.rule_results[0].accepted == 1


def test_multiple_rules_do_not_double_count_same_row() -> None:
    df = pd.DataFrame({"valor": [-5]})
    regra_a = Rule("regra_a", "A", Severity.ERROR, lambda d: d["valor"] < 0)
    regra_b = Rule("regra_b", "B", Severity.ERROR, lambda d: d["valor"] < 0)

    outcome = run_validation(df, [regra_a, regra_b], "teste")

    # A linha viola as duas regras, mas so deve ser rejeitada (e contada) uma vez.
    assert len(outcome.rejected_records) == 1
    assert outcome.accepted_df.empty
