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


def test_rio_brilhante_bate_exatamente_com_a_gia(apuracao):
    """O estorno de RB passou a fechar quando a chave virou a alíquota.

    Com a chave na carga efetiva, as importações de ureia (CFOP 3101, alíquota
    de 17% com base reduzida a 4%) estornavam 100%. Pela alíquota estornam
    76,47%, e o total cai exatamente nos R$ 331.236,11 que o Registro de
    Apuração declara na linha 003.
    """
    _, estorno, mantido = MANUAL["HINOVE (RIO BRILHANTE)"]
    filial = apuracao.filiais["HINOVE (RIO BRILHANTE)"]
    assert filial.estorno == pytest.approx(estorno, abs=CENTAVO)
    assert filial.credito_mantido == pytest.approx(mantido, abs=CENTAVO)


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
# Segregação por atividade e benefício fiscal de Rio Brilhante
#
# Os alvos desta seção NÃO vêm da planilha manual. Vêm dos três documentos
# oficiais da competência 07/2026:
#   - Registro de Apuração do ICMS, emitido em 07/08/2026
#   - GIA - Benefício Fiscal, protocolo 36160E2, retificadora de 25/08/2026
#   - GIA - Apuração Final, mesmo protocolo
#
# A GIA original invertia as colunas Industrial e Comercial. A retificadora
# corrigiu, e é ela que o motor reproduz.
# --------------------------------------------------------------------------

from apurabot.apuracao import AjustesDaApuracao          # noqa: E402
from apurabot.nucleo import atividade as ativ            # noqa: E402

RB = "HINOVE (RIO BRILHANTE)"

# Linha 003 do Registro: "Estorno de créditos para ajuste de apuração do ICMS".
# Não nasce de documento no Livro Fiscal: é declarado na aba AJUSTES.
AJUSTE_ESTORNO_INDUSTRIAL = 3_865.30

# GIA - Apuração Final, quadros "Débitos de ICMS" e "Créditos de ICMS".
#
# O crédito comercial inclui o complemento de ICMS (CFOP 2906), que é crédito
# apropriável e integra a atividade comercial.
GIA_POR_ATIVIDADE = {
    ativ.INDUSTRIAL: {"credito": 327_834.95, "estorno": 245_987.17, "debito": 412_274.17},
    ativ.COMERCIAL: {"credito": 139_921.53, "estorno": 85_248.94, "debito": 93_717.23},
}

# Quadro "CÁLCULO BENEFÍCIO FISCAL" da GIA - Benefício Fiscal.
GIA_BENEFICIO = {
    "debito_intra": 56_934.28,
    "debito_inter": 355_339.89,
    "credito_intra": 10_769.23,
    "credito_inter": 67_213.25,
    "credito_da_parcela_incentivada": 77_982.48,
    "base": 334_291.69,
    "presumido_intra": 30_930.58,
    "presumido_inter": 230_501.31,
    "presumido": 261_431.89,
    "fadefe": 5_228.64,
}


@pytest.fixture(scope="module")
def apuracao_com_ajustes(base_julho):
    """A apuração como o documento oficial a declara, com a linha 003."""
    return apurar(
        base_julho,
        ajustes=AjustesDaApuracao(
            estorno_de_credito={RB: {ativ.INDUSTRIAL: AJUSTE_ESTORNO_INDUSTRIAL}}
        ),
    )


def test_so_ms_segrega_por_atividade(apuracao):
    """SP, MT e PR apuram por estabelecimento; MS, por atividade."""
    segregam = sorted(
        f.uf for f in apuracao.filiais.values() if f.segrega_por_atividade
    )
    assert set(segregam) == {"MS"}


def test_nenhuma_linha_fica_sem_atividade(apuracao):
    """Atividade indefinida bloqueia o encerramento — regra 4 do projeto."""
    assert apuracao.sem_regra_de_atividade == []


@pytest.mark.parametrize("atividade", sorted(GIA_POR_ATIVIDADE))
def test_a_segregacao_por_atividade_reproduz_a_gia(apuracao, atividade):
    alvo = GIA_POR_ATIVIDADE[atividade]
    somas = apuracao.filiais[RB].atividade(atividade)
    assert somas.debito == pytest.approx(alvo["debito"], abs=CENTAVO)
    assert somas.estorno == pytest.approx(alvo["estorno"], abs=CENTAVO)
    assert somas.credito_bruto == pytest.approx(alvo["credito"], abs=CENTAVO)
    assert somas.confere


