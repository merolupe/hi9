"""Benefício fiscal de Rio Brilhante — Termo de Acordo n. 1.190/2018."""
from __future__ import annotations

import pytest

from apurabot.base_tratada import LinhaTratada
from apurabot.ingestao import LinhaLivro
from apurabot.nucleo.beneficio import BeneficioDesconhecido, calcular
from apurabot.nucleo.carga import ResultadoCarga, Situacao
from apurabot.nucleo.classificacao import ResultadoClassificacao

CENTAVO = 0.005


def saida(cfop, icms, uf_destino="MS"):
    dados = {
        "estabelecimento": "HINOVE (RIO BRILHANTE)",
        "entrada_saida": "Saída",
        "valor_icms": icms,
        "valor_contabil": icms * 25,
        "cfop": cfop,
        "uf_origem": "MS",
        "uf_destino": uf_destino,
    }
    return LinhaTratada(
        origem=LinhaLivro(linha_origem=2, arquivo_origem="teste.xlsx", dados=dados),
        carga=ResultadoCarga(Situacao.EQUALIZADA, carga=4.0),
        classificacao=ResultadoClassificacao(categoria="materia_prima", regra="teste"),
    )


def test_producao_propria_intraestadual_rende_sessenta_e_sete_por_cento(parametros):
    r = calcular([saida(5101, 10_000.00)], "ms_rio_brilhante", 0.0, parametros)
    assert r.intra.debito == 10_000.00
    assert r.credito_presumido == pytest.approx(6_700.00, abs=CENTAVO)


def test_producao_propria_interestadual_rende_oitenta_por_cento(parametros):
    """67% do inciso I mais os 13% do inciso II."""
    r = calcular([saida(6101, 10_000.00, "SP")], "ms_rio_brilhante", 0.0, parametros)
    assert r.inter.debito == 10_000.00
    assert r.credito_presumido == pytest.approx(8_000.00, abs=CENTAVO)


@pytest.mark.parametrize("cfop", [5102, 6102, 5905, 6934, 5910])
def test_revenda_e_remessa_ficam_fora_do_alcance(parametros, cfop):
    """A cláusula que as alcançava — a quarta — expirou em 31/12/2022."""
    r = calcular([saida(cfop, 10_000.00)], "ms_rio_brilhante", 0.0, parametros)
    assert r.credito_presumido == 0.0
    assert r.debito_fora_do_alcance == 10_000.00


def test_o_credito_mantido_abate_o_debito_antes_do_beneficio(parametros):
    """O benefício incide sobre o saldo devedor, não sobre o débito bruto."""
    r = calcular([saida(6101, 10_000.00, "SP")], "ms_rio_brilhante", 2_000.00, parametros)
    assert r.inter.saldo_devedor == pytest.approx(8_000.00, abs=CENTAVO)
    assert r.credito_presumido == pytest.approx(6_400.00, abs=CENTAVO)


def test_credito_maior_que_o_debito_nao_gera_beneficio_negativo(parametros):
    r = calcular([saida(6101, 1_000.00, "SP")], "ms_rio_brilhante", 5_000.00, parametros)
    assert r.inter.saldo_devedor == 0.0
    assert r.credito_presumido == 0.0


def test_o_credito_e_rateado_pela_participacao_do_debito(parametros):
    """Inclusive com o que está fora do alcance — o crédito é da filial inteira."""
    linhas = [saida(6101, 60_000.00, "SP"), saida(6102, 40_000.00, "SP")]
    r = calcular(linhas, "ms_rio_brilhante", 10_000.00, parametros)
    assert r.inter.credito_rateado == pytest.approx(6_000.00, abs=CENTAVO)
    assert r.credito_fora_do_alcance == pytest.approx(4_000.00, abs=CENTAVO)


def test_beneficio_nunca_supera_o_saldo_devedor(parametros):
    """Cláusula terceira: deduzido do saldo devedor efetiva e regularmente devido."""
    linhas = [saida(5101, 10_000.00), saida(6101, 20_000.00, "MG")]
    r = calcular(linhas, "ms_rio_brilhante", 1_000.00, parametros)
    assert r.confere


def test_clausula_quarta_expirada_nao_pode_ser_aplicada(parametros):
    with pytest.raises(BeneficioDesconhecido, match="vigência encerrada"):
        calcular([saida(6102, 10_000.00, "SP")],
                 "ms_rio_brilhante_clausula_quarta", 0.0, parametros)


def test_beneficio_inexistente_falha_com_mensagem_clara(parametros):
    with pytest.raises(BeneficioDesconhecido, match="não existe"):
        calcular([saida(5101, 100.0)], "beneficio_que_nao_existe", 0.0, parametros)
