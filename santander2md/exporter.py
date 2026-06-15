"""
Exportador para santander2md. Formatos: Markdown, CSV, JSON.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

from santander2md.models import Extracto


def _sanitize(text: str) -> str:
    """Sanitize text for safe embedding in tables: replace newlines, strip."""
    return text.replace("\n", " ").replace("\r", " ").strip()


def to_markdown(extracto: Extracto, output_path: str | None = None) -> str:
    """Genera reporte Markdown. Escribe a archivo si se provee output_path."""
    movs = extracto.movimientos
    md = f"""# Extracto Bancario — {extracto.cliente_nombre}

## Datos del Cliente
- **Nombre:** {extracto.cliente_nombre}
- **CUIT:** {extracto.cliente_cuit}

## Período
- **Desde:** {extracto.periodo_inicio}
- **Hasta:** {extracto.periodo_fin}

## Resumen Financiero
- **Saldo Inicial:** ${extracto.saldo_inicial or 0:,.2f}
- **Saldo Final:** ${extracto.saldo_final or 0:,.2f}
"""
    if extracto.sueldo_neto:
        md += f"- **Sueldo Neto:** ${extracto.sueldo_neto:,.2f}\n"

    md += f"""
## Estadísticas
- **Total Ingresos:** ${extracto.total_ingresos:,.2f}
- **Total Gastos:** ${extracto.total_gastos:,.2f}
- **Capacidad de Ahorro:** ${extracto.capacidad_ahorro:,.2f}
- **Cantidad de Movimientos:** {len(movs)}
- **Promedio de Gasto Diario:** ${extracto.promedio_gasto_diario:,.2f}

## Movimientos
| Fecha | Descripción | Tipo | Monto |
|-------|-------------|------|-------|
"""
    for mov in movs:
        desc = _sanitize(mov.descripcion)
        tipo = mov.tipo
        monto = mov.monto
        md += f"| {mov.fecha} | {desc} | {tipo} | ${monto:,.2f} |\n"

    if output_path:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(md, encoding="utf-8")

    return md


def to_csv(extracto: Extracto, output_path: str) -> None:
    """Exporta movimientos a CSV (fecha, tipo, monto, descripcion)."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
        writer.writerow(["fecha", "tipo", "monto", "descripcion"])
        for mov in extracto.movimientos:
            desc = _sanitize(mov.descripcion)
            monto = mov.debito if mov.debito is not None else mov.credito
            writer.writerow([mov.fecha, mov.tipo, monto, desc])


def to_json(extracto: Extracto, output_path: str) -> None:
    """Exporta el extracto completo a JSON."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(extracto.to_dict(), f, indent=2, ensure_ascii=False)


# Backward-compatible class wrapper
class Exporter:
    """Wrapper de compatibilidad para código existente."""

    @staticmethod
    def to_markdown(extracto: Extracto, output_path: str | None = None) -> str:
        return to_markdown(extracto, output_path)

    @staticmethod
    def to_csv(extracto: Extracto, output_path: str) -> None:
        to_csv(extracto, output_path)

    @staticmethod
    def to_json(extracto: Extracto, output_path: str) -> None:
        to_json(extracto, output_path)
