"""Linha de comando das notas pendentes.

    pendentes mercadorias <XML> <Conferência de Entradas> [semana anterior]
                          [--saida PASTA]
    pendentes servicos <ASIS> <Portal de Compras> [Conferência] [semana anterior]
                       [--saida PASTA]
    pendentes resumo <relatório da semana, já classificado> [--saida PASTA]
    pendentes conhecimento <parceiros.csv> <regras.json>   ← importa a base
    pendentes conhecimento <relatório classificado.xlsx>   ← mede a base

Os arquivos entram **em qualquer ordem**: cada um é reconhecido pelo próprio
cabeçalho, não pelo nome nem pela posição na linha de comando. Quem não usa
terminal não precisa disto — as duas ferramentas estão na janela da Central,
em `Hinove.bat`. A linha de comando serve para automação e para conferir uma
execução sem abrir o navegador.

O `resumo` é a terceira, e vem **depois** das outras duas: ele lê a planilha
que elas geraram, já remodelada e classificada, e devolve o painel dentro
dela. Rodar antes da classificação fechar publica número que ainda vai mudar.

As três rotinas devolvem a mesma coisa para a tela — título, fichas e listas —,
e é por isso que a impressão aqui é uma só. O código de saída também: `1`
quando a semana ficou **não encerrável**, porque há item que exige revisão
manual, e `2` quando a execução nem chegou a gerar planilha.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .cabecalho import CabecalhoNaoEncontrado, ColunasFaltando
from .papeis import PapelAmbiguo, PapelAusente, PapelDuplicado
from .planilha import EXTENSOES, PlanilhaIlegivel

LARGURA = 66


def _imprimir(resultado) -> None:
    """O painel da execução, em texto — o mesmo que a janela mostra em HTML."""
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
    if resultado.pasta_do_snapshot:
        print(f"Semana gravada em: {resultado.pasta_do_snapshot}")
    if not resultado.encerravel:
        print("\nA semana ficou como NÃO encerrável: há itens acima que "
              "exigem revisão manual.")


def _conhecimento(args) -> int:
    """Importa a base, ou a mede contra um relatório já classificado.

    Qual das duas coisas acontece é decidido pelo **conteúdo** do que chega,
    como tudo no resto do projeto: planilha é gabarito, `.csv` e `.json` são
    fonte. Misturar os dois na mesma chamada é erro, e é dito.
    """
    from .conhecimento import base as conhecido
    from .conhecimento.importacao import ArquivoNaoReconhecido, importar
    from .conhecimento.simulacao import SemRelatorioClassificado, simular

    planilhas = [a for a in args.arquivos if Path(a).suffix.lower() in EXTENSOES]
    try:
        if planilhas and len(planilhas) == len(args.arquivos):
            resultado = simular(planilhas, conhecido.carregar())
        elif planilhas:
            print("\nNão misture as fontes da base com o relatório que a mede: "
                  "são duas chamadas.\n", file=sys.stderr)
            return 2
        else:
            resultado = importar(args.arquivos)
    except (ArquivoNaoReconhecido, SemRelatorioClassificado,
            PlanilhaIlegivel, FileNotFoundError) as erro:
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
    caminho = getattr(resultado, "caminho", None)
    if caminho:
        print(f"\nBase gravada em: {caminho}")
    return 0


def _executar(dominio: str, args) -> int:
    if dominio == "resumo":
        from .resumo.execucao import SemRelatorio as SemRegistros
        from .resumo.execucao import gerar

        class Invalido(Exception):
            """Só mercadorias tem tabela de roteamento para estar inválida."""
    elif dominio == "mercadorias":
        from .mercadorias.execucao import SemRegistros, gerar
        from .mercadorias.roteamento import RoteamentoInvalido as Invalido
    else:
        from .servicos.execucao import SemRegistros, gerar

        class Invalido(Exception):
            """Só mercadorias tem tabela de roteamento para estar inválida."""

    try:
        resultado = gerar(args.arquivos, Path(args.saida))
    except (PapelAusente, PapelDuplicado, PapelAmbiguo, ColunasFaltando,
            CabecalhoNaoEncontrado, PlanilhaIlegivel, SemRegistros, Invalido,
            FileNotFoundError) as erro:
        print(f"\n{erro}\n", file=sys.stderr)
        return 2

    _imprimir(resultado)
    return 0 if resultado.encerravel else 1


#: O que cada rotina precisa receber para ter o que fazer.
EXIGIDOS = {
    "mercadorias": "Informe pelo menos o relatório de importação de XML e a "
                   "Conferência de Entradas.",
    "servicos": "Informe pelo menos o ASIS e o Portal de Compras.",
    "resumo": "Informe a planilha da semana — a que as outras duas geraram, "
              "já classificada.",
    "conhecimento": "Informe os dois arquivos da base (`.csv` e `.json`) — ou "
                    "uma planilha já classificada, para medir a base contra "
                    "ela.",
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="pendentes",
        description="Notas emitidas contra a Hinove que ainda não têm entrada.",
    )
    parser.add_argument(
        "dominio", choices=("servicos", "mercadorias", "resumo", "conhecimento"),
        help="qual das três rotinas semanais, ou a base de conhecimento")
    parser.add_argument("arquivos", nargs="*",
                        help="os relatórios da semana, em qualquer ordem")
    parser.add_argument("--saida", default=".",
                        help="pasta de destino (padrão: atual)")
    args = parser.parse_args(argv)

    print(f"\nPendentes {__version__} — notas pendentes de entrada")

    if not args.arquivos:
        print(f"\n{EXIGIDOS[args.dominio]}\n", file=sys.stderr)
        return 2
    if args.dominio == "conhecimento":
        return _conhecimento(args)
    return _executar(args.dominio, args)


if __name__ == "__main__":
    raise SystemExit(main())
