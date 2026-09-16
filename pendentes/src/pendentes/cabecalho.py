"""Achar a linha do cabeçalho e mapear coluna — **por nome, nunca por posição**.

O relatório do Sankhya não começa na linha 1: antes do cabeçalho vêm título,
data de emissão e usuário. E o cabeçalho não fica sempre na mesma linha nem
com as colunas sempre na mesma ordem. Procurar pelo nome é o que faz a
ferramenta sobreviver a isso.

Duas unificações em relação ao VBA, que fazia a mesma coisa de dois jeitos:

| | mercadorias | serviços | aqui |
|---|---|---|---|
| Janela de busca | 5 linhas × 200 colunas | 10 linhas × 400 colunas | **15 × 400** |
| Coluna faltando | lista **todas** as faltantes | aborta na **primeira** | lista todas |

A janela maior é a soma das duas, com folga: espiar cinco linhas a mais não
custa nada e evita o aborto por um relatório com uma linha de título a mais.

A ergonomia da lista completa é a de mercadorias, e ela é estritamente melhor:
quem exporta o relatório de novo corrige as cinco colunas de uma vez, em vez
de descobrir uma por rodada. A mensagem diz o nome de cada faltante e onde
cadastrar o nome novo, que é o que o Fiscalbot já faz.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Sequence

from .texto import chave_de_texto

#: Quantas linhas do começo do arquivo podem esconder o cabeçalho.
LINHAS_DE_BUSCA = 15
#: Até que coluna procurar. O Portal de Compras chega a 268 colunas.
COLUNAS_DE_BUSCA = 400


class ColunasFaltando(Exception):
    """Faltou coluna obrigatória. A mensagem traz **todas** as faltantes."""

    def __init__(self, fonte: str, faltantes: Sequence[str]) -> None:
        self.fonte = fonte
        self.faltantes = list(faltantes)
        super().__init__(
            f"O relatório {fonte} não trouxe estas colunas:\n\n  "
            + "\n  ".join(self.faltantes)
            + "\n\nSe a exportação mudou o nome de alguma delas, cadastre o "
              "nome novo em Sinônimos, na tela de configuração — não é preciso "
              "mexer em código. Se o nome está certo, confira o layout de "
              "exportação no Sankhya."
        )


class CabecalhoNaoEncontrado(Exception):
    """Nenhuma das primeiras linhas parece o cabeçalho procurado."""


@dataclass(frozen=True)
class Exigencia:
    """Uma coluna esperada: o nome canônico, os sinônimos e se é obrigatória."""

    nome: str
    sinonimos: tuple[str, ...] = ()
    obrigatoria: bool = True

    @property
    def nomes_aceitos(self) -> tuple[str, ...]:
        return (self.nome, *self.sinonimos)


@dataclass(frozen=True)
class Mapa:
    """Em que coluna está cada nome. `-1` quando a coluna não veio."""

    posicoes: dict[str, int]
    ausentes: tuple[str, ...] = ()

    def __getitem__(self, nome: str) -> int:
        return self.posicoes.get(nome, -1)

    def tem(self, nome: str) -> bool:
        return self.posicoes.get(nome, -1) >= 0

    def valor(self, linha: Sequence[Any], nome: str, padrao: Any = "") -> Any:
        """O valor daquela coluna na linha, ou `padrao` se a coluna não veio."""
        i = self.posicoes.get(nome, -1)
        if i < 0 or i >= len(linha):
            return padrao
        return linha[i]


def _normalizada(linha: Sequence[Any]) -> list[str]:
    return [chave_de_texto(v) for v in linha[:COLUNAS_DE_BUSCA]]


def localizar(linhas: Sequence[Sequence[Any]], ancoras: Iterable[str], *,
              linhas_de_busca: int = LINHAS_DE_BUSCA) -> int:
    """O índice da linha que contém **todas** as âncoras. `-1` se nenhuma tem.

    Uma âncora só não basta para separar os relatórios entre si — `Chave
    Acesso` está no XML e na Conferência de Entradas, `Nro Nota` está no XML e
    na planilha da semana anterior. É o conjunto que identifica.
    """
    alvos = [chave_de_texto(a) for a in ancoras if chave_de_texto(a)]
    if not alvos:
        return -1
    for i, linha in enumerate(linhas[:linhas_de_busca]):
        presentes = set(_normalizada(linha))
        if all(alvo in presentes for alvo in alvos):
            return i
    return -1


def exigir_cabecalho(linhas: Sequence[Sequence[Any]], ancoras: Iterable[str],
                     fonte: str, *,
                     linhas_de_busca: int = LINHAS_DE_BUSCA) -> int:
    """Como `localizar`, mas estoura nomeando a âncora que não apareceu."""
    indice = localizar(linhas, ancoras, linhas_de_busca=linhas_de_busca)
    if indice < 0:
        procuradas = ", ".join(f"'{a}'" for a in ancoras)
        raise CabecalhoNaoEncontrado(
            f"Não achei o cabeçalho do relatório {fonte} nas "
            f"{linhas_de_busca} primeiras linhas. Procurei por {procuradas}."
        )
    return indice


def achar(cabecalho: Sequence[Any], nome: str,
          sinonimos: Iterable[str] = ()) -> int:
    """A coluna pelo nome canônico ou por um dos sinônimos. `-1` se não veio."""
    normalizado = _normalizada(cabecalho)
    for candidato in (nome, *sinonimos):
        alvo = chave_de_texto(candidato)
        if not alvo:
            continue
        for i, atual in enumerate(normalizado):
            if atual == alvo:
                return i
    return -1


def achar_por_prefixo(cabecalho: Sequence[Any], prefixo: str) -> int:
    """A coluna cujo nome **começa** com o prefixo. `-1` se não veio.

    Existe por causa de uma coluna só: `Retorno semana 30` muda de nome toda
    semana, e procurá-la pelo nome inteiro é procurá-la pelo número da semana
    passada — que é justamente o que ninguém quer ter de saber.
    """
    alvo = chave_de_texto(prefixo)
    if not alvo:
        return -1
    for i, atual in enumerate(_normalizada(cabecalho)):
        if atual.startswith(alvo):
            return i
    return -1


def mapear(cabecalho: Sequence[Any], exigencias: Iterable[Exigencia],
           fonte: str) -> Mapa:
    """Localiza todas as colunas de uma vez. Estoura listando **todas** que faltam."""
    posicoes: dict[str, int] = {}
    faltantes: list[str] = []
    ausentes: list[str] = []
    for exigencia in exigencias:
        indice = achar(cabecalho, exigencia.nome, exigencia.sinonimos)
        posicoes[exigencia.nome] = indice
        if indice < 0:
            (faltantes if exigencia.obrigatoria else ausentes).append(exigencia.nome)
    if faltantes:
        raise ColunasFaltando(fonte, faltantes)
    return Mapa(posicoes, tuple(ausentes))


def exigencias_de(declaradas: Iterable[dict]) -> tuple[Exigencia, ...]:
    """As exigências vindas do parâmetro: `nome`, `sinonimos`, `obrigatoria`."""
    saida = []
    for linha in declaradas:
        bruto = linha.get("sinonimos") or ()
        if isinstance(bruto, str):
            bruto = [p.strip() for p in bruto.split(";")]
        saida.append(Exigencia(
            nome=str(linha.get("nome", "")).strip(),
            sinonimos=tuple(str(s).strip() for s in bruto if str(s).strip()),
            obrigatoria=bool(linha.get("obrigatoria", True)),
        ))
    return tuple(e for e in saida if e.nome)
