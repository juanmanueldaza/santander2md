"""
Parser para extractos de Santander Argentina.
Column-agnostic: detects amounts dynamically, last amount = saldo.
Uses pdftotext (poppler-utils) for PDF text extraction — zero Python deps.
"""

from __future__ import annotations

import logging
import re
import subprocess
from pathlib import Path

from santander2md.models import Extracto, Movimiento
from santander2md.utils import parse_monto_argentino

logger = logging.getLogger(__name__)


class ParseError(Exception):
    pass


# ── Noise detection patterns ──────────────────────────────────────────

_SKIP_PATTERNS = [
    re.compile(r"Banco Santander.*sociedad anónima", re.I),
    re.compile(r"accionista mayoritario", re.I),
    re.compile(r"Salvo error u omisión", re.I),
    re.compile(r"^\s*\d+\s*-\s*\d+\s*$"),
    re.compile(r"^\s*correlativo \d+", re.I),
    re.compile(r"tampoco lo hacen otras", re.I),
]

_SECTION_END = [
    "Movimientos en dólares", "Movimientos  en dólares",
    "Caja de Ahorro en dólares", "Resumen de tus productos",
    "Resumen  de  tus productos", "Tarjeta  Santander",
    "Tarjeta Santander", "Resumen    de  tus productos",
]

_DATE_CLEANUP = re.compile(r"^\s*\d{2}/\d{2}/\d{2}\s*")
_COMP_CLEANUP = re.compile(r"^\s*\d{5,15}\s+")


def _is_noise(line):
    return any(pat.search(line) for pat in _SKIP_PATTERNS)


# ── PDF extraction ─────────────────────────────────────────────────────

