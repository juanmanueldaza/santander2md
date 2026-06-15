"""Payments section parser."""

from __future__ import annotations

import re

from santander2md.models import PagoRealizado
from santander2md.parsers.line_parser import _LineParser
from santander2md.parsers.noise import _is_noise
from santander2md.utils import parse_monto_argentino


def _parse_pagos(section_text: str) -> list[PagoRealizado]:
    """Parse the 'Pagos' section."""
    result: list[PagoRealizado] = []
    lines = section_text.split("\n")
    in_table = False

    for line in lines:
        line_s = line.strip()
        if not line_s:
            continue
        if _is_noise(line_s):
            continue

        if not in_table:
            if re.search(r"Fecha.*(?:Comprobante|Servicio)", line_s):
                in_table = True
            continue

        if "Pagos totales" in line_s:
            break

        date_str = _LineParser.extract_date(line_s)
        if not date_str:
            continue

        comp = _LineParser.extract_comprobante(line_s)
        m = re.search(r"\$\s*([\d\.,]+)", line_s)
        if not m:
            continue

        importe = parse_monto_argentino(m.group(1))
        if importe is None:
            continue

        rest = line_s[:m.start()]
        parts = [p.strip() for p in rest.split("  ") if p.strip()]
        parts = [
            p for p in parts
            if date_str not in p and (comp is None or comp not in p)
        ]
        servicio = parts[0] if parts else ""
        medio_pago = parts[1] if len(parts) > 1 else None

        result.append(PagoRealizado(
            fecha=date_str,
            comprobante=comp,
            servicio=servicio,
            medio_pago=medio_pago,
            importe=importe,
        ))

    return result
