"""Regra de estorno por regime — casos isolados."""
from __future__ import annotations

import pytest

from apurabot.base_tratada import LinhaTratada
from apurabot.ingestao import LinhaLivro
from apurabot.nucleo.carga import ResultadoCarga, Situacao
from apurabot.nucleo.classificacao import ResultadoClassificacao
from apurabot.nucleo.estorno import RegimeDesconhecido, calcular


def tratada(estabelecimento, categoria, carga, icms, contabil, entrada=True,
            aliquota=None):
    """Monta uma linha tratada de teste.

    `aliquota` só precisa ser informada quando difere da carga efetiva — o caso
    da base reduzida, que é exatamente onde a regra de MS se decide.
    """
    dados = {
        "estabelecimento": estabelecimento,
        "entrada_saida": "Entrada" if entrada else "Saída",
        "valor_icms": icms,
        "valor_contabil": contabil,
        "aliquota_icms": carga if aliquota is None else aliquota,
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


def test_rio_brilhante_usa_a_mesma_formula_de_corumba(parametros):
    """RB não tem regra própria de estorno: é o mesmo proporcional de Corumbá.

    O que RB tem de diferente é o benefício, que vem depois e incide sobre o
    saldo devedor da atividade industrial.
    """
    rb = calcular(
        tratada("HINOVE (RIO BRILHANTE)", "frete_venda", 12.0, 87_702.34, 731_689.10),
        parametros,
    )
    corumba = calcular(
        tratada("HINOVE (CORUMBÁ- MS)", "frete_venda", 12.0, 87_702.34, 731_689.10),
        parametros,
    )
    assert rb.estorno == pytest.approx(58_471.15, abs=0.005)
    assert rb.estorno == pytest.approx(corumba.estorno, abs=0.005)


def test_a_aliquota_manda_e_nao_a_carga_efetiva(parametros):
    """As importações de ureia de Julho/2026: alíquota de 17% com base reduzida.

    Movimento Livros Fiscais, CFOP 3101, UREIA 46-00-00 Bag: valor contábil
    6.603.845,95 e base 1.553.846,05, o que dá carga efetiva de 4%. O motor
    antigo lia a carga, concluía "entrada beneficiada" e estornava 100%. A
    regra real olha a alíquota: 1 − 4/17 = 0,7647.
    """
    r = calcular(
        tratada("HINOVE (RIO BRILHANTE)", "materia_prima", 4.0, 264_153.83,
                6_603_845.95, aliquota=17.0),
        parametros,
    )
    assert r.estorno == pytest.approx(201_998.43, abs=0.005)
    assert r.credito_mantido == pytest.approx(62_155.40, abs=0.005)
    assert r.confere


@pytest.mark.parametrize(
    "aliquota, parcela",
    [(4.0, 0.0), (7.0, 0.4286), (12.0, 0.6667),
     (17.0, 0.7647), (18.0, 0.7778), (19.0, 0.7895)],
)
def test_a_parcela_nao_tributada_e_a_formula_um_menos_quatro_sobre_aliquota(
    parametros, aliquota, parcela
):
    """Tabela "REDUÇÃO ATUAL" da aba ESTORNO — é fórmula, não catálogo."""
    icms = 10_000.00
    r = calcular(
        tratada("HINOVE (RIO BRILHANTE)", "materia_prima", 4.0, icms, 250_000.00,
                aliquota=aliquota),
        parametros,
    )
    assert r.estorno == pytest.approx(icms * parcela, abs=0.005)


def test_o_credito_mantido_sempre_equivale_a_carga_de_quatro_por_cento(parametros):
    """A razão de ser da regra: o que sobra do crédito é a carga de referência."""
    for aliquota in (7.0, 12.0, 17.0, 18.0):
        base = 100_000.00
        icms = base * aliquota / 100
        r = calcular(
            tratada("HINOVE (RIO BRILHANTE)", "materia_prima", aliquota, icms, base,
                    aliquota=aliquota),
            parametros,
        )
        assert r.credito_mantido / base * 100 == pytest.approx(4.0, abs=0.005)


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


# -- SP a partir de 09/2026: o percentual exato da tabela ---------------------

def _sp(data, categoria, carga, icms, contabil, aliquota=None):
    """Entrada de Guará com data de movimento — é ela que escolhe a fórmula."""
    import datetime as dt

    linha = tratada("HINOVE (FILIAL GUARÁ)", categoria, carga, icms, contabil,
                    aliquota=aliquota)
    linha.origem.dados["data_movimento"] = dt.datetime(*data)
    return linha


@pytest.mark.parametrize("carga, percentual", [
    (7.0, 0.4286), (12.0, 0.6667), (18.0, 0.7778),
])
def test_sp_de_setembro_estorna_o_percentual_da_tabela(parametros, carga, percentual):
    """A tabela do time fiscal: 7% → 42,86%, 12% → 66,67%, 18% → 77,78%."""
    icms = carga * 100
    r = calcular(_sp((2026, 9, 10), "frete_venda", carga, icms, 10_000.0), parametros)
    assert r.estorno == pytest.approx(icms * percentual, abs=0.005)
    assert r.confere


def test_sp_cte_com_pedagio_estorna_o_percentual_e_nao_o_contabil(parametros):
    """Valor contábil acima da base: o percentual continua o da tabela."""
    r = calcular(_sp((2026, 9, 10), "frete_venda", 12.0, 1_388.65, 12_652.20),
                 parametros)
    assert r.estorno == pytest.approx(1_388.65 * 0.6667, abs=0.005)


def test_sp_ate_agosto_continua_sobre_o_valor_contabil(parametros):
    """Julho e agosto foram lançados assim — e continuam reproduzíveis."""
    r = calcular(_sp((2026, 8, 31), "frete_venda", 12.0, 1_388.65, 12_652.20),
                 parametros)
    assert r.estorno == pytest.approx(12_652.20 * 0.08, abs=0.005)


def test_sp_de_setembro_carga_de_4_nao_estorna(parametros):
    r = calcular(_sp((2026, 9, 10), "frete_compra", 4.0, 400.0, 10_000.0), parametros)
    assert r.estorno == 0.0


def test_sp_de_setembro_isentos_continuam_isentos(parametros):
    r = calcular(_sp((2026, 9, 10), "materia_prima", 12.0, 1_200.0, 10_000.0),
                 parametros)
    assert r.estorno == 0.0


# -- MS: a chave é a alíquota nominal, também com a base reduzida -------------

def _ms(data, categoria, carga, icms, contabil, aliquota):
    import datetime as dt

    linha = tratada("HINOVE (RIO BRILHANTE)", categoria, carga, icms, contabil,
                    aliquota=aliquota)
    linha.origem.dados["data_movimento"] = dt.datetime(*data)
    return linha


@pytest.mark.parametrize("data", [(2026, 8, 31), (2026, 9, 10), (2026, 10, 1)])
@pytest.mark.parametrize("aliquota, carga, percentual", [
    (7.0, 4.0, 0.4286),     # base reduzida pelo fornecedor: estorna de novo
    (12.0, 4.0, 0.6667),    # retorno de armazém com a base reduzida
    (17.0, 4.0, 0.7647),    # importação a 17% com a base reduzida
    (7.0, 7.0, 0.4286),     # nota cheia a 7%
    (12.0, 12.0, 0.6667),   # frete cheio a 12%
    (4.0, 4.0, 0.0),        # alíquota de 4%: nada a estornar
])
def test_ms_estorna_pela_aliquota_nominal(parametros, data, aliquota, carga,
                                          percentual):
    """O crédito fica em 4% da base de cálculo — antes e depois de 09/2026."""
    icms = 10_000.0 * carga / 100
    r = calcular(_ms(data, "embalagem", carga, icms, 10_000.0, aliquota),
                 parametros)
    assert r.estorno == pytest.approx(icms * percentual, abs=0.005)


def test_silicato_com_base_reduzida_fica_com_4_da_base(parametros):
    """O exemplo do time: 5.497,32 de valor, base 3.141,16 a 7%, ICMS 219,88."""
    r = calcular(_ms((2026, 9, 10), "embalagem", 4.0, 219.88, 5_497.32, 7.0),
                 parametros)
    assert r.estorno == pytest.approx(94.24, abs=0.005)
    assert 219.88 - r.estorno == pytest.approx(3_141.16 * 0.04, abs=0.01)
