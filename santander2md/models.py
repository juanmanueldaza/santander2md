"""
Modelos de datos para santander2md.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Optional, List


@dataclass
class Movimiento:
    """Un movimiento bancario (transacción)."""
    fecha: str
    descripcion: str
    debito: Optional[float] = None   # Monto debitado (gasto, positivo)
    credito: Optional[float] = None  # Monto acreditado (ingreso, positivo)

    def __post_init__(self) -> None:
        if self.debito is None and self.credito is None:
            raise ValueError("Movimiento debe tener debito o credito")

    @property
    def monto(self) -> float:
        """Devuelve el monto absoluto."""
        if self.debito is not None:
            return self.debito
        return self.credito or 0.0

    @property
    def tipo(self) -> str:
        """Devuelve 'débito' o 'crédito'."""
        return "débito" if self.debito is not None else "crédito"

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["monto"] = self.monto
        d["tipo"] = self.tipo
        return d


@dataclass
class Extracto:
    """Extracto bancario completo."""
    periodo_inicio: str
    periodo_fin: str
    cliente_nombre: str
    cliente_cuit: str
    saldo_inicial: Optional[float] = None
    saldo_final: Optional[float] = None
    sueldo_neto: Optional[float] = None
    movimientos: List[Movimiento] = field(default_factory=list)

    @property
    def total_ingresos(self) -> float:
        """Suma de créditos (sin contar sueldo)."""
        return sum(m.credito for m in self.movimientos if m.credito)

    @property
    def total_gastos(self) -> float:
        """Suma de débitos."""
        return sum(m.debito for m in self.movimientos if m.debito)

    @property
    def capacidad_ahorro(self) -> float:
        """Ingresos - Gastos."""
        return self.total_ingresos - self.total_gastos

    @property
    def cantidad_movimientos(self) -> int:
        return len(self.movimientos)

    @property
    def promedio_gasto_diario(self) -> float:
        if not self.movimientos:
            return 0.0

        try:
            inicio = datetime.strptime(self.periodo_inicio, "%d/%m/%y")
            fin = datetime.strptime(self.periodo_fin, "%d/%m/%y")
            days = max(abs((fin - inicio).days), 1)
        except (ValueError, TypeError):
            days = 30

        return self.total_gastos / days

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["total_ingresos"] = self.total_ingresos
        d["total_gastos"] = self.total_gastos
        d["capacidad_ahorro"] = self.capacidad_ahorro
        d["cantidad_movimientos"] = self.cantidad_movimientos
        return d
