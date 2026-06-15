"""Tests para exporter.py."""

import tempfile
import json
import os

from santander2md.models import Movimiento, Extracto
from santander2md.exporter import Exporter


class TestExporter:
    def setup_method(self):
        self.mov = Movimiento("01/05/26", "Pago de haberes", credito=1510287.57)
        self.ext = Extracto(
            periodo_inicio="01/05/26",
            periodo_fin="28/05/26",
            cliente_nombre="JUAN MANUEL DAZA",
            cliente_cuit="20-12345678-9",
            saldo_inicial=1917722.21,
            saldo_final=1510287.57,
            sueldo_neto=1510287.57,
            movimientos=[self.mov],
        )

    def test_to_markdown(self):
        md = Exporter.to_markdown(self.ext)
        assert "JUAN MANUEL DAZA" in md
        assert "01/05/26" in md
        assert "Pago de haberes" in md

    def test_to_csv(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            csv_path = f.name
        try:
            Exporter.to_csv(self.ext, csv_path)
            with open(csv_path) as f:
                content = f.read()
            assert "fecha" in content
            assert "01/05/26" in content
        finally:
            os.unlink(csv_path)

    def test_to_json(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json_path = f.name
        try:
            Exporter.to_json(self.ext, json_path)
            with open(json_path) as f:
                data = json.load(f)
            assert data["cliente_nombre"] == "JUAN MANUEL DAZA"
        finally:
            os.unlink(json_path)
