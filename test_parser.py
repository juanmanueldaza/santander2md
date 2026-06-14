#!/usr/bin/env python3
"""Script de prueba para el parser de Santander."""

import sys
import os

# Agregar el directorio actual al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from santander2md.parsers.santander_txt import SantanderTXTParser

def main():
    # Archivo de prueba
    txt_file = os.path.expanduser("~/Downloads/finanzas_analisis/2026-05-28_00720281007003601170.txt")
    
    if not os.path.exists(txt_file):
        print(f"Error: No se encuentra el archivo {txt_file}")
        sys.exit(1)
    
    print(f"Parseando: {txt_file}")
    print("=" * 80)
    
    # Crear parser y parsear
    parser = SantanderTXTParser(txt_file)
    extracto = parser.parse()
    
    # Imprimir resultados
    print(f"\nPeríodo: {extracto.periodo_inicio} al {extracto.periodo_fin}")
    print(f"Cliente: {extracto.cliente_nombre}")
    print(f"CUIT: {extracto.cliente_cuit}")
    print(f"\nSueldo neto: ${extracto.sueldo_neto:,.2f}")
    print(f"Saldo inicial: ${extracto.saldo_inicial:,.2f}")
    print(f"Saldo final: ${extracto.saldo_final:,.2f}")
    print(f"\nTotal movimientos: {len(extracto.movimientos)}")
    
    # Calcular estadísticas
    ingresos = sum(m.monto for m in extracto.movimientos if m.tipo == "credito")
    gastos = sum(abs(m.monto) for m in extracto.movimientos if m.tipo == "debito")
    
    print(f"\nEstadísticas:")
    print(f"  - Total ingresos (sin sueldo): ${ingresos:,.2f}")
    print(f"  - Total gastos: ${gastos:,.2f}")
    print(f"  - Capacidad de ahorro: ${ingresos - gastos:,.2f}")
    
    # Mostrar primeros 10 movimientos
    print(f"\nPrimeros 10 movimientos:")
    print("-" * 80)
    for i, mov in enumerate(extracto.movimientos[:10]):
        print(f"{i+1}. {mov}")
    
    # Guardar a Markdown
    output_file = "test_output.md"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(extracto.to_markdown())
    
    print(f"\n✓ Reporte guardado en: {output_file}")

if __name__ == "__main__":
    main()
