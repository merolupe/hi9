"""Centralização e transferência de saldo entre estabelecimentos."""
from __future__ import annotations

import copy

import pytest

from apurabot.nucleo.centralizacao import (
    AJUSTE_DE_APURACAO,
    CentralizacaoDesconhecida,
    NFE,
    SALDO_CREDOR,
    SALDO_DEVEDOR,
    SALDO_INTEGRAL,
    calcular,
    recebido_por,
)

CENTAVO = 0.005
GUARA = "HINOVE (FILIAL GUARÁ)"
REGISTRO = "HINOVE (REGISTRO)"
MATRIZ = "HINOVE (MATRIZ)"
RIO_BRILHANTE = "HINOVE (RIO BRILHANTE)"
CORUMBA = "HINOVE (CORUMBÁ- MS)"


def com_regra(parametros, grupo="sp", **campos):
    p = copy.deepcopy(parametros)
    p.filiais["regras_de_centralizacao"][grupo].update(campos)
    return p


def grupo_de(saldos, parametros, uf="SP"):
    achados = [r for r in calcular(saldos, parametros) if r.uf == uf]
    assert len(achados) == 1, f"{uf} deveria ter exatamente um grupo de centralização"
    return achados[0]


# -- a identidade da camada ------------------------------------------------

def test_o_saldo_individual_se_reparte_em_transferido_e_residual(parametros):
    r = grupo_de({GUARA: -100_000.00, REGISTRO: 287_113.66}, parametros)
    t = r.transferencias[0]
    assert t.saldo_individual == pytest.approx(
        t.valor_transferido + t.saldo_residual, abs=CENTAVO
    )
    assert r.confere


def test_a_centralizadora_recebe_a_soma_do_que_os_demais_transferem(parametros):
    r = grupo_de(
        {GUARA: -100_000.00, REGISTRO: 50_000.00, MATRIZ: 20_000.00}, parametros
    )
    assert r.total_recebido == pytest.approx(70_000.00, abs=CENTAVO)
    assert r.saldo_final == pytest.approx(-30_000.00, abs=CENTAVO)


def test_a_centralizadora_nao_transfere_para_si_mesma(parametros):
    r = grupo_de({GUARA: 500_000.00, REGISTRO: 10_000.00}, parametros)
    assert [t.origem for t in r.transferencias] == [REGISTRO]
    assert r.saldo_proprio == pytest.approx(500_000.00, abs=CENTAVO)


def test_estabelecimento_sem_movimento_fica_de_fora(parametros):
    """Quem não apurou nada não gera transferência de zero."""
    r = grupo_de({GUARA: -100.00, REGISTRO: 10_000.00}, parametros)
    assert MATRIZ not in [t.origem for t in r.transferencias]


# -- o que se transfere ----------------------------------------------------

def test_saldo_integral_transfere_devedor_e_credor(parametros):
    p = com_regra(parametros, transfere=SALDO_INTEGRAL)
    r = grupo_de({GUARA: 0.0, REGISTRO: 10_000.00, MATRIZ: -4_000.00}, p)
    por_origem = {t.origem: t.valor_transferido for t in r.transferencias}
    assert por_origem[REGISTRO] == pytest.approx(10_000.00, abs=CENTAVO)
    assert por_origem[MATRIZ] == pytest.approx(-4_000.00, abs=CENTAVO)


def test_saldo_devedor_deixa_o_credor_no_estabelecimento(parametros):
    p = com_regra(parametros, transfere=SALDO_DEVEDOR)
    r = grupo_de({GUARA: 0.0, REGISTRO: 10_000.00, MATRIZ: -4_000.00}, p)
    por_origem = {t.origem: t for t in r.transferencias}
    assert por_origem[REGISTRO].valor_transferido == pytest.approx(10_000.00, abs=CENTAVO)
    assert por_origem[MATRIZ].valor_transferido == 0.0
    assert por_origem[MATRIZ].saldo_residual == pytest.approx(-4_000.00, abs=CENTAVO)


