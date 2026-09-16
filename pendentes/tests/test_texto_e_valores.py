"""As normalizações — e a prova de que as duas `NormalizarTexto` não se confundem."""
from __future__ import annotations

from datetime import date, datetime

from pendentes.texto import (aparar, chave_de_texto, limpar_quebras,
                             sem_acento, so_digitos, texto_de)
from pendentes.valores import (chave_de_valor, data_br, data_hora, numero_br,
                               zero_ou_vazio)


# -- as duas normalizações, lado a lado ------------------------------------

def test_aparar_preserva_caixa_e_acento_e_so_colapsa_espaco():
    assert aparar("  Guardião   da   Área  ") == "Guardião da Área"


def test_chave_de_texto_sobe_a_caixa_e_tira_o_acento():
    assert chave_de_texto("  Guardião   da   Área  ") == "GUARDIAO DA AREA"


def test_as_duas_normalizacoes_nao_produzem_o_mesmo_resultado():
    """É por isso que elas deixaram de ter o mesmo nome."""
    valor = "Situação da manifestação"
    assert aparar(valor) != chave_de_texto(valor)


def test_e_chave_de_texto_que_faz_guardiao_casar_com_guardiao():
    assert chave_de_texto("Guardião") == chave_de_texto("GUARDIAO")


def test_sem_acento_nao_mexe_em_mais_nada():
    assert sem_acento("Emissão 1º") == "Emissao 1o"


def test_so_digitos_limpa_pontuacao_de_cnpj():
    assert so_digitos("12.345.678/0001-99") == "12345678000199"


def test_limpar_quebras_tira_o_retorno_escapado_do_xml():
    sujo = "SERVICO DE_x000D_\nMANUTENCAO   PREVENTIVA"
    assert limpar_quebras(sujo) == "SERVICO DE MANUTENCAO PREVENTIVA"


def test_texto_de_nao_inventa_casa_decimal_em_codigo():
    """`5552.0` é o CFOP 5552 — com a casa a mais, PROCX nenhum casa."""
    assert texto_de(5552.0) == "5552"
    assert texto_de(None) == ""
    assert texto_de(date(2026, 7, 1)) == "01/07/2026"


# -- número ----------------------------------------------------------------

def test_numero_br_nas_tres_notacoes_que_chegam():
    assert numero_br("4369.14") == 4369.14          # ASIS
    assert numero_br("4.369,14") == 4369.14         # relatório em português
    assert numero_br("4369,14") == 4369.14          # idem, sem milhar
    assert numero_br(4369.14) == 4369.14            # Sankhya, numérico


def test_numero_br_de_celula_vazia_e_zero():
    assert numero_br("") == 0.0
    assert numero_br(None) == 0.0


def test_chave_de_valor_tem_sempre_duas_casas_e_ponto():
    assert chave_de_valor("4.369,1") == "4369.10"
    assert chave_de_valor(1200) == "1200.00"


# -- data ------------------------------------------------------------------

def test_data_br_le_dd_mm_aaaa_explicitamente():
    """Sem parse explícito, `03/07/2026` vira março nos dias em que dá."""
    assert data_br("03/07/2026") == date(2026, 7, 3)


def test_data_br_devolve_o_texto_original_quando_nao_interpreta():
    assert data_br("sem data") == "sem data"
    assert data_br("31/02/2026") == "31/02/2026"


def test_data_br_aceita_data_que_ja_chega_como_data():
    assert data_br(datetime(2026, 7, 3, 9, 30)) == datetime(2026, 7, 3, 9, 30)


def test_data_hora_le_ano_de_dois_digitos_como_dois_mil():
    assert data_hora("03/07/26 14:20") == datetime(2026, 7, 3, 14, 20)


def test_data_hora_devolve_vazio_quando_nao_interpreta():
    """A assimetria com `data_br` é conhecida: é o defeito 12, à espera de medição."""
    assert data_hora("sem data") == ""


# -- o zero que não é texto ------------------------------------------------

def test_zero_ou_vazio_reconhece_as_formas_de_zero():
    assert zero_ou_vazio("") is True
    assert zero_ou_vazio("0") is True
    assert zero_ou_vazio("0,00") is True
    assert zero_ou_vazio("000") is True


def test_zero_ou_vazio_diz_nao_para_a_palavra_nao():
    """É por esta porta que a regra B1 não dispara para nota fora do CE."""
    assert zero_ou_vazio("não") is False
    assert zero_ou_vazio("divergência de quantidade") is False
