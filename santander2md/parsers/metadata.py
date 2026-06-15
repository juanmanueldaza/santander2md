"""Metadata extractors that operate on the full extracted text."""

from __future__ import annotations

import re

from santander2md.parsers.line_parser import _re_first
from santander2md.utils import parse_monto_argentino


def _extract_nombre(text: str) -> str:
    """Extract client name. Looks for uppercase name after CUIT context."""
    m = re.search(r"([A-ZÁÉÍÓÚÑ]{3,}(?:\s+[A-ZÁÉÍÓÚÑ]{3,})+)", text)
    if m:
        name = m.group(1).strip()
        skip = {
            "CONSUMIDOR FINAL", "AV HIPOLITO", "B1878FNP", "INFINITY GOLD",
            "BUENOS AIRES", "MOVIMIENTOS", "SANTANDER", "CUENTA", "FECHA",
        }
        parts = name.split()
        filtered = [
            p for p in parts
            if p not in skip
            and not re.match(r"^(?:AV|CBU|CUIT|DESDE|HASTA)\b", p)
        ]
        if filtered:
            return " ".join(filtered[:3])
    return "N/A"


def _parse_saldo_inicial(text: str) -> float | None:
    m = re.search(r"(?i)saldo\s+inicial\s+\$?\s*([\d\.,]+)", text)
    return parse_monto_argentino(m.group(1)) if m else None


def _parse_saldo_final(text: str) -> float | None:
    m = re.search(r"Total en pesos\s+\$?\s*([\d\.,]+)", text)
    if m:
        return parse_monto_argentino(m.group(1))
    # Legacy format: "SALDO FINAL   2881,63   2881,63   0,41"
    m = re.search(r"SALDO FINAL\s+([\d\.,]+)", text)
    return parse_monto_argentino(m.group(1)) if m else None


def _parse_sueldo(text: str) -> float | None:
    m = re.search(
        r"Pago de haberes.*?Transferencia s\.n\.p\..*?\$\s*([\d\.,]+)",
        text,
        re.DOTALL,
    )
    return parse_monto_argentino(m.group(1)) if m else None
