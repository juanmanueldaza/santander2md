"""
santander2md - Parser para extractos de Santander Argentina.
"""

from __future__ import annotations

from ._version import __version__  # noqa: F401 — single version source
__author__ = "Juan Manuel Daza"

from .parser import SantanderParser
from .models import Extracto, Movimiento
from .exporter import to_markdown, to_csv, to_json

__all__ = [
    "SantanderParser",
    "Extracto",
    "Movimiento",
    "to_markdown",
    "to_csv",
    "to_json",
]
