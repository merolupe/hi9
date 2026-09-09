"""A mini-linguagem das regras, operador por operador.

Ela é a parte que o time fiscal escreve à mão. Um operador que mude de
comportamento em silêncio reclassifica meses inteiros.
"""
from __future__ import annotations

from conftest import base_com, regra

from fiscalbot import predicados as p
from fiscalbot.modelo import Parametros

TABELAS = Parametros(tabelas={"FRETE": ("700000001", "700000002", "701000177")})


# -- condição de produto ---------------------------------------------------

def test_produto_por_codigo_exato_e_por_prefixo():
    assert p.cond_produto_ok("701000701", "701000701", TABELAS)
    assert not p.cond_produto_ok("701000701", "701000702", TABELAS)
    assert p.cond_produto_ok("INICIA:7010", "701000701", TABELAS)
    assert not p.cond_produto_ok("NAOINICIA:7010", "701000701", TABELAS)
    assert p.cond_produto_ok("=701000701", "701000701", TABELAS), "aceita o = legado"


def test_produto_por_tabela_nomeada():
    assert p.cond_produto_ok("TABELA:FRETE", "700000001", TABELAS)
    assert not p.cond_produto_ok("TABELA:FRETE", "999999999", TABELAS)
    assert not p.cond_produto_ok("TABELA:NAOEXISTE", "700000001", TABELAS)


def test_produto_por_tabela_com_excecao():
    assert p.cond_produto_ok("TABELAEXCETO:FRETE:700000001", "700000002", TABELAS)
    assert not p.cond_produto_ok("TABELAEXCETO:FRETE:700000001", "700000001", TABELAS)


def test_condicao_vazia_nao_restringe_nada():
    assert p.cond_produto_ok("", "qualquer", TABELAS)
    assert p.cond_par_uf_ok("", "INTRA", "SPxSP")
    assert p.cond_parceiro_ok("", "QUALQUER")


# -- condição de UF --------------------------------------------------------

def test_uf_por_par_lista_e_por_origem():
    assert p.cond_par_uf_ok("SPxSP;MTxMT", "INTRA", "SPxSP")
    assert not p.cond_par_uf_ok("SPxSP;MTxMT", "INTER", "SPxMG")
    assert p.cond_par_uf_ok("INTRA", "INTRA", "SPxSP")
    assert p.cond_par_uf_ok("UFORIG:BA;PR", "INTER", "PRxSP")
    assert not p.cond_par_uf_ok("UFORIG:BA;PR", "INTER", "SCxSP")
    assert p.cond_par_uf_ok("NAOUFORIG:SC;BA;PR", "INTER", "MGxSP")
    assert not p.cond_par_uf_ok("NAOUFORIG:SC;BA;PR", "INTER", "PRxSP")
    assert p.cond_par_uf_ok("NAOPARUF:SPxSP", "INTER", "SPxMG")


# -- condição de parceiro --------------------------------------------------

def test_parceiro_ignora_caixa_mas_produto_nao():
    """Diferença herdada do VBA, e mantida: mudá-la reclassificaria registros."""
    assert p.cond_parceiro_ok("INICIA:econet", "ECONET EDITORA")
    assert not p.cond_produto_ok("INICIA:abc", "ABC123", TABELAS)


# -- conferência por dimensão ---------------------------------------------

def test_cst_exato_e_por_lista_separada_por_virgula():
    assert p.testar_cst(regra(esp_cst="60"), "60") == ""
    assert p.testar_cst(regra(esp_cst="60"), "00") == p.ADV_CST
    assert p.testar_cst(regra(esp_cst="EM:00,20"), "20") == ""
    assert p.testar_cst(regra(esp_cst="EM:00,20"), "41") == p.ADV_CST
    assert p.testar_cst(regra(esp_cst="NAOEM:41,50"), "41") == p.ADV_CST


def test_icms_positivo_zero_e_delegado_a_carga():
    assert p.testar_icms(regra(esp_icms=">0"), 5.0) == ""
    assert p.testar_icms(regra(esp_icms=">0"), 0.0) == p.ADV_ICMS
    assert p.testar_icms(regra(esp_icms="0"), 0.0) == ""
    assert p.testar_icms(regra(esp_icms="0"), 1.0) == p.ADV_ICMS
    assert p.testar_icms(regra(esp_icms="CARGA"), 999.0) == ""


