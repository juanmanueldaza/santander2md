#!/usr/bin/env python3
"""
Parser metódico v3 - Entiende la tabla de movimientos.
"""

import re
import os

class SantanderParserV3:
    def __init__(self, txt_file: str):
        self.txt_file = txt_file
        self.lines = []
        self.data = {
            "periodo": {"inicio": None, "fin": None},
            "cliente": {"nombre": None, "cuit": None, "cbu": None},
            "saldos": {"inicial": None, "final": None},
            "sueldo_neto": None,
            "movimientos": []
        }
    
    def load_file(self):
        with open(self.txt_file, "r", encoding="utf-8", errors="ignore") as f:
            self.lines = [line.strip() for line in f.readlines()]
    
    def find_line_index(self, pattern: str) -> int:
        """Busca el índice de la línea que contiene el patrón."""
        for i, line in enumerate(self.lines):
            if pattern in line:
                return i
        return -1
    
    def extract_periodo(self):
        """Extrae el período (Desde: / Hasta:)."""
        for i, line in enumerate(self.lines):
            if "Desde:" in line:
                self.data["periodo"]["inicio"] = line.split("Desde:")[1].strip()
            if "Hasta:" in line:
                self.data["periodo"]["fin"] = line.split("Hasta:")[1].strip()
                break
    
    def extract_sueldo(self):
        """Extrae el sueldo neto buscando 'Pago de haberes'."""
        for i, line in enumerate(self.lines):
            if "Pago de haberes" in line:
                # El monto está en una línea posterior que tenga "$ X.XXX,XX"
                for j in range(i, min(i+15, len(self.lines))):
                    match = re.search(r"\$ ([0-9\.,]+)", self.lines[j])
                    if match and j > i:
                        # Verificar que no sea "Saldo total"
                        if "Saldo" not in self.lines[j] and "Total" not in self.lines[j]:
                            self.data["sueldo_neto"] = match.group(1)
                            break
                break
    
    def extract_saldo_inicial(self):
        """Extrae el saldo inicial (busca 'Saldo Inicial' y luego el monto)."""
        for i, line in enumerate(self.lines):
            if "Saldo Inicial" in line:
                # El saldo está en la próxima línea que empiece con "$"
                for j in range(i+1, min(i+5, len(self.lines))):
                    if self.lines[j].startswith("$"):
                        match = re.search(r"([0-9\.,]+)", self.lines[j])
                        if match:
                            self.data["saldos"]["inicial"] = match.group(1)
                            break
                break
    
    def extract_saldo_final(self):
        """Extrae el saldo final (busca 'Saldo total al' y luego 'Total en pesos')."""
        for i, line in enumerate(self.lines):
            if "Saldo total al" in line:
                # Buscar "Total en pesos" después
                for j in range(i, min(i+30, len(self.lines))):
                    if "Total en pesos" in self.lines[j]:
                        # El saldo está 1-2 líneas después
                        for k in range(j+1, min(j+5, len(self.lines))):
                            match = re.search(r"^\$ ([0-9\.,]+)$", self.lines[k])
                            if match:
                                self.data["saldos"]["final"] = match.group(1)
                                break
                        break
                break
    
    def parse_movements(self):
        """
        Parsea la tabla de movimientos.
        Estructura: Fecha | Comprobante | Movimiento | Cta Sueldo | Cta Corriente | Saldo
        """
        movements = []
        i = 0
        
        while i < len(self.lines):
            line = self.lines[i]
            
            # Buscar una fecha (DD/MM/YY)
            date_match = re.match(r"^(\d{2}/\d{2}/\d{2})", line)
            if date_match:
                fecha = date_match.group(1)
                comprobante = ""
                descripcion = ""
                monto_debito = None
                monto_credito = None
                
                # Leer las próximas líneas para armar el movimiento
                j = i + 1
                while j < len(self.lines):
                    next_line = self.lines[j]
                    
                    # Si encontramos otra fecha, terminamos
                    if re.match(r"^\d{2}/\d{2}/\d{2}", next_line):
                        break
                    
                    # Comprobante (solo números)
                    if re.match(r"^\d+$", next_line.strip()):
                        comprobante = next_line.strip()
                    
                    # Descripción (no empieza con $, no es fecha, no es solo números)
                    elif not next_line.startswith("$") and not re.match(r"^\d{2}/\d{2}/\d{2}", next_line):
                        descripcion += next_line + " "
                    
                    # Monto (con -$ o solo $)
                    elif next_line.startswith("-$") or next_line.startswith("$"):
                        # Extraer el monto
                        monto_match = re.search(r"([0-9\.,]+)", next_line)
                        if monto_match:
                            monto_str = monto_match.group(1)
                            if next_line.startswith("-$"):
                                monto_debito = monto_str
                            else:
                                monto_credito = monto_str
                    
                    j += 1
                
                # Solo agregar si tiene monto (debito o crédito)
                if monto_debito or monto_credito:
                    movements.append({
                        "fecha": fecha,
                        "comprobante": comprobante,
                        "descripcion": descripcion.strip(),
                        "debito": monto_debito,
                        "credito": monto_credito
                    })
                
                i = j
            else:
                i += 1
        
        self.data["movimientos"] = movements
    
    def parse(self):
        """Ejecuta todos los extractores."""
        self.load_file()
        self.extract_periodo()
        self.extract_sueldo()
        self.extract_saldo_inicial()
        self.extract_saldo_final()
        self.parse_movements()
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
        print("Últimos 10 movimientos:")
        print("-" * 80)
        for mov in self.data["movimientos"][-10:]:
            deb = f"-${mov['debito']}" if mov['debito'] else ""
            cred = f"${mov['credito']}" if mov['credito'] else ""
            print(f"{mov['fecha']} | {mov['descripcion'][:40]:<40} | {deb}{cred}")
        print()


def main():
    import sys
    
    if len(sys.argv) < 2:
        print("Uso: python parser_v3.py <archivo_txt>")
        sys.exit(1)
    
    txt_file = sys.argv[1]
    parser = SantanderParserV3(txt_file)
    data = parser.parse()
    parser.print_summary()


if __name__ == "__main__":
    main()
