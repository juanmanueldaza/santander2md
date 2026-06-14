"""
Parser v3 para extractos de Santander en formato TXT.
Corrige el parsing de montos argentinos.
"""

import re
from typing import List, Optional
from santander2md.models.extracto import Extracto, Movimiento
from santander2md.utils import parse_monto_argentino


class SantanderTXTParserV3:
    """Parser para extractos de Santander en formato TXT (v3)."""
    
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
        Busca un patrón y luego extrae el primer monto 
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
                    
                    # Buscar un monto (usar utils)
                    monto = parse_monto_argentino(linea_actual)
                    if monto is not None:
                        return monto
        
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
        """Extrae el sueldo neto."""
        return self.find_value_after_pattern("Pago de haberes", max_lines=15)
    
    def extract_saldos(self) -> tuple:
        """Extrae saldos inicial y final."""
        # Saldo inicial: buscar después de "Saldo Inicial"
        saldo_inicial = self.find_value_after_pattern("Saldo Inicial", max_lines=5)
        
        # Saldo final: buscar después de "Total en pesos" (que está después de "Saldo total al")
        saldo_final = None
        for i, linea in enumerate(self.lineas):
            if "Total en pesos" in linea:
                # El saldo está en la próxima línea no vacía
                for j in range(i+1, min(i+10, len(self.lineas))):
                    if self.lineas[j]:
                        saldo_final = parse_monto_argentino(self.lineas[j])
                        break
                break
        
        return saldo_inicial, saldo_final
    
    def parse_movements(self) -> List[Movimiento]:
        """Parsea los movimientos (implementación básica)."""
        movimientos = []
        
        # Buscar la sección de movimientos
        in_movements = False
        i = 0
        
        while i < len(self.lineas):
            linea = self.lineas[i]
            
            # Detectar inicio de movimientos
            if "Movimientos en pesos" in linea:
                in_movements = True
                i += 1
                continue
            
            if in_movements:
                # Buscar fechas (DD/MM/YY)
                if re.match(r"^\d{2}/\d{2}/\d{2}$", linea):
                    fecha = linea
                    
                    # Leer descripción y montos
                    descripcion = ""
                    monto_debito = None
                    monto_credito = None
                    
                    j = i + 1
                    while j < len(self.lineas):
                        linea_actual = self.lineas[j]
                        
                        # Si encontramos otra fecha, terminamos
                        if re.match(r"^\d{2}/\d{2}/\d{2}$", linea_actual):
                            break
                        
                        # Extraer descripción (no es monto ni fecha)
                        if not any(char in linea_actual for char in ["$", "-", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]):
                            descripcion += linea_actual + " "
                        
                        # Extraer montos
                        if "-$" in linea_actual or linea_actual.startswith("-"):
                            monto_debito = parse_monto_argentino(linea_actual)
                        elif "$" in linea_actual and not linea_actual.startswith("-"):
                            # Verificar que no sea "Saldo en cuenta"
                            if "Saldo" not in linea_actual:
                                monto_credito = parse_monto_argentino(linea_actual)
                        
                        j += 1
                    
                    # Crear movimiento si hay monto
                    if monto_debito or monto_credito:
                        movimiento = Movimiento(
                            fecha=fecha,
                            descripcion=descripcion.strip(),
                            monto=abs(monto_debito if monto_debito else monto_credito),
                            tipo="debito" if monto_debito else "credito"
                        )
                        movimientos.append(movimiento)
                    
                    i = j
                    continue
            
            i += 1
        
        return movimientos
    
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
    parser = SantanderTXTParserV3(txt_path)
    return parser.parse()
