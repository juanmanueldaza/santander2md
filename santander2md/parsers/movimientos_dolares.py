"""Dollar movement parser."""

from __future__ import annotations

import re

from santander2md.models import MovimientoDolar
from santander2md.parsers.line_parser import _LineParser, _accumulate_continuations
from santander2md.parsers.noise import _is_noise
from santander2md.utils import parse_monto_argentino


def _parse_movimientos_dolares(section_text: str) -> list[MovimientoDolar]:
    """Parse the 'Movimientos en dólares' table."""

    def _is_end(line: str) -> bool:
        return any(marker in line for marker in [
            "Movimientos en pesos",
            "Caja de Ahorro en dólares",
            "Resumen de tus productos",
            "Tarjeta Santander",
        ])

    lines = _accumulate_continuations(section_text.split("\n"), stop_pred=_is_end)
    result: list[MovimientoDolar] = []
    in_table = False

    for line in lines:
        line_s = line.strip()
        if not line_s:
            continue
        if _is_noise(line_s):
            continue

        # Skip until table header
        if not in_table:
            if re.search(r"Fecha.*(?:Movimiento|Descripción)", line_s):
                in_table = True
            continue

        # Find USD amounts: sign can be before U$S (e.g. -U$S) or not
        amounts = list(re.finditer(r"(-?)\s*U\$S\s*([\d\.,]+)", line_s))
        if not amounts:
            # Also try plain $ amounts (some statements use $ for USD too)
            amounts = list(re.finditer(r"(-?)\$\s*([\d\.,]+)", line_s))
        if not amounts:
            continue

        # Last amount is saldo (running balance)
        last_sign = amounts[-1].group(1)
        saldo_val = parse_monto_argentino(amounts[-1].group(2))
        saldo = -(saldo_val) if last_sign and last_sign.strip() == "-" else saldo_val

        # Previous amounts are the transaction
        monto: float = 0.0
        for m in amounts[:-1]:
            val = parse_monto_argentino(m.group(2))
            if val is not None:
                sign = m.group(1)
                monto += -val if sign and sign.strip() == "-" else val

        # If no previous amounts (Saldo Inicial line), use the single amount
        if len(amounts) <= 1 and "Saldo Inicial" in line_s:
            continue

        # Description
        date_str = _LineParser.extract_date(line_s)
        desc_raw = _LineParser.clean_desc(line_s[:amounts[0].start()])

        if not desc_raw or monto == 0.0:
            continue

        result.append(MovimientoDolar(
            fecha=date_str or "",
            descripcion=desc_raw,
            monto=monto,
            saldo=saldo,
        ))

    return result
