"""O relatório pronto vira uma lista de pendências, das duas frentes.

A entrada deste módulo não é um export do Sankhya: é a **saída** dos outros
dois, já remodelada à mão. Por isso o reconhecimento aqui é por **aba**, e não
por arquivo: o arquivo da semana tem `Pendentes` e `Servicos` lado a lado, e o
reconhecimento por arquivo do `papeis` recusaria — e com razão, porque lá dois
papéis no mesmo arquivo significam que alguém arrastou o relatório errado.

As duas abas podem também chegar em arquivos separados, que é o caso de quem
rodou só uma das frentes na semana. As duas situações caem aqui igual.

### As sete perguntas que o painel faz de cada nota

| No painel | Em `Pendentes` | Em `Servicos` |
|---|---|---|
| categoria | `Categoria` | é sempre `Serviços` |
| guardião | `Guardião` | `Guardiao` |
| gestor | `Gestor de apoio` | `Gestor de apoio` |
| parceiro | `Nome Parceiro (Parceiro)` | `Parceiro` |
| valor | `Valor da Nota` | `Valor NFSe (Valor Bruto)` |
| emissão | `Dh. Emissão` | `Emissao` |
| unidade | derivada de `Nome Fantasia` | derivada de `Filial` |

`[FATO]` A unidade sai do mesmo lugar nas duas: no arquivo de origem o painel
conta com `COUNTIFS(...;"*"&unidade&"*")` sobre `Nome Fantasia` de um lado e
sobre `Filial` do outro. É o de-para por trecho que a ferramenta já tem —
`HINOVE (FILIAL GUARÁ)` e `HINOVE (MATRIZ)` casam pelo mesmo mecanismo.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterable, Sequence

from .. import cabecalho as cab
from ..mercadorias import colunas as merc
from ..planilha import Aba, Arquivo, ler
from ..texto import aparar
from ..valores import data_br, numero_br
from . import colunas as col

#: Quantas linhas de cada aba são lidas só para achar o cabeçalho.
LINHAS_PARA_ESPIAR = 20

#: O nome de cada coluna de serviços que o painel lê. Os de mercadorias vêm
#: de `mercadorias.colunas`, que já os declara; serviços monta o layout com os
#: rótulos embutidos na tupla `PENDENTES`, e é por isso que estes moram aqui.
S_NUMERO = "Nro Nota"
S_EMISSAO = "Emissao"
S_PARCEIRO = "Parceiro"
S_GUARDIAO = "Guardiao"
S_GESTOR = "Gestor de apoio"
S_VALOR = "Valor NFSe (Valor Bruto)"
S_FILIAL = "Filial"

#: As âncoras que identificam cada aba do relatório pronto. `Categoria` e
#: `Chave Acesso` juntas só existem na `Pendentes`; `Valor NFSe` e `Filial`
#: juntas só na `Servicos`.
ANCORAS_DE_MERCADORIAS = (merc.C_CATEGORIA, merc.X_CHAVE, merc.X_VALOR,
                          merc.X_NOME_FANTASIA)
ANCORAS_DE_SERVICOS = (S_NUMERO, S_VALOR, S_FILIAL)


class SemRelatorio(Exception):
    """Nenhum dos arquivos tem `Pendentes` ou `Servicos` para resumir."""


@dataclass(frozen=True)
class Pendencia:
    """Uma nota pendente, com o que o painel precisa saber dela.

    `posicao` não é enfeite: é o critério de desempate dos dois TOP N. No
    arquivo de origem o desempate é o truque `V + LIN()/1000000`, que faz a
    **última** linha vencer entre iguais. Aqui isso é explícito.
    """

    categoria: str
    guardiao: str
    gestor: str
    parceiro: str
    valor: float
    emissao: date | None
    unidade: str
    origem: str
    posicao: int

    def dias(self, referencia: date) -> int | None:
        """Quantos dias desde a emissão até a data de referência."""
        if self.emissao is None:
            return None
        return (referencia - self.emissao).days


@dataclass
class Leitura:
    """O que os arquivos entregaram — e o que não entregaram."""

    pendencias: list[Pendencia]
    mercadorias: int = 0
    servicos: int = 0
    #: Abas encontradas, pelo nome do arquivo. Vai para a tela: é o que
    #: responde "o painel olhou o quê".
    abas: list[str] = None                               # type: ignore[assignment]
    #: Notas sem data de emissão — ficam fora da média e dos TOP N.
    sem_emissao: int = 0
    nao_reconhecidos: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.abas is None:
            self.abas = []


def _data(valor: Any) -> date | None:
    """A data de emissão, com a hora descartada — é o `INT()` do original."""
    convertida = data_br(valor)
    if isinstance(convertida, datetime):
        return convertida.date()
    if isinstance(convertida, date):
        return convertida
    return None


def _achar_aba(arquivo: Arquivo, ancoras: Sequence[str]) -> tuple[Aba, int] | None:
    """A primeira aba do arquivo cujo cabeçalho tem todas as âncoras."""
    for aba in arquivo.abas:
        linha = cab.localizar(aba.linhas, ancoras,
                              linhas_de_busca=LINHAS_PARA_ESPIAR)
        if linha >= 0:
            return aba, linha
    return None


def _mapa(cabecalho: Sequence[Any], nomes: Sequence[str], fonte: str) -> cab.Mapa:
    return cab.mapear(cabecalho, [cab.Exigencia(nome) for nome in nomes], fonte)


def ler_mercadorias(aba: Aba, linha_do_cabecalho: int, unidade_de,
                    a_partir_de: int = 0) -> list[Pendencia]:
    """As linhas da aba `Pendentes` viram pendências de mercadoria."""
    cabecalho = aba.linha(linha_do_cabecalho)
    mapa = _mapa(cabecalho,
                 (merc.C_CATEGORIA, merc.C_GUARDIAO, merc.C_GESTOR,
                  merc.X_NOME_PARCEIRO, merc.X_VALOR, merc.X_EMISSAO,
                  merc.X_NOME_FANTASIA, merc.X_NRO_NOTA),
                 "aba Pendentes do relatório da semana")
    linhas = cab.ate_a_ultima(aba.linhas[linha_do_cabecalho + 1:], mapa,
                              merc.X_NRO_NOTA)
    saida = []
    for linha in linhas:
        if not aparar(mapa.valor(linha, merc.X_NRO_NOTA)):
            continue
        saida.append(Pendencia(
            categoria=aparar(mapa.valor(linha, merc.C_CATEGORIA)),
            guardiao=aparar(mapa.valor(linha, merc.C_GUARDIAO)),
            gestor=aparar(mapa.valor(linha, merc.C_GESTOR)),
            parceiro=aparar(mapa.valor(linha, merc.X_NOME_PARCEIRO)),
            valor=numero_br(mapa.valor(linha, merc.X_VALOR)),
            emissao=_data(mapa.valor(linha, merc.X_EMISSAO)),
            unidade=unidade_de(mapa.valor(linha, merc.X_NOME_FANTASIA)),
            origem="mercadorias",
            posicao=a_partir_de + len(saida),
        ))
    return saida


def ler_servicos(aba: Aba, linha_do_cabecalho: int, unidade_de,
                 a_partir_de: int = 0) -> list[Pendencia]:
    """As linhas da aba `Servicos` viram pendências de serviço.

    A categoria não é lida: serviço **é** a categoria. Não há coluna dela no
    relatório de serviços, e inventar uma seria inventar classificação.
    """
    cabecalho = aba.linha(linha_do_cabecalho)
    mapa = _mapa(cabecalho,
                 (S_NUMERO, S_EMISSAO, S_PARCEIRO, S_GUARDIAO, S_GESTOR,
                  S_VALOR, S_FILIAL),
                 "aba Servicos do relatório da semana")
    linhas = cab.ate_a_ultima(aba.linhas[linha_do_cabecalho + 1:], mapa, S_NUMERO)
    saida = []
    for linha in linhas:
        if not aparar(mapa.valor(linha, S_NUMERO)):
            continue
        saida.append(Pendencia(
            categoria=col.CATEGORIA_DE_SERVICOS,
            guardiao=aparar(mapa.valor(linha, S_GUARDIAO)),
            gestor=aparar(mapa.valor(linha, S_GESTOR)),
            parceiro=aparar(mapa.valor(linha, S_PARCEIRO)),
            valor=numero_br(mapa.valor(linha, S_VALOR)),
            emissao=_data(mapa.valor(linha, S_EMISSAO)),
            unidade=unidade_de(mapa.valor(linha, S_FILIAL)),
            origem="servicos",
            posicao=a_partir_de + len(saida),
        ))
    return saida


def ler_relatorios(caminhos: Iterable[Path | str], unidade_de) -> Leitura:
    """Acha as duas abas onde elas estiverem e devolve as pendências.

    A ordem é a do painel: mercadorias primeiro, serviços depois. É ela que
    decide o desempate dos TOP N, então não é arbitrária — é a mesma ordem em
    que o arquivo de origem empilha as duas frentes na aba auxiliar.
    """
    arquivos = [ler(caminho) for caminho in caminhos]
    pendencias: list[Pendencia] = []
    leitura = Leitura(pendencias)
    usados: set[str] = set()

    for arquivo in arquivos:
        achado = _achar_aba(arquivo, ANCORAS_DE_MERCADORIAS)
        if achado is None:
            continue
        lidas = ler_mercadorias(*achado, unidade_de, len(pendencias))
        pendencias.extend(lidas)
        leitura.mercadorias += len(lidas)
        leitura.abas.append(f"{arquivo.nome} · aba '{achado[0].nome}'")
        usados.add(arquivo.nome)

    for arquivo in arquivos:
        achado = _achar_aba(arquivo, ANCORAS_DE_SERVICOS)
        if achado is None:
            continue
        lidas = ler_servicos(*achado, unidade_de, len(pendencias))
        pendencias.extend(lidas)
        leitura.servicos += len(lidas)
        leitura.abas.append(f"{arquivo.nome} · aba '{achado[0].nome}'")
        usados.add(arquivo.nome)

    leitura.nao_reconhecidos = tuple(
        arquivo.nome for arquivo in arquivos if arquivo.nome not in usados)
    leitura.sem_emissao = sum(1 for p in pendencias if p.emissao is None)

    if not pendencias and not leitura.abas:
        raise SemRelatorio(
            "Nenhum arquivo tem a aba 'Pendentes' nem a aba 'Servicos'. "
            "O resumo é montado sobre o relatório da semana já gerado e "
            "classificado, não sobre os relatórios de origem."
        )
    return leitura
