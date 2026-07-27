from __future__ import annotations

from datetime import date

import pandas as pd
from src.quality.engine import run_validation
from src.quality.validators import beneficiarios_rules, estabelecimentos_rules, operadoras_rules


def _beneficiarios_df(**overrides) -> pd.DataFrame:
    base = {
        "competencia": [date(2024, 12, 1)],
        "cd_operadora_ans": ["000001"],
        "cd_municipio_ibge": ["140010"],
        "nm_municipio": ["Boa Vista"],
        "cd_uf": ["RR"],
        "tp_sexo": ["F"],
        "de_faixa_etaria": ["25 a 29 anos"],
        "tipo_vinculo": ["Titular"],
        "segmentacao_plano": ["Ambulatorial"],
        "qt_beneficiario_ativo": [10],
        "qt_beneficiario_aderido": [1],
        "qt_beneficiario_cancelado": [0],
    }
    base.update(overrides)
    return pd.DataFrame(base)


def test_negative_quantity_is_rejected() -> None:
    df = _beneficiarios_df(qt_beneficiario_ativo=[-1])
    outcome = run_validation(df, beneficiarios_rules(), "beneficiarios")
    assert outcome.accepted_df.empty
    assert outcome.rejected_records[0]["regra_violada"] == "valores_negativos"


def test_invalid_uf_is_rejected() -> None:
    df = _beneficiarios_df(cd_uf=["ZZ"])
    outcome = run_validation(df, beneficiarios_rules(), "beneficiarios")
    assert outcome.accepted_df.empty


def test_unknown_operadora_is_warning_not_rejection() -> None:
    df = _beneficiarios_df(cd_operadora_ans=["999999"])
    outcome = run_validation(
        df, beneficiarios_rules(known_operadora_codes={"000001"}), "beneficiarios"
    )
    assert len(outcome.accepted_df) == 1  # WARNING nao rejeita
    violated = {r.rule.name: r.violated for r in outcome.rule_results}
    assert violated["operadora_inexistente"] == 1


def test_operadoras_rules_reject_duplicated_code() -> None:
    df = pd.DataFrame(
        {
            "cd_operadora_ans": ["000001", "000001"],
            "nr_cnpj": ["11111111000191", "11111111000191"],
            "nm_razao_social": ["A", "A"],
        }
    )
    outcome = run_validation(df, operadoras_rules(), "operadoras")
    assert len(outcome.accepted_df) == 1


def test_estabelecimentos_rules_flag_missing_classification() -> None:
    df = pd.DataFrame(
        {
            "cd_cnes": ["1"],
            "nm_estabelecimento": ["Hospital"],
            "cd_tipo_estabelecimento": [None],
            "cd_uf": ["RR"],
        }
    )
    outcome = run_validation(df, estabelecimentos_rules(), "estabelecimentos")
    assert len(outcome.accepted_df) == 1  # sem_classificacao e WARNING
    violated = {r.rule.name: r.violated for r in outcome.rule_results}
    assert violated["sem_classificacao"] == 1
