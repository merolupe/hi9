"""Linha de comando da central.

    central [--porta N] [--sem-navegador]

Sem argumento, abre a janela no navegador — que é o caminho de quem não usa
terminal, e o que `Hinove.bat` faz com dois cliques.
"""
from __future__ import annotations

import argparse

from .servidor import abrir


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="central",
        description="Central de Ferramentas Fiscais da Hinove Agrociência.",
    )
    parser.add_argument("--porta", type=int, default=0,
                        help="porta fixa; por padrão o sistema escolhe uma livre")
    parser.add_argument("--sem-navegador", action="store_true",
                        help="não abre o navegador sozinho; só mostra o endereço")
    args = parser.parse_args(argv)
    return abrir(porta=args.porta, navegador=not args.sem_navegador)


if __name__ == "__main__":
    raise SystemExit(main())
