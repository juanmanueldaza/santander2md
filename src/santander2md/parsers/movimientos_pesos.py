"""Peso checking-account movement parser."""

from __future__ import annotations

import logging
import re
from typing import Any

from santander2md.models import Movimiento
from santander2md.parsers.line_parser import _LineParser
from santander2md.parsers.noise import _is_noise
from santander2md.utils import parse_monto_argentino

logger = logging.getLogger(__name__)


# ── Section end markers (legacy) ───────────────────────────────────────

_SECTION_END = [
    "Movimientos en dólares",
    "Movimientos  en dólares",
    "Caja de Ahorro en dólares",
    "Resumen de tus productos",
    "Resumen  de  tus productos",
    "Tarjeta  Santander",
    "Tarjeta Santander",
    "Resumen    de  tus productos",
]


class _SectionExtractor:
    """Static helpers for finding the transaction table section in PDF text."""

    @staticmethod
    def _find_line(lines: list[str], pattern: str, start: int = 0) -> int:
        rx = re.compile(pattern)
        for i in range(start, len(lines)):
            if rx.search(lines[i]):
                return i
        return -1

    @staticmethod
    def _is_table_header(line: str) -> bool:
        return bool(
            re.search(
                r"Fecha.*Comprobante.*(?:Movimiento|Descripción)|"
                r"FECHA\s+COMPROB\.\s+SUS MOVIMIENTOS",
                line,
            )
        )

    @staticmethod
    def extract(lines: list[str]) -> list[str]:
        """Extract the main transaction section from all lines.

        Handles both modern ('Movimientos en pesos') and legacy
        ('DETALLE DE MOVIMIENTOS') formats.
        """
        start = _SectionExtractor._find_line(lines, r"Movimientos\s+en\s+pesos")
        if start < 0:
            start = _SectionExtractor._find_line(lines, r"DETALLE DE MOVIMIENTOS")
        if start < 0:
            from santander2md.parsers.errors import ParseError

            raise ParseError("No se encontró 'Movimientos en pesos'")
        end = len(lines)
        for i in range(start + 1, len(lines)):
            for m in _SECTION_END:
                if m in lines[i]:
                    end = i
                    break
            if end < len(lines):
                break
        return lines[start:end]

    @staticmethod
    def skip_to_table(section_lines: list[str]) -> list[str]:
        """Skip everything before the table header, return table body."""
        header = -1
        for i, line in enumerate(section_lines):
            if _SectionExtractor._is_table_header(line):
                header = i
                break
        if header < 0:
            from santander2md.parsers.errors import ParseError

            raise ParseError("No se encontró la cabecera de la tabla")
        return section_lines[header + 1 :]


def _parse_movimientos(full_text: str) -> list[Movimiento]:
    all_lines = full_text.split("\n")
    section_lines = _SectionExtractor.extract(all_lines)
    table_lines = _SectionExtractor.skip_to_table(section_lines)

    # Detect legacy format (no $ signs in the transaction area)
    table_text = "\n".join(table_lines[:3])
    if "$" not in table_text:
        return _parse_legacy_movimientos(table_lines)

    blocks = _group_into_blocks(table_lines)
    return _build_movements(blocks)


