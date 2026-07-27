from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

# Garante que "app" e "src" sejam importaveis quando o Streamlit roda este
# arquivo diretamente (sem instalar o projeto como pacote).
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.repositories.base import DatabaseUnavailableError  # noqa: E402
from app.repositories.data_quality_repository import DataQualityRepository  # noqa: E402
from app.utils.formatting import format_datetime  # noqa: E402

st.set_page_config(
    page_title="Pipeline de Dados da Saúde Suplementar",
    page_icon="🏥",
    layout="wide",
)

st.title("🏥 Pipeline de Dados da Saúde Suplementar")
st.markdown("""
Projeto de portfólio: extração, tratamento, qualidade e carga de dados
públicos da **ANS** (beneficiários e operadoras) e do **CNES/DATASUS**
(rede de estabelecimentos de saúde) em um Data Warehouse no **Microsoft SQL
Server**, com indicadores de distribuição da rede de saúde e dos
beneficiários por região.
""")

st.divider()

col1, col2 = st.columns([2, 1])
with col1:
    st.subheader("Navegue pelas páginas")
    st.markdown("""
- **Visão Executiva** — indicadores gerais e evolução temporal
- **Beneficiários** — distribuição por estado, município e operadora
- **Rede Assistencial** — estabelecimentos por tipo e localidade
- **Cobertura Regional** — razão beneficiários/estabelecimento e classificação exploratória
- **Operadoras** — ranking, evolução e participação por região
- **Qualidade dos Dados** — auditoria e histórico de execuções do pipeline
- **Exploração dos Dados** — tabela livre com filtros e download em CSV

Use o menu à esquerda para navegar.
""")

with col2:
    st.subheader("Status do pipeline")
    try:
        ultima = DataQualityRepository.ultima_execucao()
        if ultima.empty:
            st.warning("Nenhuma execução registrada ainda. Rode `python -m src.main --stage all`.")
        else:
            linha = ultima.iloc[0]
            st.metric("Última execução (carga)", linha["status"])
            st.caption(f"Concluída em {format_datetime(linha['dh_fim'])}")
    except DatabaseUnavailableError:
        st.error(
            "Não foi possível conectar ao SQL Server agora. Verifique se o "
            "banco está no ar e se as variáveis de ambiente em `.env` estão corretas.",
            icon="🚫",
        )

st.divider()
st.caption(
    "Dados públicos (ANS/CNES). Nenhum dado pessoal identificável de "
    "beneficiários é utilizado - ver docs/security.md para a análise de "
    "privacidade e LGPD."
)
