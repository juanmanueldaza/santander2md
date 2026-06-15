"""PDF text extraction with protocol-based abstraction."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Protocol, runtime_checkable

from santander2md.parsers.errors import ParseError


@runtime_checkable
class PDFExtractor(Protocol):
    """Protocol for PDF text extractors."""

    def extract(self, path: Path) -> str:
        """Return plain text extracted from *path*."""
        ...


class PopplerPDFExtractor:
    """Extract text from PDF using the system pdftotext binary."""

    def extract(self, path: Path) -> str:
        """Run pdftotext -layout and return stdout."""
        try:
            result = subprocess.run(
                ["pdftotext", "-layout", str(path), "-"],
                capture_output=True,
                text=True,
                timeout=30,
            )
        except FileNotFoundError as exc:
            raise ParseError(
                "pdftotext no encontrado. Instale poppler-utils:\n"
                "  sudo apt install poppler-utils"
            ) from exc
        except subprocess.TimeoutExpired as exc:
            raise ParseError("pdftotext timed out") from exc

        if result.returncode != 0:
            raise ParseError(f"pdftotext failed: {result.stderr.strip()}")
        return result.stdout
