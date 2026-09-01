#!/usr/bin/env python3
"""Este Python consegue rodar o Apurabot?

Sai com 0 quando sim, 1 quando não. Serve para o `Apurabot.bat` escolher entre
os vários Python que costumam conviver numa máquina, testando em vez de
adivinhar pelo nome do comando.

Rodando à mão, explica o que faltou:

    python verificar.py
"""
from __future__ import annotations

import importlib
import sys
from pathlib import Path

MINIMO = (3, 10)
RAIZ = Path(__file__).resolve().parent
sys.path.insert(0, str(RAIZ / "apurabot" / "src"))


def problemas() -> list[str]:
    achados = []
    if sys.version_info < MINIMO:
        atual = ".".join(str(n) for n in sys.version_info[:3])
        achados.append(
            f"Python {atual} — o Apurabot precisa do {MINIMO[0]}.{MINIMO[1]} ou mais novo."
        )
        return achados                      # sem versão, o resto nem importa

    try:
        # Importar já é o efeito: o pacote põe `vendor/` ao alcance do import.
        importlib.import_module("apurabot")
    except Exception as erro:               # noqa: BLE001
        achados.append(f"não consegui carregar o Apurabot: {erro}")
        return achados

    for nome in ("yaml", "openpyxl", "xlrd"):
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
        "\nAs bibliotecas viajam junto do código, em apurabot/src/apurabot/vendor.\n"
        "Se elas sumiram, baixe a pasta do Apurabot de novo — inteira.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
