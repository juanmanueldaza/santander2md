#!/usr/bin/env python3
"""Prueba camelot para extraer tablas de PDFs de Santander."""

import camelot
import sys

def test_extract_tables(pdf_file):
    """Extrae tablas de un PDF y muestra la primera."""
    print(f"Procesando: {pdf_file}")
    
    # Leer todas las páginas
    tables = camelot.read_pdf(pdf_file, pages="all", flavor="stream")
    
    print(f"✓ Se encontraron {len(tables)} tabla(s)")
    
    if len(tables) > 0:
        # Mostrar la primera tabla
        print("\n=== PRIMERA TABLA ===")
        print(tables[0].df.head(10))  # Primeras 10 filas
        
        # Guardar a CSV para inspección
        output_file = pdf_file.replace(".pdf", "_tabla1.csv")
        tables[0].to_csv(output_file)
        print(f"\n✓ Tabla guardada en: {output_file}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python test_camelot.py <archivo.pdf>")
        sys.exit(1)
    
    test_extract_tables(sys.argv[1])
