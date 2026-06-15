"""
Ejemplo básico de uso de santander2md.
"""

import sys
from santander2md import SantanderParser, Exporter


def main():
    if len(sys.argv) < 2:
        print("Uso: python basic_usage.py <ruta_al_pdf>")
        sys.exit(1)

    pdf_path = sys.argv[1]

    print(f"Parseando {pdf_path}...")
    parser = SantanderParser(pdf_path)
    extracto = parser.parse()

    print("\n=== RESUMEN ===")
    print(f"Cliente: {extracto.cliente_nombre}")
    print(f"Período: {extracto.periodo_inicio} al {extracto.periodo_fin}")
    print(f"Saldo inicial: ${extracto.saldo_inicial or 0:,.2f}")
    print(f"Saldo final: ${extracto.saldo_final or 0:,.2f}")
    if extracto.sueldo_neto:
        print(f"Sueldo neto: ${extracto.sueldo_neto:,.2f}")
    print(f"Total ingresos: ${extracto.total_ingresos:,.2f}")
    print(f"Total gastos: ${extracto.total_gastos:,.2f}")
    print(f"Movimientos: {extracto.cantidad_movimientos}")

    output_path = "reporte.md"
    Exporter.to_markdown(extracto, output_path)
    print(f"\n✓ Reporte guardado en {output_path}")


if __name__ == "__main__":
    main()
