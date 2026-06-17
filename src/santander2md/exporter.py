"""
Exportador para santander2md. Formatos: Markdown, CSV, JSON.
"""

from __future__ import annotations

import csv
import io
import json
from pathlib import Path

from santander2md._io import _ensure_dir
from santander2md.models import (
    CategoriaGasto,
    DetalleImpositivo,
    Extracto,
    MovimientoDolar,
    PagoRealizado,
    PlanVResumen,
    ProductSummary,
    TarjetaCreditoResumen,
    TarjetaDebitoMovimiento,
)


def _sanitize(text: str) -> str:
    """Sanitize text for safe embedding in tables: replace newlines, strip."""
    return text.replace("\n", " ").replace("\r", " ").strip()


# ═══════════════════════════════════════════════════════════════════════
#  Section renderers
# ═══════════════════════════════════════════════════════════════════════


def _render_mermaid_pie(categorias: list[CategoriaGasto]) -> str:
    """Render spending categories as a Mermaid pie chart."""
    if not categorias:
        return ""
    lines = ["```mermaid", "pie showData"]
    lines.append("    title Así usaste tu dinero")
    for c in categorias:
        # Mermaid pie values must be positive numbers (no commas)
        lines.append(f'    "{c.nombre}" : {c.total:.0f}')
    lines.append("```")
    return "\n".join(lines) + "\n"


def _render_dollar_movements(movimientos: list[MovimientoDolar]) -> str:
    """Render USD movements table."""
    if not movimientos:
        return ""
    md = "\n## Movimientos en Dólares\n\n"
    md += "| Fecha | Descripción | Tipo | Monto (U$S) | Saldo (U$S) |\n"
    md += "|-------|-------------|------|-------------|-------------|\n"
    for m in movimientos:
        desc = _sanitize(m.descripcion)
        saldo_str = f"{m.saldo:,.2f}" if m.saldo is not None else "—"
        md += f"| {m.fecha} | {desc} | {m.tipo} | {m.monto:,.2f} | {saldo_str} |\n"
    return md


def _render_spending_categories(categorias: list[CategoriaGasto]) -> str:
    """Render spending categories: Mermaid pie + table."""
    if not categorias:
        return ""
    md = "\n## Así Usaste Tu Dinero\n\n"
    md += _render_mermaid_pie(categorias)
    md += "\n| Categoría | Porcentaje | Total |\n"
    md += "|-----------|-----------|-------|\n"
    for c in categorias:
        md += f"| {c.nombre} | {c.porcentaje:.2f}% | ${c.total:,.2f} |\n"
    return md


def _render_credit_card(tc: TarjetaCreditoResumen) -> str:
    """Render full credit card section."""
    md = "\n## Tarjeta de Crédito\n\n"

    if tc.monto_pagar_pesos or tc.monto_pagar_dolares:
        md += "### Resumen\n\n"
        if tc.monto_pagar_pesos:
            md += f"- **Monto a pagar (Pesos):** ${tc.monto_pagar_pesos:,.2f}\n"
        if tc.monto_pagar_dolares:
            md += f"- **Monto a pagar (Dólares):** U$S {tc.monto_pagar_dolares:,.2f}\n"
        if tc.pago_minimo:
            md += f"- **Pago mínimo:** ${tc.pago_minimo:,.2f}\n"
        if tc.cierre:
            md += f"- **Cierre:** {tc.cierre}\n"
        if tc.vencimiento:
            md += f"- **Vencimiento:** {tc.vencimiento}\n"
        if tc.tna_pesos:
            md += f"- **TNA Pesos:** {tc.tna_pesos}%\n"
        if tc.tem_pesos:
            md += f"- **TEM Pesos:** {tc.tem_pesos}%\n"
        md += "\n"

    if tc.limites and (tc.limites.compras or tc.limites.financiacion):
        md += "### Límites\n\n"
        if tc.limites.compras:
            md += f"- **Compras:** ${tc.limites.compras:,.2f}\n"
        if tc.limites.financiacion:
            md += f"- **Financiación:** ${tc.limites.financiacion:,.2f}\n"
        if tc.limites.adelantos:
            md += f"- **Adelantos:** ${tc.limites.adelantos:,.2f}\n"
        md += "\n"

    if tc.pago_anterior:
        md += "### Pago Anterior y Devoluciones\n\n"
        md += "| Fecha | Descripción | Pesos | Dólares |\n"
        md += "|-------|-------------|-------|--------|\n"
        for pa in tc.pago_anterior:
            desc = _sanitize(pa.descripcion)
            ars = f"${pa.importe_pesos:,.2f}" if pa.importe_pesos is not None else ""
            usd = (
                f"U$S {pa.importe_dolares:,.2f}"
                if pa.importe_dolares is not None
                else ""
            )
            md += f"| {pa.fecha} | {desc} | {ars} | {usd} |\n"
        md += "\n"

    if tc.consumos:
        md += "### Consumos del Mes\n\n"
        md += "| Fecha | Descripción | Cuota | Pesos | Dólares |\n"
        md += "|-------|-------------|-------|-------|--------|\n"
        for c in tc.consumos:
            desc = _sanitize(c.descripcion)
            cuota = c.cuota or ""
            ars = f"${c.importe_pesos:,.2f}" if c.importe_pesos else ""
            usd = f"U$S {c.importe_dolares:,.2f}" if c.importe_dolares else ""
            md += f"| {c.fecha} | {desc} | {cuota} | {ars} | {usd} |\n"
        md += "\n"

    if tc.impuestos:
        md += "### Impuestos\n\n"
        md += "| Descripción | Importe |\n"
        md += "|-------------|--------|\n"
        for imp in tc.impuestos:
            md += f"| {imp.descripcion} | ${imp.importe:,.2f} |\n"
        md += "\n"

    if tc.cuotas_vencer:
        md += "### Cuotas a Vencer\n\n"
        md += "| Mes | Importe |\n"
        md += "|-----|--------|\n"
        for cv in tc.cuotas_vencer:
            md += f"| {cv.mes} | ${cv.importe:,.2f} |\n"
        md += "\n"

    return md


