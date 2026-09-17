"""A herança pelo livro, a reclassificação B1 e o split B2 — nesta ordem.

As cinco colunas de classificação são escritas **à mão pelos analistas**
depois que o arquivo é gerado. O código as cria vazias ou herdadas e nunca as
preenche por conta própria — com **uma única exceção**, que é a regra B1.

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
    posicao_do_guardiao = col.indice(col.categorizacao(0), col.C_GUARDIAO)
    posicao_do_gestor = col.indice(col.categorizacao(0), col.C_GESTOR)
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
    posicao = col.indice(col.categorizacao(0), col.C_GUARDIAO)
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
