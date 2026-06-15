"""Shared parser exceptions."""

from __future__ import annotations


class ParseError(Exception):
    """Raised when PDF text cannot be extracted or parsed."""
    pass
