"""Tests for santander2md.cli."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from santander2md import __version__

# Parent of the project root — where data/ lives
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"


def _first_pdf() -> str | None:
    """Return path to the first available PDF for testing, or None."""
    pdfs = sorted(DATA_DIR.glob("*.pdf"))
    return str(pdfs[0]) if pdfs else None


def _run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    """Run the CLI module and return the CompletedProcess."""
    return subprocess.run(
        [sys.executable, "-m", "santander2md.cli", *args],
        capture_output=True,
        text=True,
        cwd=str(PROJECT_ROOT),
        timeout=60,
    )


class TestCLIVersion:
    def test_version_flag(self) -> None:
        result = _run_cli("--version")
        assert result.returncode == 0
        assert __version__ in result.stdout


class TestCLINoCommand:
    def test_no_args_shows_help(self) -> None:
        result = _run_cli()
        assert result.returncode == 1
        assert "usage:" in result.stdout.lower() or "usage:" in result.stderr.lower()


class TestCLIParse:
    @pytest.mark.skipif(_first_pdf() is None, reason="No PDF files in data/")
    def test_parse_to_md(self, tmp_path: Path) -> None:
        pdf = _first_pdf()
        assert pdf is not None
        output = tmp_path / "out.md"
        result = _run_cli("parse", "-i", pdf, "-o", str(output))
        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert output.exists()
        content = output.read_text(encoding="utf-8")
        assert "# Extracto Bancario" in content

    def test_parse_file_not_found(self, tmp_path: Path) -> None:
        output = tmp_path / "out.md"
        result = _run_cli("parse", "-i", "/nonexistent/file.pdf", "-o", str(output))
        assert result.returncode != 0

    def test_parse_unsupported_format(self) -> None:
        pdf = _first_pdf()
        if pdf is None:
            pytest.skip("No PDF files in data/")
        result = _run_cli("parse", "-i", pdf, "-o", "/tmp/out.xml")
        assert result.returncode != 0


class TestCLIBatch:
    @pytest.mark.skipif(
        not list(DATA_DIR.glob("*.pdf")), reason="No PDF files in data/"
    )
    def test_batch_directory(self, tmp_path: Path) -> None:
        result = _run_cli(
            "batch",
            "-i",
            str(DATA_DIR),
            "-o",
            str(tmp_path),
            "-f",
            "md",
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"
        # At least one output file should exist
        outputs = list(tmp_path.glob("*.md"))
        assert len(outputs) > 0

    def test_batch_no_pdfs(self, tmp_path: Path) -> None:
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()
        result = _run_cli("batch", "-i", str(empty_dir), "-o", str(tmp_path / "out"))
        # Should not crash — may exit 0 or non-zero depending on len==0 handling
        assert "Encontrados 0 PDFs" in result.stdout