def _extract_pdf_text(pdf_path: Path) -> str:
    """Extract text from PDF using pdftotext (system tool, zero Python deps)."""
    try:
        result = subprocess.run(
            ["pdftotext", "-layout", str(pdf_path), "-"],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode != 0:
            raise ParseError(f"pdftotext failed: {result.stderr.strip()}")
        return result.stdout
    except FileNotFoundError:
        raise ParseError(
            "pdftotext no encontrado. Instale poppler-utils:\n"
            "  sudo apt install poppler-utils"
        )
    except subprocess.TimeoutExpired:
        raise ParseError("pdftotext timed out")


# ── Section extraction ─────────────────────────────────────────────────

def _find_line(lines, pattern, start=0):
    rx = re.compile(pattern)
    for i in range(start, len(lines)):
        if rx.search(lines[i]):
            return i
    return -1


def _find_section_end(lines, markers, start=0):
    for i in range(start, len(lines)):
        for m in markers:
            if m in lines[i]:
                return i
    return len(lines)


def _is_table_header(line):
    return bool(re.search(r"Fecha.*Comprobante.*(?:Movimiento|Descripción)", line))


def _extract_section(all_lines):
    start = _find_line(all_lines, r"Movimientos\s+en\s+pesos")
    if start < 0:
        raise ParseError("No se encontró 'Movimientos en pesos'")
    end = _find_section_end(all_lines, _SECTION_END, start + 1)
    return all_lines[start:end]


def _skip_to_table(section_lines):
    header = -1
    for i, line in enumerate(section_lines):
        if _is_table_header(line):
            header = i
            break
    if header < 0:
        raise ParseError("No se encontró la cabecera de la tabla")
    return section_lines[header + 1:]


# ── Line-level extraction ──────────────────────────────────────────────

def _extract_date(line):
    m = re.search(r"^\s{2,4}(\d{2}/\d{2}/\d{2})", line)
    if m:
        return m.group(1)
    m = re.match(r"\s*(\d{2}/\d{2}/\d{2})", line[:12])
    return m.group(1) if m else None


def _extract_comprobante(line):
    m = re.search(r"\b(\d{5,15})\s+[A-Za-z]", line[:60])
    return m.group(1) if m else None


def _clean_desc(text: str) -> str:
    """Strip date and comprobante prefixes from description text."""
    text = _DATE_CLEANUP.sub("", text)
    text = _COMP_CLEANUP.sub("", text)
    return text.strip()


def _split_line(line):
    """Split a table line into (description, transaction_amounts).

    The LAST $-amount on the line is treated as the running balance
    (saldo column) and excluded from transaction amounts.
    """
    amounts = list(re.finditer(r"(-?)\$\s*([\d\.,]+)", line))
    if not amounts:
        desc = _clean_desc(line.strip())
        return desc, []

    # Last amount is saldo — exclude it. Previous amounts are the tx.
    tx_amounts = amounts[:-1] if len(amounts) > 1 else []

    # Description = everything before the first amount, cleaned
    desc = _clean_desc(line[:amounts[0].start()])

    parsed = []
    for m in tx_amounts:
        sign = m.group(1)
        val = parse_monto_argentino(m.group(2))
        if val is not None and val != 0:
            parsed.append((sign, val))

    return desc, parsed


# ── Field extractors ───────────────────────────────────────────────────

def _re_first(text, pattern):
    """Return first capture group, or 'N/A' if no match."""
    m = re.search(pattern, text)
    return m.group(1) if m else "N/A"


def _extract_nombre(text: str) -> str:
    """Extract client name. Looks for uppercase name after CUIT context."""
    m = re.search(r"([A-ZÁÉÍÓÚÑ]{3,}(?:\s+[A-ZÁÉÍÓÚÑ]{3,})+)", text)
    if m:
        name = m.group(1).strip()
        # Filter out known non-name uppercase text
        skip = {"CONSUMIDOR FINAL", "AV HIPOLITO", "B1878FNP", "INFINITY GOLD",
                "BUENOS AIRES", "MOVIMIENTOS", "SANTANDER", "CUENTA", "FECHA"}
        parts = name.split()
        filtered = [p for p in parts if p not in skip
                    and not re.match(r"^(?:AV|CBU|CUIT|DESDE|HASTA)\b", p)]
        if filtered:
            return " ".join(filtered[:3])
    return "N/A"


def _parse_saldo_inicial(text):
    m = re.search(r"Saldo Inicial\s+\$?\s*([\d\.,]+)", text)
    return parse_monto_argentino(m.group(1)) if m else None


def _parse_saldo_final(text):
    m = re.search(r"Total en pesos\s+\$?\s*([\d\.,]+)", text)
    return parse_monto_argentino(m.group(1)) if m else None


def _parse_sueldo(text):
    # "s.n.p." = "sin nombre propio" (anonymous transfer)
    # The trailing \. in s\.n\.p\. is the literal period of the abbreviation,
    # followed by .*? (lazy wildcard to reach the $-amount)
    m = re.search(
        r"Pago de haberes.*?Transferencia s\.n\.p\..*?\$\s*([\d\.,]+)",
        text, re.DOTALL,
    )
    return parse_monto_argentino(m.group(1)) if m else None


# ── Movement parsing ───────────────────────────────────────────────────

def _parse_movimientos(full_text):
    all_lines = full_text.split("\n")
    section_lines = _extract_section(all_lines)
    table_lines = _skip_to_table(section_lines)
    blocks = _group_into_blocks(table_lines)
    return _build_movements(blocks)


def _group_into_blocks(lines):
    blocks = []
    current_date = ""
    current_block = None

    for line in lines:
        if not line.strip():
            continue
        if _is_noise(line):
            continue
        if _is_table_header(line):
            continue

        date_str = _extract_date(line)
        comp_str = _extract_comprobante(line)

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
            desc, amts = _split_line(line)
            if amts:
                current_block = {"fecha": current_date, "lines": [line]}

    if current_block is not None:
        blocks.append(current_block)
    return blocks


def _build_movements(blocks):
    movimientos = []
    for block in blocks:
        m = _build_block(block["fecha"], block["lines"])
        if m:
            movimientos.append(m)
    return movimientos


def _build_block(fecha, block_lines):
    desc_parts = []
    debito = None
    credito = 0.0

    for line in block_lines:
        desc, amounts = _split_line(line)
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


# ── SantanderParser ────────────────────────────────────────────────────

class SantanderParser:
    """Parser principal para extractos de Santander Argentina."""

    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path

    def parse(self) -> Extracto:
        path = Path(self.pdf_path)
        if not path.exists():
            raise FileNotFoundError(f"No existe: {self.pdf_path}")

        full_text = _extract_pdf_text(path)

        if not full_text:
            raise ParseError("No se pudo extraer texto del PDF")

        return Extracto(
            periodo_inicio=_re_first(full_text, r"Desde:\s*(\d{2}/\d{2}/\d{2})"),
            periodo_fin=_re_first(full_text, r"Hasta:\s*(\d{2}/\d{2}/\d{2})"),
            cliente_nombre=_extract_nombre(full_text),
            cliente_cuit=_re_first(full_text, r"CUIT:\s*([\d-]+)"),
            saldo_inicial=_parse_saldo_inicial(full_text),
            saldo_final=_parse_saldo_final(full_text),
            sueldo_neto=_parse_sueldo(full_text),
            movimientos=_parse_movimientos(full_text),
        )
