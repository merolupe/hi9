"""Benefício fiscal de Rio Brilhante — Termo de Acordo n. 1.190/2018.

Cláusula terceira:

    I  — 67% do saldo devedor do ICMS, aplicável **exclusivamente** às operações
         realizadas com os produtos resultantes de sua própria industrialização
         neste Estado, deduzido do saldo devedor que tenha resultado como
         efetiva e regularmente devido;
    II — adicional de 13% nas operações interestaduais, resultando em 80%.

Vigência até 31/12/2032. A cláusula quarta, que alcançava a revenda de
mercadoria adquirida em outras UFs, expirou em 31/12/2022 — por isso revenda de
terceiros e remessas ficam fora da base.

Os percentuais e a lista de CFOP estão em `parametros/regimes.yaml`, nunca aqui.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..base_tratada import LinhaTratada
from ..parametros import Parametros


# Critérios de alcance. Qual deles vale é decisão da Gerência Fiscal/Tributária,
# não do motor — ver docs/apurabot/06-decisoes-pendentes.md, item 1.
CFOP_PRODUCAO_PROPRIA = "cfop_de_producao_propria"   # leitura literal do inciso I
TODAS_AS_SAIDAS = "todas_as_saidas"                  # o que a apuração de Julho faz


class BeneficioDesconhecido(Exception):
    """A filial aponta para um benefício que não existe ou não se aplica."""


@dataclass
class ParcelaBeneficiada:
    """Um dos dois grupos que o Termo separa: intraestadual e interestadual."""

    debito: float = 0.0
    credito_rateado: float = 0.0
    percentual: float = 0.0

    @property
    def saldo_devedor(self) -> float:
        """Nunca negativo: onde há saldo credor, não há o que abater."""
        return max(self.debito - self.credito_rateado, 0.0)

    @property
    def credito_presumido(self) -> float:
        return self.saldo_devedor * self.percentual / 100.0


@dataclass
class ResultadoBeneficio:
    documento: str = ""
    criterio: str = ""
    intra: ParcelaBeneficiada = field(default_factory=ParcelaBeneficiada)
    inter: ParcelaBeneficiada = field(default_factory=ParcelaBeneficiada)
    debito_fora_do_alcance: float = 0.0
    credito_fora_do_alcance: float = 0.0
    memoria: list[str] = field(default_factory=list)

    @property
    def debito_beneficiado(self) -> float:
        return self.intra.debito + self.inter.debito

    @property
    def credito_presumido(self) -> float:
        return self.intra.credito_presumido + self.inter.credito_presumido

    @property
    def saldo_devedor_beneficiado(self) -> float:
        return self.intra.saldo_devedor + self.inter.saldo_devedor

    @property
    def confere(self) -> bool:
        """O benefício nunca supera o saldo devedor que o gerou."""
        return self.credito_presumido <= self.saldo_devedor_beneficiado + 0.005


def calcular(
    linhas: list[LinhaTratada],
    nome_beneficio: str,
    credito_mantido: float,
    params: Parametros,
) -> ResultadoBeneficio:
    """Apura o crédito presumido de um estabelecimento beneficiado.

    `linhas` são as da filial; `credito_mantido` é o crédito que sobreviveu ao
    estorno, e é ele que se abate do débito para formar o saldo devedor.
    """
    beneficios = params.regimes.get("beneficios_fiscais") or {}
    beneficio = beneficios.get(nome_beneficio)
    if beneficio is None:
        raise BeneficioDesconhecido(
            f"benefício {nome_beneficio!r} não existe em regimes.yaml"
        )
    if beneficio.get("aplicavel") is False:
        raise BeneficioDesconhecido(
            f"benefício {nome_beneficio!r} não é aplicável — vigência encerrada em "
            f"{beneficio.get('vigencia_fim')}"
        )

    presumido = beneficio["credito_presumido"]
    alcance = beneficio["alcance"]
    criterio = alcance.get("criterio", CFOP_PRODUCAO_PROPRIA)
    if criterio not in (CFOP_PRODUCAO_PROPRIA, TODAS_AS_SAIDAS):
        raise BeneficioDesconhecido(
            f"critério de alcance {criterio!r} não é reconhecido — os válidos são "
            f"{CFOP_PRODUCAO_PROPRIA!r} e {TODAS_AS_SAIDAS!r}"
        )
    cfops = set(alcance.get("cfop") or [])

    resultado = ResultadoBeneficio(
        documento=beneficio.get("documento", nome_beneficio), criterio=criterio
    )
    resultado.intra.percentual = float(presumido["saida_intraestadual"])
    resultado.inter.percentual = float(presumido["saida_interestadual"])

    for tratada in linhas:
        dados = tratada.origem.dados
        icms = dados.get("valor_icms") or 0.0
        if not tratada.relevante or not icms or dados.get("entrada_saida") != "Saída":
            continue
        if criterio == CFOP_PRODUCAO_PROPRIA and tratada.origem.cfop_int not in cfops:
            resultado.debito_fora_do_alcance += icms
            continue
        alvo = resultado.intra if not tratada.origem.interestadual else resultado.inter
        alvo.debito += icms

    _ratear_credito(resultado, credito_mantido, alcance)
    _montar_memoria(resultado, credito_mantido)
    return resultado


def _ratear_credito(
    resultado: ResultadoBeneficio, credito_mantido: float, alcance: dict[str, Any]
) -> None:
    """Distribui o crédito mantido entre as parcelas, pela participação do débito.

    O Termo não diz como ratear; a participação do débito é o critério assumido
    — ver docs/apurabot/06-decisoes-pendentes.md, item 1.
    """
    criterio = alcance.get("rateio_do_credito", "participacao_do_debito")
    if criterio != "participacao_do_debito":
        raise BeneficioDesconhecido(
            f"critério de rateio {criterio!r} não é reconhecido"
        )

    debito_total = resultado.debito_beneficiado + resultado.debito_fora_do_alcance
    if not debito_total:
        resultado.credito_fora_do_alcance = credito_mantido
        return

    for parcela in (resultado.intra, resultado.inter):
        parcela.credito_rateado = credito_mantido * (parcela.debito / debito_total)
    resultado.credito_fora_do_alcance = credito_mantido * (
        resultado.debito_fora_do_alcance / debito_total
    )


def _montar_memoria(resultado: ResultadoBeneficio, credito_mantido: float) -> None:
    linhas = [
        f"Termo: {resultado.documento}",
        f"Alcance aplicado: {resultado.criterio}",
        f"Crédito mantido rateado pela participação do débito: {credito_mantido:,.2f}",
    ]
    escopo = (
        "de produção própria"
        if resultado.criterio == CFOP_PRODUCAO_PROPRIA
        else "(todas)"
    )
    for nome, parcela in (("intraestadual", resultado.intra), ("interestadual", resultado.inter)):
        linhas.append(
            f"Saída {nome} {escopo}: débito {parcela.debito:,.2f} "
            f"− crédito {parcela.credito_rateado:,.2f} = saldo devedor "
            f"{parcela.saldo_devedor:,.2f} × {parcela.percentual:g}% = "
            f"{parcela.credito_presumido:,.2f}"
        )
    linhas.append(
        f"Fora do alcance do benefício (revenda de terceiros, remessas): débito "
        f"{resultado.debito_fora_do_alcance:,.2f}"
    )
    linhas.append(f"Crédito presumido total: {resultado.credito_presumido:,.2f}")
    resultado.memoria = linhas
