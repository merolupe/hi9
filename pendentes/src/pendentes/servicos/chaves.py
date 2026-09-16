"""As três chaves do confronto — e o índice que **consome**.

Não existe chave natural entre o ASIS e o Sankhya. As chaves são construídas
por concatenação, e as três vivem sobre o mesmo universo: os lançamentos de
serviço do Portal de Compras.

| Índice | Lado Sankhya | Quem consulta |
|---|---|---|
| `nota_e_cnpj` | número normalizado + CNPJ do parceiro | procedimentos 1 e 2 |
| `cnpj_e_valor` | CNPJ + valor com duas casas | procedimento 3 |
| `nota_e_valor` | número normalizado + valor | procedimento 4 |

O procedimento 2 consulta o **mesmo** índice do 1: o que muda é o lado do
ASIS, que oferece o número da RPS no lugar do número da nota. É o remédio para
as prefeituras que informam a RPS como número da nota.

### Por que o índice guarda uma lista, e não um índice só

Porque o confronto **consome**. Cada lançamento casa com no máximo uma nota, e
cada nota com no máximo um lançamento — sem isso, um mesmo lançamento pagaria
duas notas de mesmo valor e a aba inversa mentiria. `consumir` devolve o
primeiro lançamento ainda livre daquela chave e o marca; se todos já foram
consumidos, devolve `NENHUM`.

A escolha entre dois lançamentos homônimos é "o primeiro livre", sem critério
de desempate — e é por isso que a `Lancadas` ganha a coluna `Obs` avisando
`Chave nota+CNPJ duplicada no Sankhya`. O aviso existe porque a escolha pode
ter sido a errada.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence

from .fontes import Registro

#: O que `consumir` devolve quando não há lançamento livre para a chave.
NENHUM = -1


def chave_de_nota_e_cnpj(numero: str, cnpj: str) -> str:
    return f"{numero}|{cnpj}"


def chave_de_cnpj_e_valor(cnpj: str, valor: str) -> str:
    return f"{cnpj}|{valor}"


def chave_de_nota_e_valor(numero: str, valor: str) -> str:
    return f"{numero}|{valor}"


@dataclass
class Indice:
    """Chave → as posições dos lançamentos que a satisfazem, em ordem."""

    posicoes: dict[str, list[int]] = field(default_factory=dict)

    def acrescentar(self, chave: str, posicao: int) -> None:
        self.posicoes.setdefault(chave, []).append(posicao)

    def quantos(self, chave: str) -> int:
        return len(self.posicoes.get(chave, ()))

    def duplicada(self, chave: str) -> bool:
        """Mais de um lançamento com a mesma chave — o confronto pode ter errado."""
        return self.quantos(chave) > 1

    def consumir(self, chave: str, consumidos: list[bool]) -> int:
        """A posição do primeiro lançamento livre, já marcada. `NENHUM` se não há."""
        for posicao in self.posicoes.get(chave, ()):
            if not consumidos[posicao]:
                consumidos[posicao] = True
                return posicao
        return NENHUM


@dataclass
class Indices:
    """Os três índices, construídos de uma vez sobre os lançamentos."""

    nota_e_cnpj: Indice = field(default_factory=Indice)
    cnpj_e_valor: Indice = field(default_factory=Indice)
    nota_e_valor: Indice = field(default_factory=Indice)


def indexar(lancamentos: Sequence[Registro]) -> Indices:
    """Os três índices sobre a lista de lançamentos, na ordem dela.

    A posição guardada é a posição **na lista de lançamentos**, não a linha do
    relatório: é ela que o vetor de consumo endereça, e é ela que a aba
    inversa percorre no fim.
    """
    indices = Indices()
    for posicao, lancamento in enumerate(lancamentos):
        cnpj = lancamento.cnpj_do_parceiro
        valor = lancamento.chave_de_valor
        numero = lancamento.numero
        indices.nota_e_cnpj.acrescentar(chave_de_nota_e_cnpj(numero, cnpj), posicao)
        indices.cnpj_e_valor.acrescentar(chave_de_cnpj_e_valor(cnpj, valor), posicao)
        indices.nota_e_valor.acrescentar(chave_de_nota_e_valor(numero, valor), posicao)
    return indices
