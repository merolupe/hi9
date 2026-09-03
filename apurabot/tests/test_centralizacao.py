"""Centralização e transferência de saldo entre estabelecimentos."""
from __future__ import annotations

import copy

import pytest

from apurabot.nucleo.centralizacao import (
    AJUSTE_DE_APURACAO,
    CentralizacaoDesconhecida,
    SALDO_CREDOR,
    SALDO_DEVEDOR,
    SALDO_INTEGRAL,
    calcular,
    debito_recebido_por,
)

# Os saldos chegam à centralização na convenção de caixa da apuração:
# POSITIVO É CREDOR, NEGATIVO É DEVEDOR.
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
    r = grupo_de({GUARA: 100_000.00, REGISTRO: -287_113.66}, parametros)
    t = r.transferencias[0]
    assert t.saldo_individual == pytest.approx(
        t.valor_transferido + t.saldo_residual, abs=CENTAVO
    )
    assert r.confere


def test_a_centralizadora_recebe_a_soma_do_que_os_demais_transferem(parametros):
    r = grupo_de(
        {GUARA: 100_000.00, REGISTRO: -50_000.00, MATRIZ: -20_000.00}, parametros
    )
    assert r.total_recebido == pytest.approx(-70_000.00, abs=CENTAVO)
    assert r.saldo_final == pytest.approx(30_000.00, abs=CENTAVO)


def test_a_centralizadora_nao_transfere_para_si_mesma(parametros):
    r = grupo_de({GUARA: -500_000.00, REGISTRO: -10_000.00}, parametros)
    assert [t.origem for t in r.transferencias] == [REGISTRO]
    assert r.saldo_proprio == pytest.approx(-500_000.00, abs=CENTAVO)


def test_estabelecimento_sem_movimento_fica_de_fora(parametros):
    """Quem não apurou nada não gera transferência de zero."""
    r = grupo_de({GUARA: 100.00, REGISTRO: -10_000.00}, parametros)
    assert MATRIZ not in [t.origem for t in r.transferencias]


# -- o que se transfere ----------------------------------------------------

def test_saldo_integral_transfere_devedor_e_credor(parametros):
    """A centralizadora devendo 4.000, o crédito de 4.000 cabe inteiro."""
    p = com_regra(parametros, transfere=SALDO_INTEGRAL)
    r = grupo_de({GUARA: -4_000.00, REGISTRO: -10_000.00, MATRIZ: 4_000.00}, p)
    por_origem = {t.origem: t.valor_transferido for t in r.transferencias}
    assert por_origem[REGISTRO] == pytest.approx(-10_000.00, abs=CENTAVO)
    assert por_origem[MATRIZ] == pytest.approx(4_000.00, abs=CENTAVO)


# -- o teto: o crédito para no saldo devedor de quem recebe ----------------

def test_o_credito_para_no_saldo_devedor_da_centralizadora(parametros):
    """A transferência existe para compensar. O que passa disso fica onde está.

    É o que o Registro de Apuração mostra na competência observada: a
    centralizadora recebeu exatamente o crédito de que precisava para zerar, e
    o mês fechou com as linhas 011 e 014 em zero.
    """
    p = com_regra(parametros, transfere=SALDO_INTEGRAL)
    r = grupo_de({GUARA: -100_000.00, REGISTRO: 250_000.00}, p)
    t_ = next(t for t in r.transferencias if t.origem == REGISTRO)
    assert t_.valor_transferido == pytest.approx(100_000.00, abs=CENTAVO)
    assert t_.retido_pelo_teto == pytest.approx(150_000.00, abs=CENTAVO)
    assert t_.saldo_residual == pytest.approx(150_000.00, abs=CENTAVO)
    assert r.saldo_final == 0.0
    assert "fica onde está" in t_.instrucao


def test_o_teto_e_do_grupo_e_nao_de_cada_estabelecimento(parametros):
    """Com dois credores e uma dívida só, o teto se esgota entre os dois."""
    p = com_regra(parametros, transfere=SALDO_INTEGRAL)
    r = grupo_de({GUARA: -100_000.00, REGISTRO: 250_000.00, MATRIZ: 40_000.00}, p)
    assert r.total_recebido == pytest.approx(100_000.00, abs=CENTAVO)
    assert r.saldo_final == 0.0
    assert sum(t.retido_pelo_teto for t in r.transferencias) == pytest.approx(
        190_000.00, abs=CENTAVO
    )


def test_sem_saldo_devedor_na_centralizadora_o_credito_nao_se_move(parametros):
    p = com_regra(parametros, transfere=SALDO_INTEGRAL)
    r = grupo_de({GUARA: 2_000_000.00, REGISTRO: 250_000.00}, p)
    t_ = next(t for t in r.transferencias if t.origem == REGISTRO)
    assert t_.valor_transferido == 0.0
    assert t_.retido_pelo_teto == pytest.approx(250_000.00, abs=CENTAVO)
    assert "não fechou com saldo devedor a compensar" in t_.instrucao


