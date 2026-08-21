"""Linha de comando do Apurabot.

    apurabot base-tratada <livro_fiscal.xlsx> [--saida PASTA] [--parametros PASTA]

A interface para o time fiscal é a janela local; esta CLI é a porta de entrada
do motor, usada por ela e pelos testes.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .base_tratada import tratar
from .ingestao import LayoutInvalido
from .saida import escrever


def _comando_base_tratada(args: argparse.Namespace) -> int:
    try:
        base = tratar(args.livro, parametros=args.parametros, aba=args.aba)
    except LayoutInvalido as erro:
        print(f"\nErro de layout no Livro Fiscal:\n\n{erro}\n", file=sys.stderr)
        return 2
    except FileNotFoundError as erro:
        print(f"\n{erro}\n", file=sys.stderr)
        return 2

    resumo = base.resumo()
    destino = Path(args.saida) / f"Base_Tratada_{resumo['competencia']}.xlsx"
    escrever(base, destino)

    print(f"Competência ................. {resumo['competencia']}")
    print(f"Linhas no Livro Fiscal ...... {resumo['linhas_no_livro']:,}".replace(",", "."))
    print(f"Linhas relevantes p/ ICMS ... {resumo['linhas_relevantes']:,}".replace(",", "."))
    print(f"Alertas ..................... {resumo['alertas']}")
    print(f"Pendências .................. {resumo['pendencias']}")
    if base.com_pendencia:
        print("\nEncerramento BLOQUEADO. Primeiras pendências:")
        for t in base.com_pendencia[:5]:
            print(f"  linha {t.origem.linha_origem}: {t.pendencias[0]}")
        if len(base.com_pendencia) > 5:
            print(f"  ... e mais {len(base.com_pendencia) - 5}. Ver a aba PENDÊNCIAS.")
    else:
        print("\nSem pendências — encerramento liberado.")
    print(f"\nGerado: {destino}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="apurabot", description="Apuração mensal de ICMS da Hinove Agrociência."
    )
    sub = parser.add_subparsers(dest="comando", required=True)

    p = sub.add_parser("base-tratada", help="Trata o Livro Fiscal (camadas 1 a 4).")
    p.add_argument("livro", help="Livro Fiscal do mês (.xlsx ou .xls)")
    p.add_argument("--saida", default=".", help="pasta de destino (padrão: atual)")
    p.add_argument("--parametros", default=None, help="pasta de parâmetros")
    p.add_argument("--aba", default=None, help="força uma aba específica do arquivo")
    p.set_defaults(func=_comando_base_tratada)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
