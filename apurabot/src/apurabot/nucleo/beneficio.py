"""Camada 7 — benefício fiscal de Rio Brilhante, Termo de Acordo n. 1.190/2018.

Cláusula terceira:

    I  — 67% do saldo devedor do ICMS, aplicável **exclusivamente** às operações
         realizadas com os produtos resultantes de sua própria industrialização
         neste Estado, deduzido do saldo devedor que tenha resultado como
         efetiva e regularmente devido;
    II — adicional de 13% nas operações interestaduais, resultando em 80%.

O alcance esteve em aberto até 25/08/2026, quando três documentos oficiais de
07/2026 o fecharam. A linha 012 do Registro de Apuração nomeia a dedução como
"Industrialização própria - Incentivo TA/CDI", e a GIA - Benefício Fiscal traz
base de saídas incentivadas de R$ 412.274,17 — exatamente os CFOP 5101, 5118 e
6101 do mês. A leitura literal do inciso I é a que vale: o benefício é da
atividade industrial, não de todas as saídas.

A cadeia, conferida ao centavo contra a GIA retificadora 36160E2:

    crédito industrial normal ........  327.834,95
    (−) estorno industrial ...........  245.987,17
    (−) estorno de créditos (ajuste) .    3.865,30
    (=) crédito da parcela incentivada   77.982,48
    débito industrial 412.274,17 − 77.982,48 = base 334.291,69
      intra  (56.934,28 −  10.769,23) × 67% =  30.930,58
      inter  (355.339,89 − 67.213,25) × 80% = 230.501,31
                                    benefício 261.431,89

Vigência até 31/12/2032. A cláusula quarta, que alcançava a revenda de
mercadoria adquirida em outras UFs, expirou em 31/12/2022.

Os percentuais estão em `parametros/regimes.yaml`, nunca aqui.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from ..formato import reais
from ..parametros import Parametros
from .atividade import INTERESTADUAL, INTRAESTADUAL, TotaisAtividade

# Critério de alcance homologado: o benefício é da atividade industrial.
ATIVIDADE_INDUSTRIAL = "atividade_industrial"


class BeneficioDesconhecido(Exception):
    """A filial aponta para um benefício que não existe ou não se aplica."""


@dataclass
class ParcelaBeneficiada:
    """Um dos dois grupos que o Termo separa: intraestadual e interestadual.

    Espelha uma linha do quadro "CÁLCULO BENEFÍCIO FISCAL" da GIA.
    """

    destino: str = ""
    debito: float = 0.0              # coluna 2 — Débitos ICMS Parcela Incentivada
    credito_rateado: float = 0.0     # coluna 3 — Créditos ICMS Parcela Incentivada
    percentual: float = 0.0

    @property
    def base_do_incentivo(self) -> float:
        """Coluna 7 da GIA. Nunca negativa: sem saldo devedor não há benefício."""
        return max(self.debito - self.credito_rateado, 0.0)

    @property
    def credito_presumido(self) -> float:
        """Coluna 8 — Valor ICMS Incentivado."""
        return self.base_do_incentivo * self.percentual / 100.0

    @property
    def icms_devido(self) -> float:
        """Coluna 9 — ICMS Devido (não incentivado)."""
        return self.base_do_incentivo - self.credito_presumido


@dataclass
class ResultadoBeneficio:
    documento: str = ""
    criterio: str = ""
    credito_industrial: float = 0.0
    estorno_industrial: float = 0.0
    ajuste_de_credito: float = 0.0
    intra: ParcelaBeneficiada = field(
        default_factory=lambda: ParcelaBeneficiada(destino=INTRAESTADUAL)
    )
    inter: ParcelaBeneficiada = field(
        default_factory=lambda: ParcelaBeneficiada(destino=INTERESTADUAL)
    )
    percentual_fadefe: float = 0.0
    percentual_fadefe_adicional: float = 0.0
    memoria: list[str] = field(default_factory=list)

    @property
    def credito_da_parcela_incentivada(self) -> float:
        """O crédito industrial que sobreviveu ao estorno e aos ajustes."""
        return self.intra.credito_rateado + self.inter.credito_rateado

    @property
    def debito_beneficiado(self) -> float:
        return self.intra.debito + self.inter.debito

    @property
    def base_do_incentivo(self) -> float:
        return self.intra.base_do_incentivo + self.inter.base_do_incentivo

    @property
    def credito_presumido(self) -> float:
        return self.intra.credito_presumido + self.inter.credito_presumido

    @property
    def fadefe(self) -> float:
        """Contribuição ao Pró-Desenvolve / FADEFE. GUIA AVULSA.

        Sai no relatório como informação; não entra na conta gráfica.
        """
        return self.credito_presumido * self.percentual_fadefe / 100.0

    @property
    def fadefe_adicional(self) -> float:
        """Adicional FADEFE Equilíbrio Fiscal. Também guia avulsa."""
        return self.credito_presumido * self.percentual_fadefe_adicional / 100.0

    @property
    def confere(self) -> bool:
        """O benefício nunca supera o saldo devedor que o gerou."""
        return self.credito_presumido <= self.base_do_incentivo + 0.005


def calcular(
    industrial: TotaisAtividade,
    nome_beneficio: str,
    params: Parametros,
    ajuste_de_credito: float = 0.0,
) -> ResultadoBeneficio:
    """Apura o crédito presumido sobre o saldo devedor da atividade industrial.

    `ajuste_de_credito` são estornos de crédito da atividade industrial que não
    nascem de documento no Livro Fiscal — a linha 003 do Registro de Apuração.
    Em 07/2026 foram R$ 3.865,30. Virão de `ajustes.xlsx` na Entrega 2.
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

    alcance = beneficio["alcance"]
    criterio = alcance.get("criterio")
    if criterio != ATIVIDADE_INDUSTRIAL:
        raise BeneficioDesconhecido(
            f"critério de alcance {criterio!r} não é reconhecido — o válido é "
            f"{ATIVIDADE_INDUSTRIAL!r}, homologado contra a GIA de 07/2026"
        )
    rateio = alcance.get("rateio_do_credito", "participacao_do_debito")
    if rateio != "participacao_do_debito":
        raise BeneficioDesconhecido(f"critério de rateio {rateio!r} não é reconhecido")

    presumido = beneficio["credito_presumido"]
    fadefe = beneficio.get("fadefe") or {}

    resultado = ResultadoBeneficio(
        documento=beneficio.get("documento", nome_beneficio),
        criterio=criterio,
        credito_industrial=industrial.credito_bruto,
        estorno_industrial=industrial.estorno,
        ajuste_de_credito=ajuste_de_credito,
        percentual_fadefe=float(fadefe.get("percentual") or 0.0),
        percentual_fadefe_adicional=float(fadefe.get("percentual_adicional") or 0.0),
    )
    resultado.intra.percentual = float(presumido["saida_intraestadual"])
    resultado.inter.percentual = float(presumido["saida_interestadual"])
    resultado.intra.debito = industrial.debito_de(INTRAESTADUAL)
    resultado.inter.debito = industrial.debito_de(INTERESTADUAL)

    # O crédito da parcela incentivada é o crédito industrial que sobrou do
    # estorno — não um rateio do crédito da filial inteira.
    credito = max(industrial.credito_mantido - ajuste_de_credito, 0.0)
    debito = resultado.debito_beneficiado
    if debito:
        for parcela in (resultado.intra, resultado.inter):
            parcela.credito_rateado = credito * (parcela.debito / debito)

    _montar_memoria(resultado, industrial)
    return resultado


