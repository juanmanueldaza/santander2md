"""
Modelos de datos para santander2md.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any

# ═══════════════════════════════════════════════════════════════════════
#  Checking account (Movimientos en pesos)
# ═══════════════════════════════════════════════════════════════════════


@dataclass
class Movimiento:
    """Un movimiento bancario (transacción en pesos)."""

    fecha: str
    descripcion: str
    debito: float | None = None  # Monto debitado (gasto, positivo)
    credito: float | None = None  # Monto acreditado (ingreso, positivo)

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


# ═══════════════════════════════════════════════════════════════════════
#  Dollar checking account (Movimientos en dólares)
# ═══════════════════════════════════════════════════════════════════════


@dataclass
class MovimientoDolar:
    """Una transacción en dólares."""

    fecha: str
    descripcion: str
    monto: float  # negativo = débito, positivo = crédito
    saldo: float | None = None  # running balance

    @property
    def tipo(self) -> str:
        return "débito" if self.monto < 0 else "crédito"


# ═══════════════════════════════════════════════════════════════════════
#  Spending categories ("Así usaste tu dinero")
# ═══════════════════════════════════════════════════════════════════════


@dataclass
class CategoriaGasto:
    """Una categoría de gasto con porcentaje y total."""

    nombre: str
    porcentaje: float  # e.g. 44.11 for 44.11%
    total: float  # absolute amount in pesos


# ═══════════════════════════════════════════════════════════════════════
#  Tax withholding detail
# ═══════════════════════════════════════════════════════════════════════


@dataclass
class DetalleImpositivo:
    """Detalle impositivo — retenciones y créditos fiscales."""

    total_retencion_creditos: float | None = None
    total_retencion_debitos: float | None = None
    computable_creditos: float | None = None
    computable_debitos: float | None = None
    alicuota: float | None = None  # e.g. 33.00


# ═══════════════════════════════════════════════════════════════════════
#  Credit card — summary header
# ═══════════════════════════════════════════════════════════════════════


@dataclass
class LimiteTarjeta:
    """Límites de la tarjeta de crédito."""

    compras: float | None = None
    financiacion: float | None = None
    adelantos: float | None = None


@dataclass
class TarjetaCreditoResumen:
    """Resumen de tarjeta de crédito — cabecera."""

    monto_pagar_pesos: float | None = None
    monto_pagar_dolares: float | None = None
    pago_minimo: float | None = None
    cierre: str | None = None  # "28/05/26"
    vencimiento: str | None = None  # "05/06/26"
    tna_pesos: float | None = None
    tna_dolares: float | None = None
    tem_pesos: float | None = None
    tem_dolares: float | None = None
    sucursal: str | None = None
    numero_cuenta: str | None = None
    limites: LimiteTarjeta | None = None
    pago_anterior: list[PagoAnteriorItem] = field(default_factory=list)
    consumos: list[TarjetaCreditoMovimiento] = field(default_factory=list)
    impuestos: list[ImpuestoCredito] = field(default_factory=list)
    cuotas_vencer: list[CuotaVencer] = field(default_factory=list)


@dataclass
class PagoAnteriorItem:
    """Un ítem en 'Pago anterior y devoluciones'."""

    fecha: str
    descripcion: str
    importe_pesos: float | None = None
    importe_dolares: float | None = None


# ═══════════════════════════════════════════════════════════════════════
#  Credit card — single purchase
# ═══════════════════════════════════════════════════════════════════════


@dataclass
class TarjetaCreditoMovimiento:
    """Un consumo en tarjeta de crédito."""

    fecha: str
    descripcion: str
    cuota: str | None = None  # "03 de 06" or None
    importe_pesos: float | None = None
    importe_dolares: float | None = None


@dataclass
class ImpuestoCredito:
    """Un impuesto/retención en el resumen de tarjeta."""

    descripcion: str
    importe: float


@dataclass
class CuotaVencer:
    """Una cuota futura a vencer."""

    mes: str  # "Junio/26"
    importe: float


# ═══════════════════════════════════════════════════════════════════════
#  Plan V financing
# ═══════════════════════════════════════════════════════════════════════


@dataclass
class PlanVResumen:
    """Opciones de financiación Plan V."""

    pago_minimo: float | None = None
    saldo_financiable: float | None = None
    opciones: list[PlanVOpcion] = field(default_factory=list)
    cuotas_mensuales: list[CuotaVencer] = field(default_factory=list)


@dataclass
class PlanVOpcion:
    """Una opción de cuotas Plan V."""

    cuotas: int  # 3, 6, 12, 24
    importe: float  # monthly payment amount
    tna: float | None = None
    cftea: float | None = None


# ═══════════════════════════════════════════════════════════════════════
#  Debit card transactions
# ═══════════════════════════════════════════════════════════════════════


@dataclass
class TarjetaDebitoMovimiento:
    """Una compra con tarjeta de débito."""

    fecha: str
    comprobante: str | None = None
    establecimiento: str = ""
    importe: float = 0.0


# ═══════════════════════════════════════════════════════════════════════
#  Payments and product summary
# ═══════════════════════════════════════════════════════════════════════


@dataclass
class PagoRealizado:
    """Un pago de servicios realizado en el período."""

    fecha: str
    comprobante: str | None = None
    servicio: str = ""
    medio_pago: str | None = None
    importe: float = 0.0


@dataclass
class ProductSummary:
    """Resumen de productos — tarjetas y puntos."""

    debito_compras_pesos: float | None = None
    debito_compras_dolares: float | None = None
    credito_monto_pesos: float | None = None
    credito_monto_dolares: float | None = None
    superclub_puntos: int | None = None


# ═══════════════════════════════════════════════════════════════════════
#  Personal loans
# ═══════════════════════════════════════════════════════════════════════


@dataclass
class PrestamoPersonal:
    """Un préstamo personal activo."""

    descripcion: str = ""
    capital: float | None = None
    intereses: float | None = None
    iva: float | None = None
    cuota_actual: str | None = None  # "03/36"
    saldo_pendiente: float | None = None


# ═══════════════════════════════════════════════════════════════════════
#  Extracto — the top-level statement container
# ═══════════════════════════════════════════════════════════════════════


@dataclass
class Extracto:
    """Extracto bancario completo."""

    periodo_inicio: str
    periodo_fin: str
    cliente_nombre: str
    cliente_cuit: str
    saldo_inicial: float | None = None
    saldo_final: float | None = None
    sueldo_neto: float | None = None
    movimientos: list[Movimiento] = field(default_factory=list)

    # ── New: all statement sections (optional, backward-compatible) ──

    movimientos_dolares: list[MovimientoDolar] = field(default_factory=list)
    categorias_gasto: list[CategoriaGasto] = field(default_factory=list)
    detalle_impositivo: DetalleImpositivo | None = None
    tarjeta_credito: TarjetaCreditoResumen | None = None
    tarjeta_debito: list[TarjetaDebitoMovimiento] = field(default_factory=list)
    pagos: list[PagoRealizado] = field(default_factory=list)
    productos: ProductSummary | None = None
    plan_v: PlanVResumen | None = None
    prestamos: list[PrestamoPersonal] = field(default_factory=list)
    cuotas_vencer: list[CuotaVencer] = field(default_factory=list)

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
