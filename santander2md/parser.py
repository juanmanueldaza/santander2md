"""
Parser para extractos de Santander Argentina.
Usa pdfplumber para extraer texto y tablas de los PDFs.
"""

import pdfplumber
import re
from typing import List, Optional
from ..models import Extracto, Cliente, Periodo, Saldos, Movimiento


class SantanderParser:
    """Parser principal para extractos de Santander."""
    
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.extracto = None
    
    def parse(self) -> Extracto:
        """Parsea el PDF y devuelve un objeto Extracto."""
        with pdfplumber.open(self.pdf_path) as pdf:
            # Extraer texto de todas las páginas
            full_text = ""
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    full_text += text + "\n"
        
        # Extraer datos
        cliente = self._extract_cliente(full_text)
        periodo = self._extract_periodo(full_text)
        saldos = self._extract_saldos(full_text)
        sueldo = self._extract_sueldo(full_text)
        movimientos = self._extract_movimientos(full_text)
        
        # Crear objeto Extracto
        self.extracto = Extracto(
            periodo=periodo,
            cliente=cliente,
            saldos=saldos,
            sueldo_neto=sueldo,
            movimientos=movimientos
        )
        
        return self.extracto
    
    def _extract_cliente(self, text: str) -> Cliente:
        """Extrae datos del cliente."""
        # Buscar nombre (asumimos que es JUAN MANUEL DAZA)
        nombre_match = re.search(r"([A-ZÁÉÍÓÚÑ\s]+)\n", text)
        nombre = nombre_match.group(1).strip() if nombre_match else "N/A"
        
        # Buscar CUIT
        cuit_match = re.search(r"CUIT:\s*([\d-]+)", text)
        cuit = cuit_match.group(1) if cuit_match else "N/A"
        
        # Buscar CBU
        cbu_match = re.search(r"CBU:\s*([\d]+)", text)
        cbu = cbu_match.group(1) if cbu_match else "N/A"
        
        return Cliente(nombre=nombre, cuit=cuit, cbu=cbu)
    
    def _extract_periodo(self, text: str) -> Periodo:
        """Extrae el período del extracto."""
        inicio_match = re.search(r"Desde:\s*(\d{2}/\d{2}/\d{2})", text)
        fin_match = re.search(r"Hasta:\s*(\d{2}/\d{2}/\d{2})", text)
        
        inicio = inicio_match.group(1) if inicio_match else "N/A"
        fin = fin_match.group(1) if fin_match else "N/A"
        
        return Periodo(inicio=inicio, fin=fin)
    
    def _extract_saldos(self, text: str) -> Saldos:
        """Extrae saldos inicial y final."""
        # Saldo inicial
        inicial_match = re.search(r"Saldo Inicial\s*\n?\s*\$?\s*([\d\.,]+)", text)
        saldo_inicial = None
        if inicial_match:
            saldo_str = inicial_match.group(1).replace(".", "").replace(",", ".")
            saldo_inicial = float(saldo_str)
        
        # Saldo final
        final_match = re.search(r"Saldo total.*?Total en pesos\s*\n?\s*\$?\s*([\d\.,]+)", text, re.DOTALL)
        saldo_final = None
        if final_match:
            saldo_str = final_match.group(1).replace(".", "").replace(",", ".")
            saldo_final = float(saldo_str)
        
        return Saldos(inicial=saldo_inicial, final=saldo_final)
    
    def _extract_sueldo(self, text: str) -> Optional[float]:
        """Extrae el sueldo neto."""
        # Buscar "Pago de haberes" y luego el monto
        pattern = r"Pago de haberes.*?Transferencia s\.n\.p\..*?\$?\s*([\d\.,]+)"
        match = re.search(pattern, text, re.DOTALL)
        
        if match:
            sueldo_str = match.group(1).replace(".", "").replace(",", ".")
            return float(sueldo_str)
        
        return None
    
    def _extract_movimientos(self, text: str) -> List[Movimiento]:
        """Extrae los movimientos de la tabla."""
        movimientos = []
        
        # Buscar la sección de movimientos
        # El patrón es: FECHA + DESCRIPCIÓN + MONTO (con - para débito)
        pattern = r"(\d{2}/\d{2}/\d{2})\s+([A-Za-z\s]+)\s+(-\$)?\s*\$?\s*([\d\.,]+)"
        
        matches = re.finditer(pattern, text)
        
        for match in matches:
            fecha = match.group(1)
            descripcion = match.group(2).strip()
            es_debito = match.group(3) is not None
            monto_str = match.group(4).replace(".", "").replace(",", ".")
            monto = float(monto_str)
            
            if es_debito:
                movimiento = Movimiento(
                    fecha=fecha,
                    descripcion=descripcion,
                    debito=monto,
                    credito=None
                )
            else:
                movimiento = Movimiento(
                    fecha=fecha,
                    descripcion=descripcion,
                    debito=None,
                    credito=monto
                )
            
            movimientos.append(movimiento)
        
        return movimientos
