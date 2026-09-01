"""Orquestra as camadas 1 a 4 e produz a base tratada.

Entrada: o Livro Fiscal do mês.
Saída: uma linha tratada para cada linha do Livro, com carga equalizada,
categoria, regra aplicada e rastreabilidade — mais a lista de pendências.
"""
from __future__ import annotations

import collections
import datetime as dt
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .ingestao import Livro, ler_livro_fiscal
from .nucleo.carga import ResultadoCarga, Situacao, equalizar
from .nucleo.classificacao import ResultadoClassificacao, classificar
from .parametros import Parametros, carregar


@dataclass
class LinhaTratada:
    """Uma linha do Livro com tudo que o motor concluiu sobre ela."""

    origem: Any                      # LinhaLivro
    carga: ResultadoCarga
    classificacao: ResultadoClassificacao

    @property
    def relevante(self) -> bool:
        return self.carga.relevante_para_icms

    @property
    def pendencias(self) -> list[str]:
        motivos = []
        if self.carga.e_pendencia:
            motivos.append(f"{self.carga.situacao.value}: {self.carga.regra}")
        if self.relevante and self.classificacao.e_pendencia:
            motivos.append(f"SEM REGRA: {self.classificacao.regra}")
        return motivos

    @property
    def alertas(self) -> list[str]:
        return [self.carga.alerta] if self.carga.alerta else []


@dataclass
class BaseTratada:
    linhas: list[LinhaTratada]
    livro: Livro
    parametros: Parametros
    gerado_em: dt.datetime = field(default_factory=dt.datetime.now)

    # -- recortes -------------------------------------------------------

    @property
    def relevantes(self) -> list[LinhaTratada]:
        return [t for t in self.linhas if t.relevante]

    @property
    def com_pendencia(self) -> list[LinhaTratada]:
        return [t for t in self.linhas if t.pendencias]

    @property
    def com_alerta(self) -> list[LinhaTratada]:
        return [t for t in self.linhas if t.alertas]

    @property
    def competencia(self) -> str:
        comps = sorted(self.livro.competencias)
        return comps[0] if len(comps) == 1 else "|".join(comps)

    # -- agregações -----------------------------------------------------

    def por_estabelecimento_carga(self) -> dict[tuple[str, str, Any], dict[str, float]]:
        """Soma por estabelecimento × entrada/saída × carga efetiva.

        Mesmo recorte da aba `Dinamica` da apuração manual, e por isso o que o
        teste de regressão compara.
        """
        somas: dict[tuple, dict[str, float]] = collections.defaultdict(
            lambda: {"valor_contabil": 0.0, "base_icms": 0.0, "valor_icms": 0.0, "linhas": 0}
        )
        for t in self.linhas:
            d = t.origem.dados
            if t.carga.situacao is Situacao.CIAP:
                carga: Any = "CIAP"
            elif t.carga.carga is not None:
                carga = t.carga.carga
            else:
                carga = None
            chave = (d.get("estabelecimento"), d.get("entrada_saida"), carga)
            alvo = somas[chave]
            alvo["valor_contabil"] += d.get("valor_contabil") or 0.0
            alvo["base_icms"] += d.get("base_icms") or 0.0
            alvo["valor_icms"] += d.get("valor_icms") or 0.0
            alvo["linhas"] += 1
        return dict(somas)

    def por_categoria(self) -> dict[str, dict[str, float]]:
        somas: dict[str, dict[str, float]] = collections.defaultdict(
            lambda: {"linhas": 0, "valor_icms": 0.0}
        )
        for t in self.relevantes:
            alvo = somas[t.classificacao.categoria]
            alvo["linhas"] += 1
            alvo["valor_icms"] += t.origem.dados.get("valor_icms") or 0.0
        return dict(somas)

    @property
    def periodo(self) -> str:
        """O intervalo de datas que o livro cobre, em texto."""
        intervalo = self.livro.periodo
        if intervalo is None:
            return "(o arquivo não traz data de movimento)"
        inicio, fim = intervalo
        return f"{inicio.strftime('%d/%m/%Y')} a {fim.strftime('%d/%m/%Y')}"

    def resumo(self) -> dict[str, Any]:
        situacoes = collections.Counter(t.carga.situacao.value for t in self.linhas)
        return {
            "competencia": self.competencia,
            "arquivo": self.livro.arquivo.name,
            "sha256": self.livro.sha256,
            "periodo": self.periodo,
            "linhas_no_livro": len(self.livro),
            "linhas_relevantes": len(self.relevantes),
            "pendencias": len(self.com_pendencia),
            "alertas": len(self.com_alerta),
            "situacoes": dict(situacoes),
            "categorias": self.por_categoria(),
            "gerado_em": self.gerado_em.isoformat(timespec="seconds"),
        }

    @property
    def pode_encerrar(self) -> bool:
        """Pendência crítica bloqueia o encerramento da competência."""
        return not self.com_pendencia


def tratar(
    livro: Livro | Path | str,
    parametros: Parametros | Path | str | None = None,
    aba: str | None = None,
) -> BaseTratada:
    """Aplica as camadas 1 a 4 sobre o Livro Fiscal."""
    if not isinstance(livro, Livro):
        livro = ler_livro_fiscal(livro, aba=aba)
    if not isinstance(parametros, Parametros):
        parametros = carregar(parametros)

    linhas = [
        LinhaTratada(
            origem=linha,
            carga=(c := equalizar(linha, parametros)),
            classificacao=(
                classificar(linha, parametros)
                if c.relevante_para_icms
                else ResultadoClassificacao(
                    categoria="—", regra="linha fora da apuração de ICMS"
                )
            ),
        )
        for linha in livro
    ]
    return BaseTratada(linhas=linhas, livro=livro, parametros=parametros)
