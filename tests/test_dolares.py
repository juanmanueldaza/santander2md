"""Tests for parsers.movimientos_dolares."""

from __future__ import annotations

from santander2md.parsers.movimientos_dolares import _parse_movimientos_dolares


class TestParseMovimientosDolares:
    def test_basic_row(self) -> None:
        text = (
            "Movimientos en dólares\n"
            "Fecha Comprobante Descripción\n"
            "05/05/26 12345678 COMPRA ONLINE -U$S 59,64 U$S 1.234,56"
        )
        movs = _parse_movimientos_dolares(text)

        assert len(movs) == 1
        assert movs[0].fecha == "05/05/26"
        assert "COMPRA ONLINE" in movs[0].descripcion
        assert movs[0].monto == -59.64
        assert movs[0].saldo == 1234.56

    def test_continuation_merged(self) -> None:
        text = (
            "Movimientos en dólares\n"
            "Fecha Comprobante Descripción\n"
            "05/05/26 12345678 COMPRA\n"
            "ONLINE -U$S 59,64 U$S 1.234,56"
        )
        movs = _parse_movimientos_dolares(text)

        assert len(movs) == 1
        assert "COMPRA ONLINE" in movs[0].descripcion
        assert movs[0].monto == -59.64
