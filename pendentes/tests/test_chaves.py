"""As chaves de identidade — com atenção ao número do Portal Nacional."""
from __future__ import annotations

from pendentes.chaves import (analisar_numero_de_nfse, chave_de_acesso, cnpj,
                              cnpj_utilizavel, numero_de_nfse)


def test_o_prefixo_de_ano_do_portal_nacional_e_cortado():
    """`20260000012345` é a nota 12345 — sem o corte, nota nenhuma casa."""
    assert numero_de_nfse("20260000012345") == "12345"


def test_o_corte_do_prefixo_de_ano_e_reportado():
    """A suposição por trás do corte precisa ser contável, e não invisível."""
    analise = analisar_numero_de_nfse("20260000012345")
    assert analise.cortou_prefixo_de_ano is True

    curta = analisar_numero_de_nfse("000123")
    assert curta.cortou_prefixo_de_ano is False
    assert curta.removeu_zeros_a_esquerda is True


def test_o_corte_so_vale_a_partir_de_treze_digitos_comecando_em_20():
    assert numero_de_nfse("202600001234") == "202600001234"   # 12 dígitos
    assert numero_de_nfse("1926000012345") == "1926000012345"  # não começa em 20


def test_zeros_a_esquerda_somem_mas_sobra_sempre_um_digito():
    assert numero_de_nfse("000123") == "123"
    assert numero_de_nfse("000") == "0"
    assert numero_de_nfse("") == "0"


def test_numero_que_chega_como_numero_nao_vira_notacao_cientifica():
    assert numero_de_nfse(20260000012345) == "12345"


def test_chave_de_acesso_fica_so_com_os_44_digitos():
    bruta = " '3526 0612.345678/0001-99 5500 1000 0001 2310 0000 1234 "
    assert chave_de_acesso(bruta) == "35260612345678000199550010000001231000001234"
    assert len(chave_de_acesso(bruta)) == 44


def test_cnpj_zerado_nao_serve_de_chave():
    assert cnpj("00.000.000/0000-00") == "00000000000000"
    assert cnpj_utilizavel("00.000.000/0000-00") is False
    assert cnpj_utilizavel("") is False
    assert cnpj_utilizavel("12.345.678/0001-99") is True
