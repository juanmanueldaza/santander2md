#!/usr/bin/env python3
"""
Parser con pdfplumber - extrae tablas del PDF correctamente.
"""

import pdfplumber
import re

def parsear_extracto(pdf_file):
    """Parsea un extracto de Santander usando pdfplumber."""
    
    data = {
        "periodo": {"inicio": None, "fin": None},
        "sueldo_neto": None,
        "saldo_inicial": None,
        "saldo_final": None,
        "movimientos": []
    }
    
    with pdfplumber.open(pdf_file) as pdf:
        full_text = ""
        tables = []
        
        for page in pdf.pages:
            # Extraer texto
            text = page.extract_text()
            if text:
                full_text += text + "\n"
            
            # Extraer tablas
            page_tables = page.extract_tables()
            if page_tables:
                tables.extend(page_tables)
    
    # Extraer período
    match_inicio = re.search(r"Desde:\s*(\d{2}/\d{2}/\d{2})", full_text)
    match_fin = re.search(r"Hasta:\s*(\d{2}/\d{2}/\d{2})", full_text)
    if match_inicio:
        data["periodo"]["inicio"] = match_inicio.group(1)
    if match_fin:
        data["periodo"]["fin"] = match_fin.group(1)
    
    # Extraer sueldo
    match_sueldo = re.search(r"Pago de haberes.*?\$ ([0-9\.,]+)", full_text, re.DOTALL)
    if match_sueldo:
        data["sueldo_neto"] = match_sueldo.group(1)
    
    # Procesar tablas
    for table in tables:
        if len(table) < 2:
            continue
        
        # La tabla tiene headers: Fecha, Comprobante, Movimiento, ...
        headers = table[0]
        
        # Buscar columnas relevantes
        col_fecha = None
        col_movimiento = None
        col_debito = None
        col_credito = None
        
        for i, header in enumerate(headers):
            if header and "Fecha" in header:
                col_fecha = i
            if header and "Movimiento" in header:
                col_movimiento = i
            if header and ("Cuenta sueldo" in header or "Débito" in header or "Debito" in header):
                col_debito = i
            if header and ("Cuenta Corriente" in header or "Crédito" in header):
                col_credito = i
        
        # Procesar filas
        for row in table[1:]:
            if not row or not any(row):
                continue
            
            fecha = row[col_fecha] if col_fecha is not None and col_fecha < len(row) else None
            movimiento = row[col_movimiento] if col_movimiento is not None and col_movimiento < len(row) else None
            debito = row[col_debito] if col_debito is not None and col_debito < len(row) else None
            credito = row[col_credito] if col_credito is not None and col_credito < len(row) else None
            
            if fecha and (debito or credito):
                data["movimientos"].append({
                    "fecha": fecha.strip(),
                    "descripcion": movimiento.strip() if movimiento else "",
                    "debito": debito.strip() if debito else "",
                    "credito": credito.strip() if credito else ""
                })
    
    return data

def main():
    import sys
    
    if len(sys.argv) < 2:
        print("Uso: python parser_pdfplumber.py <archivo.pdf>")
        sys.exit(1)
    
    pdf_file = sys.argv[1]
    
    print(f"Procesando: {pdf_file}\n")
    
    data = parsear_extracto(pdf_file)
    
    print("=" * 80)
    print(f"EXTRACTO: {data['periodo']['inicio']} al {data['periodo']['fin']}")
    print("=" * 80)
    print(f"Sueldo neto: ${data['sueldo_neto']}")
    print(f"Total movimientos extraídos: {len(data['movimientos'])}")
    print()
    print("Primeros 5 movimientos:")
    for mov in data["movimientos"][:5]:
        print(f"  {mov['fecha']} | {mov['descripcion'][:40]:<40} | -{mov['debito']}{mov['credito']}")

if __name__ == "__main__":
    main()