def test_o_credito_bruto_e_a_soma_das_atividades(apuracao):
    """Nada de crédito fica fora da segregação."""
    filial = apuracao.filiais[RB]
    das_atividades = sum(t.credito_bruto for t in filial.por_atividade.values())
    assert das_atividades == pytest.approx(filial.credito_bruto, abs=CENTAVO)


def test_o_debito_industrial_e_a_base_das_saidas_incentivadas(apuracao):
    """CFOP 5101 + 5118 + 6101, e o corte intra/inter que a GIA usa."""
    somas = apuracao.filiais[RB].atividade(ativ.INDUSTRIAL)
    assert somas.debito_de(ativ.INTRAESTADUAL) == pytest.approx(
        GIA_BENEFICIO["debito_intra"], abs=CENTAVO
    )
    assert somas.debito_de(ativ.INTERESTADUAL) == pytest.approx(
        GIA_BENEFICIO["debito_inter"], abs=CENTAVO
    )


def test_o_beneficio_reproduz_a_gia_ao_centavo(apuracao_com_ajustes):
    """A cadeia inteira, do crédito industrial ao FADEFE."""
    b = apuracao_com_ajustes.filiais[RB].beneficio
    assert b is not None
    assert b.criterio == "atividade_industrial"
    assert b.credito_da_parcela_incentivada == pytest.approx(
        GIA_BENEFICIO["credito_da_parcela_incentivada"], abs=0.01
    )
    assert b.intra.credito_rateado == pytest.approx(GIA_BENEFICIO["credito_intra"], abs=0.01)
    assert b.inter.credito_rateado == pytest.approx(GIA_BENEFICIO["credito_inter"], abs=0.01)
    assert b.base_do_incentivo == pytest.approx(GIA_BENEFICIO["base"], abs=0.01)
    assert b.intra.credito_presumido == pytest.approx(
        GIA_BENEFICIO["presumido_intra"], abs=0.01
    )
    assert b.inter.credito_presumido == pytest.approx(
        GIA_BENEFICIO["presumido_inter"], abs=0.01
    )
    assert b.credito_presumido == pytest.approx(GIA_BENEFICIO["presumido"], abs=0.01)
    assert b.confere


def test_o_fadefe_de_julho_sao_dois_por_cento(apuracao_com_ajustes):
    """Relatório FAI de 07/2026: benefício fruído 261.431,90 → 5.228,64."""
    b = apuracao_com_ajustes.filiais[RB].beneficio
    assert b.percentual_fadefe == 2.0
    assert b.fadefe == pytest.approx(GIA_BENEFICIO["fadefe"], abs=0.01)
    assert b.fadefe_adicional == 0.0


def test_sem_o_ajuste_o_beneficio_para_no_livro(apuracao):
    """O que o Livro Fiscal sozinho alcança, e o que falta para a GIA.

    A diferença de R$ 3.022,85 é o efeito do estorno de créditos da linha 003
    do Registro — R$ 3.865,30 a menos de crédito industrial. É a distância
    entre motor e declaração enquanto o ajuste não for declarado; com ele, os
    dois fecham (ver `test_ajustes.py`).
    """
    b = apuracao.filiais[RB].beneficio
    assert b.credito_da_parcela_incentivada == pytest.approx(81_847.78, abs=0.01)
    assert b.credito_presumido == pytest.approx(258_409.05, abs=0.01)
    assert GIA_BENEFICIO["presumido"] - b.credito_presumido == pytest.approx(
        3_022.85, abs=0.01
    )


def test_a_revenda_nao_entra_no_beneficio(apuracao_com_ajustes):
    """Cláusula quarta expirada em 31/12/2022: revenda ficou fora da base.

    O débito comercial de R$ 93.717,23 não recebe crédito presumido nenhum.
    """
    filial = apuracao_com_ajustes.filiais[RB]
    assert filial.beneficio.debito_beneficiado == pytest.approx(412_274.17, abs=CENTAVO)
    assert filial.atividade(ativ.COMERCIAL).debito == pytest.approx(93_717.23, abs=CENTAVO)


def test_os_percentuais_sao_os_da_clausula_terceira(apuracao_com_ajustes):
    """Se a cláusula quarta valesse, haveria 50% em algum lugar. Não há."""
    b = apuracao_com_ajustes.filiais[RB].beneficio
    assert {b.intra.percentual, b.inter.percentual} == {67.0, 80.0}


def test_so_rio_brilhante_tem_beneficio(apuracao):
    com_beneficio = [f.estabelecimento for f in apuracao.filiais.values() if f.beneficio]
    assert com_beneficio == [RB]


