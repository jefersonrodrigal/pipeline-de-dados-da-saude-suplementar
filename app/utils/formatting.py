"""Formatacao pt-BR de numeros/datas/percentuais para toda a interface."""

from __future__ import annotations

from datetime import date, datetime


def format_int(value: float | int | None) -> str:
    if value is None:
        return "-"
    return f"{int(value):,}".replace(",", ".")


def format_decimal(value: float | None, casas: int = 1) -> str:
    if value is None:
        return "-"
    texto = f"{value:,.{casas}f}"
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")


def format_percent(value: float | None, casas: int = 1) -> str:
    if value is None:
        return "-"
    return f"{format_decimal(value, casas)}%"


def format_competencia(value: str | date | datetime | None) -> str:
    """Aceita 'AAAA-MM', 'AAAA-MM-DD' ou objetos date/datetime."""
    if value is None:
        return "-"
    meses = [
        "",
        "janeiro",
        "fevereiro",
        "março",
        "abril",
        "maio",
        "junho",
        "julho",
        "agosto",
        "setembro",
        "outubro",
        "novembro",
        "dezembro",
    ]
    if isinstance(value, str):
        parts = value.split("-")
        year, month = int(parts[0]), int(parts[1])
    else:
        year, month = value.year, value.month
    return f"{meses[month]}/{year}"


def format_datetime(value: datetime | None) -> str:
    if value is None:
        return "-"
    return value.strftime("%d/%m/%Y %H:%M")
