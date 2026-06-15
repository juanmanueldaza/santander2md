"""
Utilidades para santander2md.
"""

from __future__ import annotations

import re
from typing import Optional


def parse_monto_argentino(monto_str: Optional[str]) -> Optional[float]:
    """
    Parsea un monto en formato argentino a float.

    Formatos:
      "$ 1.510.287,57"  → 1510287.57
      "-$ 113.800,00"   → -113800.00
      "1.510.28757"     → 1510287.57  (coma perdida en extracción)
      "U$S 363,28"      → 363.28
      "1510287,57"      → 1510287.57
    """
    if not monto_str or not monto_str.strip():
        return None

    s = monto_str.strip()

    # Detect sign
    sign = 1
    if s.startswith("-"):
        sign = -1
        s = s[1:].strip()

    # Remove currency indicators and spaces (order matters: U$S before $)
    s = s.replace("U$S", "").replace("usd", "").replace("USD", "")
    s = s.replace("$", "").replace(" ", "").strip()

    if not s:
        return None

    # ── Normalize to standard float format ──

    if "." in s and "," in s:
        # Argentinian: 1.510.287,57 → dots are thousands, comma is decimal
        s = s.replace(".", "").replace(",", ".")

    elif "," in s:
        # Has comma, no dots: comma is decimal separator
        parts = s.split(",")
        if len(parts[-1]) <= 2:
            # 1510287,57 → 1510287.57
            s = s.replace(",", ".")
        else:
            # 1,510,287 → commas are thousand separators (no decimals)
            s = s.replace(",", "")

    elif "." in s:
        # Has dots, no commas
        parts = s.split(".")
        if len(parts) > 2 and len(parts[-1]) > 2:
            # 1.510.28757 → comma was lost, last 2 digits are cents
            s = "".join(parts[:-1]) + parts[-1][:-2] + "." + parts[-1][-2:]
        # else: 1510287.57 → already valid

    try:
        return sign * float(s)
    except (ValueError, TypeError):
        return None



