"""Regressão do Registro de Apuração do ICMS contra Julho/2026.

Os alvos vêm do Registro de Apuração emitido pelo ERP para RIO BRILHANTE. O
bloco de entradas e saídas é soma pura do Livro Fiscal — se ele não reproduzir
o registro do ERP ao centavo, ou o motor ou o ERP leu o livro errado.
"""
from __future__ import annotations

import pytest

from apurabot.apuracao import AjustesDaApuracao, apurar
from apurabot.nucleo import atividade as ativ
from apurabot.nucleo import registro as reg

CENTAVO = 0.005
RB = "HINOVE (RIO BRILHANTE)"

# Registro de Apuração do ICMS — RIO BRILHANTE, 01/07/2026 a 31/07/2026.
# (valores contábeis, base de cálculo, imposto, isentas/n.trib., outras)
ENTRADAS = {
    "do Estado": (5_302_366.31, 0.0, 2_146.57, 2_456_680.40, 2_845_685.91),
    "de outros Estados": (5_667_570.01, 1_479_555.26, 153_929.91, 3_880_746.19,
                          351_013.04),
    "do Exterior": (13_510_547.87, 1_846_038.67, 313_826.57, 5_999_625.90,
                    5_664_883.30),
}
ENTRADAS_TOTAL = (24_480_484.19, 3_325_593.93, 469_903.05, 12_337_052.49,
                  8_861_582.25)
SAIDAS = {
    "para o Estado": (7_289_225.52, 596_202.18, 101_354.35, 4_008_653.75,
                      2_684_369.59),
    "para outros Estados": (12_970_887.39, 3_371_976.03, 404_637.06, 9_227_165.58,
                            371_745.78),
    "para o Exterior": (0.0, 0.0, 0.0, 0.0, 0.0),
}
SAIDAS_TOTAL = (20_260_112.91, 3_968_178.21, 505_991.41, 13_235_819.33,
                3_056_115.37)

# Resumo da Apuração, folha 3 do mesmo documento.
AJUSTE_ESTORNO = 3_865.30          # linha 003, "estorno para ajuste de apuração"
AJUSTE_ART_68 = 46_138.68          # linha 006, art. 68 do RICMS/MS
AJUSTE_ESTORNO_DEBITO = 33_039.71  # estorno de débitos

RESUMO = {
    1: 505_991.41,
    2: 99_412.10,      # recebimento de saldo devedor do centralizador
    3: 335_101.41,     # 331.236,11 do livro + 3.865,30 de ajuste
    4: 940_504.92,
    5: 469_903.05,
    8: 549_081.44,
    10: 549_081.44,
    11: 391_423.48,
}


@pytest.fixture(scope="module")
def ajustes():
    return AjustesDaApuracao(
        estorno_de_credito={RB: {ativ.INDUSTRIAL: AJUSTE_ESTORNO}},
        outros_creditos={RB: {ativ.INDUSTRIAL: AJUSTE_ART_68}},
        estorno_de_debito={RB: {ativ.INDUSTRIAL: AJUSTE_ESTORNO_DEBITO}},
    )


@pytest.fixture(scope="module")
def registros(base_julho, parametros, ajustes):
    return reg.montar(apurar(base_julho, parametros, ajustes=ajustes),
                      parametros, ajustes)


@pytest.fixture(scope="module")
def rio_brilhante(registros):
    return next(r for r in registros if r.estabelecimento == RB)


# -- entradas e saídas: soma pura do Livro Fiscal ---------------------------

@pytest.mark.parametrize("grupo", sorted(ENTRADAS))
def test_os_subtotais_de_entrada_reproduzem_o_registro(rio_brilhante, grupo):
    assert rio_brilhante.entradas.subtotal(grupo).as_tuple() == pytest.approx(
        ENTRADAS[grupo], abs=CENTAVO
    )


@pytest.mark.parametrize("grupo", sorted(SAIDAS))
def test_os_subtotais_de_saida_reproduzem_o_registro(rio_brilhante, grupo):
    assert rio_brilhante.saidas.subtotal(grupo).as_tuple() == pytest.approx(
        SAIDAS[grupo], abs=CENTAVO
    )


def test_os_totais_reproduzem_o_registro(rio_brilhante):
    assert rio_brilhante.entradas.total.as_tuple() == pytest.approx(
        ENTRADAS_TOTAL, abs=CENTAVO
    )
    assert rio_brilhante.saidas.total.as_tuple() == pytest.approx(
        SAIDAS_TOTAL, abs=CENTAVO
    )


