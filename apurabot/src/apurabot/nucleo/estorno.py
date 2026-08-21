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
INTEGRAL_NAS_CARGAS = "integral_nas_cargas"
NENHUM = "nenhum"


class RegimeDesconhecido(Exception):
    """A filial aponta para um regime que não existe, ou o regime não tem fórmula."""


@dataclass(frozen=True)
class ResultadoEstorno:
    """O que o regime concluiu sobre uma linha."""

    credito_bruto: float = 0.0
    credito_mantido: float = 0.0
    estorno: float = 0.0
    debito: float = 0.0
    regime: str = ""
    regra: str = ""

    @property
    def confere(self) -> bool:
        """Identidade que a auditoria valida: mantido + estorno = bruto."""
        return abs(self.credito_mantido + self.estorno - self.credito_bruto) < 0.005


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

    if formula == INTEGRAL_NAS_CARGAS:
        alvos = {float(c) for c in regime.get("cargas_estornadas") or []}
        if carga is not None and carga in alvos:
            return icms, f"entrada beneficiada a {carga:g}% — estorna 100% do crédito"
        return 0.0, f"carga {carga}% fora das beneficiadas — mantém o crédito"

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
        f"{EXCEDENTE}, {INTEGRAL}, {INTEGRAL_NAS_CARGAS} e {NENHUM}"
    )
