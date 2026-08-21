"""Regra de estorno por regime — casos isolados."""
from __future__ import annotations

import pytest

from apurabot.base_tratada import LinhaTratada
from apurabot.ingestao import LinhaLivro
from apurabot.nucleo.carga import ResultadoCarga, Situacao
from apurabot.nucleo.classificacao import ResultadoClassificacao
from apurabot.nucleo.estorno import RegimeDesconhecido, calcular


def tratada(estabelecimento, categoria, carga, icms, contabil, entrada=True):
    dados = {
        "estabelecimento": estabelecimento,
        "entrada_saida": "Entrada" if entrada else "Saída",
        "valor_icms": icms,
        "valor_contabil": contabil,
    }
    return LinhaTratada(
        origem=LinhaLivro(linha_origem=2, arquivo_origem="teste.xlsx", dados=dados),
        carga=ResultadoCarga(Situacao.EQUALIZADA, carga=carga),
        classificacao=ResultadoClassificacao(categoria=categoria, regra="teste"),
    )


# -- SP, equilíbrio fiscal -------------------------------------------------

def test_sp_estorna_o_excedente_sobre_quatro_por_cento(parametros):
    """Registro, frete a 7%: 448.750,00 × 3% = 13.462,50 na apuração manual."""
    r = calcular(
        tratada("HINOVE (REGISTRO)", "frete_venda", 7.0, 31_186.28, 448_750.00),
        parametros,
    )
    assert r.estorno == pytest.approx(13_462.50, abs=0.005)
    assert r.credito_mantido == pytest.approx(17_723.78, abs=0.005)
    assert r.confere


def test_sp_base_do_estorno_e_o_valor_contabil_e_nao_a_base_de_icms(parametros):
    """Se fosse sobre a base de ICMS daria 13.365,55, não 13.462,50."""
    r = calcular(
        tratada("HINOVE (REGISTRO)", "frete_venda", 7.0, 31_186.28, 448_750.00),
        parametros,
    )
    assert r.estorno != pytest.approx(445_518.32 * 0.03, abs=0.005)


def test_sp_carga_de_quatro_por_cento_nao_estorna(parametros):
    r = calcular(
        tratada("HINOVE (REGISTRO)", "frete_compra", 4.0, 1_000.00, 25_000.00), parametros
    )
    assert r.estorno == 0.0
    assert r.credito_mantido == 1_000.00


@pytest.mark.parametrize(
    "categoria", ["revenda", "retorno_industrializacao", "ciap", "materia_prima"]
)
def test_sp_categorias_isentas_nao_estornam_nem_a_doze_por_cento(parametros, categoria):
    r = calcular(
        tratada("HINOVE (FILIAL GUARÁ)", categoria, 12.0, 6_967.37, 58_061.49), parametros
    )
    assert r.estorno == 0.0
    assert r.credito_mantido == 6_967.37


# -- MT e PR, diferimento --------------------------------------------------

def test_mt_estorna_o_credito_inteiro(parametros):
    r = calcular(
        tratada("HINOVE (BARRA DO GARÇAS - MT)", "frete_transferencia", 7.0,
                50_309.07, 722_293.40),
        parametros,
    )
    assert r.estorno == pytest.approx(50_309.07, abs=0.005)
    assert r.credito_mantido == 0.0


def test_pr_mantem_o_credito_inteiro(parametros):
    r = calcular(
        tratada("HINOVE (LONDRINA)", "frete_transferencia", 12.0, 13_882.40, 115_686.66),
        parametros,
    )
    assert r.estorno == 0.0
    assert r.credito_mantido == pytest.approx(13_882.40, abs=0.005)


# -- MS --------------------------------------------------------------------

def test_corumba_segue_a_mesma_mecanica_de_sp(parametros):
    r = calcular(
        tratada("HINOVE (CORUMBÁ- MS)", "frete_venda", 12.0, 26_160.77, 218_006.40),
        parametros,
    )
    assert r.estorno == pytest.approx(218_006.40 * 0.08, abs=0.005)


def test_rio_brilhante_estorna_integralmente_a_entrada_beneficiada(parametros):
    r = calcular(
        tratada("HINOVE (RIO BRILHANTE)", "materia_prima", 4.0, 1_000.00, 25_000.00),
        parametros,
    )
    assert r.estorno == pytest.approx(1_000.00, abs=0.005)
    assert r.credito_mantido == 0.0


def test_rio_brilhante_mantem_o_que_nao_e_entrada_beneficiada(parametros):
    r = calcular(
        tratada("HINOVE (RIO BRILHANTE)", "frete_venda", 12.0, 112_404.72, 937_542.20),
        parametros,
    )
    assert r.estorno == 0.0
    assert r.credito_mantido == pytest.approx(112_404.72, abs=0.005)


# -- invariantes e falhas --------------------------------------------------

def test_saida_gera_debito_e_nunca_estorno(parametros):
    r = calcular(
        tratada("HINOVE (FILIAL GUARÁ)", "materia_prima", 12.0, 7_851.37, 65_428.02,
                entrada=False),
        parametros,
    )
    assert r.debito == pytest.approx(7_851.37, abs=0.005)
    assert r.estorno == 0.0 and r.credito_bruto == 0.0


def test_estorno_nunca_supera_o_credito(parametros):
    """Contábil muito maior que a base não pode gerar estorno acima do ICMS."""
    r = calcular(
        tratada("HINOVE (REGISTRO)", "frete_venda", 25.0, 100.00, 1_000_000.00),
        parametros,
    )
    assert r.estorno == 100.00
    assert r.credito_mantido == 0.0


def test_filial_fora_do_cadastro_falha_com_mensagem_clara(parametros):
    with pytest.raises(RegimeDesconhecido, match="não está em filiais.yaml"):
        calcular(tratada("HINOVE (FILIAL NOVA)", "frete_venda", 12.0, 100.0, 1000.0),
                 parametros)


def test_linha_sem_icms_nao_exige_filial_cadastrada(parametros):
    """Cadastro incompleto não pode travar linha que nem apura ICMS."""
    r = calcular(tratada("EMPRESA QUALQUER", "—", 12.0, 0.0, 1000.0), parametros)
    assert r.credito_bruto == 0.0 and r.debito == 0.0
