# santander2md

Herramienta para parsear extractos bancarios de Santander Argentina y convertirlos a Markdown.

## Características

- Parsea PDFs de extractos de Santander
- Extrae datos estructurados: ingresos, gastos, saldos, movimientos
- Genera reportes en Markdown
- Exporta a CSV/JSON para análisis
- Calcula capacidad de ahorro

## Uso

```bash
python santander2md.py --input ~/Downloads/finanzas_analisis/ --output ./output/
```

## Estructura

```
santander2md/
├── santander2md.py    # Parser principal
├── analyzer.py         # Análisis de datos financieros
├── exporter.py         # Exporta a MD, CSV, JSON
├── templates/         # Templates de Markdown
└── output/           # Reportes generados
```
