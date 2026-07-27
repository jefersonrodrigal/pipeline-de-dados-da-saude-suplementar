from __future__ import annotations

from pathlib import Path

from src.transform.ans_operadoras import transform_ans_operadoras


def test_transform_drops_pii_columns(ans_operadoras_raw: Path) -> None:
    df, stats = transform_ans_operadoras(ans_operadoras_raw)
    # Minimizacao LGPD: Representante, Telefone, Endereco_eletronico etc.
    # nao devem sobreviver a transformacao.
    proibidas = {
        "representante",
        "cargo_representante",
        "telefone",
        "endereco_eletronico",
        "ddd",
        "fax",
    }
    assert proibidas.isdisjoint(set(df.columns))
    assert stats["registros_finais"] == 2


def test_transform_normalizes_uf(ans_operadoras_raw: Path) -> None:
    df, _ = transform_ans_operadoras(ans_operadoras_raw)
    assert set(df["sg_uf_sede"].unique()) == {"RR", "AC"}


def test_transform_picks_latest_snapshot(ans_operadoras_raw: Path) -> None:
    # Cria um snapshot mais novo (data posterior) e garante que ele e o usado.
    newer_dir = ans_operadoras_raw / "ans_operadoras" / "2026-02-01"
    newer_dir.mkdir(parents=True)
    header = (
        "REGISTRO_OPERADORA;CNPJ;Razao_Social;Nome_Fantasia;Modalidade;Logradouro;Numero;"
        "Complemento;Bairro;Cidade;UF;CEP;DDD;Telefone;Fax;Endereco_eletronico;Representante;"
        "Cargo_Representante;Regiao_de_Comercializacao;Data_Registro_ANS"
    )
    row = (
        '"000003";"33333333000103";"OPERADORA TRES";;"Seguradora";"RUA C";"3";;"CENTRO";'
        '"São Paulo";"SP";"01000000";"11";"777777777";;"c@teste.com";"BELTRANO";"DIRETOR";1;"2021-01-01"'
    )
    (newer_dir / "Relatorio_cadop.csv").write_text("\n".join([header, row]), encoding="utf-8")

    df, stats = transform_ans_operadoras(ans_operadoras_raw)
    assert stats["snapshot_usado"] == "2026-02-01"
    assert set(df["cd_operadora_ans"]) == {"000003"}
