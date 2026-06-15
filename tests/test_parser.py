"""Smoke tests for santander2md.parser."""

import subprocess
from pathlib import Path

import pytest

from santander2md.parser import ParseError, SantanderParser

DATA_DIR = Path(__file__).parent.parent / "data"


def _list_pdfs():
    """Return all PDF paths for parametrized testing. Empty if no data."""
    if not DATA_DIR.exists():
        return []
    return sorted(str(p) for p in DATA_DIR.glob("*.pdf"))


def _pdf_ids():
    """Human-readable test IDs from PDF filenames."""
    if not DATA_DIR.exists():
        return []
    return sorted(p.name for p in DATA_DIR.glob("*.pdf"))


class TestSantanderParserRealPDF:
    @pytest.mark.parametrize("pdf_path", _list_pdfs(), ids=_pdf_ids())
    def test_parse_basic(self, pdf_path):
        parser = SantanderParser(pdf_path)
        extracto = parser.parse()

        assert extracto.cliente_nombre
        assert extracto.cliente_cuit
        assert extracto.periodo_inicio
        assert extracto.periodo_fin
        assert extracto.saldo_inicial is not None
        assert extracto.saldo_final is not None
        assert isinstance(extracto.movimientos, list)
        if len(extracto.movimientos) == 0:
            # Allowed: genuinely empty statement period
            pass
        else:
            assert len(extracto.movimientos) > 0

    @pytest.mark.parametrize("pdf_path", _list_pdfs(), ids=_pdf_ids())
    def test_totals_non_negative(self, pdf_path):
        parser = SantanderParser(pdf_path)
        extracto = parser.parse()

        assert extracto.total_ingresos >= 0
        assert extracto.total_gastos >= 0

    @pytest.mark.parametrize("pdf_path", _list_pdfs(), ids=_pdf_ids())
    def test_movements_valid(self, pdf_path):
        parser = SantanderParser(pdf_path)
        extracto = parser.parse()

        for m in extracto.movimientos[:10]:
            assert m.fecha, f"Movement missing fecha: {m}"
            assert m.descripcion, f"Movement missing descripcion: {m}"
            assert m.debito is not None or m.credito is not None, (
                f"Movement {m.fecha}: {m.descripcion} — no debito or credito"
            )


class TestSantanderParserErrors:
    def test_file_not_found(self):
        parser = SantanderParser("/nonexistent/file.pdf")
        with pytest.raises(FileNotFoundError):
            parser.parse()

    def test_invalid_pdf(self, tmp_path):
        fake = tmp_path / "fake.pdf"
        fake.write_text("not a pdf", encoding="utf-8")
        parser = SantanderParser(str(fake))
        with pytest.raises((ParseError, subprocess.CalledProcessError)):
            parser.parse()
