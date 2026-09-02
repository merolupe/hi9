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


def numero(valor) -> float | None:
    """O inverso de `reais`: '1.234,56' → 1234.56. `None` quando não é número.

    Tolera o que o Excel devolve (float, int, '1234.56') e o que a pessoa
    digita ('R$ 1.234,56', '1234,56', ' '). Quem chama decide o que fazer com
    o `None` — aqui não se inventa zero.
    """
    if valor is None or isinstance(valor, bool):
        return None
    if isinstance(valor, (int, float)):
        return float(valor)
    texto = str(valor).strip().replace("R$", "").replace(" ", "").replace("\xa0", "")
    if not texto:
        return None
    if "," in texto:                    # 1.234,56 é brasileiro
        texto = texto.replace(".", "").replace(",", ".")
    try:
        return float(texto)
    except ValueError:
        return None
