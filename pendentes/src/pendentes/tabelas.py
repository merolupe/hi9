"""Tabelas em que a **ordem das linhas é a regra**, e não a apresentação.

Duas regras dos geradores dependem de ordem, e nas duas a ordem está hoje
enterrada na sequência de `ElseIf` do VBA:

* **a unidade derivada do nome fantasia** — `CORUMB` é testado **antes** de
  `GUAR`. Inverter os dois faz qualquer fantasia de Corumbá que contenha
  "GUAR" virar Guará, sem erro e sem aviso. É uma armadilha que só existe
  porque a ordem é invisível;
* **o roteamento das quatro condições** — a primeira verdadeira consome a
  linha, e as três seguintes nem são avaliadas.

Quando essas tabelas saem do código e viram parâmetro, a ordem precisa sair
junto. Ela vira uma coluna `ordem`, visível e editável na mesma tela — quem
cadastra a unidade nova vê que existe uma ordem e que ela decide.
"""
from __future__ import annotations

from typing import Any, Iterable, Sequence

from .texto import chave_de_texto


def por_ordem(linhas: Iterable[dict]) -> list[dict]:
    """As linhas na ordem que a coluna `ordem` manda.

    Linha sem `ordem` vai para o fim, preservando a ordem de cadastro — o
    empate nunca é resolvido por acaso.
    """
    numeradas = []
    for posicao, linha in enumerate(linhas):
        bruto = linha.get("ordem")
        try:
            ordem = int(bruto)
        except (TypeError, ValueError):
            ordem = 10 ** 6 + posicao
        numeradas.append((ordem, posicao, linha))
    return [linha for _, _, linha in sorted(numeradas, key=lambda t: (t[0], t[1]))]


def primeira_que_casa(valor: Any, linhas: Sequence[dict], *,
                      campo: str = "trecho") -> dict | None:
    """A primeira linha, na ordem, cujo trecho está contido no valor.

    A comparação é por `chave_de_texto` dos dois lados — maiúsculas, sem
    acento, sem espaço sobrando —, que é o que faz `Hinove Corumbá` casar com
    o trecho `CORUMB`.
    """
    alvo = chave_de_texto(valor)
    if not alvo:
        return None
    for linha in por_ordem(linhas):
        trecho = chave_de_texto(linha.get(campo, ""))
        if trecho and trecho in alvo:
            return linha
    return None
