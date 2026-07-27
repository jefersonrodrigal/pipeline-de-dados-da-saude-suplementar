"""Mapeamento de colunas do CNES (Cadastro Nacional de Estabelecimentos de
Saude) para os nomes padronizados usados na camada Trusted.

IMPORTANTE: ao contrario da ANS (cujas colunas foram confirmadas baixando
arquivos reais - ver docs/data_dictionary.md), o CNES nao possui uma URL de
download estavel para verificacao automatica (ver src/extract/
cnes_estabelecimentos.py). O mapeamento abaixo segue as convencoes de nomes
de campo publicamente documentadas pelo DATASUS para a base de
estabelecimentos, mas DEVE ser conferido/ajustado contra o dicionario de
dados do arquivo que voce efetivamente baixar (Downloads > Documentacao em
cnes.datasus.gov.br). Ajuste este dicionario livremente - e o UNICO lugar
que precisa mudar se o layout real for diferente.
"""

from __future__ import annotations

# origem (maiuscula, como tipicamente publicada) -> nome padronizado (Trusted)
CNES_COLUMN_MAP: dict[str, str] = {
    "CO_CNES": "cd_cnes",
    "NO_FANTASIA": "nm_estabelecimento",
    "NO_RAZAO_SOCIAL": "nm_razao_social",
    "TP_UNIDADE": "cd_tipo_estabelecimento",
    "DS_TP_UNIDADE": "ds_tipo_estabelecimento",
    "CO_MUNICIPIO": "cd_municipio_ibge",
    "NO_MUNICIPIO": "nm_municipio",
    "CO_UF": "cd_uf",
    "SG_UF": "cd_uf",
}

# Colunas minimas para o pipeline funcionar; qualquer outra coisa e ignorada.
REQUIRED_STANDARD_COLUMNS = ["cd_cnes", "nm_estabelecimento", "cd_municipio_ibge"]
