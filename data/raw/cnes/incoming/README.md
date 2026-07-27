# Entrada manual do CNES

O CNES (Cadastro Nacional de Estabelecimentos de Saude) nao possui uma URL
de download estavel (o portal exige selecao de UF/competencia via
formulario). Duas opcoes:

1. **Configuravel por URL**: defina `CNES_DOWNLOAD_URL` no `.env` se voce
   encontrar/gerar uma URL valida de download.
2. **Deposito manual (esta pasta)**: baixe o arquivo manualmente em
   https://cnes.datasus.gov.br/pages/downloads/arquivosBaseDados.jsp,
   converta para CSV/TXT se necessario (arquivos `.dbc` precisam de
   conversao previa) e coloque aqui.

## Arquivo incluso: `exemplo_estabelecimentos_FICTICIO.csv`

Este repositorio inclui um arquivo de **demonstracao com dados 100%
FICTICIOS** (nomes de estabelecimentos e codigos inventados), apenas para
que o pipeline completo (extract -> transform -> quality -> load ->
aggregate -> Streamlit) possa ser executado e demonstrado de ponta a ponta
sem depender de um download manual antes da primeira execucao.

**Para uma analise real, substitua este arquivo pelo export oficial do CNES**
e ajuste `src/transform/cnes_column_mapping.py` conforme o dicionario de
dados real do arquivo baixado.
