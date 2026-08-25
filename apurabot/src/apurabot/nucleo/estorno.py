"""Camadas 5 e 6 — regra tributária por regime e cálculo do estorno.

Toda entrada com ICMS gera crédito bruto. Quanto desse crédito fica é o que o
regime da filial decide; o resto é estorno. Saídas geram débito e não estornam.

As fórmulas são declaradas em `parametros/regimes.yaml`, nunca aqui.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..base_tratada import LinhaTratada
from ..parametros import Parametros

# Fórmulas reconhecidas. O nome vem do parâmetro `formula_estorno`.
EXCEDENTE = "excedente_sobre_carga_saida"
INTEGRAL = "integral"
PROPORCIONAL = "proporcional_parcela_nao_tributada"
NENHUM = "nenhum"


class RegimeDesconhecido(Exception):
    """A filial aponta para um regime que não existe, ou o regime não tem fórmula."""


@dataclass(frozen=True)
class ResultadoEstorno:
    """O que o regime concluiu sobre uma linha."""

    credito_bruto: float = 0.0
    credito_mantido: float = 0.0
    estorno: float = 0.0
    credito_indevido: float = 0.0
    debito: float = 0.0
    regime: str = ""
    regra: str = ""

    @property
    def confere(self) -> bool:
        """Identidade que a auditoria valida.

        crédito mantido + estorno + crédito indevido = crédito bruto

        O crédito indevido fica em parcela própria porque não é estorno: é
        crédito que não podia ter sido tomado. Somá-lo ao mantido — como fez a
        apuração consolidada de Julho/2026 — esconde o problema no resultado.
        """
        soma = self.credito_mantido + self.estorno + self.credito_indevido
        return abs(soma - self.credito_bruto) < 0.005


def _regime_da_filial(estabelecimento: str | None, params: Parametros) -> tuple[str, dict]:
    alvo = " ".join(str(estabelecimento or "").split()).casefold()
    for filial in params.filiais.get("filiais") or []:
        if " ".join(str(filial["nome"]).split()).casefold() == alvo:
            nome = filial["regime"]
            regime = (params.regimes.get("regimes") or {}).get(nome)
            if regime is None:
                raise RegimeDesconhecido(
                    f"filial {estabelecimento!r} aponta para o regime {nome!r}, "
                    "que não existe em regimes.yaml"
                )
            return nome, regime
    raise RegimeDesconhecido(
        f"estabelecimento {estabelecimento!r} não está em filiais.yaml — "
        "cadastre-o antes de apurar"
    )


def calcular(tratada: LinhaTratada, params: Parametros) -> ResultadoEstorno:
    """Aplica o regime da filial sobre uma linha já tratada."""
    dados = tratada.origem.dados
    icms = dados.get("valor_icms") or 0.0

    # A filial só precisa estar cadastrada se a linha realmente apura ICMS.
    # Linhas sem ICMS não devem travar a apuração por causa do cadastro.
    if not tratada.relevante or not icms:
        return ResultadoEstorno(regra="linha fora da apuração de ICMS")

    nome_regime, regime = _regime_da_filial(dados.get("estabelecimento"), params)

    if dados.get("entrada_saida") == "Saída":
        return ResultadoEstorno(
            debito=icms, regime=nome_regime, regra="saída — débito de ICMS"
        )

    indevido = _credito_indevido(tratada, regime)
    if indevido is not None:
        return ResultadoEstorno(
            credito_bruto=icms,
            credito_indevido=icms,
            regime=nome_regime,
            regra=indevido,
        )

    categoria = tratada.classificacao.categoria
    isentos = set(regime.get("isentos_de_estorno") or [])
    if categoria in isentos:
        return ResultadoEstorno(
            credito_bruto=icms,
            credito_mantido=icms,
            regime=nome_regime,
            regra=f"{categoria} não estorna neste regime",
        )

    formula = regime.get("formula_estorno")
    if formula is None:
        raise RegimeDesconhecido(
            f"o regime {nome_regime!r} não declara `formula_estorno` em regimes.yaml"
        )

    estorno, regra = _aplicar(formula, tratada, regime, icms)
    estorno = min(max(estorno, 0.0), icms)      # nunca negativo, nunca maior que o crédito
    return ResultadoEstorno(
        credito_bruto=icms,
        credito_mantido=icms - estorno,
        estorno=estorno,
        regime=nome_regime,
        regra=regra,
    )


def _aplicar(
    formula: str, tratada: LinhaTratada, regime: dict[str, Any], icms: float
) -> tuple[float, str]:
    carga = tratada.carga.carga

    if formula == NENHUM:
        return 0.0, "diferimento — mantém 100% do crédito"

    if formula == INTEGRAL:
        return icms, "diferimento — estorna 100% do crédito"

    if formula == PROPORCIONAL:
        referencia = regime.get("carga_de_referencia")
        if referencia is None:
            raise RegimeDesconhecido(
                "o regime usa `proporcional_parcela_nao_tributada` mas não declara "
                "`carga_de_referencia` em regimes.yaml"
            )
        referencia = float(referencia)

        # A CHAVE É A ALÍQUOTA, NÃO A CARGA EFETIVA.
        #
        # A carga efetiva serve para conferir o documento; quem comanda a
        # proporção do estorno é a alíquota da operação, porque o benefício
        # limita o crédito à carga de referência. Uma importação a 17% com base
        # reduzida tem carga efetiva de 4% e mesmo assim estorna 76,47%.
        aliquota = tratada.origem.dados.get("aliquota_icms")
        if not aliquota:
            return 0.0, "alíquota indeterminada — nada a estornar"
        aliquota = float(aliquota)
        if aliquota <= referencia:
            return (
                0.0,
                f"alíquota de {aliquota:g}% não excede a carga de referência "
                f"({referencia:g}%) — mantém o crédito",
            )

        parcela = 1.0 - referencia / aliquota
        casas = regime.get("casas_decimais_da_parcela")
        if casas is not None:
            parcela = round(parcela, int(casas))
        return (
            icms * parcela,
            f"parcela não tributada = 1 − {referencia:g}/{aliquota:g} = "
            f"{parcela:.4f}; ICMS {icms:,.2f} × {parcela:.4f} "
            f"(carga efetiva do documento: "
            f"{'—' if carga is None else format(carga, 'g') + '%'})",
        )

    if formula == EXCEDENTE:
        referencia = float(regime.get("carga_saida_referencia", 0.0))
        if carga is None or carga <= referencia:
            return 0.0, f"carga {carga}% não excede a de saída ({referencia:g}%)"
        contabil = tratada.origem.dados.get("valor_contabil") or 0.0
        excedente = (carga - referencia) / 100.0
        return (
            contabil * excedente,
            f"valor contábil × ({carga:g}% − {referencia:g}%) = "
            f"{contabil:,.2f} × {excedente:.4f}",
        )

    raise RegimeDesconhecido(
        f"fórmula de estorno {formula!r} não é reconhecida — as válidas são "
        f"{EXCEDENTE}, {INTEGRAL}, {PROPORCIONAL} e {NENHUM}"
    )


def _credito_indevido(tratada: LinhaTratada, regime: dict[str, Any]) -> str | None:
    """Devolve o motivo se o crédito da linha não puder ser apropriado."""
    for item in regime.get("creditos_indevidos") or []:
        if tratada.origem.cfop_int in set(item.get("cfop") or []):
            pendente = "" if item.get("homologado", True) else " (regra não homologada)"
            motivo = " ".join(str(item.get("motivo", "")).split())
            return f"CFOP {tratada.origem.cfop_int} — crédito indevido{pendente}: {motivo}"
    return None
