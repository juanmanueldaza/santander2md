"""Debit card section parser."""

from __future__ import annotations

import re

from santander2md.models import TarjetaDebitoMovimiento
from santander2md.parsers.line_parser import _LineParser, _accumulate_continuations
from santander2md.parsers.noise import _is_noise
from santander2md.utils import parse_monto_argentino


def _parse_debito(section_text: str) -> list[TarjetaDebitoMovimiento]:
    """Parse the 'Tarjeta de débito' section."""
    result: list[TarjetaDebitoMovimiento] = []

    def _is_end(line: str) -> bool:
        return (
            "Monto total" in line
            or re.match(r"^\s*Pagos\b", line) is not None
            or "Legales" in line
        )

    lines = _accumulate_continuations(section_text.split("\n"), stop_pred=_is_end)
    in_table = False

    for line in lines:
        line_s = line.strip()
        if not line_s:
            continue
        if _is_noise(line_s):
            continue

        # Detect table header (may appear on each page)
        if re.search(r"Fecha.*Comprobante.*Establecimiento", line_s):
            in_table = True
            continue

        if not in_table:
            continue

        # Stop at totals or end of section
        if "Monto total" in line_s:
            break
        if re.match(r"^\s*Pagos\b", line_s) or "Legales" in line_s:
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

        # Extract establecimiento: everything between date/comprobante and amount
        rest = line_s[:m.start()].strip()
        if comp and comp in rest:
            rest = rest.replace(comp, "", 1).strip()
        if date_str and date_str in rest:
            rest = rest.replace(date_str, "", 1).strip()
        establecimiento = rest

        result.append(TarjetaDebitoMovimiento(
            fecha=date_str,
            comprobante=comp,
            establecimiento=establecimiento,
            importe=importe,
        ))

    return result
