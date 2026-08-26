"""Camadas 5 a 8 — apuração de ICMS por estabelecimento.

Aplica o regime de cada filial sobre a base tratada e consolida crédito bruto,
crédito mantido, estorno e débito. Onde a UF exige — hoje MS —, o resultado sai
também segregado por atividade, porque é a segregação que dimensiona o
benefício fiscal.

Centralização de SP e DIFAL ficam para as entregas seguintes.
"""
from __future__ import annotations

import collections
from dataclasses import dataclass, field

from .base_tratada import BaseTratada
from .nucleo import atividade as ativ
from .nucleo import centralizacao as centr
from .nucleo.beneficio import ResultadoBeneficio
from .nucleo.beneficio import calcular as calcular_beneficio
from .nucleo.estorno import ResultadoEstorno, calcular
from .parametros import Parametros


@dataclass
class AjustesDaApuracao:
    """Lançamentos que não nascem de documento no Livro Fiscal.

    São as linhas 002, 003 e 006 do Registro de Apuração — outros débitos,
    estornos de créditos por ajuste e outros créditos. Em Julho/2026, para Rio
    Brilhante: R$ 99.412,10 de saldo devedor recebido do estabelecimento
    centralizador, R$ 3.865,30 de estorno de créditos e R$ 73.722,69 de crédito
    acumulado transferido.

    Hoje vêm de quem chama a apuração; na Entrega 2 virão de `ajustes.xlsx`.
    """

    # {estabelecimento: {atividade: valor}}
    estorno_de_credito: dict[str, dict[str, float]] = field(default_factory=dict)
    outros_debitos: dict[str, dict[str, float]] = field(default_factory=dict)
    outros_creditos: dict[str, dict[str, float]] = field(default_factory=dict)

    def de(self, campo: str, estabelecimento: str, atividade: str) -> float:
        mapa = getattr(self, campo).get(estabelecimento) or {}
        return float(mapa.get(atividade) or 0.0)


@dataclass
class ApuracaoFilial:
    """Resultado de um estabelecimento, antes de centralização."""

    estabelecimento: str
    uf: str
    regime: str
    credito_bruto: float = 0.0
    credito_mantido: float = 0.0
    estorno: float = 0.0
    credito_indevido: float = 0.0
    debito: float = 0.0
    linhas: int = 0
    beneficio: ResultadoBeneficio | None = None
    segrega_por_atividade: bool = False
    por_atividade: dict[str, ativ.TotaisAtividade] = field(default_factory=dict)
    por_carga: dict = field(default_factory=lambda: collections.defaultdict(
        lambda: {"credito_bruto": 0.0, "credito_mantido": 0.0, "estorno": 0.0,
                 "credito_indevido": 0.0}
    ))

    @property
    def credito_presumido(self) -> float:
        return self.beneficio.credito_presumido if self.beneficio else 0.0

    @property
    def fadefe(self) -> float:
        """Guia avulsa — informativo, fora da conta gráfica."""
        return self.beneficio.fadefe if self.beneficio else 0.0

    @property
    def saldo(self) -> float:
        """Positivo = a recolher; negativo = credor. Sem DIFAL e sem ajustes."""
        return self.debito - self.credito_mantido - self.credito_presumido

    @property
    def confere(self) -> bool:
        soma = self.credito_mantido + self.estorno + self.credito_indevido
        return abs(soma - self.credito_bruto) < 0.005

    def atividade(self, nome: str) -> ativ.TotaisAtividade:
        """Totais de uma atividade; vazios se ela não teve movimento."""
        return self.por_atividade.get(nome) or ativ.TotaisAtividade(atividade=nome)

    @property
    def atividades_sem_regra(self) -> ativ.TotaisAtividade | None:
        return self.por_atividade.get(ativ.SEM_REGRA)


