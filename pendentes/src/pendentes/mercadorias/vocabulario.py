"""Unidade, categoria e guardião — o que a ferramenta consegue reconhecer.

Este módulo existe para responder uma pergunta só: **a ferramenta sabe dizer o
que esta coisa é?** Quando não sabe, o registro não desaparece e não é
adivinhado — ele fica visível com o texto original e o caso vai para a lista
que bloqueia o encerramento da semana. É a regra nº 4 do `CLAUDE.md` traduzida
para este domínio.

`[FATO]` No VBA as três derivações existem dentro do Resumo Executivo, e
nenhuma delas avisa nada: unidade não reconhecida vira o texto cru no painel,
categoria fora da lista idem, e nota sem guardião aparece como
`(sem guardião)`. Ninguém conta, e portanto ninguém corrige.

**O Resumo Executivo saiu do porte** (decisão do Compliance Tributário de
15/09/2026) e vira outra coisa, com três categorias e as duas frentes juntas.
A agregação, os TOP N e os quatro gráficos foram com ele. A derivação ficou —
porque ela não é ornamento do painel: é o que torna possível dizer que alguma
coisa não foi reconhecida.

### A ordem é a regra, nas duas tabelas

`[FATO]` `CORUMB` é testado **antes** de `GUAR`. Inverter os dois faz qualquer
fantasia de Corumbá que contenha "GUAR" virar Guará, sem erro e sem aviso.

`[FATO]` `indireto` é testado **antes** de `direto`, e pelo mesmo motivo com
outro nome: "Indiretos" contém "direto" como subcadeia, e na ordem errada toda
categoria indireta vira direta. O comentário do VBA registra a armadilha nesses
termos.

Nas duas, a ordem deixa de ser uma sequência de `ElseIf` enterrada no código e
vira a coluna `ordem` da tabela, visível e editável na tela.

### As tabelas vazias não validam nada

A tabela de unidades **nasce vazia** e assim continua numa máquina nova: nome
de unidade é dado da empresa e não entra no repositório (regra nº 1). Enquanto
ela não for cadastrada, a derivação não acontece e **nada bloqueia** — validar
contra uma tabela vazia reprovaria todas as notas, toda semana. O mesmo vale
para as categorias e para a lista de guardiões, que nasce vazia por decisão
(pendência nº 6): sem lista cadastrada, qualquer texto entra em `Guardião`,
que é o comportamento de hoje.

O cadastro das unidades são cinco linhas. É a diferença entre a ferramenta
dizer "três unidades não reconhecidas, e são estas" e não dizer nada.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Sequence

from ..tabelas import primeira_que_casa
from ..texto import aparar, chave_de_texto

#: O que o VBA grava quando a fantasia está vazia.
SEM_UNIDADE = "(sem unidade)"
#: O que o VBA grava quando a categoria está vazia — e o comentário explica:
#: registros ainda não classificados continuam visíveis em vez de sumirem da
#: contagem.
NAO_CLASSIFICADO = "Não classificado"


@dataclass(frozen=True)
class Reconhecimento:
    """O valor derivado e se ele veio de uma linha cadastrada."""

    valor: str
    reconhecido: bool

    def __bool__(self) -> bool:                          # pragma: no cover
        return self.reconhecido


def unidade_de(fantasia, unidades: Sequence[dict]) -> Reconhecimento:
    """A unidade que o `Nome Fantasia` indica, pela tabela, na ordem dela.

    Fantasia vazia devolve `(sem unidade)` **reconhecido**: ausência de nome
    não é nome estranho, e bloquear por isso seria bloquear por um campo que a
    regra A1 já usou para descartar o que não era nosso.

    Fantasia que não casa com nenhum trecho devolve **o texto original**, como
    o VBA, e `reconhecido=False` — é o fallback que o comentário do código
    justifica: *nenhum registro desaparece silenciosamente do resumo*.
    """
    texto = aparar(fantasia)
    if not texto:
        return Reconhecimento(SEM_UNIDADE, True)
    linha = primeira_que_casa(texto, list(unidades), campo="trecho")
    if linha is None:
        return Reconhecimento(texto, not unidades)
    return Reconhecimento(str(linha.get("unidade") or texto), True)


def categoria_de(valor, categorias: Sequence[dict]) -> Reconhecimento:
    """A categoria normalizada, pela tabela, na ordem dela.

    Vazia devolve `Não classificado`, **reconhecida**: a nota que ninguém
    classificou ainda é o estado normal da segunda-feira, não um erro.
    """
    texto = aparar(valor)
    if not texto:
        return Reconhecimento(NAO_CLASSIFICADO, True)
    linha = primeira_que_casa(texto, list(categorias), campo="trecho")
    if linha is None:
        return Reconhecimento(texto, not categorias)
    return Reconhecimento(str(linha.get("categoria") or texto), True)


def guardiao_reconhecido(valor, guardioes: Sequence[str]) -> bool:
    """O `Guardião` está na lista cadastrada? Lista vazia aceita qualquer um."""
    if not guardioes:
        return True
    alvo = chave_de_texto(valor)
    if not alvo:
        return False
    return alvo in {chave_de_texto(g) for g in guardioes}


@dataclass
class NaoReconhecidos:
    """O que a ferramenta não soube dizer o que é, com quantas notas cada um."""

    unidades: dict[str, int] = field(default_factory=dict)
    categorias: dict[str, int] = field(default_factory=dict)
    sem_guardiao: int = 0

    def registrar_unidade(self, texto: str) -> None:
        self.unidades[texto] = self.unidades.get(texto, 0) + 1

    def registrar_categoria(self, texto: str) -> None:
        self.categorias[texto] = self.categorias.get(texto, 0) + 1

    @property
    def nada_a_dizer(self) -> bool:
        return not (self.unidades or self.categorias or self.sem_guardiao)

    def _listar(self, quais: dict[str, int], rotulo: str) -> list[str]:
        if not quais:
            return []
        em_ordem = sorted(quais.items(), key=lambda par: (-par[1], par[0]))
        mostrados = ", ".join(
            f'"{texto}" ({quantas} nota{"s" if quantas > 1 else ""})'
            for texto, quantas in em_ordem[:5]
        )
        resto = len(em_ordem) - 5
        return [f"{len(em_ordem)} {rotulo}: {mostrados}"
                + (f" e mais {resto}" if resto > 0 else "")]

    def bloqueios(self) -> list[str]:
        """O que vai para a lista vermelha da tela, já em texto."""
        itens = self._listar(self.unidades, "unidade(s) não reconhecida(s)")
        itens += self._listar(self.categorias, "categoria(s) não reconhecida(s)")
        if self.sem_guardiao:
            itens.append(
                f"{self.sem_guardiao} nota(s) sem guardião válido — a lista de "
                f"guardiões está cadastrada e estas não estão nela"
            )
        return itens


def conferir(fantasias_e_categorias: Iterable[tuple], *,
             unidades: Sequence[dict], categorias: Sequence[dict],
             guardioes: Sequence[str]) -> NaoReconhecidos:
    """Passa a lista de (fantasia, categoria, guardião) e acumula o que não casa."""
    relato = NaoReconhecidos()
    for fantasia, categoria, guardiao in fantasias_e_categorias:
        if unidades:
            achada = unidade_de(fantasia, unidades)
            if not achada.reconhecido:
                relato.registrar_unidade(achada.valor)
        if categorias:
            achada = categoria_de(categoria, categorias)
            if not achada.reconhecido:
                relato.registrar_categoria(achada.valor)
        if guardioes and not guardiao_reconhecido(guardiao, guardioes):
            relato.sem_guardiao += 1
    return relato
