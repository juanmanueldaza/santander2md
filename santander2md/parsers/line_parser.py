"""Low-level per-line parsing helpers shared across section parsers."""

from __future__ import annotations

import re

from santander2md.utils import parse_monto_argentino


_DATE_CLEANUP = re.compile(r"^\s*\d{2}/\d{2}/\d{2}\s*")
_COMP_CLEANUP = re.compile(r"^\s*\d{5,15}\s+")


def _re_first(text: str, pattern: str) -> str:
    """Return first capture group, or 'N/A' if no match."""
    m = re.search(pattern, text)
    return m.group(1) if m else "N/A"


def _accumulate_continuations(
    lines: list[str],
    *,
    stop_pred: "callable[[str], bool] | None" = None,
) -> list[str]:
    """Join continuation fragments (lines without a dd/mm/yy date) to the preceding line.

    Lines matching *stop_pred* are emitted as separate entries so that end
    markers are not merged into the previous transaction row. Orphan
    continuations (no preceding date-bearing line) are emitted as-is.
    """
    merged: list[str] = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if stop_pred is not None and stop_pred(stripped):
            merged.append(stripped)
            continue
        if re.search(r"\d{2}/\d{2}/\d{2}", stripped):
            merged.append(stripped)
        elif merged:
            merged[-1] = merged[-1] + " " + stripped
        else:
            merged.append(stripped)
    return merged


class _LineParser:
    """Static helpers for parsing individual table lines."""

    @staticmethod
    def extract_date(line: str) -> str | None:
        m = re.search(r"^\s{2,4}(\d{2}/\d{2}/\d{2})", line)
        if m:
            return m.group(1)
        m = re.match(r"\s*(\d{2}/\d{2}/\d{2})", line[:12])
        return m.group(1) if m else None

    @staticmethod
    def extract_comprobante(line: str) -> str | None:
        m = re.search(r"\b(\d{5,15})\s+[A-Za-z]", line[:60])
        return m.group(1) if m else None

    @staticmethod
    def clean_desc(text: str) -> str:
        """Strip date and comprobante prefixes from description text."""
        text = _DATE_CLEANUP.sub("", text)
        text = _COMP_CLEANUP.sub("", text)
        return text.strip()

    @staticmethod
    def split_line(line: str) -> tuple[str, list[tuple[str, float]]]:
        """Split a table line into (description, transaction_amounts).

        The LAST $-amount on the line is treated as the running balance
        (saldo column) and excluded from transaction amounts.
        """
        amounts = list(re.finditer(r"(-?)\$\s*([\d\.,]+)", line))
        if not amounts:
            desc = _LineParser.clean_desc(line.strip())
            return desc, []

        tx_amounts = amounts[:-1] if len(amounts) > 1 else []
        desc = _LineParser.clean_desc(line[:amounts[0].start()])

        parsed: list[tuple[str, float]] = []
        for m in tx_amounts:
            sign = m.group(1)
            val = parse_monto_argentino(m.group(2))
            if val is not None and val != 0:
                parsed.append((sign, val))

        return desc, parsed
