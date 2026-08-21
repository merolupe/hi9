"""Equalização da carga efetiva — casos isolados."""
from __future__ import annotations

import pytest

from apurabot.ingestao import LinhaLivro
from apurabot.nucleo.carga import ALERTA_NAO_HOMOLOGADA, Situacao, equalizar


def linha(**campos) -> LinhaLivro:
    padrao = {
        "valor_icms": 0.0, "valor_contabil": 0.0, "base_icms": 0.0,
        "aliquota_icms": 0.0, "cfop": None, "produto": None,
        "data_cancelamento": None, "especie": "NF", "modelo": "55",
        "produto_descricao": None, "cst": "00-Tributada integralmente",
    }
    return LinhaLivro(linha_origem=2, arquivo_origem="teste.xlsx", dados=padrao | campos)


def test_linha_sem_icms_fica_fora_da_apuracao(parametros):
    r = equalizar(linha(valor_icms=0.0, valor_contabil=1000.0), parametros)
    assert r.situacao is Situacao.SEM_ICMS
    assert not r.relevante_para_icms


def test_documento_cancelado_sai_da_apuracao(parametros):
    import datetime as dt

    r = equalizar(
        linha(valor_icms=120.0, valor_contabil=1000.0, data_cancelamento=dt.date(2026, 7, 9)),
        parametros,
    )
    assert r.situacao is Situacao.CANCELADA


@pytest.mark.parametrize(
    "icms, contabil, aliquota, esperado",
    [
        (120.00, 1000.00, 12.0, 12.0),      # exata
        (487.54, 4860.10, 12.0, 12.0),      # artefato: bruta 10,03%
        (1019.42, 9665.75, 12.0, 12.0),     # artefato: bruta 10,55%
        (555.07, 13876.28, 17.0, 4.0),      # base reduzida: 17% com carga de 4%
        (70.00, 1000.00, 7.0, 7.0),
        (180.00, 1000.00, 18.0, 18.0),
    ],
)
def test_equaliza_para_a_carga_nominal(parametros, icms, contabil, aliquota, esperado):
    r = equalizar(
        linha(valor_icms=icms, valor_contabil=contabil, aliquota_icms=aliquota), parametros
    )
    assert r.situacao is Situacao.EQUALIZADA
    assert r.carga == esperado


def test_carga_nunca_excede_a_aliquota(parametros):
    """Bruta de 5,8% está mais perto de 7% que de 4%, mas a alíquota é 4%.

    Sem o teto a equalização escolheria 7%, que é um crédito que a nota não
    destacou. O teto é o que impede isso.
    """
    r = equalizar(
        linha(valor_icms=58.0, valor_contabil=1000.0, aliquota_icms=4.0), parametros
    )
    assert r.situacao is Situacao.EQUALIZADA
    assert r.carga == 4.0


def test_carga_tolerada_gera_alerta_mas_nao_pendencia(parametros):
    r = equalizar(
        linha(valor_icms=205.0, valor_contabil=1000.0, aliquota_icms=20.5), parametros
    )
    assert r.carga == 20.5
    assert r.alerta == ALERTA_NAO_HOMOLOGADA
    assert not r.e_pendencia


def test_carga_fora_da_regua_vira_pendencia(parametros):
    """0,8% fica a mais de 2,5 pontos do degrau mais baixo da régua (4%)."""
    r = equalizar(
        linha(valor_icms=8.0, valor_contabil=1000.0, aliquota_icms=25.0), parametros
    )
    assert r.situacao is Situacao.NAO_EQUALIZADA
    assert r.e_pendencia


def test_tolerancia_alcanca_o_vao_entre_degraus(parametros):
    """Com régua e tolerância atuais, valores intermediários sempre encaixam.

    O maior vão da régua é de 5 pontos (7→12 e 12→17) e a tolerância é de 2,5,
    exatamente metade. Na prática a rede só pega valores abaixo de ~1,5% ou
    acima de ~27,5%. Este teste fixa esse comportamento para que uma mudança
    de régua ou de tolerância apareça — ver decisão pendente nº 14.
    """
    r = equalizar(
        linha(valor_icms=96.0, valor_contabil=1000.0, aliquota_icms=25.0), parametros
    )
    assert r.situacao is Situacao.EQUALIZADA
    assert r.carga == 12.0


def test_ciap_nao_divide_por_zero(parametros):
    """CFOP 1604 chega com contábil zerado e ICMS diferente de zero."""
    r = equalizar(
        linha(valor_icms=10545.88, valor_contabil=0.0, cfop=1604, produto=615000001),
        parametros,
    )
    assert r.situacao is Situacao.CIAP
    assert r.relevante_para_icms


def test_complemento_de_icms_recebe_carga_do_parametro(parametros):
    r = equalizar(
        linha(valor_icms=1210.50, valor_contabil=0.0, cfop=2906, produto=701000075),
        parametros,
    )
    assert r.carga == 4.0
    assert r.alerta == ALERTA_NAO_HOMOLOGADA     # regra ainda não homologada


def test_icms_sem_contabil_e_sem_regra_vira_pendencia(parametros):
    r = equalizar(
        linha(valor_icms=500.0, valor_contabil=0.0, cfop=1102, produto=999999999),
        parametros,
    )
    assert r.situacao is Situacao.SEM_BASE
    assert r.e_pendencia
