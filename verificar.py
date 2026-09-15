#!/usr/bin/env python3
"""Este Python consegue rodar as ferramentas fiscais?

Sai com 0 quando sim, 1 quando não. Serve para o `Hinove.bat` escolher entre
os vários Python que costumam conviver numa máquina, testando em vez de
adivinhar pelo nome do comando.

Rodando à mão, explica o que faltou:

    python verificar.py
"""
from __future__ import annotations

import sys
from pathlib import Path

MINIMO = (3, 10)
RAIZ = Path(__file__).resolve().parent
sys.path.insert(0, str(RAIZ / "central" / "src"))

#: As ferramentas que precisam carregar. A central põe as demais ao alcance
#: do import, então ela vem primeiro.
FERRAMENTAS = ("central", "apurabot", "dixml", "fiscalbot", "pendentes")

#: As bibliotecas embarcadas em `vendor/`.
BIBLIOTECAS = ("yaml", "openpyxl", "xlrd")


def problemas() -> list[str]:
    achados = []
    if sys.version_info < MINIMO:
        atual = ".".join(str(n) for n in sys.version_info[:3])
        achados.append(
            f"Python {atual} — as ferramentas precisam do "
            f"{MINIMO[0]}.{MINIMO[1]} ou mais novo."
        )
        return achados                      # sem versão, o resto nem importa

    for nome in FERRAMENTAS:
        try:
            # Importar já é o efeito: a central põe `vendor/` e as demais
            # ferramentas ao alcance do import.
            __import__(nome)
        except Exception as erro:           # noqa: BLE001
            achados.append(f"não consegui carregar {nome!r}: {erro}")

    if achados:
        return achados                      # sem as ferramentas, o resto não roda

    for nome in BIBLIOTECAS:
        try:
            __import__(nome)
        except ImportError:
            achados.append(f"falta a biblioteca {nome!r}")
    return achados


def main() -> int:
    achados = problemas()
    if not achados:
        print(f"OK — {sys.executable}")
        return 0
    print(f"Este Python não serve: {sys.executable}\n", file=sys.stderr)
    for achado in achados:
        print(f"  · {achado}", file=sys.stderr)
    print(
        "\nAs bibliotecas viajam junto do código, em `vendor/`, na raiz da pasta.\n"
        "Se elas sumiram, baixe a pasta de novo — inteira.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
