"""B1.5 — pedido de compra pendente é pendência do Suprimentos.

As três portas da regra, o cruzamento com B1 e o que ela **não** faz. Os
números citados como `[FATO]` foram medidos nas 88 linhas classificadas à mão
do relatório da semana 38; as linhas aqui são sintéticas.
"""
from __future__ import annotations

import pytest

from pendentes.cabecalho import Exigencia, mapear
from pendentes.estado import Classificacao, Livro
from pendentes.mercadorias import classificacao, conferencia, fontes
from pendentes.mercadorias import colunas as col
from pendentes.parametros import carregar_fabrica, mercadorias

from conftest import (
    COLUNAS_CE, COLUNAS_XML, FAROL_VERDE, FAROL_VERMELHO, chave_de, linha_ce,
    linha_xml,
)

LITERAIS = mercadorias(carregar_fabrica())

CONFIRMADO = LITERAIS["pedido_confirmado"]
NAO_CONFIRMADO = LITERAIS["pedido_nao_confirmado"]
GUARDIAO = LITERAIS["guardiao_do_pedido"]


def _mapa(colunas):
    return mapear(colunas, [Exigencia(nome) for nome in colunas], "teste")


def _preparar(*linhas_ce, xml=None):
    """Documentos já anotados pela Conferência de Entradas."""
    docs = fontes.ler_documentos(
        list(xml or [linha_xml("1", chave_de(1))]), _mapa(COLUNAS_XML))
    indice = conferencia.indexar(
        fontes.ler_conferencia(list(linhas_ce), _mapa(COLUNAS_CE)))
    conferencia.anotar(
        docs, indice,
        ausente_da_conferencia=LITERAIS["ausente_da_conferencia"],
        conferencia_fisica_confirmada=LITERAIS["conferencia_fisica_confirmada"],
        sem_pedido_vinculado=LITERAIS["sem_pedido_vinculado"])
    classificacao.herdar(docs, Livro("mercadorias"))
    return docs


def _rodar(docs):
    return classificacao.reclassificar_para_suprimentos(
        docs, pedido_confirmado=CONFIRMADO,
        pedido_nao_confirmado=NAO_CONFIRMADO, guardiao=GUARDIAO)


def _escrever_pedido(documento, valor):
    """Põe um rótulo na coluna `Pedido confirmado?` sem passar pelo farol.

    É o caminho real de um rótulo que a regra não conhece: a tabela
    `farol.pedido` é parâmetro editável na tela, e nada impede que alguém
    cadastre um terceiro código com um terceiro rótulo.
    """
    documento.conferencia[col.indice(col.CONFERENCIA,
                                     col.P_PEDIDO_CONFIRMADO)] = valor


def _guardiao(documento):
    return documento.categorizacao[1]


def _gestor(documento):
    return documento.categorizacao[2]


# -- a primeira porta: o pedido não foi confirmado --------------------------

def test_pedido_nao_confirmado_e_do_suprimentos():
    docs = _preparar(linha_ce(chave_de(1), farol=FAROL_VERMELHO))
    relato = _rodar(docs)

    assert relato.nao_confirmado == 1
    assert relato.reclassificadas == 1
    assert _guardiao(docs[0]) == "Suprimentos"


def test_pedido_nao_confirmado_nao_depende_da_incongruencia():
    """A primeira porta não olha incongruência — nem vazia, nem escrita."""
    for incongruencia in ("", "0", "divergência de quantidade"):
        docs = _preparar(linha_ce(chave_de(1), farol=FAROL_VERMELHO,
                                  incongruencia=incongruencia))
        assert _rodar(docs).nao_confirmado == 1


# -- a segunda porta: confirmado, mas com incongruência --------------------

