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

### O gestor sai do guardião

`[FATO]` Ligado em 24/09/2026, a pedido do time. O gestor de apoio não é
proposto por parceiro: a base guarda o gestor vigente de **cada guardião**, e
a pergunta é feita com o guardião que a linha tem depois das outras colunas —
o herdado, o de B1 ou o que a base acabou de propor.

Duas consequências, e as duas estão no código abaixo:

* guardião que vai para a `PENDENTES FIS-FAT` não ganha gestor. Aquela aba não
  tem a coluna, e B1 esvazia o gestor de propósito quando manda a nota para o
  Fiscal — preencher ali desfaria a regra por baixo;
* gestor proposto sobre guardião que também foi só sugerido é, no máximo,
  sugestão. Uma dedução não fica mais firme do que aquilo de onde saiu.
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Iterable

from ..conhecimento.base import (FIRME, SUGESTAO, Conhecimento,
                                 chave_de_operacao)
from ..conhecimento.importacao import cfop_normalizado
from ..estado import Livro
from ..texto import aparar, chave_de_texto
from . import colunas as col
from .fontes import Documento

#: Os graus aceitos por campo, do mais exigente para o mais frouxo. `nao`
#: desliga o campo.
NAO = "nao"
GRAUS = {NAO: (), FIRME: (FIRME,), SUGESTAO: (FIRME, SUGESTAO)}

#: Qual campo da base corresponde a cada coluna da planilha, **na ordem em
#: que as colunas são preenchidas**. Categoria primeiro, porque a proposta de
#: `Tipo de Operação` pode depender dela.
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


def grafias_do_livro(livro: Livro | None) -> dict[str, str]:
    """Como o time escreve hoje cada tipo de operação.

    `[FATO]` A base aprendeu `Compra Uso e Consumo`; o relatório da semana 38
    escreve `Compra Uso Consumo`. É o mesmo tipo de operação, e a ferramenta
    não pode discordar de si mesma por causa de um conectivo.

    Normalizar o **casamento** resolve metade: as duas formas passam a ser a
    mesma chave. A outra metade é qual das duas **escrever**, e a resposta não
    pode sair do histórico agregado — ele é justamente o que está defasado. Sai
    do livro: a grafia que aparece mais nas classificações que voltaram das
    pessoas é a grafia em uso. Muda a redação, a ferramenta acompanha na semana
    seguinte, sem ninguém cadastrar nada.
    """
    contagem: dict[str, dict[str, int]] = {}
    for registro in (livro.registros.values() if livro else ()):
        escrita = aparar(registro.tipo_de_operacao)
        if not escrita:
            continue
        por_grafia = contagem.setdefault(chave_de_operacao(escrita), {})
        por_grafia[escrita] = por_grafia.get(escrita, 0) + 1
    return {chave: max(grafias.items(), key=lambda t: t[1])[0]
            for chave, grafias in contagem.items()}


def preencher(documentos: Iterable[Documento], conhecimento: Conhecimento, *,
              minimo_por_coluna: dict[str, str],
              livro: Livro | None = None,
              guardioes_sem_gestor: Iterable[str] = ()) -> Preenchimento:
    """Preenche as colunas ligadas, só onde estão vazias. Devolve o que fez.

    `minimo_por_coluna` diz, para cada coluna, qual o grau **mínimo** que
    preenche: `firme`, `sugestao` ou `nao`. O parâmetro existe porque os dois
    campos não estão no mesmo estágio, e tratá-los igual erraria nos dois
    sentidos.

    `guardioes_sem_gestor` são os que a regra B2 leva para a `PENDENTES
    FIS-FAT`: ali não há `Gestor de apoio`, e a linha fica sem proposta.
    """
    relato = Preenchimento()
    ligadas = {}
    for coluna, campo in CAMPOS.items():
        grau = str(minimo_por_coluna.get(coluna) or NAO).strip().lower()
        if grau == NAO or grau not in GRAUS:
            relato.desligadas.append(coluna)
            continue
        ligadas[coluna] = (campo, GRAUS[grau])
    gestor = _grau_de(col.C_GESTOR, minimo_por_coluna, relato)
    operacao = _grau_de(col.C_TIPO_DE_OPERACAO, minimo_por_coluna, relato)
    if (not ligadas and not gestor and not operacao) or conhecimento.vazia:
        return relato

    sem_gestor = {chave_de_texto(g) for g in guardioes_sem_gestor if aparar(g)}

    grafias = grafias_do_livro(livro) if operacao else {}

    for documento in documentos:
        for coluna, (campo, aceitos) in ligadas.items():
            proposta = conhecimento.propor(
                documento.de(col.X_COD_PARCEIRO), campo,
                documento.de(col.X_NOME_FANTASIA))
            _escrever(documento, coluna, proposta, aceitos, relato)

        if gestor:
            _propor_gestor(documento, conhecimento, gestor, relato, sem_gestor)

        if operacao:
            # Depois das outras: a regra mais específica de operação é
            # por CFOP + parceiro + **categoria**, e a categoria pode ter
            # acabado de ser preenchida nesta mesma passagem.
            proposta = conhecimento.propor_operacao(
                cfop_normalizado(documento.de(col.X_CFOP)),
                documento.de(col.X_COD_PARCEIRO),
                documento.categorizacao[
                    col.POSICAO_DA_CATEGORIZACAO[col.C_CATEGORIA]])
            _escrever(documento, col.C_TIPO_DE_OPERACAO, proposta, operacao,
                      relato, grafias=grafias)
    return relato


def _grau_de(coluna: str, minimo_por_coluna: dict[str, str],
             relato: Preenchimento) -> tuple[str, ...]:
    grau = str(minimo_por_coluna.get(coluna) or NAO).strip().lower()
    if grau == NAO or grau not in GRAUS:
        relato.desligadas.append(coluna)
        return ()
    return GRAUS[grau]


def _propor_gestor(documento: Documento, conhecimento: Conhecimento,
                   aceitos: tuple[str, ...], relato: Preenchimento,
                   sem_gestor: set[str]) -> None:
    """O gestor vigente do guardião que a linha tem agora."""
    guardiao = aparar(
        documento.categorizacao[col.POSICAO_DA_CATEGORIZACAO[col.C_GUARDIAO]])
    if not guardiao or chave_de_texto(guardiao) in sem_gestor:
        return
    proposta = conhecimento.gestor_de(guardiao)
    if (proposta.confianca == FIRME
            and documento.propostas.get(col.C_GUARDIAO) == SUGESTAO):
        proposta = replace(proposta, confianca=SUGESTAO)
    _escrever(documento, col.C_GESTOR, proposta, aceitos, relato)


def _escrever(documento: Documento, coluna: str, proposta, aceitos,
              relato: Preenchimento,
              grafias: dict[str, str] | None = None) -> None:
    """Escreve a proposta naquela coluna, **se** a célula estiver vazia."""
    posicao = col.POSICAO_DA_CATEGORIZACAO[coluna]
    if aparar(documento.categorizacao[posicao]):
        return                               # já classificado: não se toca
    if not proposta or proposta.confianca not in aceitos:
        return
    valor = proposta.valor
    if grafias:
        valor = grafias.get(chave_de_operacao(valor), valor)
    documento.categorizacao[posicao] = valor
    documento.propostas[coluna] = proposta.confianca
    relato.contar(coluna, proposta.confianca)


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
