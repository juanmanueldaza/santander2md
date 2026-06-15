"""Tests for parsers.cuotas_vencer."""

from __future__ import annotations

from santander2md.parsers.cuotas_vencer import _parse_cuotas_vencer


class TestParseCuotasVencer:
    def test_standalone_format(self) -> None:
        text = (
            "Cuotas a vencer:\n"
            "Junio/26 Julio/26 Agosto/26\n"
            "$215.051,49 $199.218,18 $199.218,18"
        )
        cuotas = _parse_cuotas_vencer(text)

        assert len(cuotas) == 3
        assert cuotas[0].mes == "Junio/26"
        assert cuotas[0].importe == 215051.49
        assert cuotas[2].mes == "Agosto/26"

    def test_inline_credit_card_format(self) -> None:
        text = (
            "Tarjeta Santander\n"
            "Cuotas a vencer\n"
            "Junio/26 $215.051,49\n"
            "Julio/26 $199.218,18\n"
            "Plan V"
        )
        cuotas = _parse_cuotas_vencer(text)

        assert len(cuotas) == 2
        assert cuotas[0].mes == "Junio/26"
        assert cuotas[0].importe == 215051.49
        assert cuotas[1].mes == "Julio/26"

    def test_empty(self) -> None:
        assert _parse_cuotas_vencer("") == []
        assert _parse_cuotas_vencer(" unrelated text ") == []