def test_texto_que_nao_e_numero_no_campo_de_icms_nao_faz_nada():
    """`TABELAUF` foi parar em EspICMS na regra E11. No VBA, ali ele é inerte.

    Portado como está, não como deveria ser: o padrão-ouro foi auditado assim,
    e corrigir a regra é decisão do fiscal, na tela — não do porte.
    """
    assert p.testar_icms(regra(esp_icms="TABELAUF"), 123.0) == ""


def test_aliquota_por_lista_e_pela_matriz():
    assert p.testar_aliquota(regra(esp_aliq="7;12"), 12.0, "SPxMG", base_com()) == ""
    assert p.testar_aliquota(regra(esp_aliq="7;12"), 18.0, "SPxMG", base_com()) \
        == p.ADV_ALIQUOTA
    base = base_com(aliquotas={"SP": {"MG": 12.0}})
    assert p.testar_aliquota(regra(esp_aliq="TABELAUF"), 12.0, "SPxMG", base) == ""
    assert p.testar_aliquota(regra(esp_aliq="TABELAUF"), 12.0, "SPxRJ", base) \
        == p.ADV_ALIQUOTA, "par que não está na matriz é advertência"


def test_carga_respeita_a_tolerancia_nas_duas_pontas():
    r = regra(esp_carga="4")
    assert p.testar_carga(r, 4.04, 100.0, True, 0.05) == ""
    assert p.testar_carga(r, 3.96, 100.0, True, 0.05) == ""
    assert p.testar_carga(r, 4.06, 100.0, True, 0.05) == p.ADV_CARGA
    assert p.testar_carga(r, 4.0, 0.0, True, 0.05) == p.ADV_CARGA


def test_outros_cobre_parceiro_e_mensagens():
    assert p.testar_outros(regra(esp_outros="PARCEIRO<20"), 4.0, "") == ""
    assert p.testar_outros(regra(esp_outros="PARCEIRO<20"), 900.0, "") \
        == p.ADV_PARCEIRO
    assert p.testar_outros(regra(esp_outros="PARCEIRO<20"), "texto", "") \
        == p.ADV_PARCEIRO
    assert p.testar_outros(
        regra(esp_outros="PARCEIROINICIA:HINOVE"), 1, "HINOVE AGROCIENCIA") == ""
    assert p.testar_outros(regra(esp_outros="SEMPRE:olha isto"), 1, "") == "olha isto"


def test_secst_so_fala_quando_o_cst_observado_casa():
    r = regra(esp_outros="SECST:20:Validar operacao real")
    assert p.mensagem_secst(r, "20") == "Validar operacao real"
    assert p.mensagem_secst(r, "00") == ""


# -- Camada 0 --------------------------------------------------------------

def test_coerencia_entre_cst_e_icms():
    param = Parametros(cst_exigem_icms_positivo=("00", "20"))
    assert p.coerencia_cst_icms("00", 5.0, param) == ""
    assert p.coerencia_cst_icms("00", 0.0, param) == p.ADV_ICMS
    assert p.coerencia_cst_icms("41", 0.0, param) == ""
    assert p.coerencia_cst_icms("41", 5.0, param) == p.ADV_ICMS


def test_coerencia_entre_cfop_e_operacao():
    assert p.coerencia_cfop_operacao("5101", "INTRA") == ""
    assert p.coerencia_cfop_operacao("5101", "INTER") == p.ADV_PARCEIRO
    assert p.coerencia_cfop_operacao("6101", "INTER") == ""
    assert p.coerencia_cfop_operacao("0101", "INTRA") == p.ADV_PARCEIRO
    assert p.coerencia_cfop_operacao("5101", "INDEFINIDO") == "", "sem UF, não acusa"
    assert p.coerencia_cfop_operacao("3101", "INTRA") == "", "exterior está fora"


# -- o texto da auditoria --------------------------------------------------

def test_a_frase_de_auditoria_explica_o_que_se_esperava():
    r = regra(esp_cst="41", esp_icms="0", operacao="Transf. Uso Consumo e Ativo")
    assert p.montar_auditoria(r) == \
        "Transf. Uso Consumo e Ativo - esperado CST 41, ICMS 0"
    com_carga = regra(esp_cst="20", esp_icms="CARGA", esp_carga="4",
                      operacao="Venda")
    assert p.montar_auditoria(com_carga) == (
        "Venda - esperado CST 20, ICMS conforme carga, "
        "Carga efetiva 4% (ICMS/Vlr contabil)")
    assert p.montar_auditoria(regra(esp_cst="EM:00,20", operacao="X")) == \
        "X - esperado CST em {00,20}"