def test_pedido_confirmado_com_incongruencia_e_do_suprimentos():
    """`[FATO]` Semana 38: 5 linhas assim, 4 já marcadas `Suprimentos` à mão."""
    docs = _preparar(linha_ce(
        chave_de(1), farol=FAROL_VERDE,
        incongruencia="10-09 no pedido tem 8 produtos e na nota tem 9"))
    relato = _rodar(docs)

    assert relato.confirmado_com_incongruencia == 1
    assert _guardiao(docs[0]) == "Suprimentos"


@pytest.mark.parametrize("incongruencia", ["", "0", "0,00", "000"])
def test_pedido_confirmado_sem_incongruencia_nao_e_do_suprimentos(incongruencia):
    """Zero e vazio são a mesma coisa aqui, como em B1."""
    docs = _preparar(linha_ce(chave_de(1), farol=FAROL_VERDE,
                              incongruencia=incongruencia))
    relato = _rodar(docs)

    assert relato.reclassificadas == 0
    assert _guardiao(docs[0]) == ""


# -- a terceira porta: em branco, não há o que falar em Suprimentos --------

def test_pedido_em_branco_nao_entra_na_regra():
    docs = _preparar(linha_ce(chave_de(1), farol=""))
    relato = _rodar(docs)

    assert relato.sem_pedido == 1
    assert relato.reclassificadas == 0
    assert _guardiao(docs[0]) == ""


def test_nota_fora_do_ce_nao_entra_pela_porta_da_incongruencia():
    """`[FATO]` Semana 38: 6 linhas assim, com o literal `não` em 3 colunas.

    Sem a porta do branco elas entrariam todas na regra por causa do literal
    — `zero_ou_vazio("não")` é `False` —, e não por causa de um pedido.
    """
    docs = _preparar()  # nenhuma linha no CE

    # É o literal que faria a segunda porta disparar, se não houvesse a terceira.
    assert conferencia.valor_da_coluna(docs[0], col.P_INCONGRUENCIA) == "não"
    relato = _rodar(docs)

    assert relato.sem_pedido == 1
    assert relato.reclassificadas == 0
    assert _guardiao(docs[0]) == ""


# -- o que a regra recusa a adivinhar (regra nº 4) -------------------------

def test_rotulo_que_a_regra_nao_conhece_nao_classifica():
    """Um terceiro rótulo cadastrado no farol não vira classificação."""
    docs = _preparar(linha_ce(chave_de(1), farol=FAROL_VERDE))
    _escrever_pedido(docs[0], "Parcial")
    relato = _rodar(docs)

    assert relato.reclassificadas == 0
    assert relato.nao_reconhecido == {"Parcial": 1}
    assert _guardiao(docs[0]) == ""


def test_o_rotulo_compara_sem_ligar_para_caixa():
    """O farol de fábrica escreve `Não`; um cadastro em caixa alta serve."""
    docs = _preparar(linha_ce(chave_de(1), farol=FAROL_VERDE))
    _escrever_pedido(docs[0], " NÃO ")
    assert _rodar(docs).nao_confirmado == 1


# -- o gestor, e o cruzamento com B1 --------------------------------------

def test_a_regra_esvazia_o_gestor_do_guardiao_que_saiu():
    """O gestor herdado era do guardião antigo; quem repõe é a
    pré-categorização, que roda depois."""
    livro = Livro("mercadorias")
    livro.registros[chave_de(1)] = Classificacao(
        chave=chave_de(1), guardiao="Manutenção Guará",
        gestor_de_apoio="Joana M.")
    docs = fontes.ler_documentos([linha_xml("1", chave_de(1))],
                                 _mapa(COLUNAS_XML))
    indice = conferencia.indexar(fontes.ler_conferencia(
        [linha_ce(chave_de(1), farol=FAROL_VERMELHO)], _mapa(COLUNAS_CE)))
    conferencia.anotar(
        docs, indice,
        ausente_da_conferencia=LITERAIS["ausente_da_conferencia"],
        conferencia_fisica_confirmada=LITERAIS["conferencia_fisica_confirmada"],
        sem_pedido_vinculado=LITERAIS["sem_pedido_vinculado"])
    classificacao.herdar(docs, livro)
    assert _gestor(docs[0]) == "Joana M."

    _rodar(docs)

    assert _guardiao(docs[0]) == "Suprimentos"
    assert _gestor(docs[0]) == ""


