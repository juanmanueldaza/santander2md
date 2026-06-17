"""PDF section splitting by known headers."""

from __future__ import annotations

import re

# Ordered by typical position in the PDF, longest patterns first to avoid
# partial matches (e.g. "Tarjeta de débito" before "Tarjeta Santander").
_SECTION_HEADER_PATTERNS: list[tuple[str, str]] = [
    ("movimientos_pesos", r"Movimientos\s+en\s+pesos|DETALLE DE MOVIMIENTOS"),
    ("movimientos_dolares", r"Movimientos\s+en\s+dólares"),
    ("detalle_impositivo", r"Detalle impositivo"),
    ("categorias_gasto", r"Así\s+usaste\s+tu\s+dinero"),
    ("resumen_productos", r"Resumen\s+de\s+tus\s+productos"),
    ("tarjeta_debito", r"Tarjeta\s+de\s+débito"),
    ("tarjeta_credito", r"Tarjeta\s+Santander"),
    ("pagos", r"^\s*Pagos\s+(?:Período|en el período|totales)"),
    ("prestamos", r"^\s*Préstamos\b"),
    ("plan_v", r"Plan\s+V"),
    ("cuotas_vencer", r"Cuotas a vencer"),
]

# Patterns that appear WITHIN sections and should NOT trigger a new section.
_SUB_HEADER_BLACKLIST = [
    r"Caja de Ahorro en dólares",
    r"Caja de Ahorro en pesos",
]


def _split_sections(full_text: str) -> dict[str, str]:
    """Split full PDF text into independent section blobs.

    Returns a dict mapping section names (e.g. "movimientos_dolares")
    to their raw text, stripped of leading/trailing whitespace.
    Sections not found are absent from the dict.
    """
    lines = full_text.split("\n")
    hits: list[tuple[int, str]] = []  # (line_index, section_name)

    for i, line in enumerate(lines):
        # Skip sub-headers that look like section boundaries but aren't
        if any(re.search(p, line) for p in _SUB_HEADER_BLACKLIST):
            continue
        for sec_name, pattern in _SECTION_HEADER_PATTERNS:
            if re.search(pattern, line):
                hits.append((i, sec_name))
                break  # first match wins per line

    hits.sort(key=lambda x: x[0])

    # Merge duplicate sections (some headers repeat with different data,
    # e.g. "Préstamos" appears as summary then as detailed breakdown).
    sections: dict[str, str] = {}
    for idx, (line_no, sec_name) in enumerate(hits):
        start = line_no
        end = hits[idx + 1][0] if idx + 1 < len(hits) else len(lines)
        blob = "\n".join(lines[start:end]).strip()
        if blob:
            if sec_name in sections:
                sections[sec_name] += "\n" + blob
            else:
                sections[sec_name] = blob

    return sections
