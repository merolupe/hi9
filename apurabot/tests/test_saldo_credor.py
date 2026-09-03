"""O saldo credor — a conta gráfica atravessando a virada do mês.

O Livro Fiscal traz os documentos de uma competência e nada mais. O crédito que
sobrou do mês anterior não está lá, mas está na conta: é a linha 009 do Registro
de Apuração.

A referência é a linha 009 dos Registros de Apuração de 07/2026: FILIAL GUARÁ
(empresa 11) abre com **R$ 1.782,53** e LONDRINA (empresa 7) com
**R$ 327.121,97**. Matriz, Registro, Rio Brilhante e Corumbá fecharam junho
devedores e abrem julho zerados.

Londrina é a conta gráfica inteira num só documento: PR difere a saída, então o
mês não tem débito e a linha 014 é a soma da abertura com o crédito das
entradas — 327.121,97 + 13.882,40 = **R$ 341.004,37**, que é a abertura de
agosto.

Zerado **declarado** não é a mesma coisa que zerado por falta de declaração: no
primeiro caso o registro fecha, no segundo ele marca a linha 009. É o que a
maior parte destes testes cobre.
"""
from __future__ import annotations

import copy

import pytest

from apurabot.apuracao import AjustesDaApuracao, apurar, mes_vizinho
from apurabot.nucleo import registro as reg

CENTAVO = 0.005
GUARA = "HINOVE (FILIAL GUARÁ)"
CODIGO_GUARA = 11
LONDRINA = "HINOVE (LONDRINA)"
CODIGO_LONDRINA = 7

#: Linha 009 do Registro de 07/2026 de Guará.
ABERTURA = 1_782.53
#: O que o Livro de julho produz em Guará, já com o DIFAL de SP na conta,
#: antes de centralizar.
DO_PERIODO = 2_103_633.39
#: O saldo INDIVIDUAL: o do mês mais a abertura, antes de centralizar.
INDIVIDUAL = DO_PERIODO + ABERTURA
#: O saldo devedor que Guará recebe de Registro e Matriz por centralizar SP.
RECEBIDO = 299_560.95
#: A linha 002 traz o DIFAL da própria unidade mais o recebido.
LINHA_002 = 303_470.87
#: A linha 014 — o saldo FINAL, depois da centralização. É o que `filial.saldo`
#: devolve e o que todo relatório mostra: INDIVIDUAL − RECEBIDO.
LINHA_014 = 1_805_854.97
A_TRANSPORTAR = LINHA_014

#: Linha 009 do Registro de 07/2026 de Londrina.
ABERTURA_LONDRINA = 327_121.97
#: Crédito das entradas de julho em Londrina — a linha 005 do mesmo documento.
DO_PERIODO_LONDRINA = 13_882.40
#: Linha 014 do mesmo documento: a abertura de agosto.
A_TRANSPORTAR_LONDRINA = 341_004.37


@pytest.fixture(scope="module")
def apuracao(base_julho, parametros):
    return apurar(base_julho, parametros)


@pytest.fixture(scope="module")
def sem_declaracao(parametros):
    """Os mesmos parâmetros, com a competência de julho não declarada."""
    p = copy.deepcopy(parametros)
    p.saldos["saldos_credores"] = [
        item for item in p.saldos["saldos_credores"]
        if item.get("competencia") != "2026-07"
    ]
    return p


# -- o parâmetro ------------------------------------------------------------

def test_a_abertura_de_julho_vem_do_registro_do_erp(parametros):
    """Guará e Londrina abriram julho com crédito — a linha 009 de cada um."""
    assert parametros.saldos_credores("2026-07") == {
        CODIGO_GUARA: pytest.approx(ABERTURA, abs=CENTAVO),
        CODIGO_LONDRINA: pytest.approx(ABERTURA_LONDRINA, abs=CENTAVO),
    }


