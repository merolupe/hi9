"""Camadas 5 a 8 — apuração de ICMS por estabelecimento.

Aplica o regime de cada filial sobre a base tratada e consolida crédito bruto,
crédito mantido, estorno e débito. Centralização de SP e benefício fiscal de
Rio Brilhante ficam para as entregas seguintes.
"""
from __future__ import annotations

import collections
from dataclasses import dataclass, field

from .base_tratada import BaseTratada
from .nucleo.estorno import ResultadoEstorno, calcular
from .parametros import Parametros


@dataclass
class ApuracaoFilial:
    """Resultado de um estabelecimento, antes de centralização e benefício."""

    estabelecimento: str
    uf: str
    regime: str
    credito_bruto: float = 0.0
    credito_mantido: float = 0.0
    estorno: float = 0.0
    debito: float = 0.0
    linhas: int = 0
    por_carga: dict = field(default_factory=lambda: collections.defaultdict(
        lambda: {"credito_bruto": 0.0, "credito_mantido": 0.0, "estorno": 0.0}
    ))

    @property
    def saldo(self) -> float:
        """Positivo = a recolher; negativo = credor. Sem DIFAL e sem ajustes."""
        return self.debito - self.credito_mantido

    @property
    def confere(self) -> bool:
        return abs(self.credito_mantido + self.estorno - self.credito_bruto) < 0.005


@dataclass
class Apuracao:
    filiais: dict[str, ApuracaoFilial]
    base: BaseTratada

    @property
    def total(self) -> ApuracaoFilial:
        t = ApuracaoFilial(estabelecimento="TOTAL", uf="", regime="")
        for f in self.filiais.values():
            t.credito_bruto += f.credito_bruto
            t.credito_mantido += f.credito_mantido
            t.estorno += f.estorno
            t.debito += f.debito
            t.linhas += f.linhas
        return t

    @property
    def inconsistentes(self) -> list[ApuracaoFilial]:
        """Filiais em que crédito mantido + estorno ≠ crédito bruto."""
        return [f for f in self.filiais.values() if not f.confere]


def apurar(base: BaseTratada, parametros: Parametros | None = None) -> Apuracao:
    params = parametros or base.parametros
    uf_de = {
        " ".join(str(f["nome"]).split()).casefold(): f["uf"]
        for f in params.filiais.get("filiais") or []
    }

    filiais: dict[str, ApuracaoFilial] = {}
    for tratada in base.linhas:
        resultado: ResultadoEstorno = calcular(tratada, params)
        if not (resultado.credito_bruto or resultado.debito):
            continue

        nome = tratada.origem.dados["estabelecimento"]
        chave = " ".join(str(nome).split())
        filial = filiais.get(chave)
        if filial is None:
            filial = filiais[chave] = ApuracaoFilial(
                estabelecimento=chave,
                uf=uf_de.get(chave.casefold(), ""),
                regime=resultado.regime,
            )
        filial.credito_bruto += resultado.credito_bruto
        filial.credito_mantido += resultado.credito_mantido
        filial.estorno += resultado.estorno
        filial.debito += resultado.debito
        filial.linhas += 1

        if resultado.credito_bruto:
            carga = tratada.carga.carga if tratada.carga.carga is not None else "CIAP"
            alvo = filial.por_carga[carga]
            alvo["credito_bruto"] += resultado.credito_bruto
            alvo["credito_mantido"] += resultado.credito_mantido
            alvo["estorno"] += resultado.estorno

    return Apuracao(filiais=filiais, base=base)
