"""A base contra um relatório já classificado: quanto ela acertaria.

Sem esta medição a base é uma promessa. Com ela, a decisão de preencher ou só
sugerir deixa de ser preferência e passa a ter número — por campo, e por grau
de confiança.

### O que faz dela uma medição honesta

`[FATO]` A base de 17/09/2026 foi construída sobre os relatórios **até a
semana 37**, e o campo `ultimo_relatorio_classificado` do próprio arquivo diz
isso. Rodar a simulação contra a semana 38 é medir contra uma semana que a
base não viu. Rodar contra a 37 mediria a base contra ela mesma, e o resultado
seria bonito e inútil — por isso a simulação **avisa** quando a semana do
arquivo não é posterior à da base.

O que ela não consegue garantir: que a classificação do relatório usado como
gabarito tenha sido feita **sem** consultar a mesma base. Isso é do processo,
não do dado, e está dito na tela em vez de virar uma taxa de acerto sem
ressalva.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

from .. import cabecalho as cab
from ..mercadorias import colunas as merc
from ..planilha import ler
from ..texto import aparar, chave_de_texto
from .base import FIRME, SUGESTAO, Conhecimento
from .importacao import cfop_normalizado

#: As âncoras da aba `Pendentes` de um relatório já classificado.
ANCORAS = (merc.C_CATEGORIA, merc.C_GUARDIAO, merc.X_CHAVE, merc.X_COD_PARCEIRO)
LINHAS_PARA_ESPIAR = 20


class SemRelatorioClassificado(Exception):
    """Nenhum arquivo tem uma aba `Pendentes` já classificada."""


@dataclass
class Placar:
    """Quanto a base acertou num campo, separado por grau de confiança."""

    campo: str
    acertos: dict[str, int] = field(default_factory=dict)
    erros: dict[str, int] = field(default_factory=dict)
    sem_proposta: int = 0
    #: Os casos em que a base afirmou com confiança firme e errou. São os que
    #: importam: um erro de sugestão custa uma conferência, um erro firme
    #: entraria na planilha.
    erros_firmes: list[str] = field(default_factory=list)

    def total(self, grau: str) -> int:
        return self.acertos.get(grau, 0) + self.erros.get(grau, 0)

    def taxa(self, grau: str) -> float | None:
        total = self.total(grau)
        return self.acertos.get(grau, 0) / total if total else None

    def linha(self, grau: str) -> str:
        taxa = self.taxa(grau)
        if taxa is None:
            return f"{grau}: nenhuma proposta"
        return (f"{grau}: {self.acertos.get(grau, 0)} de {self.total(grau)} "
                f"({taxa * 100:.0f}%)")


@dataclass
class Simulacao:
    """O resultado da medição, pronto para a tela."""

    linhas: int = 0
    semana_da_base: int = 0
    placares: dict[str, Placar] = field(default_factory=dict)
    avisos: list[str] = field(default_factory=list)
    arquivos: list[str] = field(default_factory=list)

    def titulo(self) -> str:
        categoria = self.placares.get("categoria")
        taxa = categoria.taxa(FIRME) if categoria else None
        medida = "—" if taxa is None else f"{taxa * 100:.0f}%"
        return (f"Simulação sobre {self.linhas} nota(s) classificada(s) — "
                f"categoria com evidência firme: {medida}")

    def fichas(self) -> list[tuple[str, str]]:
        saida = []
        for campo, placar in self.placares.items():
            saida.append((f"{campo} — firme", str(placar.total(FIRME))))
        return saida

    def listas(self) -> list[tuple[str, list[str], str]]:
        saida: list[tuple[str, list[str], str]] = []
        firmes_errados = [linha for placar in self.placares.values()
                          for linha in placar.erros_firmes]
        if firmes_errados:
            saida.append(("Afirmou com evidência firme e errou",
                          firmes_errados, "erro"))
        if self.avisos:
            saida.append(("O que a medição não garante", self.avisos, "atencao"))
        for campo, placar in self.placares.items():
            saida.append((
                f"{campo}",
                [placar.linha(FIRME), placar.linha(SUGESTAO),
                 f"sem proposta: {placar.sem_proposta}"],
                "neutro"))
        return saida


def _achar_aba(arquivo) -> tuple[Any, int] | None:
    for aba in arquivo.abas:
        linha = cab.localizar(aba.linhas, ANCORAS,
                              linhas_de_busca=LINHAS_PARA_ESPIAR)
        if linha >= 0:
            return aba, linha
    return None


def _contar(placar: Placar, proposta, real: str, rotulo: str) -> None:
    if not proposta.valor:
        placar.sem_proposta += 1
        return
    grau = proposta.confianca
    if chave_de_texto(proposta.valor) == chave_de_texto(real):
        placar.acertos[grau] = placar.acertos.get(grau, 0) + 1
        return
    placar.erros[grau] = placar.erros.get(grau, 0) + 1
    if grau == FIRME:
        placar.erros_firmes.append(
            f"{rotulo}: a base diria '{proposta.valor}', o relatório diz "
            f"'{real or '(vazio)'}'")


def simular(caminhos: Iterable[Path | str], conhecimento: Conhecimento, *,
            semana: int = 0) -> Simulacao:
    """Roda a base sobre cada linha classificada e conta acerto e erro.

    Linha sem o campo preenchido no relatório não entra na conta daquele
    campo: ela não é gabarito de nada — é justamente o que a base existe para
    ajudar a preencher.
    """
    simulacao = Simulacao(semana_da_base=conhecimento.ultimo_relatorio_classificado)
    campos = {"categoria": Placar("categoria"), "guardiao": Placar("guardiao"),
              "operacao": Placar("operacao")}
    simulacao.placares = campos

    for caminho in caminhos:
        arquivo = ler(caminho)
        achado = _achar_aba(arquivo)
        if achado is None:
            continue
        aba, cabecalho = achado
        simulacao.arquivos.append(f"{arquivo.nome} · aba '{aba.nome}'")
        mapa = cab.mapear(
            aba.linha(cabecalho),
            [cab.Exigencia(nome) for nome in
             (merc.X_NRO_NOTA, merc.X_COD_PARCEIRO, merc.X_NOME_FANTASIA,
              merc.X_CFOP, merc.C_CATEGORIA, merc.C_GUARDIAO,
              merc.C_TIPO_DE_OPERACAO)],
            "aba Pendentes do relatório classificado")
        for linha in cab.ate_a_ultima(aba.linhas[cabecalho + 1:], mapa,
                                      merc.X_NRO_NOTA):
            if not aparar(mapa.valor(linha, merc.X_NRO_NOTA)):
                continue
            simulacao.linhas += 1
            codigo = mapa.valor(linha, merc.X_COD_PARCEIRO)
            fantasia = mapa.valor(linha, merc.X_NOME_FANTASIA)
            rotulo = f"nota {aparar(mapa.valor(linha, merc.X_NRO_NOTA))}"
            categoria = aparar(mapa.valor(linha, merc.C_CATEGORIA))

            for campo, real in (("categoria", categoria),
                                ("guardiao",
                                 aparar(mapa.valor(linha, merc.C_GUARDIAO)))):
                if not real:
                    continue
                _contar(campos[campo], conhecimento.propor(codigo, campo, fantasia),
                        real, rotulo)

            operacao = aparar(mapa.valor(linha, merc.C_TIPO_DE_OPERACAO))
            if operacao:
                _contar(campos["operacao"], conhecimento.propor_operacao(
                    cfop_normalizado(mapa.valor(linha, merc.X_CFOP)),
                    codigo, categoria), operacao, rotulo)

    if not simulacao.linhas:
        raise SemRelatorioClassificado(
            "Nenhum arquivo tem uma aba 'Pendentes' com as colunas de "
            "classificação preenchidas. A simulação precisa de um relatório "
            "já classificado para usar como gabarito."
        )

    if semana and simulacao.semana_da_base and semana <= simulacao.semana_da_base:
        simulacao.avisos.append(
            f"o relatório é da semana {semana} e a base aprendeu até a "
            f"{simulacao.semana_da_base}: a medição é sobre semana que a base "
            f"já viu, e a taxa de acerto não significa nada")
    simulacao.avisos.append(
        "a medição não sabe se quem classificou este relatório consultou a "
        "mesma base — se consultou, a taxa mede concordância, não acerto")
    return simulacao
