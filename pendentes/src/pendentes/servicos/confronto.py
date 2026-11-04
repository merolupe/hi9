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

### Nas chaves fracas, a cronologia vem antes do valor

Os procedimentos 3 (CNPJ + valor) e 4 (nota + valor) não têm o par nota +
CNPJ para ancorar o casamento, e o prestador que cobra o mesmo valor todo mês
dá a eles uma dúzia de lançamentos com a mesma chave. Pegar "o primeiro livre",
como a macro faz, casou a NFS-e de 01/10 com um lançamento de abril.

Por isso, nesses dois passos, o lançamento só serve à nota se o `Dt. Neg.`
dele **não for anterior à emissão** — com a tolerância de poucos dias que o
time calibra na tela (`tolerancia_de_emissao_dias`). Não se lança uma nota
antes de ela existir. Entre os lançamentos que passam, fica o de `Dt. Neg.`
mais próximo da emissão; o empate vai para o primeiro, na ordem do relatório.

Sem data de um dos lados, a cronologia não pode ser conferida e o casamento
fraco não acontece: a nota fica pendente, que é o erro que alguém revisa. O
erro contrário — dar como lançada uma nota que não foi — some do relatório.
Os procedimentos 1 e 2 não passam por isso: o número da nota com o CNPJ já é
a identidade.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Any, Sequence

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

#: Os procedimentos sem o par nota + CNPJ: neles, a cronologia é conferida
#: antes de o lançamento ser consumido.
PROCEDIMENTOS_COM_CRONOLOGIA = (3, 4)

#: Quantos dias o `Dt. Neg.` pode vir antes da emissão. O valor de verdade
#: é parâmetro (`confronto_servicos.tolerancia_de_emissao_dias`); este é o
#: padrão de quem chama sem informar.
TOLERANCIA_DE_EMISSAO_PADRAO = 5


@dataclass
class Confronto:
    """O que a cascata decidiu sobre cada nota e sobre cada lançamento."""

    #: Por nota: `PENDENTE`, `CANCELADA`, ou o número do procedimento que resolveu.
    procedimento: list[int] = field(default_factory=list)
    #: Por nota: a posição do lançamento casado, ou `NENHUM`.
    lancamento: list[int] = field(default_factory=list)
    #: Por lançamento: se já foi consumido por alguma nota.
    consumidos: list[bool] = field(default_factory=list)
    #: Por nota: ficou pendente porque o lançamento livre de mesma chave
    #: fraca era de antes da emissão (ou não tinha data para conferir).
    barrada_pela_data: list[bool] = field(default_factory=list)

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

    @property
    def barradas_pela_data(self) -> int:
        return sum(1 for b in self.barrada_pela_data if b)

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


def _dia(valor: Any) -> date | None:
    """A data de uma célula já convertida; `None` se ela ficou como texto."""
    if isinstance(valor, date):
        return valor.date() if hasattr(valor, "hour") else valor
    return None


def _consumir_na_cronologia(indice, chave: str, nota: NotaDeServico,
                            lancamentos: Sequence[Registro],
                            consumidos: list[bool],
                            tolerancia: int) -> tuple[int, bool]:
    """O lançamento livre de `Dt. Neg.` mais próximo, entre os que cabem.

    Devolve a posição (já marcada como consumida) e se houve lançamento livre
    recusado pela data — é isso que a tela conta.
    """
    livres = [p for p in indice.posicoes.get(chave, ()) if not consumidos[p]]
    if not livres:
        return NENHUM, False
    emissao = _dia(nota.emissao)
    if emissao is None:
        return NENHUM, True
    piso = emissao - timedelta(days=tolerancia)
    escolhido, distancia = NENHUM, None
    for posicao in livres:
        negociacao = _dia(lancamentos[posicao].data_de_negociacao)
        if negociacao is None or negociacao < piso:
            continue
        dias = abs((negociacao - emissao).days)
        if distancia is None or dias < distancia:
            escolhido, distancia = posicao, dias
    if escolhido == NENHUM:
        return NENHUM, True
    consumidos[escolhido] = True
    return escolhido, False


def confrontar(notas: Sequence[NotaDeServico], lancamentos: Sequence[Registro],
               indices: Indices, *,
               tolerancia_de_emissao_dias: int = TOLERANCIA_DE_EMISSAO_PADRAO,
               ) -> Confronto:
    """A cascata inteira: segrega as canceladas e roda os quatro passos."""
    resultado = Confronto(
        procedimento=segregar_canceladas(notas),
        lancamento=[NENHUM] * len(notas),
        consumidos=[False] * len(lancamentos),
        barrada_pela_data=[False] * len(notas),
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
            if passo in PROCEDIMENTOS_COM_CRONOLOGIA:
                achou, barrada = _consumir_na_cronologia(
                    indice, chave, nota, lancamentos, resultado.consumidos,
                    tolerancia_de_emissao_dias)
                if barrada:
                    resultado.barrada_pela_data[posicao] = True
            else:
                achou = indice.consumir(chave, resultado.consumidos)
            if achou != NENHUM:
                resultado.procedimento[posicao] = passo
                resultado.lancamento[posicao] = achou
                # Barrada no 3 e casada no 4 não é barrada: resolveu.
                resultado.barrada_pela_data[posicao] = False

    return resultado
