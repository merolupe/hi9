"""A base de conhecimento preenche o que está vazio — e a célula sai marcada.

`[FATO]` Decisão do Compliance Tributário de 22/09/2026, tomada depois da
medição contra a semana 38: **categoria preenche, guardião preenche**. A
medição está em `docs/pendentes/08-base-de-conhecimento.md` e diz, sem
maquiagem, que categoria acerta 44 de 44 com evidência firme e que guardião
acerta 77% no grau de sugestão — uma nota errada a cada quatro.

Ligar assim mesmo é decisão de quem recebe a planilha, e ela vem com três
travas que não são negociáveis:

### 1. Só preenche o que está vazio

Herança do livro e regra B1 vêm antes e **nunca** são sobrescritas. O que uma
pessoa classificou, ou o que a semana passada devolveu, vale mais do que
qualquer histórico agregado.

### 2. A célula preenchida sai marcada

Sem a marca, a planilha mente por omissão: o guardião proposto fica
indistinguível do guardião escrito por alguém que conhece a nota. Com ela,
quem confere sabe o que olhar primeiro, e quem recebe a cobrança sabe de onde
veio o nome dele ali.

A marca é cor de fundo na célula — não coluna nova. Uma coluna a mais mudaria
o layout que dezenas de pessoas leem; a cor não muda nem largura nem ordem, e
a leitura de volta na semana seguinte ignora cor.

### 3. Roda entre B1 e B2, e isso tem consequência declarada

Depois da herança e da regra B1 — que preenchem primeiro —, e **antes** do
split B2. Quer dizer que um guardião proposto encaminha a nota para a
`PENDENTES FIS-FAT` exatamente como encaminharia um guardião escrito à mão.

A alternativa era preencher depois do split, e ela produz um arquivo que se
contradiz: uma nota na `Pendentes` com `Guardião = Faturamento`. Entre um
arquivo coerente cuja sugestão pode estar errada, e um arquivo incoerente,
o primeiro é o que dá para conferir.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from ..conhecimento.base import FIRME, SUGESTAO, Conhecimento
from ..texto import aparar
from . import colunas as col
from .fontes import Documento

#: Os graus aceitos por campo, do mais exigente para o mais frouxo. `nao`
#: desliga o campo.
NAO = "nao"
GRAUS = {NAO: (), FIRME: (FIRME,), SUGESTAO: (FIRME, SUGESTAO)}

#: Qual campo do livro corresponde a cada coluna da planilha.
CAMPOS = {col.C_CATEGORIA: "categoria", col.C_GUARDIAO: "guardiao"}


@dataclass
class Preenchimento:
    """Quantas células a base preencheu, por coluna e por grau."""

    por_coluna: dict[str, dict[str, int]] = field(default_factory=dict)
    #: Colunas cujo preenchimento está desligado no parâmetro.
    desligadas: list[str] = field(default_factory=list)

    @property
    def total(self) -> int:
        return sum(sum(graus.values()) for graus in self.por_coluna.values())

    def contar(self, coluna: str, grau: str) -> None:
        self.por_coluna.setdefault(coluna, {})
        self.por_coluna[coluna][grau] = self.por_coluna[coluna].get(grau, 0) + 1

    def linhas(self) -> list[str]:
        """O que a tela mostra — por coluna, e sempre dizendo o grau."""
        saida = []
        for coluna, graus in self.por_coluna.items():
            partes = ", ".join(f"{quantas} com evidência {grau}"
                               for grau, quantas in sorted(graus.items()))
            saida.append(f"{coluna}: {partes}")
        for coluna in self.desligadas:
            saida.append(f"{coluna}: desligado no parâmetro")
        return saida


def preencher(documentos: Iterable[Documento], conhecimento: Conhecimento, *,
              minimo_por_coluna: dict[str, str]) -> Preenchimento:
    """Preenche as colunas ligadas, só onde estão vazias. Devolve o que fez.

    `minimo_por_coluna` diz, para cada coluna, qual o grau **mínimo** que
    preenche: `firme`, `sugestao` ou `nao`. O parâmetro existe porque os dois
    campos não estão no mesmo estágio, e tratá-los igual erraria nos dois
    sentidos.
    """
    relato = Preenchimento()
    ligadas = {}
    for coluna, campo in CAMPOS.items():
        grau = str(minimo_por_coluna.get(coluna) or NAO).strip().lower()
        if grau == NAO or grau not in GRAUS:
            relato.desligadas.append(coluna)
            continue
        ligadas[coluna] = (campo, GRAUS[grau])
    if not ligadas or not len(conhecimento):
        return relato

    for documento in documentos:
        for coluna, (campo, aceitos) in ligadas.items():
            posicao = col.POSICAO_DA_CATEGORIZACAO[coluna]
            if aparar(documento.categorizacao[posicao]):
                continue                     # já classificado: não se toca
            proposta = conhecimento.propor(
                documento.de(col.X_COD_PARCEIRO), campo,
                documento.de(col.X_NOME_FANTASIA))
            if not proposta or proposta.confianca not in aceitos:
                continue
            documento.categorizacao[posicao] = proposta.valor
            documento.propostas[coluna] = proposta.confianca
            relato.contar(coluna, proposta.confianca)
    return relato


def marcar(documento: Documento, colunas) -> set[int]:
    """Em que posições daquele layout estão as células propostas desta linha.

    O layout decide, não um índice escrito à mão: a `PENDENTES FIS-FAT` não
    tem `Categoria`, e uma coluna proposta que não existe lá simplesmente não
    tem posição para marcar.
    """
    posicoes = set()
    for rotulo in documento.propostas:
        posicao = col.indice(colunas, rotulo)
        if posicao >= 0:
            posicoes.add(posicao)
    return posicoes
