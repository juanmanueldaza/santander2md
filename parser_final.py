#!/usr/bin/env python3
"""
Parser FINAL - Reconstruye la tabla de movimientos analizando la estructura del TXT.
Usa solo Python puro (sin librerías externas).
"""

import re
import os

def limpiar_monto(monto_str):
    """Limpia un monto: '$ 1.510.287,57' → 1510287.57"""
    if not monto_str:
        return 0.0
    # Eliminar $, espacios, y convertir a float
    monto_str = monto_str.replace("$", "").replace(" ", "").strip()
    # Reemplazar . por nada (separador de miles) y , por . (decimal)
    partes = monto_str.split(",")
    if len(partes) == 2:
        entera = partes[0].replace(".", "")
        decimal = partes[1]
        return float(f"{entera}.{decimal}")
    return float(monto_str.replace(".", ""))

def extraer_movimientos(lines):
    """
    Extrae movimientos reconstruyendo la tabla.
    
    La tabla original tiene columnas:
    Fecha | Comprobante | Movimiento | Cta Sueldo | Cta Cte | Saldo
    
    En el TXT, cada celda está en una línea separada.
    Hay que juntar las líneas que corresponden a la misma fila.
    """
    movimientos = []
    i = 0
    
    while i < len(lines):
        line = lines[i].strip()
        
        # Buscar una fecha (DD/MM/YY)
        fecha_match = re.match(r"^(\d{2}/\d{2}/\d{2})$", line)
        if fecha_match:
            fecha = line
            comprobante = ""
            descripcion = ""
            debito = None
            credito = None
            
            # Leer las próximas líneas para armar el movimiento
            j = i + 1
            while j < len(lines):
                next_line = lines[j].strip()
                
                # Si encontrmos otra fecha, terminamos con este movimiento
                if re.match(r"^\d{2}/\d{2}/\d{2}$", next_line):
                    break
                
                # Comprobante (solo números, 7-10 dígitos)
                if re.match(r"^\d{7,10}$", next_line):
                    comprobante = next_line
                
                # Monto débito (-$ XXX.XXX,XX)
                elif next_line.startswith("-$"):
                    monto = next_line.replace("-$", "").replace(" ", "").strip()
                    debito = monto
                
                # Monto crédito ($ XXX.XXX,XX al final de la línea)
                elif next_line.startswith("$") and not next_line.startswith("-$"):
                    # Verificar que no sea un saldo (tiene formato "$ X.XXX,XX" solo)
                    monto = next_line.replace("$", "").replace(" ", "").strip()
                    if re.match(r"^[0-9\.,]+$", monto):
                        # Podría ser saldo o crédito
                        # Si la próxima línea es otra fecha o vacía, es saldo
                        if j + 1 < len(lines):
                            prox_linea = lines[j+1].strip()
                            if re.match(r"^\d{2}/\d{2}/\d{2}$", prox_linea) or prox_linea == "":
                                # Es un saldo, no un crédito
                                pass
                            else:
                                credito = monto
                
                # Descripción (lo que no es fecha, comprobante, ni monto)
                else:
                    if next_line and not next_line.startswith("$"):
                        descripcion += next_line + " "
                
                j += 1
            
            # Solo agregar si tiene monto (débito o crédito)
            if debito or credito:
                movimientos.append({
                    "fecha": fecha,
                    "comprobante": comprobante,
                    "descripcion": descripcion.strip(),
                    "debito": debito,
                    "credito": credito
                })
            
            i = j
        else:
            i += 1
    
    return movimientos

