"""SantanderParser orchestrator: extracts, splits, dispatches, assembles."""

from __future__ import annotations

import re
from pathlib import Path

from santander2md.models import Extracto
from santander2md.parsers.categorias import _parse_categorias_gasto
from santander2md.parsers.cuotas_vencer import _parse_cuotas_vencer
from santander2md.parsers.detalle_impositivo import _parse_detalle_impositivo
from santander2md.parsers.errors import ParseError
from santander2md.parsers.extraction import PDFExtractor, PopplerPDFExtractor
from santander2md.parsers.line_parser import _re_first
from santander2md.parsers.metadata import (
    _extract_nombre,
    _parse_saldo_final,
    _parse_saldo_inicial,
    _parse_sueldo,
)
from santander2md.parsers.movimientos_dolares import _parse_movimientos_dolares
from santander2md.parsers.movimientos_pesos import _parse_movimientos
from santander2md.parsers.pagos import _parse_pagos
from santander2md.parsers.plan_v import _parse_plan_v
from santander2md.parsers.prestamos import _parse_prestamos
from santander2md.parsers.productos import _parse_productos
from santander2md.parsers.sections import _split_sections
from santander2md.parsers.tarjeta_credito import _parse_tarjeta_credito
from santander2md.parsers.tarjeta_debito import _parse_debito


class SantanderParser:
    """Parser principal para extractos de Santander Argentina."""

    def __init__(
        self, pdf_path: str, pdf_extractor: PDFExtractor | None = None
    ) -> None:
        if not isinstance(pdf_path, str) or not pdf_path.strip():
            raise ValueError("pdf_path debe ser una ruta no vacía")
        if not pdf_path.lower().endswith(".pdf"):
            raise ValueError("pdf_path debe terminar en .pdf")
        self.pdf_path = pdf_path
        if pdf_extractor is not None:
            self._extractor = pdf_extractor
        else:
            self._extractor = PopplerPDFExtractor()

    def parse(self) -> Extracto:
        path = Path(self.pdf_path)
        if not path.exists():
            raise FileNotFoundError(f"No existe: {self.pdf_path}")

        full_text = self._extractor.extract(path)

        if not full_text:
            raise ParseError("No se pudo extraer texto del PDF")

        sections = _split_sections(full_text)

        periodo_inicio = _re_first(full_text, r"Desde:\s*(\d{2}/\d{2}/\d{2})")
        periodo_fin = _re_first(full_text, r"Hasta:\s*(\d{2}/\d{2}/\d{2})")
        if periodo_inicio == "N/A":
            m = re.search(
                r"CUENTA:.*?(\d{2}/\d{2}/\d{2})\s*[-–]\s*(\d{2}/\d{2}/\d{2})",
                full_text,
            )
            if m:
                periodo_inicio = m.group(1)
                periodo_fin = m.group(2)

        standalone_cuotas = _parse_cuotas_vencer(sections.get("cuotas_vencer", ""))

        extracto = Extracto(
            periodo_inicio=periodo_inicio,
            periodo_fin=periodo_fin,
            cliente_nombre=_extract_nombre(full_text),
            cliente_cuit=_re_first(full_text, r"CUIT:\s*([\d-]+)"),
            saldo_inicial=_parse_saldo_inicial(full_text),
            saldo_final=_parse_saldo_final(full_text),
            sueldo_neto=_parse_sueldo(full_text),
            movimientos=_parse_movimientos(full_text),
            movimientos_dolares=_parse_movimientos_dolares(
                sections.get("movimientos_dolares", "")
            ),
            categorias_gasto=_parse_categorias_gasto(
                sections.get("categorias_gasto", "")
            ),
            detalle_impositivo=_parse_detalle_impositivo(
                sections.get("detalle_impositivo", "")
            ),
            tarjeta_credito=_parse_tarjeta_credito(sections.get("tarjeta_credito", "")),
            tarjeta_debito=_parse_debito(sections.get("tarjeta_debito", "")),
            pagos=_parse_pagos(sections.get("pagos", "")),
            productos=_parse_productos(sections.get("resumen_productos", "")),
            plan_v=_parse_plan_v(sections.get("plan_v", "")),
            prestamos=_parse_prestamos(sections.get("prestamos", "")),
            cuotas_vencer=standalone_cuotas,
        )

        if extracto.tarjeta_credito and standalone_cuotas:
            extracto.tarjeta_credito.cuotas_vencer = standalone_cuotas

        return extracto
