"""
I/O helpers for santander2md.
Single-source implementations for common filesystem patterns.
"""

from __future__ import annotations

from pathlib import Path


def _ensure_dir(path: Path) -> None:
    """Create parent directories for a file path. Idempotent."""
    path.parent.mkdir(parents=True, exist_ok=True)


def _write_file(path: Path, content: str) -> None:
    """Write content to a file, creating parent directories as needed."""
    _ensure_dir(path)
    path.write_text(content, encoding="utf-8")
