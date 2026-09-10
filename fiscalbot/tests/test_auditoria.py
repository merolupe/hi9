"""As camadas do motor, e a ordem em que elas mandam."""
from __future__ import annotations

from conftest import base_com, registro, regra

from fiscalbot.auditoria import (ADVERTENCIA, CONFORME, VALIDACAO_MANUAL,
                                 auditar_linha)


# -- precedência -----------------------------------------------------------

def test_nota_cancelada_nao_se_audita(mapa):
    """Precedência máxima: nem a regra, nem a Camada 0 falam sobre ela."""
    base = base_com(regra("T01", esp_cst="99"))     # CST que jamais casaria
    achado = auditar_linha(registro(origem="Cancelada"), mapa, base)
    assert achado.status == CONFORME
    assert achado.operacao == "Cancelada"
    assert not achado.ocorrencias.alguma


def test_frete_de_parceiro_do_simples_nacional_espera_cst_90(mapa):
    base = base_com(regra("T01", cfop="5101"), simples_nacional=("6428",))
    conforme = auditar_linha(
        registro(esp="CT", parc=6428.0, cst="90-Outras"), mapa, base)
    assert conforme.status == CONFORME
    assert conforme.operacao == "Frete SN (Simples Nacional)"

    divergente = auditar_linha(
        registro(esp="CT", parc=6428.0, cst="00-Tributada"), mapa, base)
    assert divergente.status == ADVERTENCIA
    assert divergente.ocorrencias.cst


def test_a_camada_do_simples_nacional_vale_so_para_frete(mapa):
    """O parceiro pode vender mercadoria também; aí a regra normal manda."""
    base = base_com(regra("T01", cfop="5101", esp_cst="00"),
                    simples_nacional=("6428",))
    achado = auditar_linha(registro(esp="NF", parc=6428.0), mapa, base)
    assert achado.operacao == "Operacao de teste"


def test_compra_de_cavaco_tem_enquadramento_proprio(mapa):
    base = base_com(regra("T01", cfop="1101"), cavaco=("4350",))
    intra = auditar_linha(
        registro(cfop=1101.0, parc=4350.0, cst="51-Diferimento", icms=0.0,
                 es="Entrada"), mapa, base)
    assert intra.status == CONFORME
    assert intra.operacao == "Compra MP Cavaco"

    inter = auditar_linha(
        registro(cfop=2101.0, parc=4350.0, cst="00-Tributada", aliq=12.0,
                 ufd="MG", es="Entrada"), mapa, base)
    assert inter.status == CONFORME

    errado = auditar_linha(
        registro(cfop=2101.0, parc=4350.0, cst="00-Tributada", aliq=18.0,
                 ufd="MG", es="Entrada"), mapa, base)
    assert errado.status == ADVERTENCIA
    assert errado.ocorrencias.aliquota


# -- casamento MECE --------------------------------------------------------

def test_nota_sem_regra_vai_para_validacao_manual_com_o_cfop_no_nome(mapa):
    achado = auditar_linha(registro(), mapa, base_com(regra("T01", cfop="9999")))
    assert achado.status == VALIDACAO_MANUAL
    assert achado.operacao == "5101 - Venda"


def test_frete_sem_regra_vira_advertencia_em_vez_de_manual(mapa):
    """Frete não mapeado é problema de cadastro, e aparece como advertência."""
    base = base_com(regra("T01", cfop="9999"))
    intra = auditar_linha(registro(esp="CT"), mapa, base)
    assert intra.status == ADVERTENCIA
    assert intra.operacao == "Frete nao mapeado"
    assert intra.auditoria == "Circulacao nao mapeada"

    inter = auditar_linha(registro(esp="CT", ufd="MG"), mapa, base)
    assert inter.auditoria == "Operacao de frete nao mapeada"


def test_duas_regras_casando_acusam_a_base_e_nao_o_documento(mapa):
    base = base_com(regra("T01", cfop="5101", esp_cst="00"),
                    regra("T02", cfop="5101", esp_cst="20"))
    achado = auditar_linha(registro(), mapa, base)
    assert achado.status == ADVERTENCIA
    assert "AMBIGUA" in achado.operacao


def test_todo_cfop_preenchido_e_conferido(mapa):
    """O VBA parava no primeiro vazio e perdia o resto da lista. Corrigido."""
    base = base_com(regra("T01", cfop=("1602", "", "5101")))
    achado = auditar_linha(registro(cfop=5101.0), mapa, base)
    assert achado.operacao == "Operacao de teste", (
        "o CFOP depois da posição vazia tem que valer"
    )


def test_regra_inativa_nao_casa(mapa):
    base = base_com(regra("T01", cfop="5101", ativa=False))
    assert auditar_linha(registro(), mapa, base).status == VALIDACAO_MANUAL


# -- Camada 0 --------------------------------------------------------------

