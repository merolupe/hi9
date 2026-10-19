"""As quatro condições, na ordem, e a segregação de `Lançados`.

**A ordem é a regra.** O laço é único e a primeira condição verdadeira consome
a linha: as seguintes nem são avaliadas. Uma nota com tomador de CT-e **e**
situação "Desconhecida" vai para `CTe`, não para `Manifestados`, e trocar a
ordem das duas muda o destino de todas elas sem erro e sem aviso.

Hoje essa ordem é uma sequência de `If Not movido Then` enterrada no código.
Aqui ela é a coluna `ordem` da tabela de roteamento, visível e editável na
mesma tela — e continua sendo regra: `tabelas.por_ordem` é quem a aplica.

| Ordem | Coluna | Operador | Destino |
|---|---|---|---|
| 1 | `Tomador CT-e` | preenchido e diferente de `Não se aplica` | `CTe` |
| 2 | `Situação da manifestação` | igual a algum: desconhecida / operação não realizada | `Manifestados` |
| 3 | `Situação NF-e` | igual a `NF-e cancelada` | `Manifestados` |
| 4 | `Entrada/Saida NF-e` | igual a `Entrada` | `Entradas 3os` |

O que sobra depois das quatro **é o produto**: nota de saída ou própria, não
cancelada, com manifestação distinta das duas listadas e sem tomador de CT-e.
Ela não é `SEM REGRA` — é pendência, e é para isso que a ferramenta existe.

### Os três operadores, e por que eles são três

`[FATO]` O VBA compara de três jeitos diferentes nas quatro condições, e a
assimetria é real:

* a condição 1 usa `Trim` **só** no teste de comprimento, não no de
  desigualdade — `" Não se aplica"` com espaço à esquerda é diferente de
  `"Não se aplica"` e **vai para `CTe`**;
* a condição 2 aplica `LCase` mas **não** `Trim` nem remoção de acento — e é
  por isso que ela lista as duas grafias, com e sem acento, exatamente como o
  `.bas` faz;
* as condições 3 e 4 são igualdade exata, sensível a caixa e a acento —
  `"NF-e Cancelada"` ou `"entrada"` **não** roteiam, e a nota fica em
  `Pendentes`.

Uniformizar as três numa disciplina só é o **defeito 10** do porte, e ele
espera medição: é preciso contar, no XML real, quantas linhas têm valor que
difere do literal só por caixa, acento ou espaço. Se for zero, a uniformização
não muda destino nenhum; se for maior que zero, **o código de hoje está
perdendo linhas** — e esse número vai para o time fiscal antes da troca, não
depois. Até lá, os três operadores ficam como estão, defeito e tudo.

### `Lançados` não é uma quinta condição

A etapa 15 roda **depois** do lookup do CE, sobre uma coluna que o roteamento
nem enxerga (`Conf fiscal` nasce na etapa 13). Por isso ela mora aqui como
função separada, e não como quinta linha da tabela. A comparação dela é a
igualdade exata — `"SIM"` não move a linha —, e é a mesma assimetria de cima.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable

from ..tabelas import por_ordem
from ..texto import texto_de
from . import colunas as col
from .fontes import POSICAO, Documento

#: Os três jeitos com que o VBA compara, com o nome que a tabela usa.
OPERADORES = ("preenchido_e_diferente", "igual_a_algum", "igual")

#: O separador de valores dentro de uma condição `igual_a_algum`.
SEPARADOR = ";"


class RoteamentoInvalido(Exception):
    """A tabela de roteamento pede algo que não existe — coluna ou operador."""


@dataclass(frozen=True)
class Condicao:
    """Uma linha da tabela de roteamento, pronta para ser avaliada."""

    ordem: int
    coluna: str
    operador: str
    valores: tuple[str, ...]
    destino: str

    def descricao(self) -> str:
        return (f"{self.ordem}. {self.coluna} {self.operador} "
                f"{SEPARADOR.join(self.valores)} → {self.destino}")

    def satisfeita_por(self, documento: Documento) -> bool:
        """Avalia a condição do jeito que o VBA a avalia. Nem mais, nem menos."""
        bruto = texto_de(documento.de(self.coluna))
        alvo = self.valores[0] if self.valores else ""

        if self.operador == "preenchido_e_diferente":
            # `tomador <> "Não se aplica" And Len(Trim(tomador)) > 0`
            return bruto != alvo and bool(bruto.strip())
        if self.operador == "igual_a_algum":
            # `LCase(v) = "..."`, sem `Trim` e sem tirar acento.
            return bruto.lower() in {v.lower() for v in self.valores}
        # `igual`: igualdade de String em VBA, sem `Option Compare Text`.
        return bruto == alvo


def condicoes_de(declaradas: Iterable[dict]) -> tuple[Condicao, ...]:
    """As condições vindas do parâmetro, já na ordem em que serão avaliadas.

    Valida o que a tela pode ter cadastrado errado e **aborta nomeando** —
    coluna que não existe no XML, operador desconhecido, destino que não é
    aba. Roteamento silenciosamente inerte seria pior: a nota ficaria em
    `Pendentes` e ninguém saberia por quê.
    """
    condicoes = []
    for linha in por_ordem(list(declaradas)):
        coluna = str(linha.get("coluna", "")).strip()
        operador = str(linha.get("operador", "")).strip()
        destino = str(linha.get("destino", "")).strip()
        bruto = linha.get("valor", "")
        valores = tuple(
            parte.strip() for parte in str(bruto).split(SEPARADOR)
            if parte.strip()
        ) if not isinstance(bruto, (list, tuple)) else tuple(
            str(v).strip() for v in bruto if str(v).strip())

        if coluna not in POSICAO:
            raise RoteamentoInvalido(
                f"A condição de roteamento aponta para a coluna '{coluna}', "
                f"que não existe no relatório de importação de XML."
            )
        if operador not in OPERADORES:
            raise RoteamentoInvalido(
                f"A condição de roteamento de '{coluna}' pede o operador "
                f"'{operador}'. Os que existem são: {', '.join(OPERADORES)}."
            )
        if destino not in col.ABAS_DO_ROTEAMENTO:
            raise RoteamentoInvalido(
                f"A condição de roteamento de '{coluna}' manda a linha para "
                f"'{destino}', que não é uma das abas: "
                f"{', '.join(col.ABAS_DO_ROTEAMENTO)}."
            )
        condicoes.append(Condicao(
            ordem=len(condicoes) + 1, coluna=coluna, operador=operador,
            valores=valores, destino=destino,
        ))
    return tuple(condicoes)


@dataclass
class Roteamento:
    """Para onde cada documento foi, e por qual condição."""

    destinos: dict[str, list[Documento]] = field(default_factory=dict)
    pendentes: list[Documento] = field(default_factory=list)
    por_condicao: dict[int, int] = field(default_factory=dict)

    def quantos_em(self, destino: str) -> int:
        return len(self.destinos.get(destino, ()))


def rotear(documentos: Iterable[Documento],
           condicoes: tuple[Condicao, ...]) -> Roteamento:
    """A cascata: a primeira condição verdadeira consome a linha."""
    saida = Roteamento(destinos={aba: [] for aba in col.ABAS_DO_ROTEAMENTO})
    for documento in documentos:
        for condicao in condicoes:
            if condicao.satisfeita_por(documento):
                saida.destinos.setdefault(condicao.destino, []).append(documento)
                saida.por_condicao[condicao.ordem] = (
                    saida.por_condicao.get(condicao.ordem, 0) + 1)
                break
        else:
            saida.pendentes.append(documento)
    return saida


def segregar_lancados(documentos: Iterable[Documento],
                      valor_de_lancado: str) -> tuple[list[Documento],
                                                      list[Documento]]:
    """Separa o que já tem conferência fiscal. Devolve (lançados, o resto).

    A comparação é exata e sensível a caixa, como o VBA — `"SIM"` vindo do CE
    não moveria a linha. A coluna é localizada pelo **nome**, e não por offset:
    foi assim que a v7 consertou o `colChaveAtual + 2`, que quebrou quando o
    bloco de conferência passou de 3 para 6 colunas.
    """
    posicao = col.indice(col.CONFERENCIA, col.P_CONF_FISCAL)
    lancados, restantes = [], []
    for documento in documentos:
        atual: Any = documento.conferencia[posicao] if posicao >= 0 else ""
        (lancados if texto_de(atual) == valor_de_lancado else restantes
         ).append(documento)
    return lancados, restantes
