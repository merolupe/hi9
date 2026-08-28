"""Números como o time fiscal os lê.

O Python formata milhar com vírgula e decimal com ponto; no Brasil é o
contrário, e `287,113.66` num relatório fiscal se lê como duzentos e oitenta e
sete reais. Toda memória de cálculo e toda instrução que uma pessoa vai ler
passa por aqui.

As planilhas não precisam disto: nelas o valor vai como número, com formato de
célula. Isto é para texto.
"""
from __future__ import annotations

PROVISORIO = "\x00"


def reais(valor: float, casas: int = 2) -> str:
    """1234567.891 → '1.234.567,89'."""
    texto = f"{valor:,.{casas}f}"
    return texto.replace(",", PROVISORIO).replace(".", ",").replace(PROVISORIO, ".")
