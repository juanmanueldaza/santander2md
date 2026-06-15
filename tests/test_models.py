"""Tests for santander2md.models."""

import pytest
from santander2md.models import Movimiento, Extracto


class TestMovimiento:
    def test_debito(self):
        m = Movimiento(fecha="01/05/26", descripcion="Compra", debito=100.0)
        assert m.tipo == "débito"
        assert m.monto == 100.0
        assert m.debito == 100.0
        assert m.credito is None

    def test_credito(self):
        m = Movimiento(fecha="01/05/26", descripcion="Depósito", credito=500.0)
        assert m.tipo == "crédito"
        assert m.monto == 500.0
        assert m.credito == 500.0
        assert m.debito is None

    def test_no_amount_raises(self):
        with pytest.raises(ValueError, match="debito o credito"):
            Movimiento(fecha="01/05/26", descripcion="vacío")

    def test_to_dict(self):
        m = Movimiento(fecha="01/05/26", descripcion="Compra", debito=100.0)
        d = m.to_dict()
        assert d["fecha"] == "01/05/26"
        assert d["debito"] == 100.0
        assert d["tipo"] == "débito"


class TestExtracto:
    def test_basic(self):
        ext = Extracto(
            periodo_inicio="01/05/26",
            periodo_fin="28/05/26",
            cliente_nombre="Test",
            cliente_cuit="20-12345678-9",
            saldo_inicial=1000.0,
            saldo_final=500.0,
        )
        assert ext.total_ingresos == 0.0
        assert ext.total_gastos == 0.0
        assert ext.cantidad_movimientos == 0

    def test_totals(self):
        ext = Extracto(
            periodo_inicio="01/05/26",
            periodo_fin="28/05/26",
            cliente_nombre="Test",
            cliente_cuit="20-12345678-9",
            saldo_inicial=1000.0,
            saldo_final=500.0,
            movimientos=[
                Movimiento("01/05/26", "Compra", debito=100.0),
                Movimiento("02/05/26", "Depósito", credito=300.0),
                Movimiento("03/05/26", "Otra compra", debito=50.0),
            ],
        )
        assert ext.total_ingresos == 300.0
        assert ext.total_gastos == 150.0
        assert ext.capacidad_ahorro == 150.0
        assert ext.cantidad_movimientos == 3

    def test_sueldo_optional(self):
        ext = Extracto(
            periodo_inicio="01/05/26",
            periodo_fin="28/05/26",
            cliente_nombre="Test",
            cliente_cuit="20-12345678-9",
            saldo_inicial=1000.0,
            saldo_final=500.0,
            sueldo_neto=1500000.0,
        )
        assert ext.sueldo_neto == 1500000.0
        from santander2md.exporter import to_markdown
        md = to_markdown(ext)
        assert "Sueldo Neto" in md

    def test_to_markdown(self):
        from santander2md.exporter import to_markdown
        ext = Extracto(
            periodo_inicio="01/05/26",
            periodo_fin="28/05/26",
            cliente_nombre="Test",
            cliente_cuit="20-12345678-9",
            saldo_inicial=1000.0,
            saldo_final=500.0,
            movimientos=[
                Movimiento("01/05/26", "Compra", debito=100.0),
            ],
        )
        md = to_markdown(ext)
        assert "# Extracto Bancario" in md
        assert "Compra" in md
        assert "débito" in md

    def test_to_dict(self):
        ext = Extracto(
            periodo_inicio="01/05/26",
            periodo_fin="28/05/26",
            cliente_nombre="Test",
            cliente_cuit="20-12345678-9",
            saldo_inicial=1000.0,
            saldo_final=500.0,
        )
        d = ext.to_dict()
        assert d["periodo_inicio"] == "01/05/26"
        assert d["movimientos"] == []


class TestPromedioGastoDiario:
    """Acceptance tests for fix-promedio-gasto-diario (AC-1 through AC-8)."""

    @staticmethod
    def _ext(gastos: float = 0.0, inicio: str = "01/05/26", fin: str = "31/05/26") -> Extracto:
        movs = [Movimiento("01/05/26", "test", debito=gastos)] if gastos > 0 else []
        return Extracto(
            periodo_inicio=inicio,
            periodo_fin=fin,
            cliente_nombre="Test",
            cliente_cuit="20-12345678-9",
            movimientos=movs,
        )

    def test_31_day_period(self):
        """AC-1: 31-day period (01/05/26 → 01/06/26)."""
        ext = self._ext(gastos=3100.0, inicio="01/05/26", fin="01/06/26")
        assert ext.promedio_gasto_diario == pytest.approx(100.0)

    def test_cross_year_period(self):
        """AC-2: Cross-year period (15/09/23 → 12/01/24 = 119 days)."""
        ext = self._ext(gastos=11900.0, inicio="15/09/23", fin="12/01/24")
        assert ext.promedio_gasto_diario == pytest.approx(100.0)

    def test_na_fallback(self):
        """AC-3: 'N/A' strings fall back to /30."""
        ext = self._ext(gastos=300.0, inicio="N/A", fin="31/05/26")
        assert ext.promedio_gasto_diario == pytest.approx(10.0)

    def test_malformed_fallback(self):
        """AC-4: Malformed strings fall back to /30."""
        ext = self._ext(gastos=300.0, inicio="not-a-date", fin="31/05/26")
        assert ext.promedio_gasto_diario == pytest.approx(10.0)

    def test_same_day_guard(self):
        """AC-5: Same-day period → max(1, 0) = 1."""
        ext = self._ext(gastos=100.0, inicio="01/05/26", fin="01/05/26")
        assert ext.promedio_gasto_diario == pytest.approx(100.0)

    def test_reversed_dates(self):
        """AC-6: Reversed dates (fin < inicio) → abs() corrects sign."""
        ext = self._ext(gastos=300.0, inicio="31/05/26", fin="01/05/26")
        assert ext.promedio_gasto_diario == pytest.approx(10.0)

    def test_zero_gastos(self):
        """AC-7 variant: zero gastos → 0.0."""
        ext = self._ext(gastos=0.0)
        assert ext.promedio_gasto_diario == pytest.approx(0.0)

    def test_field_types_preserved(self):
        """AC-8: periodo_inicio/periodo_fin remain str type."""
        ext = self._ext()
        assert isinstance(ext.periodo_inicio, str)
        assert isinstance(ext.periodo_fin, str)

    def test_empty_movimientos(self):
        """Empty movimientos → returns 0.0 (existing short-circuit)."""
        ext = self._ext(gastos=0.0)
        assert ext.promedio_gasto_diario == 0.0
