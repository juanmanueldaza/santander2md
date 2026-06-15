# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

- Migrated package layout to `src/santander2md/` and build backend to Hatchling.
- Relicensed under GPL-2.0.
- Added ruff, pyright, pre-commit, and GitHub Actions CI.
- Decomposed monolithic parser into a `parsers/` sub-package with per-section modules.

## [0.1.0] - 2026-06-15

### Added

- Initial release: parse Santander Argentina account and credit-card PDF statements to Markdown, CSV, and JSON.
- CLI entry point `santander2md`.
- Support for extracting movements, credit-card summaries, loans, taxes, and installments.
