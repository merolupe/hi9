"""Regressão da apuração por estabelecimento contra Julho/2026.

Os alvos vêm da aba `ESTORNO` da planilha manual. Onde há diferença, ela é
exigida com valor exato — o teste não tolera divergência em silêncio.
"""
from __future__ import annotations

import pytest

from apurabot.apuracao import apurar

CENTAVO = 0.005

# estabelecimento -> (crédito bruto, estorno, crédito mantido) da aba ESTORNO
MANUAL = {
    "HINOVE (REGISTRO)": (286_030.83, 50_481.9672, 235_548.8628),
    "HINOVE (FILIAL GUARÁ)": (4_167_368.77, 426_771.6818, 3_740_597.0882),
    "HINOVE (BARRA DO GARÇAS - MT)": (50_309.07, 50_309.07, 0.0),
    "HINOVE (LONDRINA)": (13_882.40, 0.0, 13_882.40),
    # Corumbá vem da apuração individualizada (Empresa 9), não da consolidada:
    # crédito mantido 12.079,22, e não os 26.503,24 da consolidada, que somava
    # o crédito indevido de transferência.
    "HINOVE (CORUMBÁ- MS)": (46_464.79, 19_961.553359, 12_079.216641),
    "HINOVE (RIO BRILHANTE)": (469_903.05, 331_236.11, 138_666.94),
}

# Diferença conhecida e explicada, em reais de estorno.
ICL_RIO_BRILHANTE = -8_947.80  # 9.019,01 da ICL reclassificada, menos 71,21 de resíduo

CREDITO_INDEVIDO_CORUMBA = 14_424.02  # CFOP 2152, contraparte do 6152 de Guará


@pytest.fixture(scope="module")
def apuracao(base_julho):
    return apurar(base_julho)


def test_credito_bruto_bate_em_todas_as_filiais(apuracao):
    """O crédito bruto é leitura direta do Livro — tem que bater em todas."""
    for nome, (bruto, _, _) in MANUAL.items():
        filial = apuracao.filiais[nome]
        assert filial.credito_bruto == pytest.approx(bruto, abs=CENTAVO), nome


def test_identidade_mantido_mais_estorno_igual_bruto(apuracao):
    assert apuracao.inconsistentes == []
    assert apuracao.total.confere


@pytest.mark.parametrize(
    "nome",
    ["HINOVE (REGISTRO)", "HINOVE (FILIAL GUARÁ)",
     "HINOVE (BARRA DO GARÇAS - MT)", "HINOVE (LONDRINA)",
     "HINOVE (CORUMBÁ- MS)"],
)
def test_estorno_reproduz_exatamente_sp_mt_pr_e_corumba(apuracao, nome):
    _, estorno, mantido = MANUAL[nome]
    filial = apuracao.filiais[nome]
    assert filial.estorno == pytest.approx(estorno, abs=CENTAVO)
    assert filial.credito_mantido == pytest.approx(mantido, abs=CENTAVO)


def test_corumba_separa_o_credito_indevido_do_estorno(apuracao):
    """A apuração consolidada somava o crédito indevido ao mantido; aqui não."""
    filial = apuracao.filiais["HINOVE (CORUMBÁ- MS)"]
    assert filial.credito_indevido == pytest.approx(CREDITO_INDEVIDO_CORUMBA, abs=CENTAVO)
    # 12.079,22 + 14.424,02 = 26.503,24, o número que a consolidada trazia.
    assert filial.credito_mantido + filial.credito_indevido == pytest.approx(
        26_503.24, abs=CENTAVO
    )


def test_credito_indevido_de_corumba_e_a_contraparte_do_debito_de_guara(apuracao, base_julho):
    """A mesma transferência: CFOP 6152 sai de Guará, CFOP 2152 entra em Corumbá."""
    debito_guara = sum(
        t.origem.dados.get("valor_icms") or 0.0
        for t in base_julho.relevantes
        if t.origem.cfop_int == 6152
        and "GUAR" in str(t.origem.dados.get("estabelecimento"))
    )
    assert debito_guara == pytest.approx(CREDITO_INDEVIDO_CORUMBA, abs=CENTAVO)


def test_rio_brilhante_difere_apenas_pela_reclassificacao_da_icl(apuracao):
    _, estorno, _ = MANUAL["HINOVE (RIO BRILHANTE)"]
    diferenca = apuracao.filiais["HINOVE (RIO BRILHANTE)"].estorno - estorno
    assert diferenca == pytest.approx(ICL_RIO_BRILHANTE, abs=CENTAVO)


def test_debito_de_saida_bate_com_a_dinamica(apuracao):
    """Débitos conferidos contra os totais de saída da aba Dinamica."""
    esperado = {
        "HINOVE (REGISTRO)": 522_662.52,
        "HINOVE (FILIAL GUARÁ)": 1_633_053.78,
        "HINOVE (CORUMBÁ- MS)": 111_491.32,
        "HINOVE (RIO BRILHANTE)": 505_991.41,
    }
    for nome, debito in esperado.items():
        assert apuracao.filiais[nome].debito == pytest.approx(debito, abs=CENTAVO), nome