def _render_debit_card(movimientos: list[TarjetaDebitoMovimiento]) -> str:
    """Render debit card transactions table."""
    if not movimientos:
        return ""
    md = "\n## Tarjeta de Débito\n\n"
    md += "| Fecha | Comprobante | Establecimiento | Importe |\n"
    md += "|-------|-------------|-----------------|--------|\n"
    for m in movimientos:
        est = _sanitize(m.establecimiento)
        comp = m.comprobante or ""
        md += f"| {m.fecha} | {comp} | {est} | ${m.importe:,.2f} |\n"
    return md


def _render_payments(pagos: list[PagoRealizado]) -> str:
    """Render payments section."""
    if not pagos:
        return ""
    md = "\n## Pagos\n\n"
    md += "| Fecha | Servicio | Medio de Pago | Importe |\n"
    md += "|-------|----------|---------------|--------|\n"
    for p in pagos:
        svc = _sanitize(p.servicio)
        medio = p.medio_pago or ""
        md += f"| {p.fecha} | {svc} | {medio} | ${p.importe:,.2f} |\n"
    return md


def _render_tax_detail(detalle: DetalleImpositivo) -> str:
    """Render tax detail section."""
    md = "\n## Detalle Impositivo\n\n"
    if detalle.total_retencion_creditos is not None:
        total = detalle.total_retencion_creditos
        md += f"- **Retención por créditos:** ${total:,.2f}\n"
    if detalle.total_retencion_debitos is not None:
        md += f"- **Retención por débitos:** ${detalle.total_retencion_debitos:,.2f}\n"
    if detalle.computable_creditos is not None:
        md += f"- **Computable créditos:** ${detalle.computable_creditos:,.2f}\n"
    if detalle.computable_debitos is not None:
        md += f"- **Computable débitos:** ${detalle.computable_debitos:,.2f}\n"
    if detalle.alicuota is not None:
        md += f"- **Alícuota:** {detalle.alicuota}%\n"
    return md + "\n"


def _render_products(productos: ProductSummary) -> str:
    """Render product summary."""
    md = "\n## Resumen de Productos\n\n"
    if productos.debito_compras_pesos is not None:
        md += f"- **Débito compras (Pesos):** ${productos.debito_compras_pesos:,.2f}\n"
    if productos.debito_compras_dolares is not None:
        debito_usd = productos.debito_compras_dolares
        md += f"- **Débito compras (Dólares):** U$S {debito_usd:,.2f}\n"
    if productos.credito_monto_pesos is not None:
        md += f"- **Crédito monto (Pesos):** ${productos.credito_monto_pesos:,.2f}\n"
    if productos.credito_monto_dolares is not None:
        credito_usd = productos.credito_monto_dolares
        md += f"- **Crédito monto (Dólares):** U$S {credito_usd:,.2f}\n"
    if productos.superclub_puntos is not None:
        md += f"- **SuperClub+ Puntos:** {productos.superclub_puntos:,}\n"
    return md + "\n"


