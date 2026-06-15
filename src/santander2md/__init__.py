"""santander2md - Convert Santander Argentina statements to Markdown.

SOLID-compliant architecture:
- S: Each parser handles one statement section
- O: New formats added via parser registry or extractor injection
- L: Extractors are substitutable via the PDFExtractor protocol
- I: Focused protocols for extraction, parsing, and export
- D: Orchestrator depends on abstractions, not concrete extractors
"""

from __future__ import annotations

import logging
from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("santander2md")
except PackageNotFoundError:
    __version__ = "0.0.0"  # Development fallback

# Configure package logger (NullHandler = library best practice)
logging.getLogger(__name__).addHandler(logging.NullHandler())

# Main public API
from santander2md.exporter import to_csv, to_json, to_markdown  # noqa: E402
from santander2md.models import Extracto, Movimiento  # noqa: E402
from santander2md.parser import SantanderParser  # noqa: E402

__all__ = [
    "__version__",
    "SantanderParser",
    "Extracto",
    "Movimiento",
    "to_markdown",
    "to_csv",
    "to_json",
]