def test_a_abertura_de_agosto_e_a_linha_014_de_julho(parametros):
    """A virada do mês: o que julho transporta é o que agosto recebe."""
    assert parametros.saldos_credores("2026-08") == {
        CODIGO_GUARA: pytest.approx(2_215_164.28, abs=CENTAVO),
        CODIGO_LONDRINA: pytest.approx(A_TRANSPORTAR_LONDRINA, abs=CENTAVO),
    }


def test_a_abertura_e_indexada_pelo_codigo_da_empresa(base_julho, parametros):
    """Pelo código, nunca pelo nome — os nomes vêm com espaçamento irregular."""
    p = copy.deepcopy(parametros)
    p.saldos["saldos_credores"] = [
        {"competencia": "2026-07", "por_estabelecimento": {CODIGO_GUARA: 1_000.0}}
    ]
    assert p.saldos_credores("2026-07") == {CODIGO_GUARA: pytest.approx(1_000.0)}
    apuracao = apurar(base_julho, p)
    guara = apuracao.filiais[GUARA]
    assert guara.saldo_credor_anterior == pytest.approx(1_000.0)
    # E o que abre soma no que se transporta: 014 = 009 + o do período,
    # já descontado o saldo devedor recebido por centralizar SP.
    assert guara.credor == pytest.approx(
        DO_PERIODO + 1_000.0 - RECEBIDO, abs=CENTAVO
    )


def test_competencia_nao_declarada_e_diferente_de_declarada_em_zero(parametros):
    """`None` diz "ninguém declarou"; `{}` diria "declarado, todos zerados"."""
    assert parametros.saldos_credores("2026-06") is None
    assert parametros.saldos_credores("2026-07") is not None


def test_a_competencia_vizinha_sai_da_propria_competencia(apuracao):
    assert apuracao.competencia == "2026-07"
    assert apuracao.competencia_anterior == "2026-06"
    assert apuracao.competencia_seguinte == "2026-08"
    assert mes_vizinho("2026-01", -1) == "2025-12"
    assert mes_vizinho("2026-12", +1) == "2027-01"


# -- a conta gráfica --------------------------------------------------------

def test_guara_abre_julho_com_o_que_o_registro_declara(apuracao):
    guara = apuracao.filiais[GUARA]
    assert guara.saldo_credor_anterior == pytest.approx(ABERTURA, abs=CENTAVO)

    # O que o Livro produziu sozinho, antes de centralizar.
    assert guara.saldo_individual - guara.saldo_credor_anterior == pytest.approx(
        DO_PERIODO, abs=CENTAVO
    )
    assert guara.saldo_individual == pytest.approx(INDIVIDUAL, abs=CENTAVO)

    # E o que ele transporta de fato, depois de absorver SP: a linha 014.
    assert guara.credor == pytest.approx(LINHA_014, abs=CENTAVO)
    assert guara.a_recolher == 0.0
    assert guara.efeito_da_centralizacao == pytest.approx(-RECEBIDO, abs=CENTAVO)


def test_a_linha_014_do_registro_e_a_linha_009_do_mes_seguinte(apuracao, parametros):
    """As duas pontas da mesma conta, no documento que o fiscal assina."""
    registros = reg.montar(apuracao, parametros)
    guara = next(r for r in registros if r.estabelecimento == GUARA)
    assert guara.linha(9).valor == pytest.approx(ABERTURA, abs=CENTAVO)
    assert guara.linha(2).valor == pytest.approx(LINHA_002, abs=CENTAVO)
    assert guara.linha(14).valor == pytest.approx(LINHA_014, abs=CENTAVO)
    # 010 = 008 + 009, e 014 = 010 − 004. Sem a 009 o registro não fecharia.
    assert guara.linha(10).valor == pytest.approx(
        guara.linha(8).valor + guara.linha(9).valor, abs=CENTAVO
    )
    assert guara.linha(14).valor == pytest.approx(
        guara.linha(10).valor - guara.linha(4).valor, abs=CENTAVO
    )


