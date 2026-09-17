"""O lookup da Conferência de Entradas: seis colunas e três estados de farol.

O confronto é um só e a chave é natural — `Chave Acesso`, 44 dígitos. O que
tem regra é o que acontece nos dois casos de borda.

### Quando a chave existe no CE

As seis colunas recebem o que o CE trouxe. Três detalhes que não são óbvios:

* a **data** é guardada como data de verdade, e não como texto — é o
  `CoagirData` do VBA, e ele existe porque o CE pode entregar o campo como
  `Date` ou como número de série do Excel, dependendo do export. Valor que não
  é data vira **vazio**, e não o texto original;
* a data **retém a hora** no valor e exibe só `dd/mm/aaaa`. Filtro por
  igualdade de data exata falha, e é limitação conhecida — preservada, porque
  mudar o formato é visível para todo mundo que recebe a planilha
  (pendência nº 3);
* o **farol** de `Pedido confirmado?` tem **três** estados, não dois.

### Quando a chave **não** existe no CE

`[FATO]` O VBA grava o literal `"não"` — minúsculo — em `Conf fisica`,
`Conf fiscal` e `Incongruência`, e deixa as três colunas novas vazias. O
comentário registra a intenção: "mantém o 'não' das colunas originais; as
colunas novas ficam VAZIAS (não há informação a afirmar)".

Isso é atrito com a doutrina do próprio projeto — para o farol o código
preserva três estados, e aqui afirma "não" onde não há informação. **Fica como
está**, e não por comodidade: é por efeito colateral desse literal que a regra
B1 não dispara para nota ausente do CE. `zero_ou_vazio("não")` é `False`;
trocar o literal por vazio faria `zero_ou_vazio` devolver `True` e
**reclassificaria para Fiscal notas que nem foram conferidas**. O preservado
nº 19 do registro do porte é exatamente isto.

### Chave repetida no CE

`[FATO]` Vence a **primeira ocorrência**, nos seis dicionários, e as demais
são descartadas sem registro. A regra é segura com os dados reais — medido no
CE da semana 30: 6.864 linhas, 6.844 chaves, 17 com mais de uma linha e
**zero** divergência de pedido ou de farol entre elas. O que muda aqui é o que
falta: as duplicadas passam a ser **contadas**, e **divergência de conteúdo
entre linhas da mesma chave bloqueia o encerramento** — porque aí a primeira
ocorrência deixou de ser uma escolha inofensiva.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Sequence

from .. import farol as semaforo
from ..texto import texto_de
from ..valores import data_hora
from . import colunas as col
from .fontes import Documento, LinhaDeConferencia


@dataclass(frozen=True)
class Anotacao:
    """As seis colunas de conferência de uma chave, já no tipo de saída."""

    conf_fisica: Any
    data_da_conferencia: Any
    conf_fiscal: Any
    incongruencia: Any
    numero_do_pedido: Any
    pedido_confirmado: str

    def como_colunas(self) -> list[Any]:
        return [self.conf_fisica, self.data_da_conferencia, self.conf_fiscal,
                self.incongruencia, self.numero_do_pedido,
                self.pedido_confirmado]


@dataclass
class Conferencia:
    """O CE indexado por chave, com o que a indexação teve de descartar."""

    por_chave: dict[str, Anotacao] = field(default_factory=dict)
    linhas: int = 0
    #: Chaves que apareceram em mais de uma linha. A primeira valeu.
    chaves_duplicadas: list[str] = field(default_factory=list)
    #: Chaves duplicadas cujas linhas **não** dizem a mesma coisa sobre pedido
    #: ou farol. Estas bloqueiam: a escolha da primeira deixou de ser neutra.
    chaves_divergentes: list[str] = field(default_factory=list)
    #: Verdadeiro quando o relatório foi lido. Falso desliga o bloco inteiro.
    lida: bool = True

    def __len__(self) -> int:
        return len(self.por_chave)

    def de(self, chave: str) -> Anotacao | None:
        return self.por_chave.get(chave)


def indexar(registros: Iterable[LinhaDeConferencia],
            tabela_do_farol: semaforo.Tabela | None = None) -> Conferencia:
    """Monta o índice do CE — primeira ocorrência vence, e as outras contam."""
    indice = Conferencia()
    vistas: dict[str, LinhaDeConferencia] = {}

    for registro in registros:
        indice.linhas += 1
        primeira = vistas.get(registro.chave)
        if primeira is None:
            vistas[registro.chave] = registro
            indice.por_chave[registro.chave] = Anotacao(
                conf_fisica=texto_de(registro.conferencia_fisica),
                data_da_conferencia=data_hora(registro.data_da_conferencia),
                conf_fiscal=texto_de(registro.conf_fiscal),
                incongruencia=texto_de(registro.motivo_incongruencia),
                numero_do_pedido=texto_de(registro.numero_do_pedido),
                pedido_confirmado=semaforo.farol_de_pedido(
                    registro.pedido_confirmado, tabela_do_farol),
            )
            continue

        if registro.chave not in indice.chaves_duplicadas:
            indice.chaves_duplicadas.append(registro.chave)
        if _divergem(primeira, registro, tabela_do_farol) and (
                registro.chave not in indice.chaves_divergentes):
            indice.chaves_divergentes.append(registro.chave)

    return indice


def _divergem(primeira: LinhaDeConferencia, outra: LinhaDeConferencia,
              tabela_do_farol: semaforo.Tabela | None) -> bool:
    """Duas linhas da mesma chave dizem coisas diferentes sobre o pedido?

    Só pedido e farol, e não as seis colunas: são estas duas que o dossiê
    mediu ("zero divergência"), e são elas que mudam o que o guardião vê.
    """
    if texto_de(primeira.numero_do_pedido) != texto_de(outra.numero_do_pedido):
        return True
    return (semaforo.farol_de_pedido(primeira.pedido_confirmado, tabela_do_farol)
            != semaforo.farol_de_pedido(outra.pedido_confirmado, tabela_do_farol))


def anotar(documentos: Iterable[Documento], indice: Conferencia, *,
           ausente_da_conferencia: str) -> int:
    """Escreve as seis colunas em cada documento. Devolve quantos casaram.

    A chave é comparada **como veio** dos dois lados, sem normalizar — é o que
    o VBA faz, e é o defeito 11 do porte, que espera medição.
    """
    casaram = 0
    vazio = Anotacao(ausente_da_conferencia, "", ausente_da_conferencia,
                     ausente_da_conferencia, "", "")
    for documento in documentos:
        achada = indice.de(documento.chave_bruta)
        if achada is None:
            documento.conferencia = vazio.como_colunas()
            documento.no_ce = False
            continue
        documento.conferencia = achada.como_colunas()
        documento.no_ce = True
        casaram += 1
    return casaram


def valor_da_coluna(documento: Documento, rotulo: str) -> Any:
    """O valor de uma das seis colunas de conferência, pelo nome dela."""
    posicao = col.indice(col.CONFERENCIA, rotulo)
    if posicao < 0 or posicao >= len(documento.conferencia):
        return ""
    return documento.conferencia[posicao]


def farois(documentos: Sequence[Documento]) -> dict[str, int]:
    """Quantas notas em cada um dos três estados do farol de pedido.

    Vai para a tela porque é a distribuição que o dossiê mediu (1.242 `Sim`,
    143 `Não`, 5.459 vazio no CE da semana 30) e porque é o número que mostra,
    sem abrir a planilha, que o terceiro estado continua sendo três.
    """
    contagem = {"Sim": 0, "Não": 0, "sem pedido": 0}
    for documento in documentos:
        valor = texto_de(valor_da_coluna(documento, col.P_PEDIDO_CONFIRMADO))
        contagem[valor if valor in contagem else "sem pedido"] += 1
    return contagem