def _render_plan_v(plan: PlanVResumen) -> str:
    """Render Plan V financing options."""
    md = "\n## Plan V — Financiación\n\n"
    if plan.pago_minimo:
        md += f"- **Pago mínimo:** ${plan.pago_minimo:,.2f}\n"
    if plan.saldo_financiable:
        md += f"- **Saldo financiable:** ${plan.saldo_financiable:,.2f}\n"

    if plan.opciones:
        md += "\n| Cuotas | Importe Mensual | TNA | CFTEA |\n"
        md += "|--------|----------------|-----|-------|\n"
        for o in plan.opciones:
            tna_str = f"{o.tna}%" if o.tna else "—"
            cftea_str = f"{o.cftea}%" if o.cftea else "—"
            md += f"| {o.cuotas} | ${o.importe:,.2f} | {tna_str} | {cftea_str} |\n"
        md += "\n"

    if plan.cuotas_mensuales:
        md += "### Cuotas Mensuales\n\n"
        md += "| Mes | Importe |\n"
        md += "|-----|--------|\n"
        for cv in plan.cuotas_mensuales:
            md += f"| {cv.mes} | ${cv.importe:,.2f} |\n"
        md += "\n"

    return md


def _render_prestamos(prestamos: list) -> str:
    """Render personal loans section."""
    if not prestamos:
        return ""
    md = "\n## Préstamos Personales\n\n"
    md += "| Préstamo | Cuota | Capital | Intereses | Saldo Pendiente |\n"
    md += "|----------|-------|---------|-----------|----------------|\n"
    for p in prestamos:
        cuota = p.cuota_actual or ""
        cap = f"${p.capital:,.2f}" if p.capital else ""
        intv = f"${p.intereses:,.2f}" if p.intereses else ""
        saldo = f"${p.saldo_pendiente:,.2f}" if p.saldo_pendiente else ""
        md += f"| {p.descripcion} | {cuota} | {cap} | {intv} | {saldo} |\n"
    return md + "\n"


# ═══════════════════════════════════════════════════════════════════════
#  Main exporters
# ═══════════════════════════════════════════════════════════════════════


def to_markdown(extracto: Extracto) -> str:
    """Genera reporte Markdown completo y lo devuelve como string."""
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
"""

    # ── Spending categories (Mermaid pie chart) ──
    md += _render_spending_categories(extracto.categorias_gasto)

    # ── Dollar movements ──
    md += _render_dollar_movements(extracto.movimientos_dolares)

    # ── Movimientos en pesos ──
    md += """
## Movimientos en Pesos
| Fecha | Descripción | Tipo | Monto |
|-------|-------------|------|-------|
"""
    for mov in movs:
        desc = _sanitize(mov.descripcion)
        md += f"| {mov.fecha} | {desc} | {mov.tipo} | ${mov.monto:,.2f} |\n"

    # ── New sections ──
    if extracto.detalle_impositivo:
        md += _render_tax_detail(extracto.detalle_impositivo)

    if extracto.tarjeta_credito:
        md += _render_credit_card(extracto.tarjeta_credito)

    md += _render_debit_card(extracto.tarjeta_debito)
    md += _render_payments(extracto.pagos)

    if extracto.productos:
        md += _render_products(extracto.productos)

    if extracto.plan_v:
        md += _render_plan_v(extracto.plan_v)

    md += _render_prestamos(extracto.prestamos)

    return md


def to_csv(extracto: Extracto, output_path: str | Path) -> None:
    """Exporta movimientos a CSV (fecha, tipo, monto, descripcion)."""
    output = io.StringIO()
    writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)
    writer.writerow(["fecha", "tipo", "monto", "descripcion"])
    for mov in extracto.movimientos:
        desc = _sanitize(mov.descripcion)
        writer.writerow([mov.fecha, mov.tipo, mov.monto, desc])

    path = Path(output_path)
    _ensure_dir(path)
    path.write_text(output.getvalue(), encoding="utf-8")


def to_json(extracto: Extracto, output_path: str | Path) -> None:
    """Exporta el extracto completo a JSON."""
    path = Path(output_path)
    _ensure_dir(path)
    path.write_text(
        json.dumps(extracto.to_dict(), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
