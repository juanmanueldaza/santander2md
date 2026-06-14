"""
Parser para extractos de Santander en formato TXT (generados con pdftotext).
"""

import re
from typing import List, Optional
from santander2md.models.extracto import Extracto, Movimiento


class SantanderTXTParser:
    """Parsea extractos de Santander en formato TXT."""
    
    def __init__(self, txt_path: str):
        self.txt_path = txt_path
        self.lines = []
        self.extracto = None
    
    def load_file(self):
        """Carga el archivo TXT."""
        with open(self.txt_path, "r", encoding="utf-8", errors="ignore") as f:
            self.lines = [line.strip() for line in f.readlines()]
    
    def extract_periodo(self) -> tuple:
        """Extrae el período (Desde: / Hasta:)."""
        inicio = None
        fin = None
        
        for i, line in enumerate(self.lines):
            if "Desde:" in line:
                inicio = line.split("Desde:")[1].strip()
            if "Hasta:" in line:
                fin = line.split("Hasta:")[1].strip()
                break
        
        return inicio, fin
    
    def extract_cliente(self) -> tuple:
        """Extrae datos del cliente."""
        nombre = None
        cuit = None
        
        for i, line in enumerate(self.lines):
            if "JUAN MANUEL DAZA" in line:
                nombre = "JUAN MANUEL DAZA"
                # Buscar CUIT en las próximas líneas
                for j in range(i, min(i+10, len(self.lines))):
                    if "CUIT:" in self.lines[j]:
                        cuit = self.lines[j].split("CUIT:")[1].strip()
                        break
                break
        
        return nombre, cuit
    
    def extract_sueldo(self) -> Optional[float]:
        """Extrae el sueldo neto."""
        for i, line in enumerate(self.lines):
            if "Pago de haberes" in line:
                # Buscar el monto en las próximas líneas
                for j in range(i, min(i+15, len(self.lines))):
                    # El monto tiene formato: $ X.XXX,XX
                    match = re.search(r"\$ ([0-9\.,]+)", line)
                    if match and j > i:
                        monto_str = match.group(1).replace(".", "").replace(",", ".")
                        return float(monto_str)
                break
        return None
    
    def extract_saldos(self) -> tuple:
        """Extrae saldos inicial y final."""
        saldo_inicial = None
        saldo_final = None
        
        for i, line in enumerate(self.lines):
            # Saldo inicial
            if "Saldo Inicial" in line:
                for j in range(i+1, min(i+5, len(self.lines))):
                    if "$" in self.lines[j] and "0,00" not in self.lines[j]:
                        match = re.search(r"([0-9\.,]+)", self.lines[j])
                        if match:
                            saldo_inicial = float(match.group(1).replace(".", "").replace(",", "."))
                            break
            
            # Saldo final
            if "Saldo total al" in line:
                for j in range(i, min(i+30, len(self.lines))):
                    if "Total en pesos" in self.lines[j]:
                        # El saldo está 1-2 líneas después
                        for k in range(j+1, min(j+5, len(self.lines))):
                            match = re.search(r"\$ ([0-9\.,]+)", self.lines[k])
                            if match:
                                saldo_final = float(match.group(1).replace(".", "").replace(",", "."))
                                break
                        break
                break
        
        return saldo_inicial, saldo_final
    
    def parse_movements(self) -> List[Movimiento]:
        """Parsea los movimientos de la tabla."""
        movements = []
        
        # Buscar la sección de movimientos
        in_movements = False
        current_date = None
        
        i = 0
        while i < len(self.lines):
            line = self.lines[i]
            
            # Detectar inicio de movimientos
            if "Movimientos en pesos" in line:
                in_movements = True
                i += 1
                continue
            
            if in_movements:
                # Buscar fechas (DD/MM/YY)
                date_match = re.match(r"^(\d{2}/\d{2}/\d{2})", line)
                if date_match:
                    current_date = date_match.group(1)
                    
                    # Leer las próximas líneas para armar el movimiento
                    j = i + 1
                    descripcion = ""
                    monto_debito = None
                    monto_credito = None
                    
                    while j < len(self.lines):
                        next_line = self.lines[j]
                        
                        # Si encontramos otra fecha, terminamos
                        if re.match(r"^\d{2}/\d{2}/\d{2}", next_line):
                            break
                        
                        # Extraer descripción
                        if not next_line.startswith("$") and not next_line.startswith("-$") and not re.match(r"^\d+$", next_line):
                            descripcion += next_line + " "
                        
                        # Extraer montos
                        debito_match = re.search(r"-\$ ([0-9\.,]+)", next_line)
                        credito_match = re.search(r"^\$ ([0-9\.,]+)$", next_line)
                        
                        if debito_match:
                            monto_debito = float(debito_match.group(1).replace(".", "").replace(",", "."))
                        elif credito_match and "Saldo" not in next_line:
                            monto_credito = float(credito_match.group(1).replace(".", "").replace(",", "."))
                        
                        j += 1
                    
                    # Crear movimiento
                    if monto_debito or monto_credito:
                        movimiento = Movimiento(
                            fecha=current_date,
                            descripcion=descripcion.strip(),
                            monto=monto_debito if monto_debito else monto_credito,
                            tipo="debito" if monto_debito else "credito"
                        )
                        movements.append(movimiento)
                    
                    i = j
                    continue
            
            i += 1
        
        return movements
    
    def parse(self) -> Extracto:
        """Ejecuta el parsing completo."""
        self.load_file()
        
        # Extraer datos
        periodo_inicio, periodo_fin = self.extract_periodo()
        cliente_nombre, cliente_cuit = self.extract_cliente()
        sueldo = self.extract_sueldo()
        saldo_inicial, saldo_final = self.extract_saldos()
        movimientos = self.parse_movements()
        
        # Crear objeto Extracto
        self.extracto = Extracto(
            periodo_inicio=periodo_inicio,
            periodo_fin=periodo_fin,
            cliente_nombre=cliente_nombre,
            cliente_cuit=cliente_cuit,
            saldo_inicial=saldo_inicial,
            saldo_final=saldo_final,
            sueldo_neto=sueldo,
            movimientos=movimientos
        )
        
        return self.extracto


def parse_file(txt_path: str) -> Extracto:
    """Función auxiliar para parsear un archivo."""
    parser = SantanderTXTParser(txt_path)
    return parser.parse()