def test_o_saldo_devedor_nao_tem_teto(parametros):
    """A centralizadora assume a dívida do grupo mesmo estando credora.

    É o caso de agosto: Guará credor recebe o saldo devedor de Registro, e o
    crédito dele absorve a dívida — o grupo recolhe menos por causa disso.
    """
    p = com_regra(parametros, transfere=SALDO_INTEGRAL)
    r = grupo_de({GUARA: 2_000_000.00, REGISTRO: -201_505.74}, p)
    t_ = next(t for t in r.transferencias if t.origem == REGISTRO)
    assert t_.valor_transferido == pytest.approx(-201_505.74, abs=CENTAVO)
    assert t_.retido_pelo_teto == 0.0
    assert r.saldo_final == pytest.approx(1_798_494.26, abs=CENTAVO)


def test_saldo_devedor_deixa_o_credor_no_estabelecimento(parametros):
    """Devedor é negativo: quem tem crédito não transfere nada."""
    p = com_regra(parametros, transfere=SALDO_DEVEDOR)
    r = grupo_de({GUARA: 0.0, REGISTRO: -10_000.00, MATRIZ: 4_000.00}, p)
    por_origem = {t.origem: t for t in r.transferencias}
    assert por_origem[REGISTRO].valor_transferido == pytest.approx(
        -10_000.00, abs=CENTAVO
    )
    assert por_origem[MATRIZ].valor_transferido == 0.0
    assert por_origem[MATRIZ].saldo_residual == pytest.approx(4_000.00, abs=CENTAVO)


def test_saldo_credor_deixa_o_devedor_no_estabelecimento(parametros):
    p = com_regra(parametros, transfere=SALDO_CREDOR)
    r = grupo_de({GUARA: -4_000.00, REGISTRO: -10_000.00, MATRIZ: 4_000.00}, p)
    por_origem = {t.origem: t for t in r.transferencias}
    assert por_origem[REGISTRO].valor_transferido == 0.0
    assert por_origem[MATRIZ].valor_transferido == pytest.approx(4_000.00, abs=CENTAVO)


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
    r = grupo_de({GUARA: 100.00, REGISTRO: -287_113.66}, parametros)
    assert not hasattr(r, "pendencias")
    assert len(r.instrucoes) == 1
    assert "287.113,66" in r.instrucoes[0]   # milhar e decimal como no Brasil
    assert "devedor" in r.instrucoes[0]      # o sinal negativo vira a palavra
    assert REGISTRO in r.instrucoes[0] and GUARA in r.instrucoes[0]


def test_sem_saldo_a_transferir_nao_ha_instrucao(parametros):
    p = com_regra(parametros, transfere=SALDO_DEVEDOR)
    r = grupo_de({GUARA: 100.00, REGISTRO: 50_000.00}, p)   # os dois credores
    assert r.instrucoes == []


def test_sp_fecha_por_lancamento_e_a_nfe_vem_depois(parametros):
    """As duas coisas, e nessa ordem.

    O Registro de Apuração mostra a transferência chegando como lançamento —
    linha 002 ou 006, com a mesma redação que MS usa. A NF-e continua sendo
    emitida, só que **depois** do fechamento: ela nasce do resultado da
    apuração e não retroage, então vai escriturada na competência seguinte.
    """
    r = grupo_de({GUARA: 0.0, REGISTRO: -1_000.00}, parametros)
    assert r.mecanismo == AJUSTE_DE_APURACAO
    instrucao = r.instrucoes[0]
    assert "lançamento de ajuste no Registro de Apuração" in instrucao
    assert "NF-e" in instrucao and "5601" in instrucao
    assert "escriturada na competência seguinte" in instrucao


def test_a_regra_de_sp_esta_homologada(parametros):
    r = grupo_de({GUARA: 0.0}, parametros)
    assert r.homologado is True
    assert "NÃO HOMOLOGADA" not in " ".join(r.memoria)


# -- MS: a transferência é lançamento, não documento ------------------------

def test_ms_centraliza_em_rio_brilhante_por_ajuste_de_apuracao(parametros):
    r = grupo_de(
        {RIO_BRILHANTE: -108_915.42, CORUMBA: -99_412.10}, parametros, uf="MS"
    )
    assert r.centralizadora == RIO_BRILHANTE
    assert r.mecanismo == AJUSTE_DE_APURACAO
    assert [t.origem for t in r.transferencias] == [CORUMBA]
    assert r.total_recebido == pytest.approx(-99_412.10, abs=CENTAVO)
    assert r.saldo_final == pytest.approx(-208_327.52, abs=CENTAVO)


