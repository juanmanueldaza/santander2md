"""
Modelos de datos para santander2md.
Usa dataclasses para estructurar la información.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

@dataclass
class Cliente:
    """Datos del cliente."""
    nombre: str
    cuit: str
    cbu: str
    
    def __str__(self):
        return f"{self.nombre} (CUIT: {self.cuit})"


@dataclass
class Periodo:
    """Período del extracto."""
    inicio: str  # Formato: DD/MM/YY
    fin: str    # Formato: DD/MM/YY
    
    def __str__(self):
        return f"{self.inicio} al {self.fin}"


@dataclass
class Movimiento:
    """Un movimiento bancario (transacción)."""
    fecha: str
    descripcion: str
    debito: Optional[float] = None   # Monto negativo (gasto)
    credito: Optional[float] = None  # Monto positivo (ingreso)
    
    @property
    def monto(self) -> float:
        """Devuelve el monto absoluto."""
        if self.debito:
            return -self.debito
        return self.credito or 0.0
    
    def __str__(self):
        tipo = "DÉBITO" if self.debito else "CRÉDITO"
        monto = self.debito if self.debito else self.credito
        return f"{self.fecha} | {tipo:>8} | ${monto:>12,.2f} | {self.descripcion}"


@dataclass
class Saldos:
    """Saldos inicial y final."""
    inicial: Optional[float] = None
    final: Optional[float] = None
    
    def __str__(self):
        return f"Inicial: ${self.inicial:,.2f} | Final: ${self.final:,.2f}"


@dataclass
class Extracto:
    """Extracto bancario completo."""
    periodo: Periodo
    cliente: Cliente
    saldos: Saldos
    sueldo_neto: Optional[float] = None
    movimientos: List[Movimiento] = field(default_factory=list)
    
    @property
    def total_ingresos(self) -> float:
        """Suma de todos los créditos (excepto el sueldo)."""
        return sum(m.credito for m in self.movimientos if m.credito and m.credito > 0)
    
    @property
    def total_gastos(self) -> float:
        """Suma de todos los débitos."""
        return sum(m.debito for m in self.movimientos if m.debito and m.debito > 0)
    
    @property
    def capacidad_ahorro(self) -> float:
        """Ingresos - Gastos."""
        return self.total_ingresos - self.total_gastos
    
    def to_markdown(self) -> str:
        """Convierte el extracto a Markdown."""
        md = f"""# Extracto Santander - {self.periodo}

## Datos del Cliente
- **Nombre:** {self.cliente.nombre}
- **CUIT:** {self.cliente.cuit}
- **CBU:** {self.cliente.cbu}

## Resumen Financiero
- **Período:** {self.periodo}
- **Saldo Inicial:** ${self.saldos.inicial:,.2f}
- **Saldo Final:** ${self.saldos.final:,.2f}
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
        for mov in self.movimientos[:50]:  # Mostrar solo los primeros 50
            tipo = "DÉBITO" if mov.debito else "CRÉDITO"
            monto = mov.debito if mov.debito else mov.credito
            md += f"| {mov.fecha} | {tipo} | ${monto:,.2f} | {mov.descripcion} |\n"
        
        if len(self.movimientos) > 50:
            md += f"\n*... y {len(self.movimientos) - 50} movimientos más.*\n"
        
        return md
