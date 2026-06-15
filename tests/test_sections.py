"""Tests for parsers.sections."""

from __future__ import annotations

from santander2md.parsers.sections import _split_sections


class TestSplitSections:
    def test_all_headers(self) -> None:
        text = (
            "Movimientos en pesos\nfoo\n"
            "Movimientos en dólares\nbar\n"
            "Tarjeta Santander\nbaz"
        )
        sections = _split_sections(text)

        assert set(sections.keys()) == {
            "movimientos_pesos",
            "movimientos_dolares",
            "tarjeta_credito",
        }
        assert "foo" in sections["movimientos_pesos"]
        assert "bar" in sections["movimientos_dolares"]
        assert "baz" in sections["tarjeta_credito"]

    def test_no_headers(self) -> None:
        assert _split_sections("just some text\nwithout headers") == {}

    def test_duplicate_headers_merged(self) -> None:
        text = "Préstamos\nfirst\nPréstamos\nsecond"
        sections = _split_sections(text)

        assert "prestamos" in sections
        assert "first" in sections["prestamos"]
        assert "second" in sections["prestamos"]

    def test_blacklist_ignored(self) -> None:
        text = "Caja de Ahorro en dólares\nfoo\nMovimientos en dólares\nbar"
        sections = _split_sections(text)

        assert "movimientos_dolares" in sections
        assert "Caja de Ahorro en dólares" not in sections
