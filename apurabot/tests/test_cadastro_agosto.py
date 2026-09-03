"""Regras cadastradas a partir da rodada do pré-livro de agosto.

Três coisas que agosto trouxe e julho não tinha: complemento de ICMS lançado
contra o código da mercadoria, devolução de venda em MS, e o cadastro completo
das filiais.
"""
from __future__ import annotations

import pytest

from apurabot.ingestao import LinhaLivro
from apurabot.nucleo.atividade import COMERCIAL, INDUSTRIAL, classificar, mapa_da_uf
from apurabot.nucleo.carga import Situacao, equalizar
from apurabot.nucleo.classificacao import classificar as classificar_operacao


def linha(**campos) -> LinhaLivro:
    padrao = {
        "valor_icms": 0.0, "valor_contabil": 0.0, "base_icms": 0.0,
        "aliquota_icms": 0.0, "cfop": None, "produto": None,
        "data_cancelamento": None, "especie": "NF", "modelo": "55",
        "produto_descricao": None, "cst": "00-Tributada integralmente",
        "entrada_saida": "Entrada",
    }
    return LinhaLivro(linha_origem=2, arquivo_origem="teste.xlsx", dados=padrao | campos)


#: O lançamento que travava agosto: nota 743324 de Guará, CFOP 2906.
COMPLEMENTO = dict(
    cfop=2906, produto="130020001", produto_descricao="UREIA 46-00-00  Bag 1.000 Kg",
    valor_contabil=0.0, base_icms=2824.84, aliquota_icms=12.0, valor_icms=338.98,
)


# -- complemento de ICMS reconhecido pela forma -----------------------------

def test_complemento_lancado_no_codigo_da_mercadoria_deixa_de_travar(parametros):
    """Sem valor contábil, com base e com ICMS: é a forma do complemento.

    Antes disto o lançamento parava a competência com `SEM BASE`, porque a
    regra só reconhecia o complemento pelo código de produto próprio.
    """
    l = linha(**COMPLEMENTO)
    carga = equalizar(l, parametros)
    assert carga.situacao is Situacao.EQUALIZADA
    assert not carga.e_pendencia
    assert classificar_operacao(l, parametros).categoria == "complemento_icms"


def test_a_forma_nao_alcanca_lancamento_com_valor_contabil(parametros):
    """A trava da regra: com contábil, a carga sai da fórmula como sempre.

    Sem isso, a chave `sem_valor_contabil` alargaria o complemento para linhas
    normais — e um retorno de armazém viraria complemento.
    """
    l = linha(**{**COMPLEMENTO, "valor_contabil": 2_824.84})
    assert classificar_operacao(l, parametros).categoria != "complemento_icms"
    assert equalizar(l, parametros).carga == 12.0     # 338,98 ÷ 2.824,84


def test_sem_contabil_e_sem_base_continua_pendencia(parametros):
    """Complemento tem base. O que não tem nem base é outra coisa, e trava."""
    l = linha(**{**COMPLEMENTO, "base_icms": 0.0})
    carga = equalizar(l, parametros)
    assert carga.situacao is Situacao.SEM_BASE
    assert carga.e_pendencia


# -- devolução de venda segue a venda que desfaz ----------------------------

@pytest.mark.parametrize(
    "cfop, atividade, descricao",
    [
        (2201, INDUSTRIAL, "Dev vda prod do estab"),
        (1201, INDUSTRIAL, "Dev vda prod do estab"),
        (2202, COMERCIAL, "Dev vda merc adq ou rec terc"),
        (1202, COMERCIAL, "Dev vda merc adq ou rec terc"),
    ],
)
def test_devolucao_de_venda_cai_na_atividade_da_venda(
    parametros, cfop, atividade, descricao
):
    mapa = mapa_da_uf("MS", parametros)
    l = linha(cfop=cfop, cfop_descricao=descricao, entrada_saida="Entrada")
    assert classificar(l, mapa).atividade == atividade


# -- cadastro das filiais ---------------------------------------------------

def test_toda_filial_tem_codigo_cnpj_e_inscricao(parametros):
    """O casamento é pelo código, e o registro traz CNPJ e IE no cabeçalho."""
    filiais = parametros.filiais["filiais"]
    assert len(filiais) == 7
    for f in filiais:
        assert isinstance(f["codigo"], int), f["nome"]
        assert len(str(f["cnpj"])) == 14, f["nome"]
        assert str(f["inscricao_estadual"]).isdigit(), f["nome"]


