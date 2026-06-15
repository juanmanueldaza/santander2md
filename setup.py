"""
Setup para santander2md. Zero external dependencies.

Canonical package metadata lives in pyproject.toml [project].
This file remains only to expose the dynamic version to setuptools.
"""

from setuptools import setup, find_packages

from santander2md._version import __version__

setup(
    version=__version__,
    packages=find_packages(),
    install_requires=[],
)
