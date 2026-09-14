"""O semáforo do Sankhya: célula de HTML com emoji, traduzida para texto.

As colunas de status dos relatórios de conferência não trazem texto: trazem
HTML com uma entidade de emoji dentro, como
`<div style="..."><span>&#128994;</span></div>`. O que se lê na tela é uma
bolinha colorida; o que está na célula é o número da entidade.

**A regra que não pode ser parametrizada: vazio não é "Não".**

Célula vazia significa *nota sem pedido vinculado* — um estado distinto de
*pedido não confirmado*. A evidência está medida: na Conferência de Entradas
da semana 30, os 5.459 registros de farol vazio são exatamente os 5.459 com
`Nro. do Pedido` vazio, sem uma única exceção. Tratar vazio como "Não" faria a
ferramenta afirmar que um pedido não foi confirmado quando não há pedido
nenhum.

O que **é** parâmetro: a tabela de códigos. Trocar o ícone do semáforo no
relatório troca o número da entidade, e isso não pode exigir um commit.

Dois consumidores, duas tabelas e uma diferença de fallback que o VBA tem e
que é preservada:

| | mercadorias (`TraduzirFarolPedido`) | serviços (`DecodificarSemaforo`) |
|---|---|---|
| Códigos | 2 (verde, vermelho) | 4 (verde, vermelho, amarelo, vazio) |
| Texto sem código, sem `<` | vira **vazio** | vira **o próprio texto** |
"""
from __future__ import annotations

from typing import Any, Iterable, Sequence

from .texto import texto_de

#: Um código de entidade HTML e o rótulo que ele vira. A ordem é a de teste.
Tabela = Sequence[tuple[str, str]]

#: O farol de pedido da Conferência de Entradas — **três** estados.
FAROL_DE_PEDIDO: Tabela = (("128994", "Sim"), ("128308", "Não"))

#: O semáforo da Conferência de Serviços — **cinco** ramos, contando os dois
#: fallbacks. O círculo vazio (9711) é um código que se traduz para vazio.
SEMAFORO_DE_SERVICOS: Tabela = (
    ("128994", "Sim"),
    ("128308", "Nao"),
    ("128993", "Parcial"),
    ("9711", ""),
)


def traduzir(valor: Any, tabela: Tabela, *, texto_cru: bool = False) -> str:
    """O primeiro código presente na célula vence; ordem de tabela é regra.

    `texto_cru=False` é mercadorias: o que não tem código conhecido vira
    vazio. `texto_cru=True` é serviços: o que não tem código conhecido e não
    parece HTML volta como o próprio texto, aparado.
    """
    bruto = texto_de(valor)
    for codigo, rotulo in tabela:
        if codigo and codigo in bruto:
            return rotulo
    if "<" in bruto:
        return ""
    return bruto.strip() if texto_cru else ""


def farol_de_pedido(valor: Any, tabela: Tabela | None = None) -> str:
    """`Pedido confirmado?` da Conferência de Entradas: `Sim`, `Não` ou vazio."""
    return traduzir(valor, tabela or FAROL_DE_PEDIDO, texto_cru=False)


def semaforo(valor: Any, tabela: Tabela | None = None) -> str:
    """O semáforo da Conferência de Serviços, com o estado `Parcial`."""
    return traduzir(valor, tabela or SEMAFORO_DE_SERVICOS, texto_cru=True)


def tabela_de(linhas: Iterable[dict]) -> Tabela:
    """A tabela vinda do parâmetro: linhas com `codigo` e `rotulo`."""
    return tuple(
        (texto_de(linha.get("codigo")).strip(), texto_de(linha.get("rotulo")))
        for linha in linhas
        if texto_de(linha.get("codigo")).strip()
    )