def test_mt_zera_o_credito_e_pr_zera_o_estorno(apuracao):
    """A assimetria entre os dois diferimentos é regra, não engano."""
    assert apuracao.filiais["HINOVE (BARRA DO GARÇAS - MT)"].credito_mantido == 0.0
    assert apuracao.filiais["HINOVE (LONDRINA)"].estorno == 0.0


# --------------------------------------------------------------------------
# Benefício fiscal de Rio Brilhante — Termo de Acordo n. 1.190/2018
# --------------------------------------------------------------------------

BENEFICIO_LANCADO_EM_JULHO = 283_766.56


def test_beneficio_de_rio_brilhante_reproduz_o_que_a_apuracao_faz(apuracao):
    """O alcance do benefício é decisão em aberto, e o padrão não a antecipa.

    O parâmetro `alcance.criterio` está em `todas_as_saidas`, que é o que a
    apuração de Julho/2026 fez. Com o crédito mantido daquela apuração
    (R$ 138.666,94) o cálculo dá R$ 284.294,40 contra os R$ 283.766,56
    lançados — 0,19%. Aqui o crédito é o corrigido, então o valor difere.

    A leitura literal do Termo (só produção própria) daria bem menos, e está
    medida no teste seguinte. Nenhuma das duas é asseverada como correta —
    ver docs/apurabot/06-decisoes-pendentes.md, item 1.
    """
    beneficio = apuracao.filiais["HINOVE (RIO BRILHANTE)"].beneficio
    assert beneficio is not None
    assert beneficio.criterio == "todas_as_saidas"
    assert beneficio.credito_presumido == pytest.approx(277_369.17, abs=0.01)
    assert beneficio.debito_fora_do_alcance == 0.0


def test_a_leitura_literal_do_termo_daria_muito_menos(apuracao, base_julho):
    """Quanto custa a decisão: R$ 49 mil de diferença entre as duas leituras.

    O inciso I da cláusula terceira diz "exclusivamente às operações realizadas
    com os produtos resultantes de sua própria industrialização neste Estado".
    Restringindo a base aos CFOP de produção própria, o benefício cai.
    """
    import copy

    from apurabot.nucleo.beneficio import calcular

    params = copy.deepcopy(base_julho.parametros)
    beneficio = params.regimes["beneficios_fiscais"]["ms_rio_brilhante"]
    beneficio["alcance"]["criterio"] = "cfop_de_producao_propria"

    filial = apuracao.filiais["HINOVE (RIO BRILHANTE)"]
    linhas = [
        t for t in base_julho.linhas
        if "RIO BRILHANTE" in str(t.origem.dados.get("estabelecimento"))
    ]
    literal = calcular(linhas, "ms_rio_brilhante", filial.credito_mantido, params)

    assert literal.credito_presumido == pytest.approx(228_357.72, abs=0.01)
    assert literal.debito_fora_do_alcance == pytest.approx(93_717.24, abs=CENTAVO)
    diferenca = filial.beneficio.credito_presumido - literal.credito_presumido
    assert diferenca == pytest.approx(49_011.45, abs=0.01)


def test_a_apuracao_de_julho_nao_indica_prorrogacao_da_clausula_quarta(apuracao):
    """Se a quarta valesse, a revenda interestadual teria 50%, não 67/80.

    Débito de revenda interestadual (CFOP 6102) em Julho: R$ 47.298,29. Sob a
    cláusula quarta o benefício dela seria metade do saldo devedor. O valor
    lançado só fecha aplicando os percentuais da cláusula TERCEIRA sobre todas
    as saídas — o que aponta para base ampliada, e não para a quarta prorrogada.
    """
    filial = apuracao.filiais["HINOVE (RIO BRILHANTE)"]
    beneficio = filial.beneficio
    percentuais = {beneficio.intra.percentual, beneficio.inter.percentual}
    assert percentuais == {67.0, 80.0}
    assert 50.0 not in percentuais
def test_so_rio_brilhante_tem_beneficio(apuracao):
    com_beneficio = [f.estabelecimento for f in apuracao.filiais.values() if f.beneficio]
    assert com_beneficio == ["HINOVE (RIO BRILHANTE)"]


def test_a_base_do_beneficio_cobre_todo_o_debito_de_saida(apuracao):
    """No critério em vigor, nada fica de fora — e a soma tem que fechar."""
    beneficio = apuracao.filiais["HINOVE (RIO BRILHANTE)"].beneficio
    total = beneficio.debito_beneficiado + beneficio.debito_fora_do_alcance
    assert total == pytest.approx(505_991.41, abs=CENTAVO)


def test_o_beneficio_nao_supera_o_saldo_devedor_que_o_gerou(apuracao):
    assert apuracao.filiais["HINOVE (RIO BRILHANTE)"].beneficio.confere
