# santander2md

Parser para extractos de Santander Argentina que los convierte a Markdown, CSV o JSON.

## Instalación

```bash
pip install -e .
```

## Uso

### Línea de comandos

```bash
# Parsear un extracto individual
santander2md parse -i extracto.pdf -o reporte.md

# Procesar múltiples extractos
santander2md batch -i ./data -o ./output -f md
```

### Como librería

```python
from santander2md import SantanderParser, Exporter

# Parsear
parser = SantanderParser("extracto.pdf")
extracto = parser.parse()

# Exportar a Markdown
md = Exporter.to_markdown(extracto)
print(md)

# Guardar a archivo
Exporter.to_markdown(extracto, "reporte.md")
Exporter.to_csv(extracto, "movimientos.csv")
Exporter.to_json(extracto, "extracto.json")
```

## Estructura del Proyecto

```
santander2md/
├── santander2md/      # Código fuente
│   ├── __init__.py
│   ├── parser.py      # Parser principal
│   ├── models.py      # Dataclasses
│   ├── exporter.py    # Exportadores
│   ├── utils.py       # Utilidades
│   └── cli.py         # CLI
├── tests/             # Tests
├── examples/          # Ejemplos
├── setup.py          # Instalación
└── README.md        # Este archivo
```

## Desarrollo

```bash
# Instalar dependencias
pip install -r requirements.txt

# Ejecutar tests
pytest tests/ -v

# Formatear código
ruff format .

# Linting
ruff check .
```

## Licencia

MIT
