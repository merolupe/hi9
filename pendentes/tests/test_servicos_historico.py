"""O histórico do Portal de Compras: parceiro e pedido além da semana.

Tudo inventado — CNPJ, código, nome e número —, regra nº 1 do `CLAUDE.md`.
"""
from __future__ import annotations

import openpyxl
import pytest

from pendentes.cabecalho import Exigencia, mapear
from pendentes.servicos import enriquecimento, fontes, historico
from pendentes.servicos.execucao import gerar
from conftest import (
    COLUNAS_ASIS, COLUNAS_PORTAL, linha_asis, linha_portal, relatorio,
)

TOPS = ("2020", "2111")
ANTIGO = "55444333000122"      # parceiro que só aparece no Portal antigo
DA_SEMANA = "99888777000166"


def registros(*linhas):
    mapa = mapear(COLUNAS_PORTAL, [Exigencia(n) for n in COLUNAS_PORTAL], "t")
    return fontes.ler_registros(list(linhas), mapa)


def _pedido(numero_unico, cnpj, **campos):
    return linha_portal(numero_unico, "", cnpj, 0, top="1102",
                        descricao_do_top="PC COMPRA DE SERVICO", **campos)


# -- absorver ----------------------------------------------------------------

def test_absorver_guarda_parceiro_pedido_e_filial():
    memoria = historico.Historico()
    relato = historico.absorver(memoria, registros(
        _pedido(10, ANTIGO, codigo_do_parceiro="7007",
                nome_do_parceiro="ANTIGO LTDA", negociacao="15/12/2025"),
    ), prefixo_de_pedido="PC")

    assert memoria.parceiros[ANTIGO]["codigo"] == "7007"
    assert memoria.pedidos[ANTIGO]["numero_unico"] == 10
    assert memoria.filiais
    assert relato.parceiros_novos == 1 and relato.pedidos_novos == 1
    assert relato.primeira_data == "2025-12-15"


def test_o_pedido_mais_recente_vence_em_qualquer_ordem_de_absorcao():
    velho = registros(_pedido(10, ANTIGO, comprador="ANA"))
    novo = registros(_pedido(20, ANTIGO, comprador="BIA"))
    for ordem in ((velho, novo), (novo, velho)):
        memoria = historico.Historico()
        for lote in ordem:
            historico.absorver(memoria, lote, prefixo_de_pedido="PC")
        assert memoria.pedidos[ANTIGO]["comprador"] == "BIA"


def test_troca_dentro_do_mesmo_relatorio_nao_conta_como_mais_recente():
    memoria = historico.Historico()
    relato = historico.absorver(memoria, registros(
        _pedido(10, ANTIGO), _pedido(20, ANTIGO)), prefixo_de_pedido="PC")
    assert relato.pedidos_novos == 1 and relato.pedidos_mais_recentes == 0

    relato = historico.absorver(memoria, registros(_pedido(30, ANTIGO)),
                                prefixo_de_pedido="PC")
    assert relato.pedidos_novos == 0 and relato.pedidos_mais_recentes == 1


def test_absorver_de_novo_o_mesmo_relatorio_nao_muda_nada():
    memoria = historico.Historico()
    lote = registros(_pedido(10, ANTIGO), linha_portal(11, "5", ANTIGO, 9.0))
    historico.absorver(memoria, lote, prefixo_de_pedido="PC")
    assert not historico.absorver(memoria, lote, prefixo_de_pedido="PC").mudou


def test_cnpj_zerado_nao_entra_no_historico():
    memoria = historico.Historico()
    historico.absorver(memoria, registros(
        linha_portal(1, "1", "00000000000000", 10.0)), prefixo_de_pedido="PC")
    assert not memoria.parceiros


def test_gravar_e_carregar_devolvem_o_mesmo(tmp_path):
    memoria = historico.Historico()
    historico.absorver(memoria, registros(_pedido(10, ANTIGO)),
                       prefixo_de_pedido="PC")
    historico.gravar(memoria, "teste", raiz=tmp_path)
    relido = historico.carregar(tmp_path)
    assert relido.parceiros == memoria.parceiros
    assert relido.pedidos == memoria.pedidos
    assert not historico.carregar(tmp_path / "vazia")


