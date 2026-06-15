"""Smoke tests for santander2md.parser."""

import pytest
from pathlib import Path
from santander2md.parser import SantanderParser, ParseError


DATA_DIR = Path(__file__).parent.parent / "data"


def _find_first_pdf():
    """Find the first available PDF in data/ for testing."""
    if DATA_DIR.exists():
        for f in sorted(DATA_DIR.glob("*.pdf")):
            return str(f)
    return None


class TestSantanderParserRealPDF:
    @pytest.fixture(autouse=True)
    def _require_pdf(self):
        path = _find_first_pdf()
        if path is None:
            pytest.skip("No PDF test data available")
        return path

    def test_parse_basic(self, _require_pdf):
        parser = SantanderParser(_require_pdf)
        extracto = parser.parse()

        assert extracto.cliente_nombre
        assert extracto.cliente_cuit
        assert extracto.periodo_inicio
        assert extracto.periodo_fin
        assert extracto.saldo_inicial is not None
        assert isinstance(extracto.movimientos, list)
        assert len(extracto.movimientos) > 0

    def test_movements_have_data(self, _require_pdf):
        parser = SantanderParser(_require_pdf)
        extracto = parser.parse()

        for m in extracto.movimientos[:10]:
            assert m.fecha
            assert m.descripcion
            assert m.debito is not None or m.credito is not None

    def test_totals_non_negative(self, _require_pdf):
        parser = SantanderParser(_require_pdf)
        extracto = parser.parse()

        assert extracto.total_ingresos >= 0
        assert extracto.total_gastos >= 0


class TestSantanderParserErrors:
    def test_file_not_found(self):
        parser = SantanderParser("/nonexistent/file.pdf")
        with pytest.raises(FileNotFoundError):
            parser.parse()

    def test_invalid_pdf(self, tmp_path):
        fake = tmp_path / "fake.pdf"
        fake.write_text("not a pdf")
        parser = SantanderParser(str(fake))
        with pytest.raises(Exception):  # pdftotext fails on invalid PDF
            parser.parse()
