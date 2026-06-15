"""Noise detection and filtering for extracted PDF lines."""

from __future__ import annotations

import re

_SKIP_PATTERNS = [
    re.compile(r"Banco Santander.*sociedad anónima", re.I),
    re.compile(r"accionista mayoritario", re.I),
    re.compile(r"Salvo error u omisión", re.I),
    re.compile(r"^\s*\d+\s*-\s*\d+\s*$"),
    re.compile(r"^\s*correlativo \d+", re.I),
    re.compile(r"tampoco lo hacen otras", re.I),
]


def _is_noise(line: str) -> bool:
    """Return True if *line* is a boilerplate PDF footer/header."""
    return any(pat.search(line) for pat in _SKIP_PATTERNS)