def test_os_cnpj_sao_da_mesma_raiz_e_nao_se_repetem(parametros):
    """Sete estabelecimentos da mesma empresa: raiz igual, ordem distinta."""
    filiais = parametros.filiais["filiais"]
    raizes = {str(f["cnpj"])[:8] for f in filiais}
    assert raizes == {"14031191"}
    ordens = [str(f["cnpj"])[8:12] for f in filiais]
    assert len(set(ordens)) == len(ordens)


def test_o_registro_traz_o_cabecalho_cadastrado(base_julho, parametros):
    from apurabot.apuracao import apurar
    from apurabot.nucleo import registro as reg

    registros = reg.montar(apurar(base_julho, parametros), parametros)
    for r in registros:
        assert r.cnpj and r.inscricao_estadual, r.estabelecimento


# -- o frete de custo em MS, de agosto em diante ----------------------------
#
# Critério confirmado pela Gerência Fiscal/Tributária em 03/09/2026: em MS,
# frete que entra como CUSTO é produção; frete de venda, que é DESPESA, é
# comercial. A GIA de 07/2026 classificou o frete de transferência como
# comercial, então a regra nova vale de 08/2026 em diante — e julho continua
# reproduzindo o que foi declarado.

FRETE_TRANSFERENCIA = dict(
    cfop=2352,
    produto="700000002",
    produto_descricao="Fretes sobre Transf/ Remessa/ Retorno (Custo)",
    valor_contabil=27_553.05, base_icms=27_553.05,
    aliquota_icms=7.0, valor_icms=1_928.72,
)

import datetime as dt  # noqa: E402  (perto de quem usa)


def test_frete_de_transferencia_em_ms_e_producao_de_agosto_em_diante(parametros):
    mapa = mapa_da_uf("MS", parametros)
    agosto = linha(**FRETE_TRANSFERENCIA, data_movimento=dt.date(2026, 8, 14))
    assert classificar(agosto, mapa).atividade == INDUSTRIAL


def test_em_julho_o_mesmo_frete_continua_comercial(parametros):
    """Regra 3 do repositório: competência antiga não muda de número sozinha.

    Se esta classificação mudasse para trás, o estorno industrial de julho
    subiria R$ 1.866,58 e o benefício de Rio Brilhante cairia R$ 1.946,12
    contra a GIA já declarada.
    """
    mapa = mapa_da_uf("MS", parametros)
    julho = linha(**FRETE_TRANSFERENCIA, data_movimento=dt.date(2026, 7, 14))
    assert classificar(julho, mapa).atividade == COMERCIAL


def test_frete_de_venda_em_ms_e_comercial_nos_dois_meses(parametros):
    """A outra ponta do critério: despesa é comercial, e sempre foi."""
    mapa = mapa_da_uf("MS", parametros)
    campos = dict(FRETE_TRANSFERENCIA, produto_descricao="Fretes sobre Vendas")
    for data in (dt.date(2026, 7, 14), dt.date(2026, 8, 14)):
        assert classificar(linha(**campos, data_movimento=data), mapa).atividade == (
            COMERCIAL
        )


def test_almoxarifado_e_venda_conjunta_sao_despesa(parametros):
    """As duas descrições que o critério "(Custo)" não marca.

    Respondidas em 03/09/2026: são despesa, e portanto comerciais. Já caíam em
    comercial pela atividade do CFOP — o que muda é que agora estão no
    parâmetro como regra, e não por coincidência.
    """
    mapa = mapa_da_uf("MS", parametros)
    for descricao in (
        "Fretes sobre Compras (Almoxarifado)",
        "Fretes sobre Transf/ Retorno - Venda conjunta",
    ):
        campos = dict(FRETE_TRANSFERENCIA, produto_descricao=descricao)
        for data in (dt.date(2026, 7, 14), dt.date(2026, 8, 14)):
            resultado = classificar(linha(**campos, data_movimento=data), mapa)
            assert resultado.atividade == COMERCIAL, (descricao, data)
            assert "descrição contém" in resultado.regra, descricao


def test_venda_conjunta_nao_cai_na_regra_do_frete_de_transferencia(parametros):
    """A ordem da lista importa: despesa é avaliada antes de custo.

    "Fretes sobre Transf/ Retorno - Venda conjunta" e "Fretes sobre Transf/
    Remessa/ Retorno (Custo)" começam parecido. Se a regra de custo viesse
    primeiro e alguém afrouxasse o texto dela, a venda conjunta iria parar em
    industrial de agosto em diante — e ninguém veria.
    """
    mapa = mapa_da_uf("MS", parametros)
    ordem = [r["contem"] for r in mapa["por_descricao"]]
    assert ordem.index("Fretes sobre Transf/ Retorno - Venda conjunta") < ordem.index(
        "Fretes sobre Transf/ Remessa/ Retorno"
    )
