# PLAN: santander2md

## Objetivo
Crear una librería Python para parsear extractos de Santander Argentina y convertirlos a Markdown.

## Arquitectura

```
santander2md/
├── santander2md/
│   ├── __init__.py
│   ├── parser.py          # Parser principal de PDFs
│   ├── models.py         # Modelos de datos (dataclasses)
│   ├── exporter.py       # Exporta a MD, CSV, JSON
│   └── utils.py          # Utilidades
├── tests/
│   └── test_parser.py
├── examples/
│   └── basic_usage.py
├── setup.py              # Para instalar como paquete
├── requirements.txt
└── README.md
```

## SDD Cycles

### Cycle 1: Parser básico (PDF → Datos estructurados)
- [ ] Crear `models.py` con dataclasses
- [ ] Implementar `parser.py` usando `pdfplumber`
- [ ] Extraer: período, cliente, saldos, sueldo, movimientos
- [ ] Tests básicos

### Cycle 2: Exportadores (Datos → Markdown/CSV/JSON)
- [ ] Implementar `exporter.py`
- [ ] Template de Markdown
- [ ] Exportar a CSV y JSON

### Cycle 3: CLI y empaquetado
- [ ] Crear CLI (`__main__.py`)
- [ ] Configurar `setup.py` para instalar como paquete
- [ ] Documentación en README

### Cycle 4: Refinamiento y tests
- [ ] Manejo de errores
- [ ] Soporte para múltiples extractos (batch)
- [ ] Tests de integración

## Stack Técnico
- **PDF parsing:** `pdfplumber` (mejor que `pdftotext`)
- **Data structures:** `dataclasses`
- **Export:** `jinja2` para templates MD
- **CLI:** `argparse` o `click`

## Dependencias (requirements.txt)
```
pdfplumber>=0.9.0
jinja2>=3.1.0
click>=8.0.0
```

## Próximo paso
Arrancar con Cycle 1: Crear `models.py` y `parser.py`.
