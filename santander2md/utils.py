"""
Utilidades para santander2md.
"""

import re
from typing import Optional


def parse_monto_argentino(monto_str: str) -> Optional[float]:
    """
    Parsea un monto en formato argentino a float.
    
    Formatos soportados:
    - "1.510.287,57" → 1510287.57
    - "151.028.757,00" → 151028757.00
    - "$ 1.510.287,57" → 1510287.57
    - "-$ 113.800,00" → -113800.00
    
    Args:
        monto_str: String con el monto
        
    Returns:
        float o None si no se pudo parsear
    """
    if not monto_str:
        return None
    
    # Limpiar el string
    monto_limpio = monto_str.strip()
    
    # Detectar signo negativo
    signo = 1
    if monto_limpio.startswith("-"):
        signo = -1
        monto_limpio = monto_limpio[1:].strip()
    
    # Remover símbolos de moneda
    monto_limpio = monto_limpio.replace("$", "").replace("US", "").strip()
    
    # Caso especial: si tiene puntos y comas
    if "." in monto_limpio and "," in monto_limpio:
        # Formato: 1.510.287,57
        # El último punto es separador de miles, la coma es decimal
        # Remover todos los puntos excepto el que está antes de la coma
        partes = monto_limpio.split(",")
        if len(partes) == 2:
            parte_entera = partes[0].replace(".", "")  # Remover puntos de miles
            parte_decimal = partes[1]
            monto_limpio = parte_entera + "." + parte_decimal
    
    # Caso: solo tiene punto (ej: 1510287.57)
    elif "." in monto_limpio and "," not in monto_limpio:
        # Asumir que el punto es decimal
        pass
    
    # Caso: solo tiene coma (ej: 1510287,57)
    elif "," in monto_limpio and "." not in monto_limpio:
        monto_limpio = monto_limpio.replace(",", ".")
    
    # Intentar convertir a float
    try:
        return signo * float(monto_limpio)
    except ValueError:
        return None


def extract_monto_from_line(line: str) -> Optional[float]:
    """
    Extrae un monto de una línea de texto.
    
    Args:
        line: Línea de texto
        
    Returns:
        float o None
    """
    # Buscar patrones de monto
    patterns = [
        r"-\$\s*([0-9\.,]+)",  # -$ 113.800,00
        r"\$\s*([0-9\.,]+)",    # $ 1.510.287,57
        r"([0-9\.]+\,[0-9]+)", # 1.510.287,57
        r"([0-9\,]+\.[0-9]+)", # 1,510,287.57
    ]
    
    for pattern in patterns:
        match = re.search(pattern, line)
        if match:
            return parse_monto_argentino(match.group(1))
    
    return None


if __name__ == "__main__":
    # Tests
    test_cases = [
        ("$ 1.510.287,57", 1510287.57),
        ("-$ 113.800,00", -113800.00),
        ("151.028.757,00", 151028757.00),
        ("1.510.287,57", 1510287.57),
    ]
    
    print("Probando parse_monto_argentino:")
    for input_str, expected in test_cases:
        result = parse_monto_argentino(input_str)
        status = "✓" if result == expected else "✗"
        print(f"  {status} '{input_str}' → {result} (esperado: {expected})")
