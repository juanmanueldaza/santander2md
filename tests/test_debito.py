"""Tests for parsers.tarjeta_debito."""

from __future__ import annotations

from santander2md.parsers.tarjeta_debito import _parse_debito


class TestParseDebito:
    def test_single_line_row(self) -> None:
        text = (
            "Tarjeta de débito\n"
            "Fecha Comprobante Establecimiento Importe\n"
            "05/05/26 123456 SUPERMERCADO $ 15.000,00\n"
            "Monto total"
        )
        movs = _parse_debito(text)

        assert len(movs) == 1
        assert movs[0].fecha == "05/05/26"
        assert movs[0].establecimiento == "SUPERMERCADO"
        assert movs[0].importe == 15000.00

    def test_two_line_row(self) -> None:
        text = (
            "Tarjeta de débito\n"
            "Fecha Comprobante Establecimiento Importe\n"
            "05/05/26\n"
            "123456 SUPERMERCADO $ 15.000,00\n"
            "Monto total"
        )
        movs = _parse_debito(text)

        assert len(movs) == 1
        assert movs[0].fecha == "05/05/26"
        assert "SUPERMERCADO" in movs[0].establecimiento
        assert movs[0].importe == 15000.00
