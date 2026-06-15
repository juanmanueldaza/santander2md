"""
CLI para santander2md. Zero external dependencies — uses argparse (stdlib).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from santander2md.parser import SantanderParser
from santander2md.exporter import Exporter

_FORMAT_HANDLERS = {
    ".md":   Exporter.to_markdown,
    ".csv":  Exporter.to_csv,
    ".json": Exporter.to_json,
    "md":    Exporter.to_markdown,
    "csv":   Exporter.to_csv,
    "json":  Exporter.to_json,
}


def cmd_parse(args):
    """Parse a single extracto."""
    ext = Path(args.output).suffix.lower()
    handler = _FORMAT_HANDLERS.get(ext)
    if not handler:
        sys.exit(f"Formato no soportado: {ext}")

    print(f"Parseando {args.input}...")
    parser = SantanderParser(args.input)
    extracto = parser.parse()
    handler(extracto, args.output)
    print(f"✓ Guardado en {args.output}")


def cmd_batch(args):
    """Parse multiple extractos from a directory."""
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
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
            handler(extracto, str(output_path))
            print(f"  ✓ {output_path.name}")
        except Exception as e:
            print(f"  ✗ Error: {e}", file=sys.stderr)

    print(f"\n✓ Proceso completado. Resultados en {args.output_dir}")


def main():
    parser = argparse.ArgumentParser(
        prog="santander2md",
        description="Parser para extractos de Santander Argentina a Markdown/CSV/JSON",
    )
    parser.add_argument("--version", action="version", version="santander2md 0.1.0")
    sub = parser.add_subparsers(dest="command")

    # parse
    p = sub.add_parser("parse", help="Parsea un extracto individual")
    p.add_argument("-i", "--input", required=True, help="PDF de entrada")
    p.add_argument("-o", "--output", required=True, help="Archivo de salida (.md, .csv, .json)")
    p.set_defaults(func=cmd_parse)

    # batch
    b = sub.add_parser("batch", help="Parsea múltiples extractos en lote")
    b.add_argument("-i", "--input-dir", required=True, help="Directorio con PDFs")
    b.add_argument("-o", "--output-dir", required=True, help="Directorio de salida")
    b.add_argument("-f", "--format", choices=["md", "csv", "json"], default="md",
                   help="Formato de salida (default: md)")
    b.set_defaults(func=cmd_batch)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)
    args.func(args)


if __name__ == "__main__":
    main()
