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

def test_corumba_estorna_a_parcela_nao_tributada_sobre_o_icms(parametros):
    """MS não é SP: o estorno incide sobre o ICMS, não sobre o valor contábil.

    Empresa 9, aba ENTRADAS: CFOP 2352, ICMS 18.092,40 × 66,67% = 12.062,20308.
    """
    r = calcular(
        tratada("HINOVE (CORUMBÁ- MS)", "frete_venda", 12.0, 18_092.40, 150_770.00),
        parametros,
    )
    assert r.estorno == pytest.approx(12_062.20308, abs=0.0005)
    assert r.credito_mantido == pytest.approx(6_030.19692, abs=0.0005)


def test_corumba_a_sete_por_cento(parametros):
    """Empresa 9: CFOP 2102, ICMS 5.880,00 × 42,86% = 2.520,168."""
    r = calcular(
        tratada("HINOVE (CORUMBÁ- MS)", "produto_quimico", 7.0, 5_880.00, 84_000.00),
        parametros,
    )
    assert r.estorno == pytest.approx(2_520.168, abs=0.0005)


def test_o_que_sobra_do_estorno_de_ms_leva_a_carga_a_quatro_por_cento(parametros):
    """É a razão de ser dos percentuais: 12% × (1 − 0,6667) ≈ 4%."""
    contabil, icms = 100_000.00, 12_000.00
    r = calcular(
        tratada("HINOVE (CORUMBÁ- MS)", "frete_venda", 12.0, icms, contabil), parametros
    )
    assert r.credito_mantido / contabil * 100 == pytest.approx(4.0, abs=0.005)


def test_corumba_nao_estorna_carga_de_quatro_por_cento(parametros):
    r = calcular(
        tratada("HINOVE (CORUMBÁ- MS)", "materia_prima", 4.0, 1_000.00, 25_000.00),
        parametros,
    )
    assert r.estorno == 0.0


def test_credito_de_transferencia_recebida_e_indevido_e_nao_estorno(parametros):
    """CFOP 2152 em Corumbá: o crédito não é apropriado nem estornado.

    Fica em parcela própria para não se confundir com estorno na conciliação —
    foi somá-lo ao crédito mantido que produziu a divergência da apuração
    consolidada de Julho/2026.
    """
    linha = tratada("HINOVE (CORUMBÁ- MS)", "materia_prima", 4.0, 14_424.02, 360_618.45)
    linha.origem.dados["cfop"] = 2152
    r = calcular(linha, parametros)
    assert r.credito_indevido == pytest.approx(14_424.02, abs=0.005)
    assert r.credito_mantido == 0.0
    assert r.estorno == 0.0
    assert r.confere


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