def test_a_instrucao_de_ms_nao_pede_nfe(parametros):
    r = grupo_de({RIO_BRILHANTE: 0.0, CORUMBA: -99_412.10}, parametros, uf="MS")
    assert "NF-e" not in r.instrucoes[0]
    assert "Registro de Apuração" in r.instrucoes[0]


def test_as_duas_ufs_alimentam_a_linha_002_por_lancamento(parametros):
    """SP e MS recebem o saldo devedor do centralizado do mesmo jeito.

    Era só MS enquanto SP estava desenhada como NF-e. O Registro de Apuração de
    Guará mostra "recebimento de saldo devedor — estabelecimento centralizador"
    na linha 002, exatamente como o de Rio Brilhante.
    """
    resultados = calcular(
        {GUARA: 100.00, REGISTRO: -10_000.00,
         RIO_BRILHANTE: 0.0, CORUMBA: -99_412.10},
        parametros,
    )
    # Positivo: o livro registra débito em positivo, e é aqui que a convenção
    # de caixa da apuração é trocada pela da conta gráfica.
    assert debito_recebido_por(resultados, RIO_BRILHANTE) == pytest.approx(
        99_412.10, abs=CENTAVO
    )
    assert debito_recebido_por(resultados, GUARA) == pytest.approx(
        10_000.00, abs=CENTAVO
    )


def test_a_convencao_de_sinal_e_a_do_caixa(parametros):
    """Saldo credor é dinheiro a favor; devedor sai do caixa.

    A conta gráfica trata o débito como positivo. Aqui o sinal é o do efeito
    financeiro, porque é assim que quem fecha a competência lê o resultado.
    """
    r = grupo_de({GUARA: 0.0, REGISTRO: -287_113.66, MATRIZ: 40_000.00}, parametros)
    por_origem = {t.origem: t for t in r.transferencias}
    assert por_origem[REGISTRO].saldo_individual < 0, "devedor é negativo"
    assert por_origem[MATRIZ].saldo_individual > 0, "credor é positivo"
    assert "devedor" in por_origem[REGISTRO].instrucao
    assert "credor" in por_origem[MATRIZ].instrucao


# -- as duas pontas do lançamento -------------------------------------------

def test_quem_transfere_tambem_lanca(base_julho, parametros):
    """A transferência aparece nos DOIS Registros, em linhas opostas.

    Antes só a centralizadora lançava. O centralizado fechava devendo o mesmo
    valor que ela já tinha assumido, e quem lesse os dois documentos via o
    grupo pagando duas vezes — foi o que o Registro de Corumbá de 08/2026
    mostrou.

    O Registro de 07/2026 de Corumbá, emitido pelo ERP, traz a linha que
    faltava: 006 = 99.412,10, "Transferência de saldo devedor para
    estabelecimento centralizador", e fecha em 013 = 0,00.
    """
    from apurabot.apuracao import apurar
    from apurabot.nucleo import registro as reg

    apuracao = apurar(base_julho, parametros)
    registros = {r.estabelecimento: r for r in reg.montar(apuracao, parametros)}

    corumba = registros["HINOVE (CORUMBÁ- MS)"]
    rb = registros["HINOVE (RIO BRILHANTE)"]
    transferido = -apuracao.filiais["HINOVE (CORUMBÁ- MS)"].saldo

    # Quem transfere: linha 006, e o documento fecha zerado.
    assert corumba.linha(6).valor == pytest.approx(transferido, abs=0.005)
    assert corumba.linha(13).valor == pytest.approx(0.0, abs=0.005)
    assert any(
        "Transferência de saldo devedor" in descricao
        for descricao, _ in corumba.linha(6).discriminacao
    ), corumba.linha(6).discriminacao

    # Quem recebe: linha 002, com o mesmo valor.
    assert rb.linha(2).valor >= transferido - 0.005
    assert any(
        "Recebimento de saldo devedor" in descricao
        for descricao, _ in rb.linha(2).discriminacao
    ), rb.linha(2).discriminacao


def test_o_grupo_deve_uma_vez_so(base_julho, parametros):
    """Somando os 013 de um grupo, o total é o do grupo — não o dobro."""
    from apurabot.apuracao import apurar
    from apurabot.nucleo import registro as reg

    apuracao = apurar(base_julho, parametros)
    registros = {r.estabelecimento: r for r in reg.montar(apuracao, parametros)}
    for resultado in apuracao.centralizacao:
        nomes = [resultado.centralizadora] + [
            t.origem for t in resultado.transferencias
        ]
        soma = sum(registros[n].linha(13).valor for n in nomes if n in registros)
        assert soma == pytest.approx(
            max(-resultado.saldo_final, 0.0), abs=0.01
        ), resultado.uf
