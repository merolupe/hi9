"""A herança pelo livro, as reclassificações B1 e B1.5, e o split B2.

As cinco colunas de classificação são escritas **à mão pelos analistas**
depois que o arquivo é gerado. O código as cria vazias ou herdadas e nunca as
preenche por adivinhação. Duas regras sobrescrevem, e as duas dizem por quê:
**B1** (o lançamento fiscal) e **B1.5** (o pedido de compra). A base de
conhecimento também preenche, mas só célula vazia e sempre marcada — está em
`precategorizacao.py`, e é proposta, não regra.

### A herança deixa de vir do arquivo da semana passada

`[FATO]` No VBA, o estado inteiro da rotina mora dentro de `XMLAnterior.xls`:
o PROCX lê a aba `Pendentes` anterior e, como segunda fonte, a
`PENDENTES FIS-FAT`. Quem renomeia errado o arquivo, perde o anexo do e-mail
ou salva por cima perde a classificação de todo mundo — e a macro **aborta**
quando o arquivo não está lá.

Aqui a herança vem do **livro** (`dados/pendentes/classificacao/mercadorias.
yaml`), e a planilha da semana anterior, quando vem, é ingerida nele antes.
Três defeitos caem por construção, e vale dizer exatamente quais:

| O que o VBA faz | O que acontece aqui |
|---|---|
| lê as **colunas 1 a 5 por posição fixa**, sem consultar cabeçalho (defeito 8) | o livro tem campo com nome; a planilha devolvida é lida por cabeçalho, com sinônimo |
| `lastRow = Cells(Rows.Count, 6)` — a coluna 6 no código (defeito 9) | não existe última linha por coluna mágica: a lista de documentos é a lista |
| `colChaveNova = colChaveAtual + 5` — offset que depende de o bloco ter 5 colunas | não existe offset: a chave é um campo do documento |

`[FATO]` Os dois offsets são o mesmo antipadrão que a **v7 já havia removido**
da etapa 15, onde `colChaveAtual + 2` quebrou quando o bloco de conferência
passou de 3 para 6 colunas. Ele sobreviveu na etapa 17 porque ninguém mexeu
nela desde então. Com o livro, ele não tem onde existir.

E um ganho que não é sobre defeito: **a classificação sobrevive à semana em
que a nota sai de `Pendentes`.** Uma nota roteada para `CTe` ou movida para
`Lançados` não tem a classificação lida por ninguém no VBA; se ela voltar na
semana seguinte, volta vazia. O livro guarda todo mundo, para sempre.

### B1 — a única regra que sobrescreve

Mercadoria conferida fisicamente e sem divergência é pendência de lançamento
**fiscal**, não da área requisitante. Então `Guardião` vira `Fiscal` e
`Gestor de apoio` é esvaziado — por cima do que foi herdado.

`[FATO]` A ordem importa duas vezes: se B1 rodasse **antes** da herança, o
valor herdado a sobrescreveria; se rodasse **depois** de B2, os registros já
teriam saído da principal e o split não os pegaria.

A condição é escrita aqui com as três partes explícitas — *esteve no CE* **e**
*física confirmada* **e** *incongruência vazia ou zero*. No VBA a primeira
parte é implícita: a nota ausente do CE recebe o literal `"não"`, e
`EhZeroOuVazio("não")` é `False`. O resultado é o mesmo; o que muda é que a
regra passa a dizer o que faz, em vez de depender de um literal para funcionar.

### B1.5 — pedido de compra pendente é pendência do Suprimentos

O farol de pedido tem três estados, e até aqui o do meio não tinha dono: ele
aparecia na planilha e não virava cobrança de ninguém. Agora vira, e o
`Guardião` é o **Suprimentos** — sem aba própria, na `Pendentes` junto com as
outras áreas, porque o Suprimentos responde no mesmo ritmo que elas.

`[FATO]` Medido nas 88 linhas classificadas à mão da semana 38: cinco notas
têm pedido confirmado **com** incongruência preenchida, e quatro delas o time
marcou como `Suprimentos` — a quinta como `Manutenção Guará`. Nenhuma linha
daquela semana tem o pedido como não confirmado, então **a primeira porta da
regra entra sem medição** e a primeira semana real vai dizer se ela acerta.

`[DECISÃO]` Quando as duas regras querem a mesma linha — física conferida, sem
incongruência, e pedido não confirmado — **B1.5 vence**, porque ela roda
depois. A leitura é a do impedimento: o Fiscal não lança nota cujo pedido não
foi confirmado, então quem destrava é o Suprimentos. Na semana 38 esse
cruzamento tem zero linhas; quando aparecer, é a primeira coisa a conferir.

Diferente de B1, ela esvazia o gestor **só quando troca o guardião**: aí o
gestor herdado pertencia à área que saiu, e a pré-categorização repõe o gestor
vigente do Suprimentos. Na linha que já era do Suprimentos o gestor fica como
está — ali ele é julgamento humano, não sobra de herança, e apagá-lo para
reescrever o mesmo nome perderia informação.

### B2 — move, não copia

`Guardião` igual a `Fiscal` ou a `Faturamento` sai da `Pendentes` e vai para a
`PENDENTES FIS-FAT`. É **movimento**: a linha não fica nas duas. A aba de
destino tem as mesmas colunas menos `Gestor de apoio` e `Categoria`; o
`Retorno` permanece, e o comentário do VBA diz por quê — "é mantido para
histórico".
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Sequence

from ..estado import Livro
from ..texto import aparar
from ..valores import zero_ou_vazio
from . import colunas as col
from .conferencia import valor_da_coluna
from .fontes import Documento


@dataclass
class Heranca:
    """O que o livro devolveu para a planilha desta semana."""

    herdadas: int = 0
    sem_classificacao: int = 0
    com_retorno: int = 0
    novas: list[str] = field(default_factory=list)


def herdar(documentos: Iterable[Documento], livro: Livro) -> Heranca:
    """Preenche as cinco colunas de classificação a partir do livro."""
    relato = Heranca()
    for documento in documentos:
        registro = livro.de(documento.chave)
        retorno = registro.ultimo_retorno
        documento.categorizacao = [
            registro.tipo_de_operacao,
            registro.guardiao,
            registro.gestor_de_apoio,
            registro.categoria,
            retorno,
        ]
        if registro.vazia():
            relato.sem_classificacao += 1
            relato.novas.append(documento.chave)
        else:
            relato.herdadas += 1
        if retorno:
            relato.com_retorno += 1
    return relato


def reclassificar_para_fiscal(documentos: Iterable[Documento], *,
                              conferencia_fisica_confirmada: str,
                              guardiao: str) -> int:
    """B1 — as três condições, explícitas. Devolve quantas foram reclassificadas."""
    posicao_do_guardiao = col.POSICAO_DA_CATEGORIZACAO[col.C_GUARDIAO]
    posicao_do_gestor = col.POSICAO_DA_CATEGORIZACAO[col.C_GESTOR]
    reclassificadas = 0

    for documento in documentos:
        if not documento.no_ce:
            continue
        fisica = aparar(valor_da_coluna(documento, col.P_CONF_FISICA))
        if fisica.casefold() != aparar(conferencia_fisica_confirmada).casefold():
            continue
        if not zero_ou_vazio(valor_da_coluna(documento, col.P_INCONGRUENCIA)):
            continue
        documento.categorizacao[posicao_do_guardiao] = guardiao
        documento.categorizacao[posicao_do_gestor] = ""
        reclassificadas += 1

    return reclassificadas


def guardiao_de(documento: Documento) -> str:
    """O `Guardião` da linha, aparado — é como o VBA o compara em B2."""
    posicao = col.POSICAO_DA_CATEGORIZACAO[col.C_GUARDIAO]
    return aparar(documento.categorizacao[posicao])


def dividir_fis_fat(documentos: Iterable[Documento],
                    guardioes: Sequence[str]) -> tuple[list[Documento],
                                                       list[Documento]]:
    """B2 — devolve (os que vão para a FIS-FAT, os que ficam na principal).

    A comparação é tolerante a caixa e a espaço nas pontas (`StrComp` com
    `vbTextCompare` sobre `Trim`), diferente da etapa 15 e do roteamento. A
    assimetria é do VBA e está registrada no defeito 10.
    """
    alvos = {aparar(g).casefold() for g in guardioes if aparar(g)}
    fis_fat, principal = [], []
    for documento in documentos:
        (fis_fat if guardiao_de(documento).casefold() in alvos
         else principal).append(documento)
    return fis_fat, principal


@dataclass
class Suprimentos:
    """O que a regra do pedido de compra fez, e o que ela não soube ler."""

    nao_confirmado: int = 0
    confirmado_com_incongruencia: int = 0
    sem_pedido: int = 0
    nao_reconhecido: dict[str, int] = field(default_factory=dict)

    @property
    def reclassificadas(self) -> int:
        """As duas portas somadas — quantas linhas viraram do Suprimentos."""
        return self.nao_confirmado + self.confirmado_com_incongruencia


def reclassificar_para_suprimentos(documentos: Iterable[Documento], *,
                                   pedido_confirmado: str,
                                   pedido_nao_confirmado: str,
                                   guardiao: str) -> Suprimentos:
    """B1.5 — pedido de compra pendente é pendência do Suprimentos.

    Três portas, e a terceira é a que protege a regra:

    | `Pedido confirmado?` | `Incongruência` | o que acontece |
    |---|---|---|
    | não confirmado | qualquer | vira `Suprimentos` |
    | confirmado | preenchida | vira `Suprimentos` |
    | **em branco** | qualquer | **não se toca na linha** |

    O branco não é ausência de resposta, é ausência de pedido: nota sem pedido
    vinculado não tem o que confirmar, e não há o que falar em Suprimentos. É
    também o que mantém fora da regra a nota que nem esteve na Conferência de
    Entradas — nela o VBA grava o literal `não` em `Incongruência`, que
    `zero_ou_vazio` recusa, e sem a porta do branco essas linhas entrariam
    todas pela segunda porta, por um literal e não por um pedido.

    Valor que não é nem um rótulo nem o outro **não classifica** (regra nº 4):
    é contado em `nao_reconhecido` e a linha fica como estava.
    """
    posicao_do_guardiao = col.POSICAO_DA_CATEGORIZACAO[col.C_GUARDIAO]
    posicao_do_gestor = col.POSICAO_DA_CATEGORIZACAO[col.C_GESTOR]
    confirmado = aparar(pedido_confirmado).casefold()
    nao_confirmado = aparar(pedido_nao_confirmado).casefold()
    relato = Suprimentos()

    for documento in documentos:
        pedido = aparar(valor_da_coluna(documento, col.P_PEDIDO_CONFIRMADO))
        if not pedido:
            relato.sem_pedido += 1
            continue

        comparavel = pedido.casefold()
        if comparavel == nao_confirmado:
            relato.nao_confirmado += 1
        elif comparavel == confirmado:
            incongruencia = valor_da_coluna(documento, col.P_INCONGRUENCIA)
            if zero_ou_vazio(incongruencia):
                continue
            relato.confirmado_com_incongruencia += 1
        else:
            relato.nao_reconhecido[pedido] = (
                relato.nao_reconhecido.get(pedido, 0) + 1)
            continue

        anterior = documento.categorizacao[posicao_do_guardiao]
        documento.categorizacao[posicao_do_guardiao] = guardiao
        # O gestor só envelhece se o guardião **mudar**: numa linha que já era
        # do Suprimentos, ele é o gestor escrito à mão, e apagá-lo perderia
        # julgamento humano para reescrever o mesmo nome no lugar.
        if aparar(anterior).casefold() != aparar(guardiao).casefold():
            documento.categorizacao[posicao_do_gestor] = ""

    return relato
