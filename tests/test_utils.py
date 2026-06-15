"""Tests for santander2md.utils."""

import pytest
from santander2md.utils import parse_monto_argentino


class TestParseMontoArgentino:
    @pytest.mark.parametrize("input_str,expected", [
        ("$ 1.510.287,57", 1510287.57),
        ("-$ 113.800,00", -113800.00),
        ("1.510.287,57", 1510287.57),
        ("1.510.28757", 1510287.57),
        ("$1.510.28757", 1510287.57),
        ("U$S 363,28", 363.28),
        ("1510287.57", 1510287.57),
        ("1510287,57", 1510287.57),
        ("$ 0,00", 0.0),
        ("$ 25.000,00", 25000.0),
        ("-$ 535.539,94", -535539.94),
    ])
    def test_formats(self, input_str, expected):
        assert parse_monto_argentino(input_str) == pytest.approx(expected)

    @pytest.mark.parametrize("input_str", ["", None, "   ", "abc", "N/A"])
    def test_invalid(self, input_str):
        assert parse_monto_argentino(input_str) is None

