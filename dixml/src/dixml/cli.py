"""Linha de comando do DiXML.

    dixml <lote.zip> [outro.zip ...] [--saida PASTA]

Quem não usa terminal não precisa disto: a ferramenta está na janela da
central, em `Hinove.bat`. A linha de comando serve para automação e para
conferir um lote grande sem abrir o navegador.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .extracao import escrever, extrair, nome_sugerido
from .pacote import PacoteGrandeDemais

LARGURA = 66


def _listar(titulo: str, itens: list[str], teto: int = 20) -> None:
    if not itens:
        return
    print(f"\n{titulo}")
    print("─" * min(LARGURA, len(titulo)))
    for item in itens[:teto]:
        print(f"  · {item}")
    if len(itens) > teto:
        print(f"  ... e mais {len(itens) - teto}.")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="dixml",
        description="Transforma um lote de XML de nota (NF-e e CT-e) em planilha.",
    )
    parser.add_argument("pacotes", nargs="+", help="um ou mais arquivos .zip")
    parser.add_argument("--saida", default=".", help="pasta de destino (padrão: atual)")
    args = parser.parse_args(argv)

    caminhos = [Path(p) for p in args.pacotes]
    faltando = [str(c) for c in caminhos if not c.is_file()]
    if faltando:
        print("\nArquivo não encontrado:", *faltando, sep="\n  · ", file=sys.stderr)
        return 2

    print(f"\nDiXML {__version__} — XML de nota para planilha")
    print("─" * LARGURA)
    for caminho in caminhos:
        print(f"  {caminho}")

    try:
        resultado = extrair(caminhos, progresso=lambda n: print(f"  ...{n} XMLs lidos"))
    except PacoteGrandeDemais as erro:
        print(f"\n{erro}\n", file=sys.stderr)
        return 2

    print()
    for linha in resultado.resumo():
        print(f"  {linha}")

    _listar("Não reconhecidos", resultado.nao_reconhecidos)
    _listar("Com erro de leitura", resultado.com_erro)
    _listar("Pacotes ilegíveis", resultado.pacotes_com_erro)

    destino = Path(args.saida) / nome_sugerido()
    escrever(resultado, destino)
    print(f"\nGerado: {destino}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
