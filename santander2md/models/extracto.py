"""
Modelos de datos para santander2md.
"""

from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class Movimiento:
    """Un movimiento bancario."""
    fecha: str
    descripcion: str
    monto: float  # Positivo = ingreso, Negativo = gasto
    tipo: str  # "debito" o "credito"
    
    def __str__(self):
        signo = "-" if self.tipo == "debito" else "+"
        return f"{self.fecha} | {signo}${abs(self.monto):,.2f} | {self.descripcion}"


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
        """Suma de ingresos (sin contar el sueldo)."""
        return sum(m.monto for m in self.movimientos if m.tipo == "credito")
    
    @property
    def total_gastos(self) -> float:
        """Suma de gastos (valores absolutos)."""
        return sum(abs(m.monto) for m in self.movimientos if m.tipo == "debito")
    
    @property
    def capacidad_ahorro(self) -> float:
        """Ingresos - Gastos."""
        return self.total_ingresos - self.total_gastos
    
    def to_markdown(self) -> str:
        """Genera reporte en Markdown."""
        md = f"""# Extracto Santander - {self.periodo_inicio} al {self.periodo_fin}

## Datos del Cliente
- **Nombre:** {self.cliente_nombre}
- **CUIT:** {self.cliente_cuit}

## Resumen Financiero
- **Saldo Inicial:** ${self.saldo_inicial:,.2f}
- **Saldo Final:** ${self.saldo_final:,.2f}
- **Sueldo Neto:** ${self.sueldo_neto:,.2f}

## Estadísticas
- **Total Ingresos:** ${self.total_ingresos:,.2f}
- **Total Gastos:** ${self.total_gastos:,.2f}
- **Capacidad de Ahorro:** ${self.capacidad_ahorro:,.2f}
- **Número de Movimientos:** {len(self.movimientos)}

## Movimientos

| Fecha | Tipo | Monto | Descripción |
|-------|-------|-------|-------------|
"""
        for mov in self.movimientos[:50]:
            tipo_str = "DÉBITO" if mov.tipo == "debito" else "CRÉDITO"
            md += f"| {mov.fecha} | {tipo_str} | ${mov.monto:,.2f} | {mov.descripcion} |\n"
        
        if len(self.movimientos) > 50:
            md += f"\n*... y {len(self.movimientos) - 50} movimientos más.*\n"
        
        return md