@dataclass
class Apuracao:
    filiais: dict[str, ApuracaoFilial]
    base: BaseTratada
    centralizacao: list[centr.ResultadoCentralizacao] = field(default_factory=list)

    @property
    def total(self) -> ApuracaoFilial:
        t = ApuracaoFilial(estabelecimento="TOTAL", uf="", regime="")
        for f in self.filiais.values():
            t.credito_bruto += f.credito_bruto
            t.credito_mantido += f.credito_mantido
            t.estorno += f.estorno
            t.credito_indevido += f.credito_indevido
            t.debito += f.debito
            t.linhas += f.linhas
        return t

    @property
    def credito_presumido(self) -> float:
        return sum(f.credito_presumido for f in self.filiais.values())

    @property
    def fadefe(self) -> float:
        return sum(f.fadefe for f in self.filiais.values())

    @property
    def inconsistentes(self) -> list[ApuracaoFilial]:
        """Filiais em que crédito mantido + estorno ≠ crédito bruto."""
        return [f for f in self.filiais.values() if not f.confere]

    @property
    def saldos(self) -> dict[str, float]:
        """Saldo individual de cada estabelecimento, antes da centralização."""
        return {f.estabelecimento: f.saldo for f in self.filiais.values()}

    @property
    def pendencias_de_centralizacao(self) -> list[str]:
        return [m for c in self.centralizacao for m in c.pendencias]

    @property
    def sem_regra_de_atividade(self) -> list[ApuracaoFilial]:
        """Filiais com linha que não casou com nenhuma atividade.

        Bloqueia o encerramento: sem a atividade não há como dimensionar o
        benefício, e classificar por adivinhação é o que a regra 4 proíbe.
        """
        return [f for f in self.filiais.values() if f.atividades_sem_regra]


def apurar(
    base: BaseTratada,
    parametros: Parametros | None = None,
    ajustes: AjustesDaApuracao | None = None,
) -> Apuracao:
    params = parametros or base.parametros
    ajustes = ajustes or AjustesDaApuracao()

    cadastro = {
        " ".join(str(f["nome"]).split()).casefold(): f
        for f in params.filiais.get("filiais") or []
    }

    filiais: dict[str, ApuracaoFilial] = {}
    for tratada in base.linhas:
        resultado: ResultadoEstorno = calcular(tratada, params)
        if not (resultado.credito_bruto or resultado.debito):
            continue

        chave = " ".join(str(tratada.origem.dados["estabelecimento"]).split())
        filial = filiais.get(chave)
        if filial is None:
            ficha = cadastro.get(chave.casefold()) or {}
            uf = ficha.get("uf", "")
            filial = filiais[chave] = ApuracaoFilial(
                estabelecimento=chave,
                uf=uf,
                regime=resultado.regime,
                segrega_por_atividade=ativ.mapa_da_uf(uf, params) is not None,
            )
        filial.credito_bruto += resultado.credito_bruto
        filial.credito_mantido += resultado.credito_mantido
        filial.estorno += resultado.estorno
        filial.credito_indevido += resultado.credito_indevido
        filial.debito += resultado.debito
        filial.linhas += 1

        if filial.segrega_por_atividade:
            _somar_na_atividade(filial, tratada, resultado, params)

        if resultado.credito_bruto:
            carga = tratada.carga.carga if tratada.carga.carga is not None else "CIAP"
            alvo = filial.por_carga[carga]
            alvo["credito_bruto"] += resultado.credito_bruto
            alvo["credito_mantido"] += resultado.credito_mantido
            alvo["estorno"] += resultado.estorno
            alvo["credito_indevido"] += resultado.credito_indevido

    # Camada 7 — benefício fiscal. Vem depois do estorno e depois da segregação,
    # porque incide sobre o saldo devedor da atividade industrial.
    for chave, filial in filiais.items():
        nome_beneficio = (cadastro.get(chave.casefold()) or {}).get("beneficio_fiscal")
        if not nome_beneficio:
            continue
        filial.beneficio = calcular_beneficio(
            filial.atividade(ativ.INDUSTRIAL),
            nome_beneficio,
            params,
            ajuste_de_credito=ajustes.de(
                "estorno_de_credito", chave, ativ.INDUSTRIAL
            ),
        )

    apuracao = Apuracao(filiais=filiais, base=base)

    # Camada 9 — centralização. Vem por último porque opera sobre o saldo já
    # apurado de cada estabelecimento.
    apuracao.centralizacao = centr.calcular(apuracao.saldos, base.livro, params)
    return apuracao


def _somar_na_atividade(
    filial: ApuracaoFilial,
    tratada,
    resultado: ResultadoEstorno,
    params: Parametros,
) -> None:
    mapa = ativ.mapa_da_uf(filial.uf, params)
    if mapa is None:
        return
    classificada = ativ.classificar(tratada.origem, mapa)
    alvo = filial.por_atividade.get(classificada.atividade)
    if alvo is None:
        alvo = filial.por_atividade[classificada.atividade] = ativ.TotaisAtividade(
            atividade=classificada.atividade
        )
    alvo.credito_bruto += resultado.credito_bruto
    alvo.credito_mantido += resultado.credito_mantido
    alvo.estorno += resultado.estorno
    alvo.credito_indevido += resultado.credito_indevido
    alvo.debito += resultado.debito
    alvo.linhas += 1
    if resultado.debito and classificada.destino:
        alvo.debito_por_destino[classificada.destino] = (
            alvo.debito_por_destino.get(classificada.destino, 0.0) + resultado.debito
        )