def _montar_memoria(resultado: ResultadoBeneficio, industrial: TotaisAtividade) -> None:
    linhas = [
        f"Termo: {resultado.documento}",
        f"Alcance: {resultado.criterio}",
        f"Crédito industrial bruto: {reais(resultado.credito_industrial)}",
        f"(−) estorno industrial: {reais(resultado.estorno_industrial)}",
    ]
    if resultado.ajuste_de_credito:
        linhas.append(f"(−) estorno de créditos (ajuste): {reais(resultado.ajuste_de_credito)}")
    linhas.append(
        f"(=) crédito da parcela incentivada: "
        f"{reais(resultado.credito_da_parcela_incentivada)}"
    )
    linhas.append(
        f"Débito industrial {reais(industrial.debito)} − crédito da parcela "
        f"incentivada = base {reais(resultado.base_do_incentivo)}"
    )
    for nome, parcela in (("intraestadual", resultado.intra),
                          ("interestadual", resultado.inter)):
        linhas.append(
            f"Saída {nome}: débito {reais(parcela.debito)} − crédito "
            f"{reais(parcela.credito_rateado)} = base {reais(parcela.base_do_incentivo)} "
            f"× {parcela.percentual:g}% = {reais(parcela.credito_presumido)}"
        )
    linhas.append(f"Crédito presumido total: {reais(resultado.credito_presumido)}")
    if resultado.percentual_fadefe:
        linhas.append(
            f"FADEFE {resultado.percentual_fadefe:g}% sobre o benefício fruído: "
            f"{reais(resultado.fadefe)} — guia avulsa, fora da conta gráfica"
        )
    resultado.memoria = linhas
