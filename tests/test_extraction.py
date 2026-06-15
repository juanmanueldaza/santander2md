"""Tests for parsers.extraction."""

from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

from santander2md.parsers.errors import ParseError
from santander2md.parsers.extraction import PopplerPDFExtractor


class TestPopplerPDFExtractor:
    def test_extract_success(self, tmp_path: Path) -> None:
        extractor = PopplerPDFExtractor()
        pdf_path = tmp_path / "sample.pdf"
        pdf_path.write_text("pdf bytes", encoding="utf-8")

        with patch("santander2md.parsers.extraction.subprocess.run") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=["pdftotext", "-layout", str(pdf_path), "-"],
                returncode=0,
                stdout="extracted text",
                stderr="",
            )
            text = extractor.extract(pdf_path)

        assert text == "extracted text"
        mock_run.assert_called_once_with(
            ["pdftotext", "-layout", str(pdf_path), "-"],
            capture_output=True,
            text=True,
            timeout=30,
        )

    def test_extract_not_found(self, tmp_path: Path) -> None:
        extractor = PopplerPDFExtractor()
        pdf_path = tmp_path / "sample.pdf"
        pdf_path.write_text("pdf bytes", encoding="utf-8")

        with patch(
            "santander2md.parsers.extraction.subprocess.run",
            side_effect=FileNotFoundError,
        ):
            with pytest.raises(ParseError):
                extractor.extract(pdf_path)

    def test_extract_non_zero_exit(self, tmp_path: Path) -> None:
        extractor = PopplerPDFExtractor()
        pdf_path = tmp_path / "sample.pdf"
        pdf_path.write_text("pdf bytes", encoding="utf-8")

        with patch("santander2md.parsers.extraction.subprocess.run") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=["pdftotext", "-layout", str(pdf_path), "-"],
                returncode=1,
                stdout="",
                stderr="pdftotext exploded",
            )
            with pytest.raises(ParseError, match="pdftotext exploded"):
                extractor.extract(pdf_path)
