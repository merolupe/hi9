"""A nota pendente × o pedido da Conferência de Serviços (colunas 29 a 36).

Uma nota pendente não é só "não lançada": muitas vezes ela **já está anexada a
um pedido de compra** e espera lançamento. Dizer isso à área requisitante,
antes de qualquer retorno humano, é o que estas oito colunas fazem.

O dossiê dava esta parte como desconhecida. Ela está inteira no código, e a
regra é literal:

**Âncora.** `código do parceiro | código da empresa`. O código da empresa vem
do de-para dinâmico de filiais, pelo CNPJ do tomador. Sem cadastro de parceiro
ou sem código de filial, não há como ancorar — e a coluna 36 diz qual dos dois
faltou, em vez de ficar vazia.

**Filtro de data.** O anexo tem de ser da data de emissão **ou depois**. A
comparação é por dia; a hora do anexo é descartada na comparação e preservada
no valor.

**Filtro de valor, em duas varreduras.** Primeiro o valor exato — a razão
entre o valor do pedido e o da nota dentro da tolerância de `0,005`. Só se
**nenhum** exato aparecer é que se procura o múltiplo inteiro (de 2× a 12×),
que é a assinatura de um pedido global cobrindo várias notas. A ordem importa:
um pedido global nunca deve roubar o vínculo de um pedido específico.

**Desempate.** Vence o maior `Nro. Unico`, e é só isso — não há critério de
proximidade nem de data. Quando há mais de um candidato, o vínculo sai
marcado como **ambíguo**, com a contagem, e o ambíguo bloqueia o encerramento
da semana: a ferramenta escolheu um, mas não sabe se escolheu o certo.

Os três limiares — tolerância, múltiplo mínimo e máximo — são parâmetro, na
carga de fábrica. Não são regra tributária; são calibragem de heurística, e o
time fiscal muda sem desenvolvedor.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence

from ..farol import SEMAFORO_DE_SERVICOS, semaforo
from .enriquecimento import SEM_CADASTRO
from .fontes import Anexo, NotaDeServico

#: O rótulo da coluna 36 quando não houve como ancorar o vínculo pelo
#: parceiro. Quando o que falta é o código da filial, o VBA grava
#: `Nao encontrado` — não distingue os dois casos, e aqui a célula continua
#: dizendo a mesma coisa. Quem distingue é a tela: o CNPJ de tomador sem
#: filial vira **lista bloqueante**, com o CNPJ nomeado.
SEM_CADASTRO_DE_PARCEIRO = "Sem cadastro de parceiro"
NAO_ENCONTRADO = "Nao encontrado"

#: Quantas colunas o bloco ocupa na `Pendentes`: da 29 à 36.
LARGURA = 8


@dataclass(frozen=True)
class Vinculo:
    """O pedido a que a nota parece estar anexada, e o quanto disso é confiança."""

    numero_unico: Any = ""
    data_do_anexo: Any = ""
    valor: Any = ""
    fator: str = ""
    status_do_lancamento: Any = ""
    pedido_confirmado: str = ""
    motivo_da_incongruencia: str = ""
    confianca: str = ""
    ambiguo: bool = False
    candidatos: int = 0

    @property
    def encontrado(self) -> bool:
        return bool(self.fator)

    def como_colunas(self) -> list[Any]:
        """As oito colunas, na ordem em que entram na `Pendentes`."""
        return [
            self.numero_unico, self.data_do_anexo, self.valor, self.fator,
            self.status_do_lancamento, self.pedido_confirmado,
            self.motivo_da_incongruencia, self.confianca,
        ]


#: O vínculo que não existe porque a Conferência de Serviços não foi lida. A
#: coluna 36 fica **vazia**: não é "não encontrei", é "não procurei".
NAO_PROCURADO = Vinculo()


def indexar(anexos: Sequence[Anexo]) -> dict[str, list[int]]:
    """Os anexos por `parceiro | empresa`, na ordem do relatório.

    Linha sem nenhum dos dois códigos não indexa nada — a chave `"|"` casaria
    com toda nota sem cadastro e sem filial.
    """
    indice: dict[str, list[int]] = {}
    for posicao, anexo in enumerate(anexos):
        if not (anexo.parceiro or anexo.empresa):
            continue
        indice.setdefault(anexo.chave, []).append(posicao)
    return indice


def _dia(valor: Any) -> Any:
    """O dia de uma data ou data-hora. `None` quando não é data."""
    data = getattr(valor, "date", None)
    if callable(data):
        return data()
    return valor if hasattr(valor, "year") else None


def _candidato(anexo: Anexo, dia_da_emissao: Any) -> bool:
    """O anexo serve: é de data conhecida, do dia da emissão ou depois, e tem valor."""
    dia = _dia(anexo.data_do_anexo)
    if dia is None or dia < dia_da_emissao:
        return False
    return anexo.valor > 0


def _rotulo(exatos: int, multiplos: int) -> str:
    if exatos == 1:
        return "Exato"
    if exatos > 1:
        return f"Exato (ambiguo: {exatos} candidatos)"
    if multiplos == 1:
        return "Multiplo (pedido global)"
    return f"Multiplo (ambiguo: {multiplos} candidatos)"


def vincular(nota: NotaDeServico, *, codigo_do_parceiro: str,
             codigo_da_filial: str, anexos: Sequence[Anexo],
             indice: dict[str, list[int]], conferencia_lida: bool = True,
             tolerancia: float = 0.005, multiplo_minimo: int = 2,
             multiplo_maximo: int = 12, tabela_do_semaforo=None) -> Vinculo:
    """O vínculo daquela nota com um pedido, ou o motivo de não haver nenhum."""
    if not conferencia_lida:
        return NAO_PROCURADO
    if codigo_do_parceiro == SEM_CADASTRO:
        return Vinculo(confianca=SEM_CADASTRO_DE_PARCEIRO)
    if not codigo_da_filial:
        return Vinculo(confianca=NAO_ENCONTRADO)

    dia_da_emissao = _dia(nota.emissao)
    if dia_da_emissao is None or nota.valor <= 0:
        return Vinculo(confianca=NAO_ENCONTRADO)

    posicoes = indice.get(f"{codigo_do_parceiro}|{codigo_da_filial}", ())
    melhor = -1
    melhor_numero_unico = float("-inf")
    melhor_fator = 0
    exatos = 0
    multiplos = 0

    # 1ª varredura: o valor exato. Um pedido específico sempre ganha de um
    # pedido global — por isso a segunda varredura só roda se esta não achar.
    for posicao in posicoes:
        anexo = anexos[posicao]
        if not _candidato(anexo, dia_da_emissao):
            continue
        if abs(anexo.valor / nota.valor - 1) < tolerancia:
            exatos += 1
            if anexo.numero_unico > melhor_numero_unico:
                melhor_numero_unico = anexo.numero_unico
                melhor, melhor_fator = posicao, 1

    if exatos == 0:
        # 2ª varredura: o múltiplo inteiro — a assinatura do pedido global.
        for posicao in posicoes:
            anexo = anexos[posicao]
            if not _candidato(anexo, dia_da_emissao):
                continue
            razao = anexo.valor / nota.valor
            for fator in range(multiplo_minimo, multiplo_maximo + 1):
                if abs(razao - fator) < tolerancia:
                    multiplos += 1
                    if anexo.numero_unico > melhor_numero_unico:
                        melhor_numero_unico = anexo.numero_unico
                        melhor, melhor_fator = posicao, fator
                    break

    if melhor < 0:
        return Vinculo(confianca=NAO_ENCONTRADO)

    anexo = anexos[melhor]
    candidatos = exatos or multiplos
    return Vinculo(
        numero_unico=anexo.numero_unico,
        data_do_anexo=anexo.data_do_anexo,
        valor=anexo.valor,
        fator=f"{melhor_fator}x",
        status_do_lancamento=anexo.status_do_lancamento,
        pedido_confirmado=semaforo(anexo.pedido_confirmado,
                                   tabela_do_semaforo or SEMAFORO_DE_SERVICOS),
        motivo_da_incongruencia=anexo.motivo_da_incongruencia,
        confianca=_rotulo(exatos, multiplos),
        ambiguo=candidatos > 1,
        candidatos=candidatos,
    )
