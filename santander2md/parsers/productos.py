"""Product summary section parser."""

from __future__ import annotations

import re

from santander2md.models import ProductSummary
from santander2md.utils import parse_monto_argentino


def _parse_productos(section_text: str) -> ProductSummary | None:
    """Parse the 'Resumen de tus productos' section."""
    result = ProductSummary()
    lines = section_text.split("\n")

    for i, line in enumerate(lines):
        line_s = line.strip()
        if re.match(r"\$\s*[\d\.,\s]+", line_s) and i + 1 < len(lines):
            pesos_vals = re.findall(r"\$\s*([\d\.,\s]+)", line_s)
            for j in range(i + 1, min(i + 4, len(lines))):
                next_s = lines[j].strip()
                usd_vals = re.findall(r"U\$S\s*([\d\.,\s]+)", next_s)
                if usd_vals:
                    if len(pesos_vals) >= 2:
                        result.debito_compras_pesos = parse_monto_argentino(pesos_vals[0])
                        result.credito_monto_pesos = parse_monto_argentino(pesos_vals[1])
                    if len(usd_vals) >= 2:
                        result.debito_compras_dolares = parse_monto_argentino(usd_vals[0])
                        result.credito_monto_dolares = parse_monto_argentino(usd_vals[1])
                    break
            break

    for line in lines:
        line_s = line.strip()
        if re.match(r"^\d[\d\.]+$", line_s):
            try:
                result.superclub_puntos = int(line_s.replace(".", ""))
            except ValueError:
                pass
            break

    if all(v is None for v in [
        result.debito_compras_pesos, result.debito_compras_dolares,
        result.credito_monto_pesos, result.credito_monto_dolares,
        result.superclub_puntos,
    ]):
        return None
    return result
