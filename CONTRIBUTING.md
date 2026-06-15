# Contributing to santander2md

Thanks for your interest! Here's how to set up your dev environment and contribute.

## Development Setup

```bash
# Clone the repo
git clone https://github.com/juanmanueldaza/santander2md.git
cd santander2md

# Install system dependency (pdftotext)
# Ubuntu/Debian:
sudo apt-get install -y poppler-utils
# macOS:
brew install poppler

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# or: .venv\Scripts\activate  # Windows

# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest -v

# Lint and type check
ruff check .
ruff format --check .
pyright
```

## Pre-commit Hooks

This project uses pre-commit hooks to automatically lint, format, and type-check your code before each commit.

```bash
# Install pre-commit
pip install pre-commit

# Install the hooks
pre-commit install

# (Optional) Run all hooks on the entire codebase once
pre-commit run --all-files
```

## Making Changes

1. Create a branch: `git checkout -b my-feature`
2. Make your changes
3. Ensure all tests pass: `pytest -v`
4. Ensure linting passes: `ruff check . && ruff format --check .`
5. Ensure type checking passes: `pyright`
6. Commit with a descriptive message (see commit conventions below)
7. Push and open a Pull Request

## Commit Conventions

- Use conventional commit format: `type(scope): description`
- Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `ci`
- Reference issue numbers: `fix #2`, `closes #5`
- Keep commits focused — one logical change per commit

## Code Style

- **Formatter**: ruff (line length 88, target Python 3.10+)
- **Type checker**: pyright (strict mode)
- **Linting**: ruff check with rules E, W, F, I, B, UP
- **Type annotations**: required on all public function signatures
- **Zero-dependency core**: only Python stdlib in the main package

## Testing

- **Framework**: pytest
- **Test location**: `tests/` directory, files named `test_*.py`
- **All tests must pass** before merging

## Questions?

Open an issue at [github.com/juanmanueldaza/santander2md/issues](https://github.com/juanmanueldaza/santander2md/issues).
