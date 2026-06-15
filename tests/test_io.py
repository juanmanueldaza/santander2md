"""Tests for santander2md._io."""

from pathlib import Path

from santander2md._io import _ensure_dir, _write_file


class TestEnsureDir:
    def test_creates_parent_directory(self, tmp_path: Path) -> None:
        file_path = tmp_path / "a" / "b" / "c.txt"
        _ensure_dir(file_path)
        assert file_path.parent.exists()
        assert file_path.parent.is_dir()

    def test_idempotent(self, tmp_path: Path) -> None:
        file_path = tmp_path / "x" / "y" / "z.txt"
        _ensure_dir(file_path)
        _ensure_dir(file_path)  # second call should not raise
        assert file_path.parent.exists()

    def test_already_existing_dir(self, tmp_path: Path) -> None:
        existing = tmp_path / "exists"
        existing.mkdir()
        file_path = existing / "test.txt"
        _ensure_dir(file_path)  # should not fail when parent exists


class TestWriteFile:
    def test_writes_content_and_creates_dirs(self, tmp_path: Path) -> None:
        file_path = tmp_path / "deep" / "nested" / "out.txt"
        _write_file(file_path, "hello world")
        assert file_path.exists()
        assert file_path.read_text(encoding="utf-8") == "hello world"

    def test_overwrites_existing(self, tmp_path: Path) -> None:
        file_path = tmp_path / "out.txt"
        _write_file(file_path, "first")
        _write_file(file_path, "second")
        assert file_path.read_text(encoding="utf-8") == "second"

    def test_unicode_content(self, tmp_path: Path) -> None:
        file_path = tmp_path / "unicode.txt"
        content = "José María — €50,00"
        _write_file(file_path, content)
        assert file_path.read_text(encoding="utf-8") == content
