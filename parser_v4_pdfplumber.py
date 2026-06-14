#!/usr/bin/env python3
"""
Parser v4 - Usa pdfplumber para extraer texto con posiciones.
Esto permite entender la tabla de movimientos correctamente.
"""

import pdfplumber
import re
import os
from typing import Dict, List, Optional

class SantanderParserV4:
    def __init__(self, pdf_file: str):
        self.pdf_file = pdf_file
        self.data = {
            "periodo": {"inicio": None, "fin": None},
            "cliente": {"nombre": None, "cuit": None, "cbu": None},
            "saldos": {"inicial": None, "final": None},
            "sueldo_neto": None,
            "movimientos": []
        }
    
    def extract_text_with_layout(self) -> str:
        """Extrae texto preservando el layout (como -layout en pdftotext)."""
        full_text = ""
        with pdfplumber.open(self.pdf_file) as pdf:
            for page in pdf.pages:
                text = page.extract_text(layout=True)
                if text:
                    full_text += text + "\n"
        return full_text
    
    def extract_periodo(self, text: str):
        """Extrae el período del extracto."""
        # Buscar "Desde: DD/MM/YY" y "Hasta: DD/MM/YY"
        match_inicio = re.search(r"Desde:\s*(\d{2}/\d{2}/\d{2})", text)
        match_fin = re.search(r"Hasta:\s*(\d{2}/\d{2}/\d{2})", text)
        
        if match_inicio:
            self.data["periodo"]["inicio"] = match_inicio.group(1)
        if match_fin:
            self.data["periodo"]["fin"] = match_fin.group(1)
    
    def extract_sueldo(self, text: str):
        """Extrae el sueldo neto (Pago de haberes)."""
        # Buscar "Pago de haberes" y luego el monto
        pattern = r"Pago de haberes.*?Transferencia s\.n\.p\..*?\$ ([0-9\.,]+)"
        match = re.search(pattern, text, re.DOTALL)
        if match:
            self.data["sueldo_neto"] = match.group(1)
    
    def extract_saldos(self, text: str):
        """Extrae saldos inicial y final."""
        # Saldo inicial
        match_inicial = re.search(r"Saldo Inicial\s*\n\s*\$ ([0-9\.,]+)", text)
        if match_inicial:
            self.data["saldos"]["inicial"] = match_inicial.group(1)
        
        # Saldo final (buscar "Saldo total al" y luego "Total en pesos")
        match_final = re.search(r"Saldo total al.*?Total en pesos\s*\n\s*\$ ([0-9\.,]+)", text, re.DOTALL)
        if match_final:
            self.data["saldos"]["final"] = match_final.group(1)
    
    def extract_movements(self, text: str):
        """Extrae movimientos de la tabla."""
        movements = []
        lines = text.split("\n")
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Buscar una fecha al inicio de la línea (DD/MM/YY)
            date_match = re.match(r"^(\d{2}/\d{2}/\d{2})", line)
            if date_match:
                fecha = date_match.group(1)
                rest_of_line = line[len(fecha):].strip()
                
                # El resto de la línea puede tener: comprobante + descripción + montos
                # Ejemplo: "04/05/26 2496454  Compra con tarjeta de debito  -$ 113.800,00  $ 1.803.922,21"
                
                # Buscar débito ( -$ XXX.XXX,XX)
                debito_match = re.search(r"-\$\s*([0-9\.,]+)", line)
                # Buscar crédito ($ XXX.XXX,XX al final)
                credito_match = re.search(r"(?<!\-)\$\s*([0-9\.,]+)\s*$", line)
                
                descripcion = ""
                # La descripción está entre el comprobante y los montos
                # Por ahora, extraer todo lo que no sea números/fechas
                if debito_match or credito_match:
                    # Limpiar la línea para extraer descripción
                    clean_line = re.sub(r"^(\d{2}/\d{2}/\d{2})\s*\d*\s*", "", line)
                    clean_line = re.sub(r"-\$\s*[0-9\.,]+\s*", "", clean_line)
                    clean_line = re.sub(r"\$\s*[0-9\.,]+\s*$", "", clean_line)
                    descripcion = clean_line.strip()
                
                movements.append({
                    "fecha": fecha,
                    "descripcion": descripcion,
                    "debito": debito_match.group(1) if debito_match else None,
                    "credito": credito_match.group(1) if credito_match else None
                })
            
            i += 1
        
        self.data["movimientos"] = movements
    
    def parse(self):
        """Ejecuta todo el parsing."""
        # Extraer texto con layout
        text = self.extract_text_with_layout()
        
        if not text:
            raise Exception("No se pudo extraer texto del PDF")
        
        # Guardar texto para debug
        debug_file = self.pdf_file.replace(".pdf", "_debug.txt")
        with open(debug_file, "w", encoding="utf-8") as f:
            f.write(text)
        
        # Extraer datos
        self.extract_periodo(text)
        self.extract_sueldo(text)
        self.extract_saldos(text)
        self.extract_movements(text)
        
        return self.data
    
    def print_summary(self):
        """Imprime un resumen."""
        print("=" * 80)
        print(f"EXTRACTO SANTANDER: {self.data['periodo']['inicio']} al {self.data['periodo']['fin']}")
        print("=" * 80)
        print()
        print(f"Sueldo neto: ${self.data['sueldo_neto']}")
        print(f"Saldo inicial: ${self.data['saldos']['inicial']}")
        print(f"Saldo final: ${self.data['saldos']['final']}")
        print(f"Total movimientos: {len(self.data['movimientos'])}")
        print()
        print("Primeros 5 movimientos:")
        print("-" * 80)
        for mov in self.data["movimientos"][:5]:
            deb = f"-${mov['debito']}" if mov['debito'] else ""
            cred = f"${mov['credito']}" if mov['credito'] else ""
            print(f"{mov['fecha']} | {mov['descripcion'][:40]:<40} | {deb}{cred}")


def main():
    import sys
    
    if len(sys.argv) < 2:
        print("Uso: python parser_v4_pdfplumber.py <archivo_pdf>")
        sys.exit(1)
    
    pdf_file = sys.argv[1]
    
    if not os.path.exists(pdf_file):
        print(f"Error: No existe el archivo {pdf_file}")
        sys.exit(1)
    
    parser = SantanderParserV4(pdf_file)
    data = parser.parse()
    parser.print_summary()
    
    print(f"\n✓ Texto extraído guardado en: {pdf_file.replace('.pdf', '_debug.txt')}")


if __name__ == "__main__":
    main()
