"""Tests for santander2md.utils."""

import pytest
from santander2md.utils import parse_monto_argentino


class TestParseMontoArgentino:
    @pytest.mark.parametrize("input_str,expected", [
        # Standard Argentinian: dots=thousands, comma=decimal
        ("$ 1.510.287,57", 1510287.57),
        ("-$ 113.800,00", -113800.00),
        ("1.510.287,57", 1510287.57),
        ("$ 25.000,00", 25000.0),
        ("-$ 535.539,94", -535539.94),
        # Comma lost in extraction: dots=thousands, last 2 chars=cents
        ("1.510.28757", 1510287.57),
        ("$1.510.28757", 1510287.57),
        ("461.04837", 461048.37),       # single dot, comma lost
        ("866.68863", 866688.63),       # single dot, comma lost
        # Multiple dots, last dot is decimal (comma replaced by dot)
        ("100.000.00", 100000.00),
        # Already valid decimal: dot IS decimal
        ("U$S 363,28", 363.28),
        ("1510287.57", 1510287.57),
        ("1510287,57", 1510287.57),
        ("363.28", 363.28),
        # Space-as-decimal (comma→space in PDF extraction)
        ("$ 461.048 37", 461048.37),
        ("$ 866.688 63", 866688.63),
        # Zero / edge
        ("$ 0,00", 0.0),
    ])
    def test_formats(self, input_str, expected):
        assert parse_monto_argentino(input_str) == pytest.approx(expected)

    @pytest.mark.parametrize("input_str", ["", None, "   ", "abc", "N/A"])
    def test_invalid(self, input_str):
        assert parse_monto_argentino(input_str) is None

