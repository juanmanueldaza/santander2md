"""
Parser v2 para extractos de Santander en formato TXT.
Versión corregida: maneja líneas vacías correctamente.
"""

import re
from typing import List, Optional
from santander2md.models.extracto import Extracto, Movimiento


class SantanderTXTParserV2:
    """Parser para extractos de Santander en formato TXT (v2)."""
    
    def __init__(self, txt_path: str):
        self.txt_path = txt_path
        self.lineas = []
        self.extracto = None
    
    def load_file(self):
        """Carga el archivo TXT."""
        with open(self.txt_path, "r", encoding="utf-8", errors="ignore") as f:
            self.lineas = [line.strip() for line in f.readlines()]
    
    def find_value_after_pattern(self, pattern: str, max_lines: int = 20) -> Optional[float]:
        """
        Busca un patrón y luego extrae el primer monto ($ X.XXX,XX) 
        que aparezca después del patrón (salteando líneas vacías).
        """
        for i, linea in enumerate(self.lineas):
            if pattern in linea:
                # Buscar el monto en las próximas max_lines líneas
                for j in range(i+1, min(i+max_lines, len(self.lineas))):
                    linea_actual = self.lineas[j]
                    
                    # Saltear líneas vacías
                    if not linea_actual:
                        continue
                    
                    # Buscar un monto (formato: $ X.XXX,XX o -$ X.XXX,XX)
                    match = re.search(r"(-?)\$\s*([0-9\.,]+)", linea_actual)
                    if match:
                        signo = -1 if match.group(1) == "-" else 1
                        monto_str = match.group(2).replace(".", "").replace(",", ".")
                        return signo * float(monto_str)
        
        return None
    
    def extract_periodo(self) -> tuple:
        """Extrae el período (Desde: / Hasta:)."""
        inicio = None
        fin = None
        
        for i, linea in enumerate(self.lineas):
            if "Desde:" in linea:
                inicio = linea.split("Desde:")[1].strip()
            if "Hasta:" in linea:
                fin = linea.split("Hasta:")[1].strip()
                break
        
        return inicio, fin
    
    def extract_cliente(self) -> tuple:
        """Extrae datos del cliente."""
        nombre = None
        cuit = None
        
        for i, linea in enumerate(self.lineas):
            if "JUAN MANUEL DAZA" in linea:
                nombre = "JUAN MANUEL DAZA"
                # Buscar CUIT en las próximas líneas
                for j in range(i, min(i+10, len(self.lineas))):
                    if "CUIT:" in self.lineas[j]:
                        cuit = self.lineas[j].split("CUIT:")[1].strip()
                        break
                break
        
        return nombre, cuit
    
    def extract_sueldo(self) -> Optional[float]:
        """Extrae el sueldo neto usando el método genérico."""
        return self.find_value_after_pattern("Pago de haberes", max_lines=15)
    
    def extract_saldos(self) -> tuple:
        """Extrae saldos inicial y final."""
        saldo_inicial = self.find_value_after_pattern("Saldo Inicial", max_lines=5)
        saldo_final = self.find_value_after_pattern("Total en pesos", max_lines=5)
        
        return saldo_inicial, saldo_final
    
    def parse_movements(self) -> List[Movimiento]:
        """Parsea los movimientos (implementación simplificada)."""
        # Por ahora, implementación básica
        # TODO: Mejorar esto en la próxima versión
        return []
    
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
    parser = SantanderTXTParserV2(txt_path)
    return parser.parse()