def _parse_legacy_movimientos(lines: list[str]) -> list[Movimiento]:
    """Parse pre-2022 legacy format: no $ signs, trailing '-' for debits."""
    result: list[Movimiento] = []
    current_date = ""
    pending: list[str] = []

    def _flush(block_lines: list[str]) -> Movimiento | None:
        if not block_lines:
            return None
        desc_parts: list[str] = []
        debito: float | None = None
        credito: float = 0.0

        for bline in block_lines:
            s = bline.strip()
            debit_matches = list(re.finditer(r"([\d\.,]+)\s*-\s*$", s))
            credit_matches = list(
                re.finditer(
                    r"(?<!\d)(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)(?![\d\-])",
                    s,
                )
            )

            desc_start = 0
            if re.match(r"\d{2}/\d{2}/\d{2}", s):
                desc_start = 10

            desc_raw = s[desc_start:].strip()
            for dm in debit_matches:
                desc_raw = desc_raw.replace(dm.group(0), "").strip()
            for cm in credit_matches:
                if cm.start() >= desc_start:
                    desc_raw = desc_raw.replace(cm.group(0), "").strip()
            if desc_raw:
                desc_parts.append(desc_raw)

            for dm in debit_matches:
                val = parse_monto_argentino(dm.group(1))
                if val is not None:
                    debito = (debito or 0) + val
            for cm in credit_matches:
                if cm.start() >= desc_start:
                    val = parse_monto_argentino(cm.group(1))
                    if val is not None and val > 0:
                        credito += val

        descripcion = " ".join(desc_parts).strip()
        if not descripcion:
            return None
        if credito == 0 and debito is None:
            return None
        try:
            return Movimiento(
                fecha=current_date,
                descripcion=descripcion,
                debito=debito,
                credito=credito if credito > 0 else None,
            )
        except ValueError:
            return None

    for line in lines:
        s = line.strip()
        if not s:
            continue
        if _is_noise(s):
            continue
        if _SectionExtractor._is_table_header(s):
            continue
        if "SALDO INICIAL" in s:
            continue
        if "SALDO FINAL" in s or "TOTAL RETENCION" in s:
            break

        date_str = _LineParser.extract_date(s) or re.match(r"(\d{2}/\d{2}/\d{2})", s)
        date_val = (
            date_str
            if isinstance(date_str, str)
            else (date_str.group(1) if date_str else None)
        )

        if date_val:
            if pending:
                mov = _flush(pending)
                if mov:
                    result.append(mov)
            current_date = date_val
            pending = [s]
        elif pending:
            pending.append(s)

    if pending:
        mov = _flush(pending)
        if mov:
            result.append(mov)

    return result


def _group_into_blocks(lines: list[str]) -> list[dict[str, Any]]:
    blocks: list[dict[str, Any]] = []
    current_date = ""
    current_block: dict[str, Any] | None = None

    for line in lines:
        if not line.strip():
            continue
        if _is_noise(line):
            continue
        if _SectionExtractor._is_table_header(line):
            continue

        date_str = _LineParser.extract_date(line)
        comp_str = _LineParser.extract_comprobante(line)

        if "Saldo Inicial" in line:
            continue
        if date_str:
            current_date = date_str

        if comp_str:
            if current_block is not None:
                blocks.append(current_block)
            current_block = {"fecha": current_date, "lines": [line]}
        elif current_block is not None:
            current_block["lines"].append(line)
        else:
            desc, amts = _LineParser.split_line(line)
            if amts:
                current_block = {"fecha": current_date, "lines": [line]}

    if current_block is not None:
        blocks.append(current_block)
    return blocks


def _build_movements(blocks: list[dict[str, Any]]) -> list[Movimiento]:
    movimientos: list[Movimiento] = []
    for block in blocks:
        m = _build_block(block["fecha"], block["lines"])
        if m:
            movimientos.append(m)
    return movimientos


def _build_block(fecha: str, block_lines: list[str]) -> Movimiento | None:
    desc_parts: list[str] = []
    debito: float | None = None
    credito: float = 0.0

    for line in block_lines:
        desc, amounts = _LineParser.split_line(line)
        if desc:
            desc_parts.append(desc)
        for sign, val in amounts:
            if sign == "-":
                debito = (debito or 0) + val
            else:
                credito += val

    descripcion = " ".join(desc_parts).strip()
    if not descripcion:
        return None
    if credito == 0 and debito is None:
        return None

    try:
        return Movimiento(
            fecha=fecha,
            descripcion=descripcion,
            debito=debito,
            credito=credito if credito > 0 else None,
        )
    except ValueError as exc:
        logger.warning("Skipping movement block fecha=%s: %s", fecha, exc)
        return None
