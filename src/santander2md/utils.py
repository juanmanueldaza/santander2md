"""
Utilidades para santander2md.
"""

from __future__ import annotations


def parse_monto_argentino(monto_str: str | None) -> float | None:
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

    # Remove currency indicators (order matters: U$S before $)
    s = s.replace("U$S", "").replace("usd", "").replace("USD", "")
    s = s.replace("$", "").strip()

    if not s:
        return None

    # ── Space-as-decimal heuristic ──
    # In some PDF extractions, the comma is replaced by a space.
    # "59 64" → 59.64, "0 00" → 0.00
    # Only apply when there are NO dots or commas at all.
    if "." not in s and "," not in s and " " in s:
        # Replace the LAST space with a dot (decimal), keep rest as separator-less
        parts = s.rsplit(" ", 1)
        if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
            s = parts[0] + "." + parts[1]
        else:
            s = s.replace(" ", "")
    else:
        s = s.replace(" ", "")

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
        # Has dots, no commas. Need to determine if dots are thousand
        # separators or decimal separators (or a mix of both).
        parts = s.split(".")
        if len(parts) > 1:
            last = parts[-1]
            if len(last) > 2:
                # >2 chars after last dot → comma was lost in extraction,
                # dots are thousand separators, last 2 chars are cents.
                # "461.04837" → 461048.37
                # "1.510.28757" → 1510287.57
                s = "".join(parts[:-1]) + last[:-2] + "." + last[-2:]
            elif len(parts) > 2:
                # Multiple dots, last part ≤2 chars → last dot is decimal,
                # previous dots are thousand separators.
                # "100.000.00" → 100000.00
                s = "".join(parts[:-1]) + "." + last
            # else: single dot, 1-2 chars after → dot IS decimal, already valid
            # "1510287.57" → 1510287.57, "363.28" → 363.28

    try:
        return sign * float(s)
    except (ValueError, TypeError):
        return None
