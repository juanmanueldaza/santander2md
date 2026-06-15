"""Spending category parser."""

from __future__ import annotations

import re

from santander2md.models import CategoriaGasto
from santander2md.parsers.noise import _is_noise
from santander2md.utils import parse_monto_argentino


def _parse_categorias_gasto(section_text: str) -> list[CategoriaGasto]:
    """Parse the 'Así usaste tu dinero' spending categories."""
    all_lines = [
        line for line in section_text.split("\n")
        if line.strip() and not _is_noise(line.strip())
    ]
    result: list[CategoriaGasto] = []
    i = 0

    while i < len(all_lines):
        line = all_lines[i].strip()

        if "Así usaste tu dinero" in line or re.match(r"^\s*\*\s*Salvo error", line):
            i += 1
            continue

        # Category-name line: text with no digits, no $, no %
        if re.search(r"\d", line) or "$" in line or "%" in line:
            i += 1
            continue

        # Find matching percentage line
        pct_line = ""
        pct_line_idx = -1
        for j in range(i + 1, min(i + 4, len(all_lines))):
            if "%" in all_lines[j]:
                pct_line = all_lines[j]
                pct_line_idx = j
                break
        if not pct_line:
            i += 1
            continue

        # Find matching amount line
        amt_line = ""
        for j in range(pct_line_idx + 1, min(pct_line_idx + 3, len(all_lines))):
            if "$" in all_lines[j]:
                amt_line = all_lines[j]
                break
        if not amt_line:
            i += 1
            continue

        # Extract percentages in order
        pcts: list[float] = []
        for m in re.finditer(r"(\d+(?:[.,]\d+)?)\s*%", pct_line):
            try:
                pcts.append(float(m.group(1).replace(",", ".")))
            except ValueError:
                pcts.append(0.0)

        # Extract amounts in order
        amounts: list[float] = []
        for m in re.finditer(r"\$\s*([\d\.,]+)", amt_line):
            val = parse_monto_argentino(m.group(1))
            amounts.append(val or 0.0)

        # Split categories at positions where a capitalized word starts
        # after at least 2 spaces (column gaps in the PDF table)
        cat_boundaries: list[int] = [0]
        for m in re.finditer(r"\s{2,}([A-ZÁÉÍÓÚÑ])", line):
            cat_boundaries.append(m.start(1))

        categories: list[str] = []
        for idx in range(len(cat_boundaries)):
            start = cat_boundaries[idx]
            end = cat_boundaries[idx + 1] if idx + 1 < len(cat_boundaries) else len(line)
            cat_name = line[start:end].strip()
            if cat_name:
                categories.append(cat_name)

        # Match 1:1 by position
        for idx, cat_name in enumerate(categories):
            pct = pcts[idx] if idx < len(pcts) else 0.0
            amt = amounts[idx] if idx < len(amounts) else 0.0
            result.append(CategoriaGasto(nombre=cat_name, porcentaje=pct, total=amt))

        i = pct_line_idx + 2

    return result
