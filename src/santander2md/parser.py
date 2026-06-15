"""Backward-compatible shim for the refactored parsers package."""

from __future__ import annotations

from santander2md.parsers.errors import ParseError
from santander2md.parsers.orchestrator import SantanderParser

__all__ = ["ParseError", "SantanderParser"]
