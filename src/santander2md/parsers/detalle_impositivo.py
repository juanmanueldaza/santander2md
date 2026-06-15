"""Tax withholding detail parser."""

from __future__ import annotations

import re

from santander2md.models import DetalleImpositivo
from santander2md.utils import parse_monto_argentino


def _parse_detalle_impositivo(section_text: str) -> DetalleImpositivo | None:
    """Parse tax withholding detail."""
    result = DetalleImpositivo()

    m = re.search(r"Total retencion.*creditos:?\s+\$?\s*([\d\.,]+)", section_text)
    if m:
        result.total_retencion_creditos = parse_monto_argentino(m.group(1))

    m = re.search(r"Total retencion.*debitos:?\s+\$?\s*([\d\.,]+)", section_text)
    if m:
        result.total_retencion_debitos = parse_monto_argentino(m.group(1))

    m = re.search(
        r"(?i)por creditos alicuota\s+([\d,]+)\s*%:?\s+\$?\s*([\d\.,]+)",
        section_text,
    )
    if m:
        result.alicuota = float(m.group(1).replace(",", "."))
        result.computable_creditos = parse_monto_argentino(m.group(2))

    m = re.search(
        r"(?i)por debitos alicuota\s+[\d,]+\s*%:?\s+\$?\s*([\d\.,]+)",
        section_text,
    )
    if m:
        result.computable_debitos = parse_monto_argentino(m.group(1))

    if all(
        v is None
        for v in [
            result.total_retencion_creditos,
            result.total_retencion_debitos,
            result.computable_creditos,
            result.computable_debitos,
        ]
    ):
        return None
    return result
