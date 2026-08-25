"""Benefício fiscal de Rio Brilhante — Termo de Acordo n. 1.190/2018.

O benefício incide sobre o saldo devedor da ATIVIDADE INDUSTRIAL. Isso deixou
de ser leitura e passou a ser fato documentado em 25/08/2026: a linha 012 do
Registro de Apuração de 07/2026 nomeia a dedução como "Industrialização
própria - Incentivo TA/CDI", e a GIA - Benefício Fiscal traz base de saídas
incentivadas de R$ 412.274,17, que é exatamente CFOP 5101 + 5118 + 6101.
"""
from __future__ import annotations

import copy

import pytest

from apurabot.nucleo.atividade import INDUSTRIAL, INTERESTADUAL, INTRAESTADUAL
from apurabot.nucleo.atividade import TotaisAtividade
from apurabot.nucleo.beneficio import BeneficioDesconhecido, calcular

CENTAVO = 0.005


def industrial(debito_intra=0.0, debito_inter=0.0, credito=0.0, estorno=0.0):
    """Monta os totais da atividade industrial de um estabelecimento."""
    return TotaisAtividade(
        atividade=INDUSTRIAL,
        credito_bruto=credito,
        credito_mantido=credito - estorno,
        estorno=estorno,
        debito=debito_intra + debito_inter,
        debito_por_destino={INTRAESTADUAL: debito_intra, INTERESTADUAL: debito_inter},
    )


# -- os dois percentuais do Termo -----------------------------------------

def test_saida_intraestadual_rende_sessenta_e_sete_por_cento(parametros):
    r = calcular(industrial(debito_intra=10_000.00), "ms_rio_brilhante", parametros)
    assert r.intra.debito == 10_000.00
    assert r.credito_presumido == pytest.approx(6_700.00, abs=CENTAVO)


def test_saida_interestadual_rende_oitenta_por_cento(parametros):
    """67% do inciso I mais os 13% do inciso II."""
    r = calcular(industrial(debito_inter=10_000.00), "ms_rio_brilhante", parametros)
    assert r.inter.debito == 10_000.00
    assert r.credito_presumido == pytest.approx(8_000.00, abs=CENTAVO)


# -- a cadeia do crédito da parcela incentivada ---------------------------

def test_o_credito_da_parcela_incentivada_e_o_industrial_que_sobrou_do_estorno(
    parametros,
):
    """Não é rateio do crédito da filial: é o crédito da própria atividade."""
    r = calcular(
        industrial(debito_inter=10_000.00, credito=5_000.00, estorno=3_000.00),
        "ms_rio_brilhante",
        parametros,
    )
    assert r.credito_da_parcela_incentivada == pytest.approx(2_000.00, abs=CENTAVO)
    assert r.inter.base_do_incentivo == pytest.approx(8_000.00, abs=CENTAVO)
    assert r.credito_presumido == pytest.approx(6_400.00, abs=CENTAVO)


def test_o_ajuste_de_credito_reduz_a_parcela_incentivada(parametros):
    """Linha 003 do Registro — estorno de créditos que não vem do Livro."""
    r = calcular(
        industrial(debito_inter=10_000.00, credito=5_000.00, estorno=3_000.00),
        "ms_rio_brilhante",
        parametros,
        ajuste_de_credito=500.00,
    )
    assert r.credito_da_parcela_incentivada == pytest.approx(1_500.00, abs=CENTAVO)
    assert r.credito_presumido == pytest.approx(6_800.00, abs=CENTAVO)


def test_o_credito_e_rateado_pela_participacao_do_debito(parametros):
    """Quadro CÁLCULO BENEFÍCIO FISCAL da GIA: uma linha por percentual."""
    r = calcular(
        industrial(debito_intra=40_000.00, debito_inter=60_000.00, credito=10_000.00),
        "ms_rio_brilhante",
        parametros,
    )
    assert r.intra.credito_rateado == pytest.approx(4_000.00, abs=CENTAVO)
    assert r.inter.credito_rateado == pytest.approx(6_000.00, abs=CENTAVO)


def test_credito_maior_que_o_debito_nao_gera_beneficio_negativo(parametros):
    r = calcular(
        industrial(debito_inter=1_000.00, credito=5_000.00),
        "ms_rio_brilhante",
        parametros,
    )
    assert r.inter.base_do_incentivo == 0.0
    assert r.credito_presumido == 0.0


def test_beneficio_nunca_supera_o_saldo_devedor(parametros):
    """Cláusula terceira: deduzido do saldo devedor efetiva e regularmente devido."""
    r = calcular(
        industrial(debito_intra=10_000.00, debito_inter=20_000.00, credito=1_000.00),
        "ms_rio_brilhante",
        parametros,
    )
    assert r.confere


def test_sem_debito_industrial_nao_ha_beneficio(parametros):
    """Um mês sem produção própria não frui o Termo, por mais crédito que tenha."""
    r = calcular(industrial(credito=50_000.00), "ms_rio_brilhante", parametros)
    assert r.credito_presumido == 0.0
    assert r.credito_da_parcela_incentivada == 0.0


# -- FADEFE — guia avulsa --------------------------------------------------

def test_fadefe_e_dois_por_cento_do_beneficio_fruido(parametros):
    r = calcular(industrial(debito_inter=10_000.00), "ms_rio_brilhante", parametros)
    assert r.credito_presumido == pytest.approx(8_000.00, abs=CENTAVO)
    assert r.fadefe == pytest.approx(160.00, abs=CENTAVO)
    assert r.fadefe_adicional == 0.0


def test_o_fadefe_nao_entra_na_conta_grafica(parametros):
    """É guia avulsa: sai no relatório, não abate nem acresce a apuração."""
    r = calcular(industrial(debito_inter=10_000.00), "ms_rio_brilhante", parametros)
    assert r.inter.icms_devido == pytest.approx(2_000.00, abs=CENTAVO)
    assert r.inter.base_do_incentivo == pytest.approx(
        r.inter.credito_presumido + r.inter.icms_devido, abs=CENTAVO
    )


# -- falhas ----------------------------------------------------------------

def test_criterio_de_alcance_desconhecido_falha(parametros):
    p = copy.deepcopy(parametros)
    p.regimes["beneficios_fiscais"]["ms_rio_brilhante"]["alcance"]["criterio"] = "xyz"
    with pytest.raises(BeneficioDesconhecido, match="não é reconhecido"):
        calcular(industrial(debito_intra=100.0), "ms_rio_brilhante", p)


def test_clausula_quarta_expirada_nao_pode_ser_aplicada(parametros):
    with pytest.raises(BeneficioDesconhecido, match="vigência encerrada"):
        calcular(
            industrial(debito_inter=10_000.00),
            "ms_rio_brilhante_clausula_quarta",
            parametros,
        )


def test_beneficio_inexistente_falha_com_mensagem_clara(parametros):
    with pytest.raises(BeneficioDesconhecido, match="não existe"):
        calcular(industrial(debito_intra=100.0), "beneficio_que_nao_existe", parametros)
