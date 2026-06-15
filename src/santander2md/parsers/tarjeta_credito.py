"""Credit card section parser."""

from __future__ import annotations

import re

from santander2md.models import (
    ImpuestoCredito,
    LimiteTarjeta,
    PagoAnteriorItem,
    TarjetaCreditoMovimiento,
    TarjetaCreditoResumen,
)
from santander2md.parsers.cuotas_vencer import _parse_cuotas_vencer
from santander2md.parsers.line_parser import _accumulate_continuations, _LineParser
from santander2md.parsers.noise import _is_noise
from santander2md.utils import parse_monto_argentino


def _parse_tarjeta_credito(section_text: str) -> TarjetaCreditoResumen | None:
    """Parse the full credit card section."""
    resumen = TarjetaCreditoResumen()
    lines = section_text.split("\n")

    # ── Header fields ──
    for i, line in enumerate(lines):
        line_s = line.strip()
        if "Total en pesos" in line_s and "Total en dólares" in line_s:
            for j in range(i + 1, min(i + 4, len(lines))):
                val_line = lines[j].strip()
                if "$" in val_line or "U$S" in val_line:
                    ars_matches = list(re.finditer(r"\$\s*([\d\.,]+)", val_line))
                    usd_matches = list(re.finditer(r"U\$S\s*([\d\.,]+)", val_line))
                    date_matches = list(re.finditer(r"(\d{2}/\d{2}/\d{2})", val_line))

                    if ars_matches:
                        val = parse_monto_argentino(ars_matches[0].group(1))
                        if val is not None:
                            resumen.monto_pagar_pesos = val
                    if len(ars_matches) > 1:
                        val = parse_monto_argentino(ars_matches[1].group(1))
                        if val is not None:
                            resumen.pago_minimo = val
                    if usd_matches:
                        raw = usd_matches[0].group(1)
                        val = parse_monto_argentino(raw)
                        if val is not None:
                            if "." not in raw and "," not in raw:
                                val = val / 100
                            resumen.monto_pagar_dolares = val
                    dates = [m.group(1) for m in date_matches]
                    if dates:
                        resumen.cierre = dates[0]
                    if len(dates) > 1:
                        resumen.vencimiento = dates[1]
                    break
            break

    # Sucursal / TNA / TEM row
    for i, line in enumerate(lines):
        line_s = line.strip()
        if "Sucursal" in line_s and "Tasa nominal anual" in line_s:
            for j in range(i + 1, min(i + 3, len(lines))):
                val_line = lines[j].strip()
                if "Ituzaingo" in val_line or re.search(r"Pesos:\s*[\d,]+", val_line):
                    if m := re.search(r"(\d+\s*-\s*\w+)", val_line):
                        resumen.sucursal = m.group(1)
                    if m := re.search(r"(\d{9,})", val_line):
                        resumen.numero_cuenta = m.group(1)
                    if m := re.search(r"Pesos:\s*([\d,]+)\s*%", val_line):
                        resumen.tna_pesos = float(m.group(1).replace(",", "."))
                    if m := re.search(r"Dólares:\s*([\d,]+)\s*%", val_line):
                        resumen.tna_dolares = float(m.group(1).replace(",", "."))
                    tem_matches = list(re.finditer(r"Pesos:\s*([\d,]+)\s*%", val_line))
                    if len(tem_matches) > 1:
                        tem_raw = tem_matches[1].group(1)
                        resumen.tem_pesos = float(tem_raw.replace(",", "."))
                    dol_pattern = r"Dólares:\s*([\d,]+)\s*%"
                    dol_matches = list(re.finditer(dol_pattern, val_line))
                    if len(dol_matches) > 1:
                        dol_raw = dol_matches[1].group(1)
                        resumen.tem_dolares = float(dol_raw.replace(",", "."))
                    break
            break

    # ── Límites ──
    limites = LimiteTarjeta()
    for i, line in enumerate(lines):
        if "Compras" in line and "Financiación" in line and "Adelantos" in line:
            for j in range(i + 1, min(i + 3, len(lines))):
                val_line = lines[j].strip()
                vals = list(re.finditer(r"\$\s*([\d\.,]+)", val_line))
                if len(vals) >= 3:
                    limites.compras = parse_monto_argentino(vals[0].group(1))
                    limites.financiacion = parse_monto_argentino(vals[1].group(1))
                    limites.adelantos = parse_monto_argentino(vals[2].group(1))
                break
            break
    if limites.compras or limites.financiacion or limites.adelantos:
        resumen.limites = limites

    resumen.pago_anterior = _parse_pago_anterior(lines)
    resumen.consumos = _parse_consumos_credito(lines)
    resumen.impuestos = _parse_impuestos_credito(lines)
    resumen.cuotas_vencer = _parse_cuotas_vencer(section_text)

    if (
        resumen.monto_pagar_pesos is None
        and resumen.monto_pagar_dolares is None
        and not resumen.consumos
        and not resumen.impuestos
    ):
        return None
    return resumen


