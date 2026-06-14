"""
santander2md - Parser para extractos de Santander Argentina.
"""

__version__ = "0.1.0"
__author__ = "Juan Manuel Daza"

from santander2md.parsers.santander_txt import SantanderTXTParser
from santander2md.models.extracto import Extracto, Movimiento

__all__ = ["SantanderTXTParser", "Extracto", "Movimiento"]
