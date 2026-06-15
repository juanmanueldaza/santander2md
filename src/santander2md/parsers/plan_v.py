"""Plan V financing options parser."""

from __future__ import annotations

import re

from santander2md.models import PlanVOpcion, PlanVResumen
from santander2md.utils import parse_monto_argentino


def _parse_plan_v(section_text: str) -> PlanVResumen | None:
    """Parse Plan V financing options."""
    result = PlanVResumen()
    flat = section_text.replace("\n", " ")

    m = re.search(r"pago mínimo\s+de\s+\$?\s*([\d\.,]+)", flat, re.I)
    if m:
        result.pago_minimo = parse_monto_argentino(m.group(1))

    m = re.search(r"saldo financiable\s+de\s+\$?\s*([\d\.,]+)", flat, re.I)
    if m:
        result.saldo_financiable = parse_monto_argentino(m.group(1))

    for m in re.finditer(
        r"(\d+)\s+cuotas?\s+de\s+\$?\s*([\d\.,]+)\s*\(TNA\s+Fija:\s*([\d,]+)%",
        flat,
        re.I,
    ):
        cuotas = int(m.group(1))
        importe = parse_monto_argentino(m.group(2))
        tna = float(m.group(3).replace(",", ".")) if m.group(3) else None

        cftea = None
        cftea_m = re.search(r"CFTEA[^:]*:\s*([\d,]+)%", flat[m.end() : m.end() + 60])
        if cftea_m:
            cftea = float(cftea_m.group(1).replace(",", "."))

        if importe is not None:
            result.opciones.append(
                PlanVOpcion(
                    cuotas=cuotas,
                    importe=importe,
                    tna=tna,
                    cftea=cftea,
                )
            )

    if result.pago_minimo is None and not result.opciones:
        return None
    return result
