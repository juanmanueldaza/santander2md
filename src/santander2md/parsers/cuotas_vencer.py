"""Unified 'Cuotas a vencer' parser (standalone and inline credit-card)."""

from __future__ import annotations

import re

from santander2md.models import CuotaVencer
from santander2md.utils import parse_monto_argentino


def _parse_cuotas_vencer(section_text: str) -> list[CuotaVencer]:
    """Parse 'Cuotas a vencer' from either standalone or inline CC text."""
    lines = section_text.split("\n")
    result: list[CuotaVencer] = []

    # Format A (standalone): month names line + $ amounts line
    months: list[str] = []
    amounts: list[float] = []
    in_section = False

    for line in lines:
        s = line.strip()
        if not s:
            continue
        if "Cuotas a vencer" in s:
            in_section = True
            continue
        if not in_section:
            # Also allow parsing without explicit header for standalone blobs
            pass
        if "Plan V" in s or "Tasa" in s:
            if in_section:
                break
            continue

        if re.match(r"^[A-Z][a-záéíóú]+/\d{2}", s):
            months = re.findall(r"([A-Z][a-záéíóú]+/\d{2})", s)
        elif s.startswith("$") or re.search(r"\$\s*[\d\.,]+", s):
            amounts = []
            for m in re.finditer(r"\$\s*([\d\.,]+)", s):
                val = parse_monto_argentino(m.group(1))
                if val is not None:
                    amounts.append(val)

    for i in range(min(len(months), len(amounts))):
        result.append(CuotaVencer(mes=months[i], importe=amounts[i]))

    # Format B (inline CC): "Mes/AA  $importe" per line
    in_section = False
    for line in lines:
        s = line.strip()
        if not s:
            continue
        if "Cuotas a vencer" in s:
            in_section = True
            continue
        if not in_section:
            continue
        if "Plan V" in s or "Tasa" in s:
            break

        m = re.search(r"(\w+/\d{2})\s+\$?\s*([\d\.,]+)", s)
        if m:
            mes = m.group(1)
            importe = parse_monto_argentino(m.group(2))
            if importe is not None:
                result.append(CuotaVencer(mes=mes, importe=importe))

    return result
