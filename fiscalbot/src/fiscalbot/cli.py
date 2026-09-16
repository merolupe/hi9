"""Linha de comando do Fiscalbot.

    fiscalbot <Movimento_Livros_Fiscais.xls> [--saida PASTA]

Quem não usa terminal não precisa disto: a ferramenta está na janela da
Central, em `Hinove.bat`. A linha de comando serve para automação.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from . import base as bases
from .execucao import auditar, escrever, nome_sugerido
from .planilha import LayoutInvalido

LARGURA = 66


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="fiscalbot",
        description="Auditoria do Livro Fiscal de ICMS da Hinove Agrociência.",
    )
    parser.add_argument("relatorio", help="Movimento Livros Fiscais (.xls ou .xlsx)")
    parser.add_argument("--saida", default=".", help="pasta de destino (padrão: atual)")
    args = parser.parse_args(argv)

    print(f"\nFiscalbot {__version__} — auditoria do Livro Fiscal")
    print("─" * LARGURA)

    base = bases.carregar()
    try:
        resultado = auditar(Path(args.relatorio), base,
                            progresso=lambda n: print(f"  ...{n} registros"))
    except (LayoutInvalido, FileNotFoundError) as erro:
        print(f"\n{erro}\n", file=sys.stderr)
        return 2

    print()
    for linha in resultado.resumo():
        print(f"  {linha}")

    faltando = resultado.colunas_nao_encontradas
    if faltando:
        print(f"\n  Colunas opcionais ausentes: {', '.join(faltando)}")
        print("  As camadas que dependem delas não rodaram.")

    print("\nOcorrências por dimensão")
    print("─" * 24)
    for rotulo, quantos in resultado.por_dimensao():
        print(f"  {rotulo:<16}{quantos:>6}")

    manuais = resultado.manuais_por_operacao()
    if manuais:
        print("\nValidação manual, por operação")
        print("─" * 30)
        for operacao, quantos in manuais[:15]:
            print(f"  {operacao[:44]:<46}{quantos:>5}")
        if len(manuais) > 15:
            print(f"  ... e mais {len(manuais) - 15} operações.")

    destino = Path(args.saida) / nome_sugerido(resultado.arquivo)
    escrever(resultado, destino)
    print(f"\nGerado: {destino}")
    return 0 if not resultado.advertencias else 1


if __name__ == "__main__":
    raise SystemExit(main())