# -- o cadastro da semana, complementado -----------------------------------

def _memoria(*linhas):
    memoria = historico.Historico()
    historico.absorver(memoria, registros(*linhas), prefixo_de_pedido="PC")
    return memoria


def test_parceiro_sem_movimento_na_semana_sai_com_o_codigo_do_historico():
    memoria = _memoria(_pedido(10, ANTIGO, codigo_do_parceiro="7007",
                               nome_do_parceiro="ANTIGO LTDA"))
    cadastro = enriquecimento.cadastrar(
        registros(linha_portal(1, "1", DA_SEMANA, 10.0)), tops=TOPS,
        prefixo_de_pedido="PC", historico=memoria)

    assert cadastro.codigo_do_parceiro(ANTIGO) == "7007"
    assert cadastro.nome_do_parceiro(ANTIGO, "NOME DO ASIS") == "ANTIGO LTDA"
    assert cadastro.veio_do_historico(ANTIGO)
    assert not cadastro.veio_do_historico(DA_SEMANA)


def test_a_semana_vence_o_historico_no_cadastro_do_parceiro():
    memoria = _memoria(linha_portal(99, "1", DA_SEMANA, 1.0,
                                    codigo_do_parceiro="1111"))
    cadastro = enriquecimento.cadastrar(
        registros(linha_portal(1, "1", DA_SEMANA, 10.0,
                               codigo_do_parceiro="2222")),
        tops=TOPS, prefixo_de_pedido="PC", historico=memoria)
    assert cadastro.codigo_do_parceiro(DA_SEMANA) == "2222"


def test_o_pedido_de_meses_atras_aparece_quando_a_semana_nao_tem():
    memoria = _memoria(_pedido(10, DA_SEMANA, comprador="ANA"))
    cadastro = enriquecimento.cadastrar(
        registros(linha_portal(1, "1", DA_SEMANA, 10.0)), tops=TOPS,
        prefixo_de_pedido="PC", historico=memoria)
    assert cadastro.pedido_de(DA_SEMANA).comprador == "ANA"


def test_o_pedido_da_semana_vence_o_historico_mais_antigo():
    memoria = _memoria(_pedido(10, DA_SEMANA, comprador="ANA"))
    cadastro = enriquecimento.cadastrar(
        registros(_pedido(20, DA_SEMANA, comprador="BIA")), tops=TOPS,
        prefixo_de_pedido="PC", historico=memoria)
    assert cadastro.pedido_de(DA_SEMANA).comprador == "BIA"
    assert DA_SEMANA not in cadastro.pedidos_do_historico


# -- de ponta a ponta ---------------------------------------------------------

@pytest.fixture()
def pastas(tmp_path):
    (tmp_path / "saida").mkdir()
    return tmp_path


def _semana(pastas, nome, linhas_do_portal):
    asis = relatorio(pastas / f"ASIS{nome}.xlsx", COLUNAS_ASIS, [
        linha_asis("3003", ANTIGO, "90.00", prestador="ANTIGO DO ASIS"),
    ])
    portal = relatorio(pastas / f"PC{nome}.xlsx", COLUNAS_PORTAL,
                       linhas_do_portal)
    return gerar([asis, portal], pastas / "saida",
                 raiz_dos_dados=pastas / "dados", responsavel="teste")


def _pendente(resultado, numero):
    livro = openpyxl.load_workbook(resultado.planilha)
    return next(l for l in livro["Pendentes"].iter_rows(min_row=2,
                                                       values_only=True)
                if str(l[0]) == numero)