def test_o_beneficio_nao_supera_o_saldo_devedor_que_o_gerou(apuracao_com_ajustes):
    assert apuracao_com_ajustes.filiais[RB].beneficio.confere


# --------------------------------------------------------------------------
# Centralização
# --------------------------------------------------------------------------

def test_o_saldo_de_corumba_e_o_que_rio_brilhante_recebe_do_centralizador(apuracao):
    """A centralização de MS aparece nos dois lados, e os dois batem.

    O Registro de Apuração de Rio Brilhante traz, em Outros Débitos,
    R$ 99.412,10 de "Recebimento de saldo devedor - estabelecimento
    centralizador". Esse é exatamente o saldo devedor que Corumbá apura.

    O saldo vem na convenção de caixa — devedor é negativo —, e o que entra no
    livro da centralizadora é o débito, positivo.
    """
    corumba = apuracao.filiais["HINOVE (CORUMBÁ- MS)"]
    assert corumba.saldo == pytest.approx(-99_412.10, abs=CENTAVO)
    assert corumba.a_recolher == pytest.approx(99_412.10, abs=CENTAVO)
    assert corumba.credor == 0.0


def _grupo(apuracao, uf):
    return next(c for c in apuracao.centralizacao if c.uf == uf)


def test_sp_centraliza_em_guara(apuracao):
    assert _grupo(apuracao, "SP").centralizadora == "HINOVE (FILIAL GUARÁ)"


def test_ms_centraliza_em_rio_brilhante(apuracao):
    """Corumbá transfere o saldo devedor; Rio Brilhante o recebe na linha 002."""
    grupo = _grupo(apuracao, "MS")
    assert grupo.centralizadora == "HINOVE (RIO BRILHANTE)"
    assert grupo.total_recebido == pytest.approx(-99_412.10, abs=CENTAVO)
    assert apuracao.debito_por_centralizacao(RB) == pytest.approx(
        99_412.10, abs=CENTAVO
    )


def test_registro_transfere_o_saldo_devedor_para_guara(apuracao):
    """Identidade da camada, sobre os saldos reais da competência."""
    grupo = _grupo(apuracao, "SP")
    registro = next(t for t in grupo.transferencias if t.origem == "HINOVE (REGISTRO)")
    assert registro.saldo_individual == pytest.approx(-299_450.70, abs=CENTAVO)
    assert registro.saldo_individual == pytest.approx(
        registro.valor_transferido + registro.saldo_residual, abs=CENTAVO
    )
    assert grupo.confere


def test_a_transferencia_e_instrucao_e_nao_bloqueia_o_encerramento(apuracao):
    """A nota de transferência é emitida depois que a competência fecha.

    O documento nasce do resultado da apuração e vai escriturado no mês
    seguinte — cobrá-lo dentro do livro apurado seria pedir que o efeito
    precedesse a causa. O que a ferramenta entrega é a instrução do que emitir.
    """
    grupo = _grupo(apuracao, "SP")
    assert grupo.instrucoes
    assert any("HINOVE (REGISTRO)" in i for i in grupo.instrucoes)
    assert all("NF-e" in i for i in grupo.instrucoes)


def test_o_saldo_traz_o_credor_como_positivo(apuracao):
    """Guará fecha credor e Registro fecha devedor — os sinais dizem qual é qual.

    Saldo credor é crédito que se transporta; saldo devedor sai do caixa. É a
    leitura de quem fecha a competência, não a da conta gráfica.
    """
    guara = apuracao.filiais["HINOVE (FILIAL GUARÁ)"]
    # Julho abre zerado: o Registro de 06/2026 fecha a linha 014 em 0,00.
    assert guara.saldo_credor_anterior == 0.0
    assert guara.saldo == pytest.approx(2_103_633.39, abs=CENTAVO)
    assert guara.credor == pytest.approx(2_103_633.39, abs=CENTAVO)
    assert guara.a_recolher == 0.0

    registro = apuracao.filiais["HINOVE (REGISTRO)"]
    assert registro.saldo == pytest.approx(-299_450.70, abs=CENTAVO)
    assert registro.a_recolher == pytest.approx(299_450.70, abs=CENTAVO)


def test_o_saldo_do_total_e_a_soma_dos_saldos_das_filiais(apuracao):
    """O benefício fiscal não pode sumir na linha de total."""
    soma = sum(f.saldo for f in apuracao.filiais.values())
    assert apuracao.total.saldo == pytest.approx(soma, abs=CENTAVO)
    assert apuracao.total.credito_presumido == pytest.approx(
        apuracao.credito_presumido, abs=CENTAVO
    )
