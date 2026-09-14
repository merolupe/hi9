"""A leitura de ponta a ponta: dos `.zip` até a planilha.

Um XML que não é NF-e nem CT-e não é erro: o lote da SEFAZ vem cheio de
eventos, cartas de correção, cancelamentos e inutilizações. Eles são contados
à parte e ficam visíveis no resumo — quem confere precisa saber que estavam
ali e não entraram na planilha.
"""
from __future__ import annotations

import xml.etree.ElementTree as ET
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from . import cte, datas, nfe, pacote, planilha


@dataclass
class Tabela:
    """Uma aba da planilha: as colunas na ordem certa e as linhas."""

    nome: str
    colunas: list[str] = field(default_factory=list)
    linhas: list[dict[str, Any]] = field(default_factory=list)
    colunas_de_data: list[str] = field(default_factory=list)

    def __len__(self) -> int:
        return len(self.linhas)


@dataclass
class Extracao:
    """O que a leitura de um lote produziu, incluindo o que não deu certo."""

    pacotes: list[str] = field(default_factory=list)
    xmls_lidos: int = 0
    nfe: Tabela = field(default_factory=lambda: Tabela("NFe"))
    cte: Tabela = field(default_factory=lambda: Tabela("CTe"))
    nao_reconhecidos: list[str] = field(default_factory=list)
    com_erro: list[str] = field(default_factory=list)
    pacotes_com_erro: list[str] = field(default_factory=list)

    @property
    def notas(self) -> int:
        """Notas distintas — a planilha tem uma linha por item, não por nota."""
        return len({linha.get("Chave", "") for linha in self.nfe.linhas if linha.get("Chave")})

    @property
    def conhecimentos(self) -> int:
        return len(self.cte.linhas)

    def resumo(self) -> list[str]:
        """O resumo em linhas de texto, para o terminal e para a janela."""
        return [
            f"Pacotes lidos: {len(self.pacotes)}",
            f"XMLs encontrados: {self.xmls_lidos}",
            f"NF-e: {self.notas} nota(s), {len(self.nfe)} linha(s) de item",
            f"CT-e: {self.conhecimentos} documento(s)",
            f"Não reconhecidos (eventos, inutilizações etc.): {len(self.nao_reconhecidos)}",
            f"Com erro de leitura: {len(self.com_erro)}",
            f"Pacotes ilegíveis: {len(self.pacotes_com_erro)}",
        ]


def _ordenar_colunas_de_nfe(linhas: list[dict[str, Any]]) -> list[str]:
    """Colunas fixas primeiro, sementes da Reforma depois, o resto ao aparecer."""
    colunas = list(nfe.COLUNAS_BASE)
    vistas = set(colunas)
    for coluna in nfe.COLUNAS_SEMENTE:
        if coluna not in vistas:
            colunas.append(coluna)
            vistas.add(coluna)
    for linha in linhas:
        for coluna in linha:
            if coluna not in vistas:
                colunas.append(coluna)
                vistas.add(coluna)
    return colunas


def _ordenar_colunas_de_cte(linhas: list[dict[str, Any]]) -> list[str]:
    """Sem lista fixa: a ordem é a de aparição, que segue a ordem do XML."""
    colunas: list[str] = []
    vistas: set[str] = set()
    for linha in linhas:
        for coluna in linha:
            if coluna not in vistas:
                colunas.append(coluna)
                vistas.add(coluna)
    return colunas


def extrair(
    caminhos: list[Path], progresso: Callable[[int], None] | None = None
) -> Extracao:
    """Lê todos os `.zip` informados e devolve o resultado consolidado.

    Consolidado de propósito: vários `.zip` selecionados de uma vez vão para a
    mesma planilha, que é como a conferência mensal é feita.
    """
    resultado = Extracao(pacotes=[Path(c).name for c in caminhos])
    linhas_nfe: list[dict[str, Any]] = []
    linhas_cte: list[dict[str, Any]] = []

    for nome, conteudo in pacote.xmls(caminhos, resultado.pacotes_com_erro):
        resultado.xmls_lidos += 1
        try:
            raiz = ET.fromstring(conteudo)
        except ET.ParseError as erro:
            resultado.com_erro.append(f"{nome} ({erro})")
            continue

        da_nfe = nfe.processar(raiz, nome)
        if da_nfe:
            linhas_nfe.extend(da_nfe)
        else:
            do_cte = cte.processar(raiz, nome)
            if do_cte:
                linhas_cte.append(do_cte)
            else:
                resultado.nao_reconhecidos.append(nome)

        if progresso and resultado.xmls_lidos % 200 == 0:
            progresso(resultado.xmls_lidos)

    resultado.nfe.linhas = linhas_nfe
    resultado.nfe.colunas = _ordenar_colunas_de_nfe(linhas_nfe)
    resultado.cte.linhas = linhas_cte
    resultado.cte.colunas = _ordenar_colunas_de_cte(linhas_cte)

    for tabela in (resultado.nfe, resultado.cte):
        tabela.colunas, tabela.linhas, tabela.colunas_de_data = datas.separar(
            tabela.colunas, tabela.linhas
        )
    return resultado


def nome_sugerido(agora: datetime | None = None) -> str:
    """O nome do arquivo de saída. Carimbo de hora evita sobrescrever o anterior."""
    agora = agora or datetime.now()
    return f"DiXML_{agora:%Y-%m-%d_%H%M}.xlsx"


def escrever(resultado: Extracao, destino: Path) -> Path:
    return planilha.escrever(
        Path(destino),
        [
            (t.nome, t.colunas, t.linhas, t.colunas_de_data)
            for t in (resultado.nfe, resultado.cte)
        ],
    )
