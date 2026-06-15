"""Personal loans section parser."""

from __future__ import annotations

import re

from santander2md.models import PrestamoPersonal
from santander2md.utils import parse_monto_argentino


def _parse_prestamos(section_text: str) -> list[PrestamoPersonal]:
    """Parse the 'Préstamos Personales' section."""
    result: list[PrestamoPersonal] = []
    lines = section_text.split("\n")
    i = 0

    while i < len(lines):
        line_s = lines[i].strip()
        if not line_s:
            i += 1
            continue

        m = re.match(r"Número:\s*(\d+)\s+Saldo:\s+\$?\s*([\d\.,]+)", line_s)
        if m:
            loan = PrestamoPersonal()
            loan.descripcion = f"Préstamo {m.group(1)}"
            loan.saldo_pendiente = parse_monto_argentino(m.group(2))

            for j in range(i + 1, min(i + 5, len(lines))):
                next_s = lines[j].strip()
                if re.match(r"Cuota\s+Capital", next_s):
                    continue
                cuota_m = re.match(
                    r"(\d+)\s+de\s+(\d+)\s+\$?\s*([\d\.,]+)\s+\$?\s*([\d\.,]+)"
                    r"\s+\$?\s*([\d\.,]+)\s+\$?\s*([\d\.,]+)(?:\s+\$?\s*([\d\.,]+))?"
                    r"\s+\$?\s*([\d\.,]+)\s+(\w+)",
                    next_s,
                )
                if cuota_m:
                    loan.cuota_actual = f"{cuota_m.group(1)}/{cuota_m.group(2)}"
                    loan.capital = parse_monto_argentino(cuota_m.group(3))
                    loan.intereses = parse_monto_argentino(cuota_m.group(4))
                    break

            if loan.capital is not None:
                result.append(loan)
            i += 2
        else:
            i += 1

    return result