def test_a_carga_do_portal_longo_tira_o_sem_cadastro_da_semana(pastas):
    longo = relatorio(pastas / "Cabecalho_da_Nota.xlsx", COLUNAS_PORTAL, [
        _pedido(10, ANTIGO, codigo_do_parceiro="7007",
                nome_do_parceiro="ANTIGO LTDA", comprador="ANA",
                negociacao="15/12/2025"),
    ])
    assert historico.e_portal_de_compras(longo)
    carga = historico.carregar_relatorios([longo], raiz=pastas / "dados",
                                          responsavel="teste")
    assert "1 parceiro(s)" in carga.titulo()

    resultado = _semana(pastas, "1", [linha_portal(1, "1", DA_SEMANA, 10.0)])
    linha = _pendente(resultado, "3003")
    assert linha[2] == "7007"
    assert linha[3] == "ANTIGO LTDA"
    assert linha[11] == "ANA"                      # Ultimo Comprador
    assert resultado.parceiros_pelo_historico == 1
    assert resultado.pedidos_pelo_historico == 1


def test_cada_semana_ensina_a_seguinte(pastas):
    """O Portal de uma semana fica; a seguinte, mesmo sem o parceiro, o acha."""
    primeira = _semana(pastas, "1", [
        linha_portal(1, "1", DA_SEMANA, 10.0),
        _pedido(2, ANTIGO, codigo_do_parceiro="7007"),
    ])
    assert _pendente(primeira, "3003")[2] == "7007"

    segunda = _semana(pastas, "2", [linha_portal(3, "1", DA_SEMANA, 10.0)])
    assert _pendente(segunda, "3003")[2] == "7007"
    assert segunda.parceiros_pelo_historico == 1


@pytest.mark.parametrize("cnpj_no_livro, migra", [
    ("", True),                 # veio da planilha devolvida, sem CNPJ
    (ANTIGO, True),             # o livro já sabia que era este prestador
    ("12345678000190", False),  # era outro prestador com o mesmo número
])
def test_a_classificacao_da_chave_sem_cadastro_passa_para_o_codigo(
        pastas, cnpj_no_livro, migra):
    """O Guardião escrito quando a nota era `Sem cadastro` não se perde."""
    primeira = _semana(pastas, "1", [linha_portal(1, "1", DA_SEMANA, 10.0)])
    assert _pendente(primeira, "3003")[2] == "Sem cadastro"

    from pendentes import estado
    livro = estado.carregar("servicos", raiz=pastas / "dados")
    livro.registros["3003|Sem cadastro"] = estado.Classificacao(
        "3003|Sem cadastro", guardiao="Suprimentos", cnpj=cnpj_no_livro)
    estado.gravar(livro, "teste", raiz=pastas / "dados")

    longo = relatorio(pastas / "Longo.xlsx", COLUNAS_PORTAL, [
        _pedido(10, ANTIGO, codigo_do_parceiro="7007")])
    historico.carregar_relatorios([longo], raiz=pastas / "dados")

    segunda = _semana(pastas, "2", [linha_portal(3, "1", DA_SEMANA, 10.0)])
    linha = _pendente(segunda, "3003")
    assert linha[2] == "7007"
    assert (linha[4] or "") == ("Suprimentos" if migra else "")
    assert segunda.classificacoes_migradas == (1 if migra else 0)


def test_o_confronto_continua_so_com_o_portal_da_semana(pastas):
    """Lançamento antigo no histórico não transforma pendente em lançada."""
    longo = relatorio(pastas / "Longo.xlsx", COLUNAS_PORTAL, [
        linha_portal(10, "3003", ANTIGO, 90.00, codigo_do_parceiro="7007")])
    historico.carregar_relatorios([longo], raiz=pastas / "dados")

    resultado = _semana(pastas, "1", [linha_portal(1, "1", DA_SEMANA, 10.0)])
    assert resultado.lancadas == 0 and resultado.pendentes == 1


def test_a_semana_nao_e_confundida_com_portal_de_compras(pastas):
    asis = relatorio(pastas / "ASIS.xlsx", COLUNAS_ASIS,
                     [linha_asis("1", DA_SEMANA, "1.00")])
    assert not historico.e_portal_de_compras(asis)
