"""Põe as bibliotecas embarcadas ao alcance do import.

As bibliotecas de terceiros vivem em `vendor/`, na raiz do repositório, e são
as mesmas para todas as ferramentas. O porquê está em `vendor/LEIA-ME.md`:
resumido, a máquina do time fiscal não instala nada.

A pasta entra no **fim** do `sys.path` — se o administrador já tiver instalado
a biblioteca na máquina, é a dele que vale.
"""
from __future__ import annotations

import sys
from pathlib import Path


def _localizar() -> Path:
    for pasta in Path(__file__).resolve().parents:
        candidata = pasta / "vendor"
        if (candidata / "openpyxl").is_dir():
            return candidata
    return Path(__file__).resolve().parents[3] / "vendor"


VENDOR = _localizar()


def preparar() -> None:
    caminho = str(VENDOR)
    if VENDOR.is_dir() and caminho not in sys.path:
        sys.path.append(caminho)


preparar()