def _parse_pago_anterior(lines: list[str]) -> list[PagoAnteriorItem]:
    """Parse 'Pago anterior y devoluciones' sub-section in credit card."""
    result: list[PagoAnteriorItem] = []
    merged = _accumulate_continuations(
        lines,
        stop_pred=lambda s: (
            s.startswith("Total") or "Consumos del mes" in s or "Consumos totales" in s
        ),
    )
    in_section = False
    in_table = False

    for s in merged:
        if _is_noise(s):
            continue

        if "Pago anterior" in s:
            in_section = True
            continue
        if not in_section:
            continue
        if "Consumos del mes" in s or "Consumos totales" in s:
            break

        if not in_table:
            if "Fecha" in s and "Descripción" in s:
                in_table = True
            continue

        if s.startswith("Total"):
            break

        date_str = _LineParser.extract_date(s)

        ars_match = re.search(r"(-?)\$\s*([\d\.,]+)", s)
        usd_match = re.search(r"(-?)U\$S\s*([\d\.,]+)", s)

        ars = None
        usd = None
        if ars_match:
            val = parse_monto_argentino(ars_match.group(2))
            if val is not None:
                ars = -val if ars_match.group(1) == "-" else val
        if usd_match:
            val = parse_monto_argentino(usd_match.group(2))
            if val is not None:
                usd = -val if usd_match.group(1) == "-" else val

        if not ars and not usd:
            continue

        desc_start = 0
        if date_str and date_str in s:
            desc_start = s.index(date_str) + len(date_str)
        first_amt = min(
            ars_match.start() if ars_match else len(s),
            usd_match.start() if usd_match else len(s),
        )
        desc = s[desc_start:first_amt].strip()

        result.append(
            PagoAnteriorItem(
                fecha=date_str or "",
                descripcion=desc,
                importe_pesos=ars,
                importe_dolares=usd,
            )
        )

    return result


def _parse_consumos_credito(lines: list[str]) -> list[TarjetaCreditoMovimiento]:
    """Parse credit card purchase table within the Tarjeta Santander section."""
    result: list[TarjetaCreditoMovimiento] = []
    in_section = False
    in_table = False

    for line in lines:
        line_s = line.strip()
        if not line_s:
            continue
        if _is_noise(line_s):
            continue

        if re.search(r"Consumos del mes", line_s):
            in_section = True
            continue
        if not in_section:
            continue

        if re.search(r"Impuestos|Impuesto de sellos|IIBB percepción|IVA RG", line_s):
            break
        if "Consumos totales" in line_s:
            break

        if not in_table:
            if re.search(r"Fecha.*Comprobante.*(?:Consumo|Descripción)", line_s):
                in_table = True
            continue

        date_str = _LineParser.extract_date(line_s)
        if not date_str:
            continue

        comp = _LineParser.extract_comprobante(line_s)

        usd_match = re.search(r"U\$S\s*([\d\.,]+)", line_s)
        ars_match = re.search(r"\$\s*([\d\.,]+)", line_s)

        usd = parse_monto_argentino(usd_match.group(1)) if usd_match else None
        ars = parse_monto_argentino(ars_match.group(1)) if ars_match else None

        cuota_match = re.search(r"(\d{2}\s+de\s+\d{2})", line_s)
        cuota = cuota_match.group(1) if cuota_match else None

        desc_start = 0
        if comp:
            desc_start = line_s.index(comp) + len(comp)
        first_amount = line_s.find("$", desc_start)
        if first_amount < 0:
            first_amount = len(line_s)
        desc = line_s[desc_start:first_amount].strip()

        result.append(
            TarjetaCreditoMovimiento(
                fecha=date_str,
                descripcion=desc,
                cuota=cuota,
                importe_pesos=ars,
                importe_dolares=usd,
            )
        )

    return result


def _parse_impuestos_credito(lines: list[str]) -> list[ImpuestoCredito]:
    """Parse credit card tax/retention items."""
    result: list[ImpuestoCredito] = []
    in_section = False

    for line in lines:
        line_s = line.strip()
        if not line_s:
            continue

        if re.search(r"Impuesto de sellos|IIBB percepción|IVA RG|DB RG", line_s):
            in_section = True
        if not in_section:
            continue
        if (
            "Consumos totales" in line_s
            or "Cuotas a vencer" in line_s
            or "Plan V" in line_s
        ):
            break

        m = re.search(r"\$\s*([\d\.,]+)", line_s)
        if m:
            amount = parse_monto_argentino(m.group(1))
            desc = line_s[: m.start()].strip()
            if desc and amount is not None:
                result.append(ImpuestoCredito(descripcion=desc, importe=amount))

    return result
