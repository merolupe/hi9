"""Achar o cabeçalho e mapear coluna por nome — e a mensagem que lista todas."""
from __future__ import annotations

import pytest

from pendentes import cabecalho as cab

CABECALHO = ["Chave Acesso", "Conferência Física", "Conf. Fiscal",
             "Motivo Incongruência", "Dh. Conferência Física",
             "Nro. do Pedido", "Pedido confirmado?"]

RELATORIO = [
    ["Conferência de Entradas"],
    ["Emitido em 14/09/2026"],
    [],
    CABECALHO,
    ["3526...", "Sim", "Sim", "", "05/07/2026", "7788", ""],
]


def test_o_cabecalho_e_achado_mesmo_com_linhas_de_titulo_na_frente():
    assert cab.localizar(RELATORIO, ["Chave Acesso", "Conf. Fiscal"]) == 3


def test_o_conjunto_de_ancoras_e_o_que_separa_um_relatorio_do_outro():
    """`Chave Acesso` sozinha está no XML e na Conferência de Entradas."""
    assert cab.localizar(RELATORIO, ["Chave Acesso", "Tomador CT-e"]) == -1


def test_cabecalho_fora_da_janela_de_busca_nao_e_achado():
    longe = [["lixo"]] * 20 + [CABECALHO]
    assert cab.localizar(longe, ["Chave Acesso", "Conf. Fiscal"]) == -1


def test_exigir_cabecalho_nomeia_a_ancora_que_nao_apareceu():
    with pytest.raises(cab.CabecalhoNaoEncontrado) as erro:
        cab.exigir_cabecalho([["nada"]], ["Nro. Unico"], "Portal de Compras")
    assert "Nro. Unico" in str(erro.value)
    assert "Portal de Compras" in str(erro.value)


def test_a_coluna_e_achada_por_nome_sem_depender_de_caixa_nem_de_acento():
    assert cab.achar(["GUARDIAO", "Categoria"], "Guardião") == 0


def test_o_sinonimo_cadastrado_acha_a_coluna_renomeada():
    """É o que faz a ferramenta sobreviver a uma mudança de layout sem commit."""
    cabecalho = ["Nro. Nota Fiscal", "Valor"]
    assert cab.achar(cabecalho, "Nro Nota") == -1
    assert cab.achar(cabecalho, "Nro Nota", ("Nro. Nota Fiscal",)) == 0


def test_a_coluna_de_retorno_e_achada_por_prefixo():
    """`Retorno semana 30` muda de nome toda semana."""
    cabecalho = ["Guardião", "Retorno semana 30"]
    assert cab.achar_por_prefixo(cabecalho, "Retorno") == 1


def test_mapear_lista_todas_as_colunas_faltantes_de_uma_vez():
    """A ergonomia de mercadorias vence a de serviços, que abortava na primeira."""
    exigencias = [cab.Exigencia(nome) for nome in CABECALHO]
    incompleto = ["Chave Acesso", "Conferência Física"]

    with pytest.raises(cab.ColunasFaltando) as erro:
        cab.mapear(incompleto, exigencias, "Conferência de Entradas")

    assert erro.value.faltantes == [
        "Conf. Fiscal", "Motivo Incongruência", "Dh. Conferência Física",
        "Nro. do Pedido", "Pedido confirmado?",
    ]
    texto = str(erro.value)
    for nome in erro.value.faltantes:
        assert nome in texto
    assert "Sinônimos" in texto


def test_coluna_opcional_ausente_nao_aborta_e_fica_registrada():
    exigencias = [cab.Exigencia("Chave Acesso"),
                  cab.Exigencia("Categoria", obrigatoria=False)]
    mapa = cab.mapear(["Chave Acesso"], exigencias, "semana anterior")
    assert mapa.tem("Chave Acesso")
    assert not mapa.tem("Categoria")
    assert mapa.ausentes == ("Categoria",)


def test_o_mapa_devolve_o_valor_da_linha_e_o_padrao_quando_a_coluna_nao_veio():
    exigencias = [cab.Exigencia("Chave Acesso"),
                  cab.Exigencia("Categoria", obrigatoria=False)]
    mapa = cab.mapear(["Chave Acesso"], exigencias, "semana anterior")
    assert mapa.valor(["3526..."], "Chave Acesso") == "3526..."
    assert mapa.valor(["3526..."], "Categoria", "(sem)") == "(sem)"


def test_as_exigencias_vem_do_parametro_com_sinonimos_e_obrigatoriedade():
    declaradas = [
        {"nome": "Guardião", "sinonimos": ["Guardiao"], "obrigatoria": False},
        {"nome": "Chave Acesso"},
        {"nome": ""},
    ]
    exigencias = cab.exigencias_de(declaradas)
    assert [e.nome for e in exigencias] == ["Guardião", "Chave Acesso"]
    assert exigencias[0].sinonimos == ("Guardiao",)
    assert exigencias[0].obrigatoria is False
    assert exigencias[1].obrigatoria is True
