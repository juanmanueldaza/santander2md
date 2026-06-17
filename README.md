# santander2md
![PyPI version](https://img.shields.io/pypi/v/santander2md.svg)


Convert Santander Argentina account and credit-card PDF statements to clean Markdown.

## Installation

**Recommended** (using pipx - installs in isolated environment):

```bash
pipx install santander2md
```

Or with pip (in a virtual environment):

```bash
pip install santander2md
```

> **Note**: On modern Linux systems (Debian, Ubuntu 23.04+, Fedora), use `pipx` to avoid the "externally-managed-environment" error.

You also need the `pdftotext` binary from Poppler:

```bash
# Ubuntu/Debian
sudo apt-get install -y poppler-utils

# macOS
brew install poppler
```

## Usage

### Command line

```bash
# Convert a single PDF to Markdown
santander2md parse -i extracto.pdf -o reporte.md

# Process multiple statements
santander2md batch -i ./data -o ./output -f md
```

### As a library

```python
from santander2md import SantanderParser, to_markdown

parser = SantanderParser("extracto.pdf")
extracto = parser.parse()
md = to_markdown(extracto)
print(md)
```

## Output

The tool produces Markdown summaries of:

- Account movements (pesos and dollars)
- Credit-card summaries and purchases
- Taxes and withholding details
- Loans and installment plans
- Pending installments (`cuotas a vencer`)

## Development

```bash
# Install system dependency
sudo apt-get install -y poppler-utils

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest -v

# Lint and type check
ruff check .
ruff format --check .
pyright
```

## Project Structure

```
santander2md/
├── src/santander2md/   # Source package
│   ├── parsers/        # PDF extraction and section parsers
│   ├── models.py       # Data models
│   ├── exporter.py     # Markdown exporter
│   ├── utils.py        # Shared utilities
│   └── cli.py          # CLI entry point
├── tests/              # Test suite
├── examples/           # Usage examples
├── pyproject.toml      # Project metadata and tool config
└── README.md           # This file
```

## License

Apache-2.0
