"""
CLI para santander2md. Zero external dependencies — uses argparse (stdlib).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from santander2md import __version__
from santander2md._io import _ensure_dir
from santander2md.exporter import to_csv, to_json, to_markdown
from santander2md.parser import ParseError, SantanderParser

_FORMAT_HANDLERS = {
    ".md": to_markdown,
    ".csv": to_csv,
    ".json": to_json,
    "md": to_markdown,
    "csv": to_csv,
    "json": to_json,
}


def cmd_parse(args: argparse.Namespace) -> None:
    """Parse a single extracto."""
    ext = Path(args.output).suffix.lower()
    handler = _FORMAT_HANDLERS.get(ext)
    if not handler:
        sys.exit(f"Formato no soportado: {ext}")

    print(f"Parseando {args.input}...")
    parser = SantanderParser(args.input)
    extracto = parser.parse()
    if ext == ".md":
        md = handler(extracto)
        output_path = Path(args.output)
        _ensure_dir(output_path)
        output_path.write_text(md, encoding="utf-8")
    else:
        handler(extracto, args.output)
    print(f"✓ Guardado en {args.output}")


def cmd_batch(args: argparse.Namespace) -> None:
    """Parse multiple extractos from a directory."""
    output_dir = Path(args.output_dir)
    _ensure_dir(output_dir / ".keep")
    pdf_files = sorted(Path(args.input_dir).glob("*.pdf"))
    handler = _FORMAT_HANDLERS.get(args.format)
    if not handler:
        sys.exit(f"Formato no soportado: {args.format}")

    print(f"Encontrados {len(pdf_files)} PDFs")
    for pdf_path in pdf_files:
        try:
            print(f"Procesando {pdf_path.name}...")
            parser = SantanderParser(str(pdf_path))
            extracto = parser.parse()
            output_path = output_dir / f"{pdf_path.stem}.{args.format}"
            if args.format == "md":
                md = handler(extracto)
                _ensure_dir(output_path)
                output_path.write_text(md, encoding="utf-8")
            else:
                handler(extracto, str(output_path))
            print(f"  ✓ {output_path.name}")
        except (ParseError, FileNotFoundError, OSError) as e:
            print(f"  ✗ Error: {e}", file=sys.stderr)

    print(f"\n✓ Proceso completado. Resultados en {args.output_dir}")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="santander2md",
        description="Parser para extractos de Santander Argentina a Markdown/CSV/JSON",
    )
    parser.add_argument(
        "--version", action="version", version=f"santander2md {__version__}"
    )
    sub = parser.add_subparsers(dest="command")

    # parse
    p = sub.add_parser("parse", help="Parsea un extracto individual")
    p.add_argument("-i", "--input", required=True, help="PDF de entrada")
    p.add_argument(
        "-o", "--output", required=True, help="Archivo de salida (.md, .csv, .json)"
    )
    p.set_defaults(func=cmd_parse)

    # batch
    b = sub.add_parser("batch", help="Parsea múltiples extractos en lote")
    b.add_argument("-i", "--input-dir", required=True, help="Directorio con PDFs")
    b.add_argument("-o", "--output-dir", required=True, help="Directorio de salida")
    b.add_argument(
        "-f",
        "--format",
        choices=["md", "csv", "json"],
        default="md",
        help="Formato de salida (default: md)",
    )
    b.set_defaults(func=cmd_batch)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)
    args.func(args)


if __name__ == "__main__":
    main()