def parsear_extracto(txt_file):
    """Parsea un extracto completo."""
    
    with open(txt_file, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()
    
    # Limpiar líneas (eliminar saltos y espacios extra)
    lines = [line.strip() for line in lines]
    
    data = {
        "archivo": os.path.basename(txt_file),
        "periodo": {"inicio": None, "fin": None},
        "cliente": {"nombre": None, "cuit": None, "cbu": None},
        "saldos": {"inicial": None, "final": None},
        "sueldo_neto": None,
        "movimientos": []
    }
    
    # Extraer período
    for i, line in enumerate(lines):
        if "Desde:" in line:
            data["periodo"]["inicio"] = line.split("Desde:")[1].strip()
        if "Hasta:" in line:
            data["periodo"]["fin"] = line.split("Hasta:")[1].strip()
            break
    
    # Extraer cliente
    for i, line in enumerate(lines):
        if "JUAN MANUEL" in line:
            data["cliente"]["nombre"] = "JUAN MANUEL DAZA"
            # Buscar CUIT y CBU
            for j in range(i, min(i+10, len(lines))):
                if "CUIT:" in lines[j]:
                    data["cliente"]["cuit"] = lines[j].split("CUIT:")[1].strip()
                if "CBU:" in lines[j]:
                    data["cliente"]["cbu"] = lines[j].split("CBU:")[1].strip()
            break
    
    # Extraer sueldo
    for i, line in enumerate(lines):
        if "Pago de haberes" in line:
            # Buscar el monto en las próximas líneas
            for j in range(i, min(i+15, len(lines))):
                if "$" in lines[j] and "Saldo" not in lines[j] and "Total" not in lines[j]:
                    match = re.search(r"\$ ([0-9\.,]+)", lines[j])
                    if match:
                        data["sueldo_neto"] = match.group(1)
                        break
            break
    
    # Extraer saldos
    for i, line in enumerate(lines):
        if "Saldo Inicial" in line:
            for j in range(i+1, min(i+5, len(lines))):
                if lines[j].startswith("$"):
                    match = re.search(r"([0-9\.,]+)", lines[j])
                    if match:
                        data["saldos"]["inicial"] = match.group(1)
                        break
        
        if "Saldo total al" in line:
            for j in range(i, min(i+30, len(lines))):
                if "Total en pesos" in lines[j]:
                    for k in range(j+1, min(j+5, len(lines))):
                        if lines[k].startswith("$"):
                            match = re.search(r"([0-9\.,]+)", lines[k])
                            if match:
                                data["saldos"]["final"] = match.group(1)
                                break
                    break
            break
    
    # Extraer movimientos
    data["movimientos"] = extraer_movimientos(lines)
    
    return data

def generar_markdown(data):
    """Genera un reporte en Markdown."""
    md = f"""# Extracto Santander - {data['periodo']['inicio']} al {data['periodo']['fin']}

## Datos del Cliente
- **Nombre:** {data['cliente']['nombre']}
- **CUIT:** {data['cliente']['cuit']}
- **CBU:** {data['cliente']['cbu']}

## Resumen Financiero
- **Saldo Inicial:** $ {data['saldos']['inicial'] if data['saldos']['inicial'] else 'N/A'}
- **Saldo Final:** $ {data['saldos']['final'] if data['saldos']['final'] else 'N/A'}
- **Sueldo Neto:** $ {data['sueldo_neto'] if data['sueldo_neto'] else 'N/A'}

## Estadísticas
- **Total movimientos:** {len(data['movimientos'])}
- **Total débitos:** $ {sum(limpiar_monto(m['debito']) for m in data['movimientos'] if m['debito']):,.2f}
- **Total créditos:** $ {sum(limpiar_monto(m['credito']) for m in data['movimientos'] if m['credito']):,.2f}

## Movimientos

| Fecha | Comprobante | Descripción | Débito | Crédito |
|-------|-------------|-------------|---------|----------|
"""
    
    for mov in data["movimientos"][:50]:  # Mostrar primeros 50
        deb = f"$ {mov['debito']}" if mov['debito'] else ""
        cred = f"$ {mov['credito']}" if mov['credito'] else ""
        md += f"| {mov['fecha']} | {mov['comprobante']} | {mov['descripcion'][:40]} | {deb} | {cred} |\n"
    
    if len(data["movimientos"]) > 50:
        md += f"\n*... y {len(data['movimientos']) - 50} movimientos más.*\n"
    
    return md

def main():
    import sys
    
    if len(sys.argv) < 2:
        print("Uso: python parser_final.py <archivo_txt>")
        sys.exit(1)
    
    txt_file = sys.argv[1]
    
    if not os.path.exists(txt_file):
        print(f"Error: No existe el archivo {txt_file}")
        sys.exit(1)
    
    print(f"Procesando: {txt_file}\n")
    
    data = parsear_extracto(txt_file)
    
    # Imprimir resumen
    print("=" * 80)
    print(f"EXTRACTO: {data['periodo']['inicio']} al {data['periodo']['fin']}")
    print("=" * 80)
    print(f"Sueldo neto: ${data['sueldo_neto']}")
    print(f"Saldo inicial: ${data['saldos']['inicial']}")
    print(f"Saldo final: ${data['saldos']['final']}")
    print(f"Total movimientos: {len(data['movimientos'])}")
    print()
    
    # Generar Markdown
    md = generar_markdown(data)
    
    # Guardar a archivo
    output_file = txt_file.replace(".txt", ".md")
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(md)
    
    print(f"✓ Reporte Markdown guardado en: {output_file}")
    print(f"✓ Primeros movimientos:\n")
    
    # Mostrar primeros 5 movimientos
    for mov in data["movimientos"][:5]:
        print(f"  {mov['fecha']} | {mov['descripcion'][:40]:<40} | -${mov['debito'] if mov['debito'] else ''}{'$' + mov['credito'] if mov['credito'] else ''}")

if __name__ == "__main__":
    main()