def test_saldo_credor_deixa_o_devedor_no_estabelecimento(parametros):
    p = com_regra(parametros, transfere=SALDO_CREDOR)
    r = grupo_de({GUARA: 0.0, REGISTRO: 10_000.00, MATRIZ: -4_000.00}, p)
    por_origem = {t.origem: t for t in r.transferencias}
    assert por_origem[REGISTRO].valor_transferido == 0.0
    assert por_origem[MATRIZ].valor_transferido == pytest.approx(-4_000.00, abs=CENTAVO)


def test_regra_de_transferencia_desconhecida_falha(parametros):
    p = com_regra(parametros, transfere="xyz")
    with pytest.raises(CentralizacaoDesconhecida, match="não é reconhecido"):
        calcular({GUARA: 0.0}, p)


def test_mecanismo_desconhecido_falha(parametros):
    p = com_regra(parametros, mecanismo="pombo-correio")
    with pytest.raises(CentralizacaoDesconhecida, match="mecanismo"):
        calcular({GUARA: 0.0}, p)


# -- a instrução, no lugar da cobrança de documento ------------------------

def test_a_transferencia_vira_instrucao_e_nao_pendencia(parametros):
    """A nota nasce da apuração: cobrá-la dentro da competência é circular.

    O que a camada devolve é o que precisa ser emitido depois do encerramento.
    """
    r = grupo_de({GUARA: -100.00, REGISTRO: 287_113.66}, parametros)
    assert not hasattr(r, "pendencias")
    assert len(r.instrucoes) == 1
    assert "287,113.66" in r.instrucoes[0]
    assert REGISTRO in r.instrucoes[0] and GUARA in r.instrucoes[0]


def test_sem_saldo_a_transferir_nao_ha_instrucao(parametros):
    p = com_regra(parametros, transfere=SALDO_DEVEDOR)
    r = grupo_de({GUARA: -100.00, REGISTRO: -50_000.00}, p)
    assert r.instrucoes == []


def test_a_instrucao_de_sp_pede_nfe_com_o_cfop_parametrizado(parametros):
    r = grupo_de({GUARA: 0.0, REGISTRO: 1_000.00}, parametros)
    assert r.mecanismo == NFE
    assert "NF-e" in r.instrucoes[0]
    assert "5601" in r.instrucoes[0]


def test_a_regra_de_sp_ainda_nao_esta_homologada(parametros):
    """Enquanto o fiscal não confirmar, o relatório diz que a regra é rascunho."""
    r = grupo_de({GUARA: 0.0}, parametros)
    assert r.homologado is False
    assert "NÃO HOMOLOGADA" in " ".join(r.memoria)


# -- MS: a transferência é lançamento, não documento ------------------------

def test_ms_centraliza_em_rio_brilhante_por_ajuste_de_apuracao(parametros):
    r = grupo_de({RIO_BRILHANTE: 108_915.42, CORUMBA: 99_412.10}, parametros, uf="MS")
    assert r.centralizadora == RIO_BRILHANTE
    assert r.mecanismo == AJUSTE_DE_APURACAO
    assert [t.origem for t in r.transferencias] == [CORUMBA]
    assert r.total_recebido == pytest.approx(99_412.10, abs=CENTAVO)


def test_a_instrucao_de_ms_nao_pede_nfe(parametros):
    r = grupo_de({RIO_BRILHANTE: 0.0, CORUMBA: 99_412.10}, parametros, uf="MS")
    assert "NF-e" not in r.instrucoes[0]
    assert "Registro de Apuração" in r.instrucoes[0]


def test_so_o_ajuste_de_apuracao_alimenta_a_linha_002(parametros):
    """A linha 002 do registro é o recebimento por lançamento, não por NF-e.

    Onde a transferência tem documento próprio, ela não vira ajuste na conta
    gráfica da centralizadora — entra pela escrituração da nota.
    """
    resultados = calcular(
        {GUARA: -100.00, REGISTRO: 10_000.00,
         RIO_BRILHANTE: 0.0, CORUMBA: 99_412.10},
        parametros,
    )
    assert recebido_por(resultados, RIO_BRILHANTE) == pytest.approx(
        99_412.10, abs=CENTAVO
    )
    assert recebido_por(resultados, GUARA) == 0.0
