"""Linha de comando das notas pendentes.

    pendentes servicos <ASIS> <Portal de Compras> [Conferência] [semana anterior]
                       [--saida PASTA]

Os arquivos entram **em qualquer ordem**: cada um é reconhecido pelo próprio
cabeçalho, não pelo nome nem pela posição na linha de comando. Quem não usa
terminal não precisa disto — as duas ferramentas estão na janela da Central,
em `Hinove.bat`. A linha de comando serve para automação e para conferir uma
execução sem abrir o navegador.

O motor de mercadorias ainda não existe; `pendentes mercadorias` responde
dizendo isso, em vez de fingir que roda.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .cabecalho import CabecalhoNaoEncontrado, ColunasFaltando
from .papeis import PapelAmbiguo, PapelAusente, PapelDuplicado
from .planilha import PlanilhaIlegivel

LARGURA = 66

AINDA_NAO = """
O motor de mercadorias (GerarPendentes) ainda não foi portado. O que já está
no repositório é o núcleo comum das duas rotinas e o motor de serviços.

O plano, com o que trava o quê, está em docs/pendentes/04-plano-de-entrega.md.
"""


def _servicos(args) -> int:
    from .servicos.execucao import SemRegistros, gerar

    try:
        resultado = gerar(args.arquivos, Path(args.saida))
    except (PapelAusente, PapelDuplicado, PapelAmbiguo, ColunasFaltando,
            CabecalhoNaoEncontrado, PlanilhaIlegivel, SemRegistros,
            FileNotFoundError) as erro:
        print(f"\n{erro}\n", file=sys.stderr)
        return 2

    print(f"\n{resultado.titulo()}")
    print("─" * LARGURA)
    for rotulo, valor in resultado.fichas():
        print(f"  {rotulo:<28}{valor:>8}")

    for titulo, itens, tom in resultado.listas():
        marca = {"erro": "!", "atencao": "·", "neutro": " "}.get(tom, " ")
        print(f"\n{titulo}")
        print("─" * len(titulo))
        for item in itens:
            print(f"  {marca} {item}")

    print(f"\nGerado: {resultado.planilha}")
    print(f"Semana gravada em: {resultado.pasta_do_snapshot}")
    if not resultado.encerravel:
        print("\nA semana ficou como NÃO encerrável: há itens acima que "
              "exigem revisão manual.")
    return 0 if resultado.encerravel else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="pendentes",
        description="Notas emitidas contra a Hinove que ainda não têm entrada.",
    )
    parser.add_argument("dominio", choices=("servicos", "mercadorias"),
                        help="qual das duas rotinas semanais")
    parser.add_argument("arquivos", nargs="*",
                        help="os relatórios da semana, em qualquer ordem")
    parser.add_argument("--saida", default=".",
                        help="pasta de destino (padrão: atual)")
    args = parser.parse_args(argv)

    print(f"\nPendentes {__version__} — notas pendentes de entrada")

    if args.dominio == "mercadorias":
        print(AINDA_NAO)
        return 2
    if not args.arquivos:
        print("\nInforme pelo menos o ASIS e o Portal de Compras.\n",
              file=sys.stderr)
        return 2
    return _servicos(args)


if __name__ == "__main__":
    raise SystemExit(main())
