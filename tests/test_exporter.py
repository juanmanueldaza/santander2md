"""Tests para exporter.py."""

import json
from pathlib import Path

from santander2md.exporter import to_markdown, to_csv, to_json
from santander2md.models import Movimiento, Extracto


class TestExporter:
    def setup_method(self) -> None:
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

    def test_to_markdown(self) -> None:
        md = to_markdown(self.ext)
        assert "JUAN MANUEL DAZA" in md
        assert "01/05/26" in md
        assert "Pago de haberes" in md

    def test_to_csv(self, tmp_path: Path) -> None:
        csv_path = tmp_path / "test.csv"
        to_csv(self.ext, str(csv_path))
        content = csv_path.read_text(encoding="utf-8")
        assert "fecha" in content
        assert "01/05/26" in content
        # Verify mov.monto is used (should be 1510287.57)
        assert "1510287.57" in content

    def test_to_json(self, tmp_path: Path) -> None:
        json_path = tmp_path / "test.json"
        to_json(self.ext, str(json_path))
        data = json.loads(json_path.read_text(encoding="utf-8"))
        assert data["cliente_nombre"] == "JUAN MANUEL DAZA"
