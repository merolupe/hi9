"""A conta do painel — e nada além da conta.

Este módulo não sabe o que é uma célula. Ele recebe as pendências das duas
frentes e devolve os cinco blocos que o painel mostra: a tabela por categoria,
os dois TOP N, o corte por unidade e o corte por guardião. Quem desenha é o
`escrita`.

### A média de dias sai da emissão, nas duas frentes

`[FATO]` No arquivo de origem a média de mercadorias vem de `Dias Emissão
Doc`, a coluna que o VBA grava sem conversão e formata como data, e a de
serviços vem de `referência − média das emissões`. As duas contas dão o mesmo
número porque a coluna quebrada guarda o serial do Excel, e serial e contagem
de dias coincidem nessa faixa.

Aqui as duas saem da emissão. Medido contra o relatório da semana 38, dígito a
dígito: Indiretos 10,684211, Diretos 3,4, Serviços 16,743243 — exatamente os
três números do painel. A escolha não muda resultado e tira do caminho uma
coluna que a pendência nº 2 ainda pode mudar.

### O desempate dos TOP N é o de lá, escrito por extenso

`[FATO]` O painel original desempata com `V + LIN()/1000000` e `MAIOR(...)`.
O efeito é que, entre notas com o mesmo valor ou o mesmo tempo, vence a que
está **mais embaixo** na lista. Aqui isso é uma chave de ordenação — e a
ordem da lista é mercadorias primeiro, serviços depois, como lá.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Iterable, Sequence

from ..tabelas import por_ordem
from . import colunas as col
from .fontes import Pendencia


@dataclass(frozen=True)
class LinhaDeCategoria:
    """Uma linha da tabela por categoria."""

    categoria: str
    quantidade: int
    valor: float
    #: `None` quando nenhuma nota daquela categoria tem data de emissão.
    media_dias: float | None


@dataclass(frozen=True)
class Corte:
    """Um recorte do total — por unidade ou por guardião."""

    nome: str
    quantidade: dict[str, int]
    valor: dict[str, float]

    @property
    def total_da_quantidade(self) -> int:
        return sum(self.quantidade.values())

    @property
    def total_do_valor(self) -> float:
        return sum(self.valor.values())


@dataclass
class Painel:
    """Tudo o que o painel mostra, já calculado."""

    referencia: date
    categorias: list[LinhaDeCategoria] = field(default_factory=list)
    total: LinhaDeCategoria | None = None
    unidades: list[Corte] = field(default_factory=list)
    guardioes: list[Corte] = field(default_factory=list)
    #: Só os guardiões que o gráfico mostra, já cortados no limite.
    guardioes_do_grafico: list[Corte] = field(default_factory=list)
    top_dias: list[Pendencia] = field(default_factory=list)
    top_valor: list[Pendencia] = field(default_factory=list)
    #: Notas de mercadoria cuja `Categoria` não é nenhuma das do painel.
    #: Elas **não entram na conta** — e é por isso que existem nesta lista.
    sem_categoria: list[Pendencia] = field(default_factory=list)
    #: Guardiões que a configuração manda deixar fora do ranking.
    fora_do_ranking: list[str] = field(default_factory=list)


def _media(valores: Sequence[int]) -> float | None:
    return sum(valores) / len(valores) if valores else None


def _linha(categoria: str, notas: Sequence[Pendencia],
           referencia: date) -> LinhaDeCategoria:
    dias = [p.dias(referencia) for p in notas]
    return LinhaDeCategoria(
        categoria=categoria,
        quantidade=len(notas),
        valor=sum(p.valor for p in notas),
        media_dias=_media([d for d in dias if d is not None]),
    )


def _nomes_das_unidades(unidades: Iterable[dict]) -> list[str]:
    """As unidades cadastradas, na ordem da tabela e sem repetir.

    Duas linhas podem apontar para a mesma unidade — `GUAR` e `GUARA` são
    dois trechos e uma unidade só. O painel mostra a unidade uma vez.
    """
    nomes: list[str] = []
    for linha in por_ordem(unidades):
        nome = str(linha.get("unidade") or "").strip()
        if nome and nome not in nomes:
            nomes.append(nome)
    return nomes


def _corte(nome: str, notas: Sequence[Pendencia]) -> Corte:
    quantidade = {c: 0 for c in col.CATEGORIAS}
    valor = {c: 0.0 for c in col.CATEGORIAS}
    for nota in notas:
        if nota.categoria not in quantidade:
            continue
        quantidade[nota.categoria] += 1
        valor[nota.categoria] += nota.valor
    return Corte(nome, quantidade, valor)


def _ordenar(notas: Sequence[Pendencia], chave, quantas: int) -> list[Pendencia]:
    """Os `quantas` maiores por `chave`, com a última linha vencendo o empate."""
    com_chave = [(chave(p), p.posicao, p) for p in notas if chave(p) is not None]
    com_chave.sort(key=lambda t: (t[0], t[1]), reverse=True)
    return [p for _, _, p in com_chave[:quantas]]


def montar(pendencias: Sequence[Pendencia], *, referencia: date,
           unidades: Iterable[dict] = (), linhas_do_top: int = 5,
           guardioes_no_grafico: int = 8,
           fora_do_ranking: Iterable[str] = ()) -> Painel:
    """As pendências viram painel.

    Nota de mercadoria cuja categoria não é `Diretos` nem `Indiretos` **fica
    de fora de todas as contas** — como no arquivo de origem, onde o
    `CONT.SE` só conta as duas. A diferença é que aqui ela não some em
    silêncio: sai na lista `sem_categoria`, que a execução usa para bloquear.
    É a regra nº 4 aplicada ao painel.
    """
    painel = Painel(referencia=referencia)
    painel.sem_categoria = [p for p in pendencias if p.categoria not in col.CATEGORIAS]
    contadas = [p for p in pendencias if p.categoria in col.CATEGORIAS]

    painel.categorias = [
        _linha(categoria, [p for p in contadas if p.categoria == categoria],
               referencia)
        for categoria in col.CATEGORIAS
    ]
    painel.total = _linha(col.TOTAL, contadas, referencia)

    painel.unidades = [
        _corte(nome, [p for p in contadas if p.unidade == nome])
        for nome in _nomes_das_unidades(unidades)
    ]

    painel.fora_do_ranking = [str(g).strip() for g in fora_do_ranking
                              if str(g).strip()]
    excluidos = {g.casefold() for g in painel.fora_do_ranking}
    nomes: list[str] = []
    for nota in contadas:
        if nota.guardiao and nota.guardiao not in nomes:
            nomes.append(nota.guardiao)
    cortes = [_corte(nome, [p for p in contadas if p.guardiao == nome])
              for nome in nomes if nome.casefold() not in excluidos]
    # Maior primeiro; entre iguais, quem apareceu antes na lista. O arquivo de
    # origem ordena a tabela à mão antes de aplicar `MAIOR` — aqui a ordem é
    # a regra, e está escrita.
    cortes.sort(key=lambda c: (-c.total_da_quantidade, nomes.index(c.nome)))
    painel.guardioes = cortes
    painel.guardioes_do_grafico = cortes[:guardioes_no_grafico]

    painel.top_dias = _ordenar(contadas, lambda p: p.dias(referencia),
                               linhas_do_top)
    painel.top_valor = _ordenar(contadas, lambda p: p.valor, linhas_do_top)
    return painel
