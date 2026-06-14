#!/usr/bin/env python3
"""
Parser metódico para extractos de Santander Argentina.
Extrae TODA la data: ingresos, gastos, saldos, movimientos.
"""

import re
import os
from datetime import datetime
from typing import Dict, List, Optional

class SantanderParser:
    def __init__(self, txt_file: str):
        self.txt_file = txt_file
        self.lines = []
        self.data = {
            "periodo": {"inicio": None, "fin": None},
            "cliente": {"nombre": None, "cuit": None, "cbu": None},
            "saldos": {"inicial": None, "final": None},
            "sueldo_neto": None,
            "cuenta_sueldo": {"saldo": None},
            "cuenta_corriente": {"saldo": None},
            "tarjeta_credito": {"monto_a_pagar": None, "vencimiento": None},
            "movimientos": []
        }
        
    def load_file(self):
        """Carga el archivo TXT."""
        with open(self.txt_file, "r", encoding="utf-8", errors="ignore") as f:
            self.lines = [line.strip() for line in f.readlines()]
    
    def extract_periodo(self):
        """Extrae el período del extracto."""
        for i, line in enumerate(self.lines):
            if "Período de movimientos" in line:
                # Buscar "Desde: " y "Hasta: " en las próximas líneas
                for j in range(i, min(i+10, len(self.lines))):
                    if "Desde:" in self.lines[j]:
                        fecha_inicio = self.lines[j].split("Desde:")[1].strip()
                        self.data["periodo"]["inicio"] = fecha_inicio
                    if "Hasta:" in self.lines[j]:
                        fecha_fin = self.lines[j].split("Hasta:")[1].strip()
                        self.data["periodo"]["fin"] = fecha_fin
                        break
                break
    
    def extract_cliente(self):
        """Extrae datos del cliente."""
        for i, line in enumerate(self.lines):
            if "JUAN MANUEL DAZA" in line:
                self.data["cliente"]["nombre"] = "JUAN MANUEL DAZA"
                # Buscar CUIT y CBU en las próximas líneas
                for j in range(i, min(i+10, len(self.lines))):
                    if "CUIT:" in self.lines[j]:
                        self.data["cliente"]["cuit"] = self.lines[j].split("CUIT:")[1].strip()
                    if "CBU:" in self.lines[j]:
                        self.data["cliente"]["cbu"] = self.lines[j].split("CBU:")[1].strip()
                break
    
    def extract_saldos(self):
        """Extrae saldos inicial y final."""
        for i, line in enumerate(self.lines):
            # Saldo inicial
            if "Saldo Inicial" in line:
                # El saldo está en la próxima línea que tenga un número
                for j in range(i+1, min(i+5, len(self.lines))):
                    match = re.search(r"([0-9\.,]+)", self.lines[j])
                    if match and "$" not in self.lines[j]:  # No sea la línea de "Saldo Inicial $ X"
                        # El saldo inicial está en la misma línea o la próxima
                        continue
                    if "$" in self.lines[j]:
                        match = re.search(r"\$ ([0-9\.,]+)", self.lines[j])
                        if match:
                            self.data["saldos"]["inicial"] = match.group(1)
                            break
            
            # Saldo final (buscar "Saldo total al")
            if "Saldo total al" in line:
                # Buscar "Total en pesos" y luego el saldo
                for j in range(i, min(i+20, len(self.lines))):
                    if "Total en pesos" in self.lines[j]:
                        # El saldo está unas líneas después
                        for k in range(j+1, min(j+5, len(self.lines))):
                            match = re.search(r"\$ ([0-9\.,]+)", self.lines[k])
                            if match:
                                self.data["saldos"]["final"] = match.group(1)
                                break
                        break
                break
    
    def extract_sueldo(self):
        """Extrae el sueldo neto (Pago de haberes)."""
        for i, line in enumerate(self.lines):
            if "Pago de haberes" in line:
                # Buscar el monto en las próximas líneas
                for j in range(i, min(i+10, len(self.lines))):
                    match = re.search(r"\$ ([0-9\.,]+)", self.lines[j])
                    if match and j > i:  # No sea la misma línea
                        self.data["sueldo_neto"] = match.group(1)
                        break
                break
    
    def extract_movimientos(self):
        """Extrae todos los movimientos (gastos e ingresos)."""
        movimientos = []
        current_date = None
        
        for i, line in enumerate(self.lines):
            # Buscar fechas (formato DD/MM/YY)
            date_match = re.search(r"^(\d{2}/\d{2}/\d{2})", line)
            if date_match:
                current_date = date_match.group(1)
            
            # Buscar débitos (gastos): "-$ XXX.XXX,XX"
            debito_match = re.search(r"-\$ ([0-9\.,]+)", line)
            if debito_match and current_date:
                monto = debito_match.group(1)
                # Buscar descripción en la próxima línea
                descripcion = ""
                if i+1 < len(self.lines):
                    next_line = self.lines[i+1]
                    if not re.search(r"^(\d{2}/\d{2}/\d{2})", next_line) and "$" not in next_line:
                        descripcion = next_line
                
                movimientos.append({
                    "fecha": current_date,
                    "tipo": "debito",
                    "monto": monto,
                    "descripcion": descripcion
                })
            
            # Buscar créditos (ingresos): "$ XXX.XXX,XX" (pero no sea saldo)
            credito_match = re.search(r"^\$ ([0-9\.,]+)$", line)
            if credito_match and current_date and "Saldo" not in line and "Total" not in line:
                monto = credito_match.group(1)
                # Verificar que sea un monto significativo (no centavos)
                monto_num = float(monto.replace(".", "").replace(",", "."))
                if monto_num > 1000:  # Ignorar montos pequeños
                    descripcion = ""
                    if i+1 < len(self.lines):
                        next_line = self.lines[i+1]
                        if not re.search(r"^(\d{2}/\d{2}/\d{2})", next_line) and "$" not in next_line:
                            descripcion = next_line
                    
                    movimientos.append({
                        "fecha": current_date,
                        "tipo": "credito",
                        "monto": monto,
                        "descripcion": descripcion
                    })
        
        self.data["movimientos"] = movimientos
    
    def parse(self):
        """Ejecuta todos los extractores."""
        self.load_file()
        self.extract_periodo()
        self.extract_cliente()
        self.extract_saldos()
        self.extract_sueldo()
        self.extract_movimientos()
        return self.data
    
    def to_markdown(self) -> str:
        """Convierte los datos a Markdown."""
        md = f"""# Extracto Santander - {self.data['periodo']['inicio']} al {self.data['periodo']['fin']}

## Datos del Cliente
- **Nombre:** {self.data['cliente']['nombre']}
- **CUIT:** {self.data['cliente']['cuit']}
- **CBU:** {self.data['cliente']['cbu']}

## Resumen Financiero
- **Saldo Inicial:** $ {self.data['saldos']['inicial'] if self.data['saldos']['inicial'] else 'N/A'}
- **Saldo Final:** $ {self.data['saldos']['final'] if self.data['saldos']['final'] else 'N/A'}
- **Sueldo Neto:** $ {self.data['sueldo_neto'] if self.data['sueldo_neto'] else 'N/A'}

## Movimientos ({len(self.data['movimientos'])} transacciones)

| Fecha | Tipo | Monto | Descripción |
|-------|-------|-------|-------------|
"""
        for mov in self.data["movimientos"][:50]:  # Mostrar solo los primeros 50
            md += f"| {mov['fecha']} | {mov['tipo']} | $ {mov['monto']} | {mov['descripcion']} |\n"
        
        if len(self.data["movimientos"]) > 50:
            md += f"\n*... y {len(self.data['movimientos']) - 50} movimientos más.*\n"
        
        return md


def main():
    import sys
    
    if len(sys.argv) < 2:
        print("Uso: python parser_v2.py <archivo_txt>")
        sys.exit(1)
    
    txt_file = sys.argv[1]
    
    if not os.path.exists(txt_file):
        print(f"Error: No existe el archivo {txt_file}")
        sys.exit(1)
    
    parser = SantanderParser(txt_file)
    data = parser.parse()
    
    # Imprimir en JSON para debug
    import json
    print(json.dumps(data, indent=2, ensure_ascii=False))
    
    # Imprimir Markdown
    print("\n" + "="*80)
    print(parser.to_markdown())


if __name__ == "__main__":
    main()
