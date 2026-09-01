"""Linha de comando do Apurabot.

    apurabot apurar <livro_fiscal.xlsx> [--saida PASTA]
    apurabot base-tratada <livro_fiscal.xlsx> [--saida PASTA]

`apurar` é a execução mensal: lê o Livro Fiscal, apura o ICMS de cada
estabelecimento e grava o caderno em `.xlsx`. `base-tratada` para no
tratamento, sem apurar — serve para conferir a classificação antes de fechar.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .apuracao import Apuracao, apurar
from .base_tratada import BaseTratada, tratar
from .conferencia import ROTULO_DA_ATIVIDADE
from .erros import FALTA_DE_PARAMETRO, ONDE_CADASTRAR
from .formato import reais
from .ingestao import LayoutInvalido
from .nucleo import atividade as ativ
from .saida import escrever

LARGURA = 66


def _titulo(texto: str) -> None:
    print(f"\n{texto}")
    print("─" * min(LARGURA, len(texto)))


def _campo(rotulo: str, valor: object, largura: int = 30) -> None:
    print(f"{rotulo.ljust(largura, '.')} {valor}")


def _milhar(n: int) -> str:
    return f"{n:,}".replace(",", ".")


def _ler(args: argparse.Namespace) -> BaseTratada | int:
    try:
        return tratar(args.livro, parametros=args.parametros, aba=args.aba)
    except LayoutInvalido as erro:
        print(f"\nErro de layout no Livro Fiscal:\n\n{erro}\n", file=sys.stderr)
        return 2
    except FileNotFoundError as erro:
        print(f"\n{erro}\n", file=sys.stderr)
        return 2


def _cabecalho(base: BaseTratada) -> dict:
    resumo = base.resumo()
    _titulo(f"Apurabot {__version__} — apuração de ICMS")
    _campo("Competência", resumo["competencia"])
    _campo("Período do movimento", resumo["periodo"])
    _campo("Arquivo", resumo["arquivo"])
    _campo("Linhas no Livro Fiscal", _milhar(resumo["linhas_no_livro"]))
    _campo("Linhas relevantes para ICMS", _milhar(resumo["linhas_relevantes"]))
    _campo("Alertas", resumo["alertas"])
    return resumo


def _pendencias(base: BaseTratada, apuracao: Apuracao | None) -> int:
    da_base = base.com_pendencia
    sem_atividade = apuracao.sem_regra_de_atividade if apuracao else []
    total = len(da_base) + len(sem_atividade)

    if not total:
        _titulo("Encerramento liberado")
        print("Nenhuma pendência.")
        return 0

    _titulo(f"Encerramento BLOQUEADO — {total} pendência(s)")
    for t in da_base[:5]:
        print(f"  linha {t.origem.linha_origem}: {t.pendencias[0]}")
    if len(da_base) > 5:
        print(f"  ... e mais {len(da_base) - 5} na aba PENDÊNCIAS.")
    for f in sem_atividade:
        somas = f.atividades_sem_regra
        print(f"  {f.estabelecimento}: {somas.linhas} linha(s) sem atividade definida")
    return total


def _apuracao(apuracao: Apuracao) -> None:
    _titulo("Apuração por estabelecimento")
    print(
        f"  {'estabelecimento':<32}{'UF':<4}{'crédito':>14}{'débito':>14}"
        f"{'saldo':>16}{'a recolher':>14}"
    )
    for f in sorted(apuracao.filiais.values(), key=lambda f: (f.uf, f.estabelecimento)):
        print(
            f"  {f.estabelecimento:<32}{f.uf:<4}{reais(f.credito_mantido):>14}"
            f"{reais(f.debito):>14}{reais(f.saldo):>16}{reais(f.a_recolher):>14}"
        )
    print(
        "\n  Saldo positivo é credor; negativo sai do caixa."
        " O saldo já abre com o crédito do mês anterior."
    )

    _saldo_credor(apuracao)

    por_atividade = [f for f in apuracao.filiais.values() if f.segrega_por_atividade]
    if por_atividade:
        _titulo("Segregação por atividade")
        for f in sorted(por_atividade, key=lambda f: f.estabelecimento):
            print(f"  {f.estabelecimento}")
            for nome in ativ.ORDEM:
                if nome not in f.por_atividade:
                    continue
                t = f.por_atividade[nome]
                rotulo = ROTULO_DA_ATIVIDADE.get(nome, nome)
                print(
                    f"    {rotulo:<22}crédito {reais(t.credito_bruto):>13}   "
                    f"estorno {reais(t.estorno):>13}   débito {reais(t.debito):>13}"
                )

    for f in sorted(apuracao.filiais.values(), key=lambda f: f.estabelecimento):
        if not f.beneficio:
            continue
        _titulo(f"Benefício fiscal — {f.estabelecimento}")
        for passo in f.beneficio.memoria:
            print(f"  {passo}")

    if apuracao.centralizacao:
        _titulo("Centralização")
        for c in apuracao.centralizacao:
            for passo in c.memoria:
                print(f"  {passo}")
            print()

    instrucoes = apuracao.instrucoes_de_centralizacao
    if instrucoes:
        _titulo("Transferências a emitir após o encerramento")
        for instrucao in instrucoes:
            print(f"  {instrucao}")


def _saldo_credor(apuracao: Apuracao) -> None:
    """A conta gráfica não começa do zero — e não termina no fim do mês."""
    com_saldo = [
        f
        for f in sorted(apuracao.filiais.values(), key=lambda f: (f.uf, f.estabelecimento))
        if f.saldo_credor_anterior or f.credor
    ]
    if not com_saldo:
        return

    anterior, seguinte = apuracao.competencia_anterior, apuracao.competencia_seguinte
    _titulo("Saldo credor")
    print(
        f"  {'estabelecimento':<32}{'veio de ' + anterior:>18}"
        f"{'apurado no mês':>18}{'vai para ' + seguinte:>18}"
    )
    for f in com_saldo:
        print(
            f"  {f.estabelecimento:<32}{reais(f.saldo_credor_anterior):>18}"
            f"{reais(f.saldo_do_periodo):>18}{reais(f.credor):>18}"
        )
    if not apuracao.saldos_declarados:
        print(
            f"\n  A abertura de {apuracao.competencia} não está declarada em "
            "parametros/saldos.yaml —\n  a apuração rodou como se todos os "
            "estabelecimentos abrissem o mês zerados."
        )
    print(
        f"\n  A última coluna é a abertura de {seguinte}: cadastre-a em "
        "parametros/saldos.yaml."
    )


def _comando_apurar(args: argparse.Namespace) -> int:
    base = _ler(args)
    if isinstance(base, int):
        return base

    resumo = _cabecalho(base)
    try:
        apuracao = apurar(base)
    except FALTA_DE_PARAMETRO as erro:
        print(f"\nFalta cadastrar uma regra:\n\n{erro}\n", file=sys.stderr)
        print(f"{ONDE_CADASTRAR}\n", file=sys.stderr)
        return 2
    _apuracao(apuracao)
    pendentes = _pendencias(base, apuracao)

    destino = Path(args.saida) / f"Apuracao_{resumo['competencia']}.xlsx"
    escrever(base, destino, apuracao=apuracao)
    print(f"\nGerado: {destino}")
    return 0 if not pendentes else 1


def _comando_base_tratada(args: argparse.Namespace) -> int:
    base = _ler(args)
    if isinstance(base, int):
        return base

    resumo = _cabecalho(base)
    pendentes = _pendencias(base, None)

    destino = Path(args.saida) / f"Base_Tratada_{resumo['competencia']}.xlsx"
    escrever(base, destino)
    print(f"\nGerado: {destino}")
    return 0 if not pendentes else 1


def _comando_janela(args: argparse.Namespace) -> int:
    from .web import abrir

    return abrir(porta=args.porta, navegador=not args.sem_navegador)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="apurabot",
        description="Apuração mensal de ICMS da Hinove Agrociência.",
    )
    # Sem subcomando, abre a janela: é o caminho de quem não usa terminal.
    sub = parser.add_subparsers(dest="comando")
    parser.set_defaults(func=_comando_janela, porta=0, sem_navegador=False)

    def comum(p):
        p.add_argument("livro", help="Livro Fiscal do mês (.xlsx ou .xls)")
        p.add_argument("--saida", default=".", help="pasta de destino (padrão: atual)")
        p.add_argument("--parametros", default=None, help="pasta de parâmetros")
        p.add_argument("--aba", default=None, help="força uma aba específica do arquivo")

    p = sub.add_parser("apurar", help="Apura o ICMS do mês e grava o caderno.")
    comum(p)
    p.set_defaults(func=_comando_apurar)

    p = sub.add_parser("base-tratada", help="Só trata e classifica, sem apurar.")
    comum(p)
    p.set_defaults(func=_comando_base_tratada)

    p = sub.add_parser(
        "janela",
        help="Abre o Apurabot no navegador — é o padrão quando não se passa comando.",
    )
    p.add_argument("--porta", type=int, default=0,
                   help="porta fixa; por padrão o sistema escolhe uma livre")
    p.add_argument("--sem-navegador", action="store_true",
                   help="não abre o navegador sozinho; só mostra o endereço")
    p.set_defaults(func=_comando_janela)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
