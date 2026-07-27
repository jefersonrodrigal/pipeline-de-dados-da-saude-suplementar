"""Fixtures compartilhadas. Todos os dados aqui sao FICTICIOS e pequenos -
os testes nunca dependem dos arquivos publicos completos da ANS/CNES."""

from __future__ import annotations

import zipfile
from pathlib import Path

import pytest

# Cabecalho identico ao layout real da ANS (confirmado durante o
# desenvolvimento baixando um arquivo real), com linhas de exemplo
# ficticias. Inclui: 2 linhas que colapsam no mesmo grao da fato (mesma
# operadora/municipio/sexo/faixa/vinculo, planos diferentes - testa
# agregacao) e 1 linha duplicada exata (testa deteccao de duplicidade).
_ANS_BENEFICIARIOS_HEADER = (
    "ID_CMPT_MOVEL;CD_OPERADORA;NM_RAZAO_SOCIAL;NR_CNPJ;MODALIDADE_OPERADORA;SG_UF;"
    "CD_MUNICIPIO;NM_MUNICIPIO;TP_SEXO;DE_FAIXA_ETARIA;DE_FAIXA_ETARIA_REAJ;CD_PLANO;"
    "TP_VIGENCIA_PLANO;DE_CONTRATACAO_PLANO;DE_SEGMENTACAO_PLANO;DE_ABRG_GEOGRAFICA_PLANO;"
    "COBERTURA_ASSIST_PLAN;TIPO_VINCULO;QT_BENEFICIARIO_ATIVO;QT_BENEFICIARIO_ADERIDO;"
    "QT_BENEFICIARIO_CANCELADO;DT_CARGA"
)
_ANS_BENEFICIARIOS_ROWS = [
    '"2024-12";"000001";"OPERADORA TESTE UM";"11111111000191";"COOPERATIVA MEDICA";"RR";'
    '"140010";"Boa Vista";"F";"25 a 29 anos";"24 a 28 anos";"111111111";"P";'
    '"Individual ou Familiar";"Ambulatorial + Hospitalar";"Nacional";"Médico-hospitalar";'
    '"Titular";10;1;0;"2026-01-01"',
    '"2024-12";"000001";"OPERADORA TESTE UM";"11111111000191";"COOPERATIVA MEDICA";"RR";'
    '"140010";"Boa Vista";"F";"25 a 29 anos";"24 a 28 anos";"222222222";"P";'
    '"Coletivo Empresarial";"Ambulatorial + Hospitalar";"Nacional";"Médico-hospitalar";'
    '"Titular";5;0;0;"2026-01-01"',
    '"2024-12";"000001";"OPERADORA TESTE UM";"11111111000191";"COOPERATIVA MEDICA";"RR";'
    '"140010";"Boa Vista";"F";"25 a 29 anos";"24 a 28 anos";"222222222";"P";'
    '"Coletivo Empresarial";"Ambulatorial + Hospitalar";"Nacional";"Médico-hospitalar";'
    '"Titular";5;0;0;"2026-01-01"',
    '"2024-12";"999999";"OPERADORA SEM CADASTRO";"99999999000199";"MEDICINA DE GRUPO";"RR";'
    '"140002";"Amajari";"M";"1 a 4 anos";"0 a 18 anos";"333333333";"P";'
    '"Individual ou Familiar";"Odontológico";"Grupo de municípios";"Odontológico";'
    '"Dependente";3;1;1;"2026-01-01"',
]


def _write_ans_zip(path: Path, rows: list[str]) -> Path:
    csv_content = "\n".join([_ANS_BENEFICIARIOS_HEADER, *rows])
    csv_name = path.stem + ".csv"
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr(csv_name, csv_content)
    return path


@pytest.fixture
def raw_dir(tmp_path: Path) -> Path:
    return tmp_path / "raw"


@pytest.fixture
def ans_beneficiarios_raw(raw_dir: Path) -> Path:
    target_dir = raw_dir / "ans_beneficiarios" / "202412"
    target_dir.mkdir(parents=True)
    _write_ans_zip(target_dir / "pda-024-icb-RR-2024_12.zip", _ANS_BENEFICIARIOS_ROWS)
    return raw_dir


@pytest.fixture
def ans_operadoras_raw(raw_dir: Path) -> Path:
    target_dir = raw_dir / "ans_operadoras" / "2026-01-01"
    target_dir.mkdir(parents=True)
    header = (
        "REGISTRO_OPERADORA;CNPJ;Razao_Social;Nome_Fantasia;Modalidade;Logradouro;Numero;"
        "Complemento;Bairro;Cidade;UF;CEP;DDD;Telefone;Fax;Endereco_eletronico;Representante;"
        "Cargo_Representante;Regiao_de_Comercializacao;Data_Registro_ANS"
    )
    rows = [
        '"000001";"11111111000191";"OPERADORA TESTE UM";;"Cooperativa Médica";"RUA A";"1";;'
        '"CENTRO";"Boa Vista";"RR";"69300000";"95";"999999999";;"contato@teste.com";'
        '"FULANO DE TAL";"DIRETOR";4;"2020-01-01"',
        '"000002";"22222222000102";"OPERADORA TESTE DOIS";;"Medicina de Grupo";"RUA B";"2";;'
        '"CENTRO";"Rio Branco";"AC";"69900000";"68";"888888888";;"contato2@teste.com";'
        '"CICLANO";"DIRETORA";1;"2019-05-10"',
    ]
    (target_dir / "Relatorio_cadop.csv").write_text("\n".join([header, *rows]), encoding="utf-8")
    return raw_dir


@pytest.fixture
def cnes_raw(raw_dir: Path) -> Path:
    target_dir = raw_dir / "cnes" / "202412"
    target_dir.mkdir(parents=True)
    header = "CO_CNES;NO_FANTASIA;TP_UNIDADE;DS_TP_UNIDADE;CO_MUNICIPIO;NO_MUNICIPIO;CO_UF"
    rows = [
        "1000001;Hospital Teste;05;Hospital Geral;140010;Boa Vista;RR",
        "1000002;UBS Teste;02;Posto de Saúde;140010;Boa Vista;RR",
        "1000003;UBS Amajari Teste;02;Posto de Saúde;140002;Amajari;RR",
    ]
    (target_dir / "estabelecimentos_teste.csv").write_text(
        "\n".join([header, *rows]), encoding="utf-8"
    )
    return raw_dir