def test_camada_zero_cobre_registro_sem_regra_nenhuma(mapa):
    """Sem regra, a coerência entre CST e ICMS ainda é conferida."""
    base = base_com(regra("T01", cfop="9999"))
    achado = auditar_linha(registro(cst="00-Tributada", icms=0.0), mapa, base)
    assert achado.status == VALIDACAO_MANUAL
    assert achado.ocorrencias.icms, "CST 00 sem ICMS tinha que acusar"


def test_camada_zero_nao_conta_a_mesma_divergencia_duas_vezes(mapa):
    """Onde a regra já se pronunciou sobre o ICMS, a Camada 0 se cala."""
    base = base_com(regra("T01", cfop="5101", esp_icms="0"))
    achado = auditar_linha(registro(cst="00-Tributada", icms=5.0), mapa, base)
    assert achado.ocorrencias.icms.count("Advertencia") == 1


def test_cfop_de_entrada_em_operacao_interestadual_acusa(mapa):
    """Regra B: o primeiro dígito do CFOP tem que combinar com INTRA/INTER."""
    base = base_com(regra("T01", cfop="5101"))
    achado = auditar_linha(registro(ufd="MG"), mapa, base)
    assert achado.ocorrencias.outros


# -- as seis dimensões -----------------------------------------------------

def test_carga_efetiva_dentro_e_fora_da_tolerancia(mapa):
    base = base_com(regra("T01", cfop="5101", esp_carga="4", esp_icms="CARGA"))
    dentro = auditar_linha(registro(icms=4.02, vcont=100.0, cst="20-Reducao"),
                           mapa, base)
    assert not dentro.ocorrencias.carga
    fora = auditar_linha(registro(icms=4.5, vcont=100.0, cst="20-Reducao"),
                         mapa, base)
    assert fora.ocorrencias.carga


def test_carga_sem_valor_contabil_acusa_em_vez_de_dividir_por_zero(mapa):
    base = base_com(regra("T01", cfop="5101", esp_carga="4"))
    achado = auditar_linha(registro(vcont=""), mapa, base)
    assert achado.ocorrencias.carga


def test_aliquota_pela_matriz_de_ufs(mapa):
    base = base_com(regra("T01", cfop="6101", esp_aliq="TABELAUF"),
                    aliquotas={"SP": {"MG": 12.0}})
    conforme = auditar_linha(registro(cfop=6101.0, ufd="MG", aliq=12.0), mapa, base)
    assert not conforme.ocorrencias.aliquota
    divergente = auditar_linha(registro(cfop=6101.0, ufd="MG", aliq=7.0), mapa, base)
    assert divergente.ocorrencias.aliquota


def test_par_de_ufs_nao_se_perde_ao_subir_a_caixa(mapa):
    """`PRxSP` em maiúscula vira `PRXSP` e a UF de origem some. Já quebrou."""
    base = base_com(regra("T01", cfop="2907", es="Entrada",
                          cond_par_uf="UFORIG:PR", operacao="Retorno PR"),
                    regra("T02", cfop="2907", es="Entrada",
                          cond_par_uf="NAOUFORIG:PR", operacao="Retorno outros"))
    achado = auditar_linha(
        registro(cfop=2907.0, es="Entrada", ufo="PR", ufd="SP"), mapa, base)
    assert achado.operacao == "Retorno PR"


def test_secst_manda_para_validacao_manual_e_anexa_o_recado(mapa):
    base = base_com(regra("T01", cfop="5101", esp_cst="",
                          esp_outros="SECST:20:Validar operacao real"))
    achado = auditar_linha(registro(cst="20-Reducao", icms=1.0), mapa, base)
    assert achado.status == VALIDACAO_MANUAL
    assert "Validar operacao real" in achado.auditoria

    outro = auditar_linha(registro(cst="00-Tributada", icms=1.0), mapa, base)
    assert outro.status == CONFORME


def test_sempre_vira_advertencia_incondicional(mapa):
    base = base_com(regra("T01", cfop="5101",
                          esp_outros="SEMPRE:Circulacao nao mapeada"))
    achado = auditar_linha(registro(), mapa, base)
    assert achado.status == ADVERTENCIA
    assert achado.ocorrencias.outros == "Circulacao nao mapeada"


def test_produto_de_industrializacao_so_circula_em_cfop_proprio(mapa):
    base = base_com(regra("T01", cfop="5101"),
                    tabelas={"CFOP_IND": ("5101",)})
    achado = auditar_linha(registro(descprod="Ind. Semente tratada"), mapa, base)
    assert "industrializacao" in achado.ocorrencias.produto


def test_a_camada_de_industrializacao_nao_vale_para_frete(mapa):
    base = base_com(regra("T01", cfop="5101", especie="CT"),
                    tabelas={"CFOP_IND": ("5101",)})
    achado = auditar_linha(
        registro(esp="CT", descprod="Ind. Semente tratada"), mapa, base)
    assert not achado.ocorrencias.produto
