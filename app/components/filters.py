"""Filtros globais reutilizados pelas paginas (periodo, estado).

Cada pagina decide QUAIS destes filtros mostrar e em que combinacao, mas a
logica de leitura/formatacao das opcoes fica centralizada aqui para nao
duplicar consultas de "periodos disponiveis" / "estados disponiveis" em
cada pagina.
"""

from __future__ import annotations

from app.repositories.beneficiary_repository import BeneficiaryRepository
from src.utils.period import from_sk_tempo

import streamlit as st


def select_periodo(container=st.sidebar, key: str = "filtro_periodo") -> int | None:
    periodos = BeneficiaryRepository.periodos_disponiveis()
    if periodos.empty:
        container.warning("Nenhum período disponível ainda - rode o pipeline (`--stage all`).")
        return None
    opcoes = periodos["sk_tempo"].tolist()
    labels = dict(zip(periodos["sk_tempo"], periodos["ano_mes_extenso"], strict=True))
    # "or" faz curto-circuito (so chama from_sk_tempo se a chave nao existir
    # em labels) - ao contrario de labels.get(sk, from_sk_tempo(sk)), que
    # avaliaria from_sk_tempo(sk) SEMPRE (argumento default e avaliado
    # ansiosamente em Python, mesmo quando a chave existe).
    return container.selectbox(
        "Competência",
        options=opcoes,
        format_func=lambda sk: labels.get(sk) or from_sk_tempo(sk),
        key=key,
    )


def select_estado(
    container=st.sidebar, key: str = "filtro_estado", allow_all: bool = True
) -> str | None:
    estados = BeneficiaryRepository.estados_disponiveis()
    if estados.empty:
        return None
    opcoes = estados["cd_uf"].tolist()
    labels = dict(zip(estados["cd_uf"], estados["nm_uf"], strict=True))
    if allow_all:
        opcoes = [None, *opcoes]
    return container.selectbox(
        "Estado (UF)",
        options=opcoes,
        format_func=lambda uf: "Todos os estados" if uf is None else labels.get(uf, uf),
        key=key,
    )


def active_filters_caption(periodo_label: str | None, uf_label: str | None) -> None:
    partes = []
    if periodo_label:
        partes.append(f"competência **{periodo_label}**")
    if uf_label:
        partes.append(f"estado **{uf_label}**")
    if partes:
        st.caption("Filtros ativos: " + " · ".join(partes))