def test_o_total_e_a_soma_dos_subtotais(rio_brilhante):
    """Nenhuma linha do livro fica fora de um grupo de procedência."""
    for bloco in (rio_brilhante.entradas, rio_brilhante.saidas):
        somado = [0.0] * 5
        for grupo in bloco.grupos():
            for i, v in enumerate(bloco.subtotal(grupo).as_tuple()):
                somado[i] += v
        assert somado == pytest.approx(bloco.total.as_tuple(), abs=CENTAVO)


def test_o_imposto_creditado_do_livro_e_o_credito_bruto_da_apuracao(registros):
    """Trava entre os dois blocos: os dois leram o mesmo livro."""
    for registro in registros:
        assert registro.confere_com_a_apuracao, registro.estabelecimento


# -- resumo -----------------------------------------------------------------

@pytest.mark.parametrize("codigo", sorted(RESUMO))
def test_o_resumo_reproduz_o_registro(rio_brilhante, codigo):
    assert rio_brilhante.linha(codigo).valor == pytest.approx(
        RESUMO[codigo], abs=CENTAVO
    )


def test_a_linha_002_vem_da_centralizacao_e_nao_de_ajuste(base_julho, parametros):
    """R$ 99.412,10 é o saldo devedor de Corumbá, calculado — não declarado.

    Em MS a transferência para o centralizador é lançamento de ajuste no
    Registro de Apuração, e a ferramenta o calcula a partir do saldo apurado.
    """
    registros = reg.montar(apurar(base_julho, parametros), parametros, None)
    rb = next(r for r in registros if r.estabelecimento == RB)
    assert rb.linha(2).valor == pytest.approx(99_412.10, abs=CENTAVO)
    assert any(
        "centralizador" in descricao for descricao, _ in rb.linha(2).discriminacao
    )


def test_o_subtotal_004_e_a_soma_de_001_002_e_003(rio_brilhante):
    r = rio_brilhante
    assert r.linha(4).valor == pytest.approx(
        r.linha(1).valor + r.linha(2).valor + r.linha(3).valor, abs=CENTAVO
    )


def test_o_subtotal_008_e_a_soma_de_005_006_e_007(rio_brilhante):
    r = rio_brilhante
    assert r.linha(8).valor == pytest.approx(
        r.linha(5).valor + r.linha(6).valor + r.linha(7).valor, abs=CENTAVO
    )


def test_o_estorno_do_livro_entra_na_linha_003_discriminado(rio_brilhante):
    discriminacao = dict(
        (d, v) for d, v in ((x[0], x[1]) for x in rio_brilhante.linha(3).discriminacao)
    )
    assert sum(discriminacao.values()) == pytest.approx(
        rio_brilhante.linha(3).valor, abs=CENTAVO
    )
    assert AJUSTE_ESTORNO in [round(v, 2) for v in discriminacao.values()]


def test_o_imposto_a_recolher_nao_e_negativo(registros):
    for registro in registros:
        assert registro.linha(13).valor >= 0.0
        assert registro.linha(14).valor >= 0.0
        assert not (registro.linha(13).valor and registro.linha(14).valor)


def test_a_deducao_nao_supera_o_saldo_devedor(registros):
    """O benefício abate imposto; não gera crédito."""
    for registro in registros:
        assert registro.linha(12).valor <= registro.linha(11).valor + CENTAVO


# -- o que ainda não veio fica marcado --------------------------------------

def test_sem_ajuste_declarado_as_linhas_saem_marcadas(base_julho, parametros):
    """O registro diz o que falta em vez de fingir um total."""
    registros = reg.montar(apurar(base_julho, parametros), parametros, None)
    rb = next(r for r in registros if r.estabelecimento == RB)
    assert rb.aguarda_ajustes
    assert {i.codigo for i in rb.resumo if i.aguarda_ajuste} == {3, 6, 7, 9}


def test_com_ajuste_declarado_nada_fica_marcado(rio_brilhante):
    assert not rio_brilhante.aguarda_ajustes


# -- totalizador ------------------------------------------------------------

def test_o_totalizador_soma_os_estabelecimentos(registros):
    total = reg.totalizador(registros, "2026-07")
    assert total.gerencial
    assert total.entradas.total.imposto == pytest.approx(
        sum(r.entradas.total.imposto for r in registros), abs=CENTAVO
    )
    assert total.linha(1).valor == pytest.approx(
        sum(r.linha(1).valor for r in registros), abs=CENTAVO
    )


def test_o_totalizador_herda_a_marca_de_ajuste_pendente(base_julho, parametros):
    registros = reg.montar(apurar(base_julho, parametros), parametros, None)
    assert reg.totalizador(registros, "2026-07").aguarda_ajustes
