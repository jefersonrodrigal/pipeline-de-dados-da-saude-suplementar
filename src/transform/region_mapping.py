"""Referencia geografica fixa (27 UFs + DF), usada para normalizar
`dim.dim_localidade` sem depender de uma tabela IBGE externa completa.

Esta lista e estavel (a divisao politico-administrativa do Brasil nao muda
com frequencia) e por isso e seguramente embutida no codigo, ao contrario
dos ~5.570 municipios, que sao derivados diretamente dos proprios arquivos
de origem (ver src/transform/ans_beneficiarios.py).
"""

from __future__ import annotations

UF_INFO: dict[str, tuple[str, str]] = {
    "AC": ("Acre", "Norte"),
    "AL": ("Alagoas", "Nordeste"),
    "AP": ("Amapá", "Norte"),
    "AM": ("Amazonas", "Norte"),
    "BA": ("Bahia", "Nordeste"),
    "CE": ("Ceará", "Nordeste"),
    "DF": ("Distrito Federal", "Centro-Oeste"),
    "ES": ("Espírito Santo", "Sudeste"),
    "GO": ("Goiás", "Centro-Oeste"),
    "MA": ("Maranhão", "Nordeste"),
    "MT": ("Mato Grosso", "Centro-Oeste"),
    "MS": ("Mato Grosso do Sul", "Centro-Oeste"),
    "MG": ("Minas Gerais", "Sudeste"),
    "PA": ("Pará", "Norte"),
    "PB": ("Paraíba", "Nordeste"),
    "PR": ("Paraná", "Sul"),
    "PE": ("Pernambuco", "Nordeste"),
    "PI": ("Piauí", "Nordeste"),
    "RJ": ("Rio de Janeiro", "Sudeste"),
    "RN": ("Rio Grande do Norte", "Nordeste"),
    "RS": ("Rio Grande do Sul", "Sul"),
    "RO": ("Rondônia", "Norte"),
    "RR": ("Roraima", "Norte"),
    "SC": ("Santa Catarina", "Sul"),
    "SP": ("São Paulo", "Sudeste"),
    "SE": ("Sergipe", "Nordeste"),
    "TO": ("Tocantins", "Norte"),
    "XX": ("Não informado", "Não informado"),
}

VALID_UFS = set(UF_INFO.keys())


def uf_name(cd_uf: str) -> str:
    return UF_INFO.get(cd_uf, ("Não informado", "Não informado"))[0]


def uf_region(cd_uf: str) -> str:
    return UF_INFO.get(cd_uf, ("Não informado", "Não informado"))[1]
