"""Centralização e transferência de saldo entre estabelecimentos."""
from __future__ import annotations

import copy

import pytest

from apurabot.nucleo.centralizacao import (
    CentralizacaoDesconhecida,
    SALDO_CREDOR,
    SALDO_DEVEDOR,
    SALDO_INTEGRAL,
    calcular,
)

CENTAVO = 0.005
GUARA = "HINOVE (FILIAL GUARÁ)"
REGISTRO = "HINOVE (REGISTRO)"
MATRIZ = "HINOVE (MATRIZ)"


def com_regra(parametros, **campos):
    p = copy.deepcopy(parametros)
    p.filiais["regras_de_centralizacao"]["sp"].update(campos)
    return p


def um_grupo(saldos, parametros, livro=None):
    resultados = calcular(saldos, livro, parametros)
    assert len(resultados) == 1, "SP é o único grupo de centralização cadastrado"
    return resultados[0]


# -- a identidade da camada ------------------------------------------------

def test_o_saldo_individual_se_reparte_em_transferido_e_residual(parametros):
    r = um_grupo({GUARA: -100_000.00, REGISTRO: 287_113.66}, parametros)
    t = r.transferencias[0]
    assert t.saldo_individual == pytest.approx(
        t.valor_transferido + t.saldo_residual, abs=CENTAVO
    )
    assert r.confere


def test_a_centralizadora_recebe_a_soma_do_que_os_demais_transferem(parametros):
    r = um_grupo({GUARA: -100_000.00, REGISTRO: 50_000.00, MATRIZ: 20_000.00}, parametros)
    assert r.total_recebido == pytest.approx(70_000.00, abs=CENTAVO)
    assert r.saldo_final == pytest.approx(-30_000.00, abs=CENTAVO)


def test_a_centralizadora_nao_transfere_para_si_mesma(parametros):
    r = um_grupo({GUARA: 500_000.00, REGISTRO: 10_000.00}, parametros)
    assert [t.origem for t in r.transferencias] == [REGISTRO]
    assert r.saldo_proprio == pytest.approx(500_000.00, abs=CENTAVO)


def test_estabelecimento_sem_movimento_fica_de_fora(parametros):
    """Quem não apurou nada não gera transferência de zero."""
    r = um_grupo({GUARA: -100.00, REGISTRO: 10_000.00}, parametros)
    assert MATRIZ not in [t.origem for t in r.transferencias]


# -- o que se transfere ----------------------------------------------------

def test_saldo_integral_transfere_devedor_e_credor(parametros):
    p = com_regra(parametros, transfere=SALDO_INTEGRAL)
    r = um_grupo({GUARA: 0.0, REGISTRO: 10_000.00, MATRIZ: -4_000.00}, p)
    por_origem = {t.origem: t.valor_transferido for t in r.transferencias}
    assert por_origem[REGISTRO] == pytest.approx(10_000.00, abs=CENTAVO)
    assert por_origem[MATRIZ] == pytest.approx(-4_000.00, abs=CENTAVO)


def test_saldo_devedor_deixa_o_credor_no_estabelecimento(parametros):
    p = com_regra(parametros, transfere=SALDO_DEVEDOR)
    r = um_grupo({GUARA: 0.0, REGISTRO: 10_000.00, MATRIZ: -4_000.00}, p)
    por_origem = {t.origem: t for t in r.transferencias}
    assert por_origem[REGISTRO].valor_transferido == pytest.approx(10_000.00, abs=CENTAVO)
    assert por_origem[MATRIZ].valor_transferido == 0.0
    assert por_origem[MATRIZ].saldo_residual == pytest.approx(-4_000.00, abs=CENTAVO)


def test_saldo_credor_deixa_o_devedor_no_estabelecimento(parametros):
    p = com_regra(parametros, transfere=SALDO_CREDOR)
    r = um_grupo({GUARA: 0.0, REGISTRO: 10_000.00, MATRIZ: -4_000.00}, p)
    por_origem = {t.origem: t for t in r.transferencias}
    assert por_origem[REGISTRO].valor_transferido == 0.0
    assert por_origem[MATRIZ].valor_transferido == pytest.approx(-4_000.00, abs=CENTAVO)


def test_regra_de_transferencia_desconhecida_falha(parametros):
    p = com_regra(parametros, transfere="xyz")
    with pytest.raises(CentralizacaoDesconhecida, match="não é reconhecido"):
        calcular({GUARA: 0.0}, None, p)


# -- as travas da NF-e -----------------------------------------------------

def test_transferencia_sem_nfe_bloqueia_o_encerramento(parametros):
    r = um_grupo({GUARA: -100.00, REGISTRO: 287_113.66}, parametros)
    assert r.pendencias
    assert "sem NF-e escriturada" in r.pendencias[0]


def test_sem_saldo_a_transferir_nao_se_cobra_nfe(parametros):
    p = com_regra(parametros, transfere=SALDO_DEVEDOR)
    r = um_grupo({GUARA: -100.00, REGISTRO: -50_000.00}, p)
    assert r.pendencias == []


def test_a_regra_de_sp_ainda_nao_esta_homologada(parametros):
    """Enquanto o fiscal não confirmar, o relatório diz que a regra é rascunho."""
    r = um_grupo({GUARA: 0.0}, parametros)
    assert r.homologado is False
    assert "NÃO HOMOLOGADA" in " ".join(r.memoria)