def test_londrina_fecha_julho_na_linha_014_do_documento(apuracao, parametros):
    """PR difere a saída: sem débito, a conta é abertura mais crédito do mês.

    É a checagem mais direta que existe da virada do mês — as três linhas do
    Registro de Londrina (009, 005 e 014) saem do mesmo documento do ERP, e a
    014 é exatamente o que `saldos.yaml` declara como abertura de agosto.
    """
    londrina = apuracao.filiais[LONDRINA]
    assert londrina.saldo_credor_anterior == pytest.approx(
        ABERTURA_LONDRINA, abs=CENTAVO
    )
    assert londrina.credito_mantido == pytest.approx(
        DO_PERIODO_LONDRINA, abs=CENTAVO
    )
    assert londrina.debito == 0.0
    assert londrina.credor == pytest.approx(A_TRANSPORTAR_LONDRINA, abs=CENTAVO)
    assert londrina.a_recolher == 0.0

    registro = next(
        r for r in reg.montar(apuracao, parametros)
        if r.estabelecimento == LONDRINA
    )
    assert registro.linha(9).valor == pytest.approx(ABERTURA_LONDRINA, abs=CENTAVO)
    assert registro.linha(5).valor == pytest.approx(
        DO_PERIODO_LONDRINA, abs=CENTAVO
    )
    assert registro.linha(14).valor == pytest.approx(
        A_TRANSPORTAR_LONDRINA, abs=CENTAVO
    )


def test_competencia_declarada_e_declaracao_completa(apuracao):
    """Quem não aparece no parâmetro abriu o mês em zero.

    Julho declara dois: Guará e Londrina. Os outros quatro fecharam junho
    devedores, e a ausência deles no parâmetro é a declaração de que abriram
    zerados — não é falta de declaração.
    """
    assert apuracao.saldos_declarados
    com_abertura = {GUARA, LONDRINA}
    outros = [
        f for f in apuracao.filiais.values()
        if f.estabelecimento not in com_abertura
    ]
    assert outros
    assert all(f.saldo_credor_anterior == 0.0 for f in outros)


def test_a_abertura_nao_mexe_no_credito_nem_no_debito_do_mes(apuracao):
    """A abertura entra na conta, não na escrituração.

    Se ela vazasse para o crédito bruto ou para o estorno, a conferência linha a
    linha deixaria de fechar — e a regressão contra a planilha manual cairia.
    """
    guara = apuracao.filiais[GUARA]
    assert guara.credito_bruto == pytest.approx(4_167_368.77, abs=CENTAVO)
    assert guara.estorno == pytest.approx(426_771.6818, abs=CENTAVO)
    assert guara.debito == pytest.approx(1_633_053.78, abs=CENTAVO)
    assert guara.confere


def test_a_abertura_reduz_o_que_sai_do_caixa(base_julho, parametros):
    """Num estabelecimento devedor, o crédito de abertura abate o imposto.

    Registro fecha julho devendo 287.113,66. Com uma abertura hipotética de
    100.000,00 o saldo da filial cai na mesma medida.

    A linha 013 do Registro dele é outra coisa: Registro é centralizado em SP,
    então o que sobra depois da abertura vai para Guará na linha 006, e o
    documento fecha em zero. O saldo da FILIAL é antes de centralizar; a linha
    013 do REGISTRO é depois.
    """
    ajustes = AjustesDaApuracao(saldo_credor_anterior={"HINOVE (REGISTRO)": 100_000.0})
    apuracao = apurar(base_julho, parametros, ajustes)
    filial = apuracao.filiais["HINOVE (REGISTRO)"]
    assert filial.saldo_individual == pytest.approx(-199_450.70, abs=CENTAVO)
    assert filial.credor == 0.0
    # O saldo final é zero: ele transfere tudo para Guará.
    assert filial.a_recolher == 0.0

    registro = next(
        r for r in reg.montar(apuracao, parametros, ajustes)
        if r.estabelecimento == "HINOVE (REGISTRO)"
    )
    assert registro.linha(9).valor == pytest.approx(100_000.0, abs=CENTAVO)
    assert registro.linha(6).valor == pytest.approx(199_450.70, abs=CENTAVO)
    assert registro.linha(13).valor == pytest.approx(0.0, abs=CENTAVO)


