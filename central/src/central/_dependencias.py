"""O que a central precisa ter ao alcance do import: `vendor/` e as ferramentas.

A central é a única parte do repositório que conhece o repositório inteiro —
é o trabalho dela. Cada ferramenta vive em `<projeto>/src/<pacote>`, e é isso
que esta função põe no `sys.path`, junto com as bibliotecas embarcadas de
`vendor/` (ver `vendor/LEIA-ME.md`).

Nenhuma ferramenta importa outra. Quem costura é a central, e só ela.
"""
from __future__ import annotations

import sys
from pathlib import Path


def _raiz() -> Path:
    for pasta in Path(__file__).resolve().parents:
        if (pasta / "vendor" / "openpyxl").is_dir():
            return pasta
    return Path(__file__).resolve().parents[3]


RAIZ = _raiz()
VENDOR = RAIZ / "vendor"


def _acrescentar(caminho: Path) -> None:
    texto = str(caminho)
    if caminho.is_dir() and texto not in sys.path:
        sys.path.append(texto)


def preparar() -> None:
    """Bibliotecas embarcadas e ferramentas, sempre no **fim** do `sys.path`.

    No fim, e não no começo: se o administrador instalou alguma dessas
    bibliotecas na máquina, é a dele que vale.
    """
    _acrescentar(VENDOR)
    for projeto in sorted(RAIZ.iterdir()):
        if projeto.is_dir() and (projeto / "src").is_dir():
            _acrescentar(projeto / "src")


preparar()
