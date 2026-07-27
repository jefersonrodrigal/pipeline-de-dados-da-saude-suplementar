from __future__ import annotations

from app.utils.formatting import format_competencia, format_decimal, format_int, format_percent


def test_format_int_uses_pt_br_thousand_separator() -> None:
    assert format_int(1234567) == "1.234.567"
    assert format_int(None) == "-"


def test_format_decimal_uses_pt_br_comma() -> None:
    assert format_decimal(1234.5, 1) == "1.234,5"
    assert format_decimal(None) == "-"


def test_format_percent_appends_symbol() -> None:
    assert format_percent(12.34) == "12,3%"
    assert format_percent(None) == "-"


def test_format_competencia_from_string() -> None:
    assert format_competencia("2024-12") == "dezembro/2024"


def test_format_competencia_none() -> None:
    assert format_competencia(None) == "-"
