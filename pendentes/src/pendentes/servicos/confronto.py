"""A cascata dos quatro procedimentos — **por passos**, nunca por linha.

Esta é a armadilha nº 1 do porte, e ela merece a frase inteira: **o laço
externo é o procedimento, e o interno é a nota.** Cada procedimento varre
todas as notas antes de o seguinte começar.

Invertido — uma nota de cada vez, tentando os quatro procedimentos nela —, o
resultado muda e piora. O procedimento 3 (CNPJ + valor) é uma chave fraca; se
ele rodar para a primeira nota antes de o procedimento 1 (nota + CNPJ) ter
rodado para a segunda, ele consome um lançamento que pertencia, por chave
forte, àquela segunda nota. A segunda nota vira pendente sem ser, e o
resultado passa a depender **da ordem das linhas no relatório** — dois
relatórios com o mesmo conteúdo em ordens diferentes produzem planilhas
diferentes.

O comentário do VBA registra que este foi o desenho inicial e que foi
corrigido. Aqui a ordem é explícita, e há teste que falha se alguém inverter
os dois laços (`test_a_cascata_por_passos_nao_e_a_cascata_por_linha`).

### A segregação das canceladas vem antes de tudo

Nota cancelada não é pendência nem lançamento, e sai do confronto **antes** do
primeiro passo. A ordem importa pelo mesmo motivo: uma cancelada que casasse
por CNPJ + valor consumiria um lançamento legítimo de outra nota.

O efeito colateral é conhecido e está documentado: se uma nota cancelada
chegou a ser lançada no Sankhya, aquele lançamento nunca é consumido e aparece
em `Sem Correspondencia ASIS`, inflando a medida de lacuna de captura do ASIS
com um caso que não é lacuna nenhuma. O remédio seria pior que a doença, e o
número é aproximado por construção.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence

from .chaves import (
    NENHUM, Indices, chave_de_cnpj_e_valor, chave_de_nota_e_cnpj,
    chave_de_nota_e_valor,
)
from .fontes import NotaDeServico, Registro

#: A nota ainda não casou com nenhum lançamento.
PENDENTE = 0
#: A nota está cancelada e não entra no confronto.
CANCELADA = -1
#: Os quatro procedimentos, na ordem em que rodam. A ordem é a regra.
PROCEDIMENTOS = (1, 2, 3, 4)

#: Como cada procedimento se chama para quem lê a tela.
NOMES = {
    1: "nota+CNPJ",
    2: "RPS+CNPJ",
    3: "CNPJ+valor",
    4: "nota+valor",
}

#: O procedimento de chave fraca: casa por nota e valor, **sem CNPJ**. A
#: própria macro manda revisar esses casos à mão, e aqui eles bloqueiam o
#: encerramento da semana.
PROCEDIMENTO_FRACO = 4


@dataclass
class Confronto:
    """O que a cascata decidiu sobre cada nota e sobre cada lançamento."""

    #: Por nota: `PENDENTE`, `CANCELADA`, ou o número do procedimento que resolveu.
    procedimento: list[int] = field(default_factory=list)
    #: Por nota: a posição do lançamento casado, ou `NENHUM`.
    lancamento: list[int] = field(default_factory=list)
    #: Por lançamento: se já foi consumido por alguma nota.
    consumidos: list[bool] = field(default_factory=list)

    def resolvida(self, posicao: int) -> bool:
        return self.procedimento[posicao] > PENDENTE

    @property
    def lancadas(self) -> int:
        return sum(1 for p in self.procedimento if p > PENDENTE)

    @property
    def canceladas(self) -> int:
        return sum(1 for p in self.procedimento if p == CANCELADA)

    @property
    def pendentes(self) -> int:
        """Por diferença, como no VBA — e a identidade tem de fechar."""
        return len(self.procedimento) - self.lancadas - self.canceladas

    @property
    def sem_correspondencia(self) -> int:
        return sum(1 for consumido in self.consumidos if not consumido)

    def por_procedimento(self) -> dict[int, int]:
        """Quantas notas cada procedimento resolveu.

        A soma tem de dar `lancadas` — é a identidade aritmética que serve de
        teste de regressão visível na tela, e é por ela que se sabe, sem abrir
        teste nenhum, que o porte continua fazendo o que fazia.
        """
        return {p: sum(1 for q in self.procedimento if q == p)
                for p in PROCEDIMENTOS}


def segregar_canceladas(notas: Sequence[NotaDeServico]) -> list[int]:
    """O estado inicial de cada nota: `CANCELADA` ou `PENDENTE`."""
    return [CANCELADA if nota.cancelada else PENDENTE for nota in notas]


def _chave(passo: int, nota: NotaDeServico) -> str | None:
    """A chave que aquele procedimento consulta. `None` quando ele não se aplica."""
    if passo == 1:
        return chave_de_nota_e_cnpj(nota.numero, nota.cnpj_do_prestador)
    if passo == 2:
        # O RPS vazio ou zero não é identidade de nada — o VBA o descarta, e
        # sem esse descarte a chave "0|cnpj" casaria notas sem relação.
        if not nota.rps or nota.rps == "0":
            return None
        return chave_de_nota_e_cnpj(nota.rps, nota.cnpj_do_prestador)
    if passo == 3:
        return chave_de_cnpj_e_valor(nota.cnpj_do_prestador, nota.chave_de_valor)
    return chave_de_nota_e_valor(nota.numero, nota.chave_de_valor)


def _indice(passo: int, indices: Indices):
    """O procedimento 2 consulta o **mesmo** índice do 1, por outro lado."""
    if passo in (1, 2):
        return indices.nota_e_cnpj
    if passo == 3:
        return indices.cnpj_e_valor
    return indices.nota_e_valor


def confrontar(notas: Sequence[NotaDeServico], lancamentos: Sequence[Registro],
               indices: Indices) -> Confronto:
    """A cascata inteira: segrega as canceladas e roda os quatro passos."""
    resultado = Confronto(
        procedimento=segregar_canceladas(notas),
        lancamento=[NENHUM] * len(notas),
        consumidos=[False] * len(lancamentos),
    )

    # O laço externo é o PASSO. Trocar estes dois `for` de lugar muda o
    # resultado e o torna dependente da ordem das linhas — ver o docstring
    # do módulo, e o teste que trava a inversão.
    for passo in PROCEDIMENTOS:
        indice = _indice(passo, indices)
        for posicao, nota in enumerate(notas):
            if resultado.procedimento[posicao] != PENDENTE:
                continue
            chave = _chave(passo, nota)
            if chave is None:
                continue
            achou = indice.consumir(chave, resultado.consumidos)
            if achou != NENHUM:
                resultado.procedimento[posicao] = passo
                resultado.lancamento[posicao] = achou

    return resultado