def test_o_ajuste_aprovado_prevalece_sobre_o_parametro(base_julho, parametros):
    """A rodada pode declarar outra abertura sem editar o arquivo de parâmetro."""
    ajustes = AjustesDaApuracao(saldo_credor_anterior={GUARA: 1.0})
    apuracao = apurar(base_julho, parametros, ajustes)
    assert apuracao.filiais[GUARA].saldo_credor_anterior == pytest.approx(1.0)


# -- o que ninguém declarou não é preenchido por conta própria ---------------

def test_competencia_sem_declaracao_marca_a_linha_009(base_julho, sem_declaracao):
    """Regra 4 do repositório: sem regra, marca — não adivinha.

    Aqui a apuração roda e produz número, porque zero é a única leitura possível
    do silêncio. O registro é que não deixa passar em branco.
    """
    apuracao = apurar(base_julho, sem_declaracao)
    assert not apuracao.saldos_declarados
    assert apuracao.filiais[GUARA].saldo_credor_anterior == 0.0

    registros = reg.montar(apuracao, sem_declaracao)
    guara = next(r for r in registros if r.estabelecimento == GUARA)
    assert guara.linha(9).aguarda_ajuste
    # Sem a abertura, a 014 sai menor exatamente pelo que não foi declarado.
    assert guara.linha(14).valor == pytest.approx(LINHA_014 - ABERTURA, abs=CENTAVO)


def test_com_a_declaracao_a_linha_009_para_de_esperar(apuracao, parametros):
    registros = reg.montar(apuracao, parametros)
    for registro in registros:
        assert not registro.linha(9).aguarda_ajuste


# -- a centralização enxerga o saldo já aberto ------------------------------

def test_o_grupo_de_sp_consolida_com_a_abertura(apuracao):
    """A abertura é do estabelecimento e chega ao grupo pelo saldo dele."""
    sp = next(g for g in apuracao.centralizacao if g.uf == "SP")
    assert sp.centralizadora == GUARA
    # `saldo_proprio` da centralização é o INDIVIDUAL, antes de receber.
    assert sp.saldo_proprio == pytest.approx(INDIVIDUAL, abs=CENTAVO)
    assert sp.saldo_final == pytest.approx(LINHA_014, abs=CENTAVO)


# -- as saídas -------------------------------------------------------------

def test_o_painel_publica_as_duas_pontas(base_julho, parametros):
    from apurabot.web import painel

    apuracao = apurar(base_julho, parametros)
    registros = reg.montar(apuracao, parametros)
    dados = painel.montar(base_julho, apuracao, registros)
    assert dados["competencia_anterior"] == "2026-06"
    assert dados["competencia_seguinte"] == "2026-08"
    assert dados["saldos_declarados"] is True
    guara = next(f for f in dados["filiais"] if f["estabelecimento"] == GUARA)
    assert guara["saldo_credor_anterior"] == pytest.approx(ABERTURA, abs=CENTAVO)
    assert guara["credor"] == pytest.approx(A_TRANSPORTAR, abs=CENTAVO)


def test_a_planilha_entrega_a_abertura_do_mes_seguinte(base_julho, parametros, tmp_path):
    """Quem fecha agosto tem que achar o número sem subtrair linha do registro."""
    import openpyxl

    from apurabot.saida import escrever

    destino = tmp_path / "com_saldo.xlsx"
    escrever(base_julho, destino, apurar(base_julho, parametros))
    aba = openpyxl.load_workbook(destino)["APURAÇÃO POR FILIAL"]
    celulas = [c.value for linha in aba.iter_rows() for c in linha]
    texto = "\n".join(str(v) for v in celulas if v)

    assert "Saldo credor — linhas 009 e 014 do Registro de Apuração" in texto
    assert "vai para 2026-08" in texto
    assert "veio de 2026-06" in texto
    assert "saldo credor anterior" in texto
    assert any(
        isinstance(v, float) and abs(v - A_TRANSPORTAR) < CENTAVO for v in celulas
    ), "a planilha não traz a linha 014 de Guará"
