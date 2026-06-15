"""
Setup para santander2md. Zero external dependencies.
"""

import os
from setuptools import setup, find_packages

setup(
    name="santander2md",
    version="0.1.0",
    author="Juan Manuel Daza",
    author_email="juan@daza.ar",
    description="Parser para extractos de Santander Argentina a Markdown",
    long_description=open("README.md", encoding="utf-8").read() if os.path.exists("README.md") else "",
    long_description_content_type="text/markdown",
    url="https://github.com/juanmanueldaza/santander2md",
    packages=find_packages(),
    install_requires=[],
    entry_points={
        "console_scripts": [
            "santander2md=santander2md.cli:main",
        ],
    },
    python_requires=">=3.10",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: Python :: 3.14",
    ],
)