def test_b1_e_depois_b1_5_o_suprimentos_vence():
    """Física conferida, sem incongruência, pedido não confirmado.

    B1 quer `Fiscal`, B1.5 quer `Suprimentos`, e vence quem roda depois — a
    leitura é a do impedimento: não se lança nota de pedido não confirmado.
    `[FATO]` Zero linhas assim na semana 38; a decisão está sem medição.
    """
    docs = _preparar(linha_ce(chave_de(1), fisica="Sim", incongruencia="",
                              farol=FAROL_VERMELHO))

    assert classificacao.reclassificar_para_fiscal(
        docs,
        conferencia_fisica_confirmada=LITERAIS["conferencia_fisica_confirmada"],
        guardiao=LITERAIS["guardiao_da_reclassificacao"]) == 1
    assert _guardiao(docs[0]) == "Fiscal"

    _rodar(docs)

    assert _guardiao(docs[0]) == "Suprimentos"


def test_o_suprimentos_nao_vai_para_a_fis_fat():
    """Sem aba própria: a regra devolve a linha para a `Pendentes`."""
    docs = _preparar(linha_ce(chave_de(1), farol=FAROL_VERMELHO))
    _rodar(docs)

    para_fis_fat, pendentes = classificacao.dividir_fis_fat(
        docs, LITERAIS["guardioes_da_fis_fat"])

    assert para_fis_fat == []
    assert len(pendentes) == 1


def test_o_relato_conta_cada_linha_uma_vez():
    docs = _preparar(
        linha_ce(chave_de(1), farol=FAROL_VERMELHO),
        linha_ce(chave_de(2), farol=FAROL_VERDE, incongruencia="divergiu"),
        linha_ce(chave_de(3), farol=FAROL_VERDE, incongruencia=""),
        linha_ce(chave_de(4), farol=""),
        xml=[linha_xml(str(n), chave_de(n)) for n in (1, 2, 3, 4)])
    relato = _rodar(docs)

    assert relato.nao_confirmado == 1
    assert relato.confirmado_com_incongruencia == 1
    assert relato.sem_pedido == 1
    assert relato.reclassificadas == 2
    assert [_guardiao(d) for d in docs] == [
        "Suprimentos", "Suprimentos", "", ""]


def test_a_regra_preserva_o_gestor_de_quem_ja_era_do_suprimentos():
    """Achado pela suíte de ponta a ponta: apagar aqui perderia o nome escrito
    à mão para reescrever o mesmo `Suprimentos` no guardião."""
    livro = Livro("mercadorias")
    livro.registros[chave_de(1)] = Classificacao(
        chave=chave_de(1), guardiao="Suprimentos", gestor_de_apoio="Joana M.")
    docs = fontes.ler_documentos([linha_xml("1", chave_de(1))],
                                 _mapa(COLUNAS_XML))
    indice = conferencia.indexar(fontes.ler_conferencia(
        [linha_ce(chave_de(1), farol=FAROL_VERMELHO)], _mapa(COLUNAS_CE)))
    conferencia.anotar(
        docs, indice,
        ausente_da_conferencia=LITERAIS["ausente_da_conferencia"],
        conferencia_fisica_confirmada=LITERAIS["conferencia_fisica_confirmada"],
        sem_pedido_vinculado=LITERAIS["sem_pedido_vinculado"])
    classificacao.herdar(docs, livro)

    assert _rodar(docs).nao_confirmado == 1
    assert _guardiao(docs[0]) == "Suprimentos"
    assert _gestor(docs[0]) == "Joana M."
