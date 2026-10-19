"""A tela de parâmetros das pendentes e a consulta das bases.

Tudo numa pasta de dados descartável (`HINOVE_DADOS`): a tela grava a base
viva, e o teste não pode gravar na de quem o roda.
"""
from __future__ import annotations

import pytest

from pendentes import configuracao, parametros
from pendentes.conhecimento import base as conhecido
from pendentes.conhecimento import consulta
from pendentes.servicos import historico


@pytest.fixture(autouse=True)
def dados(tmp_path, monkeypatch):
    monkeypatch.setenv("HINOVE_DADOS", str(tmp_path))
    return tmp_path


def _problemas(problemas, gravidade):
    return [p for p in problemas if p["gravidade"] == gravidade]


UNIDADES = [
    {"ordem": 1, "trecho": "MATRIZ-FILIAIS", "unidade": "Matriz-Filiais"},
    {"ordem": 2, "trecho": "CORUMB", "unidade": "Corumbá"},
    {"ordem": 3, "trecho": "MATRIZ", "unidade": "Matriz"},
]


# -- ida e volta --------------------------------------------------------------

def test_a_carga_de_fabrica_volta_da_tela_sem_erro():
    """O que a tela mostra, gravado sem mexer, é uma base válida."""
    gravou, problemas = configuracao.gravar(configuracao.ler(), "teste")
    assert gravou, problemas
    assert parametros.caminho_da_base().is_file()


def test_as_secoes_e_os_dados_tem_as_mesmas_chaves():
    tela = configuracao.ler()
    for secao in configuracao.secoes():
        assert secao["id"] in tela
        chaves = {c["chave"] for c in secao["campos"]}
        for linha in tela[secao["id"]]:
            assert set(linha) == chaves, secao["id"]


def test_unidades_gravadas_chegam_ao_motor():
    tela = configuracao.ler()
    tela["unidades"] = UNIDADES
    gravou, _ = configuracao.gravar(tela, "teste")
    assert gravou
    assert [u["trecho"] for u in parametros.unidades(parametros.carregar())] == [
        "MATRIZ-FILIAIS", "CORUMB", "MATRIZ"]


def test_o_que_a_tela_nao_mostra_continua_no_arquivo():
    """Gravar mescla: roteamento, papéis e farol não somem."""
    antes = parametros.carregar()
    tela = configuracao.ler()
    tela["guardioes"] = [{"guardiao": "Suprimentos"}]
    assert configuracao.gravar(tela, "teste")[0]
    depois = parametros.carregar()
    for secao in ("roteamento", "papeis", "farol", "mercadorias"):
        assert depois[secao] == antes[secao], secao
    assert depois["guardioes"] == ["Suprimentos"]
    assert depois["atualizado_por"] == "teste"


# -- o que impede gravar ---------------------------------------------------

def test_ordem_repetida_nas_unidades_nao_grava():
    tela = configuracao.ler()
    tela["unidades"] = [dict(UNIDADES[0]), {**UNIDADES[1], "ordem": 1}]
    gravou, problemas = configuracao.gravar(tela, "teste")
    assert not gravou
    assert any("repetida" in p["mensagem"] for p in _problemas(problemas, "erro"))
    assert not parametros.caminho_da_base().is_file()


def test_trecho_que_nunca_casa_vira_aviso_e_grava():
    tela = configuracao.ler()
    tela["unidades"] = [{"ordem": 1, "trecho": "MATRIZ", "unidade": "Matriz"},
                        {"ordem": 2, "trecho": "MATRIZ-FILIAIS",
                         "unidade": "Matriz-Filiais"}]
    gravou, problemas = configuracao.gravar(tela, "teste")
    assert gravou
    avisos = _problemas(problemas, "aviso")
    assert any("MATRIZ-FILIAIS" in p["onde"] and "nunca vai casar" in p["mensagem"]
               for p in avisos)


def test_cnpj_de_filial_curto_nao_grava():
    tela = configuracao.ler()
    tela["filiais"] = [{"cnpj": "14.031.191/0001-6", "codigo": "1", "nome": "X"}]
    gravou, problemas = configuracao.gravar(tela, "teste")
    assert not gravou
    assert "14 dígitos" in _problemas(problemas, "erro")[0]["mensagem"]


def test_cnpj_de_filial_e_gravado_so_com_digitos():
    tela = configuracao.ler()
    tela["filiais"] = [{"cnpj": "11.222.333/0001-44", "codigo": "1", "nome": "X"}]
    assert configuracao.gravar(tela, "teste")[0]
    assert parametros.filiais(parametros.carregar())[0]["cnpj"] == "11222333000144"


@pytest.mark.parametrize("valor, grava", [
    ("sugestao", True), ("Sugestão", True), ("NÃO", True), ("talvez", False)])
def test_pre_categorizacao_so_aceita_os_tres_graus(valor, grava):
    tela = configuracao.ler()
    tela["pre_categorizacao"][0]["guardiao"] = valor
    assert configuracao.gravar(tela, "teste")[0] is grava


def test_multiplo_minimo_maior_que_o_maximo_nao_grava():
    tela = configuracao.ler()
    tela["confronto_servicos"][0].update(multiplo_minimo="13", multiplo_maximo="12")
    assert not configuracao.gravar(tela, "teste")[0]


def test_sem_top_de_lancamento_nao_grava():
    tela = configuracao.ler()
    tela["confronto_servicos"][0]["tops_de_lancamento"] = " ; "
    assert not configuracao.gravar(tela, "teste")[0]


def test_tolerancia_com_virgula_e_entendida():
    tela = configuracao.ler()
    tela["confronto_servicos"][0]["tolerancia_da_razao"] = "0,01"
    assert configuracao.gravar(tela, "teste")[0]
    assert parametros.confronto_de_servicos(
        parametros.carregar())["tolerancia_da_razao"] == 0.01


def test_semana_fixada_grava_com_aviso():
    tela = configuracao.ler()
    tela["semana"][0]["numero"] = "40"
    gravou, problemas = configuracao.gravar(tela, "teste")
    assert gravou and _problemas(problemas, "aviso")
    assert parametros.semana_de(parametros.carregar())[1] == 40


def test_semana_fora_do_ano_nao_grava():
    tela = configuracao.ler()
    tela["semana"][0]["numero"] = "60"
    assert not configuracao.gravar(tela, "teste")[0]


# -- sinônimos -------------------------------------------------------------

def test_sinonimo_cadastrado_chega_a_exigencia_da_coluna():
    tela = configuracao.ler()
    linha = next(l for l in tela["sinonimos"]
                 if l["coluna"] == "Valor NFe" and l["fonte"].startswith("ASIS"))
    linha["sinonimos"] = "Valor da NFS-e; Vlr NFSe"
    assert configuracao.gravar(tela, "teste")[0]
    exigencia = next(e for e in parametros.colunas_de(parametros.carregar(), "asis")
                     if e.nome == "Valor NFe")
    assert exigencia.sinonimos == ("Valor da NFS-e", "Vlr NFSe")


def test_linha_de_sinonimo_para_coluna_que_nao_existe_nao_grava():
    tela = configuracao.ler()
    tela["sinonimos"].append({"fonte": "ASIS (serviços)", "coluna": "Inventada",
                              "sinonimos": "x"})
    gravou, problemas = configuracao.gravar(tela, "teste")
    assert not gravou
    assert "não tem a coluna" in _problemas(problemas, "erro")[0]["mensagem"]


def test_remover_a_linha_de_sinonimo_nao_apaga_a_coluna():
    tela = configuracao.ler()
    tela["sinonimos"] = []
    assert configuracao.gravar(tela, "teste")[0]
    assert parametros.colunas_de(parametros.carregar(), "asis")


# -- unidades × histórico ----------------------------------------------------

def test_filial_do_historico_sem_unidade_vira_aviso():
    memoria = historico.Historico(filiais={
        "11222333000144": {"nome": "HINOVE (LONDRINA)", "codigo": "7"}})
    historico.gravar(memoria, "teste")
    tela = configuracao.ler()
    tela["unidades"] = UNIDADES
    gravou, problemas = configuracao.gravar(tela, "teste")
    assert gravou
    assert any("LONDRINA" in p["mensagem"] for p in _problemas(problemas, "aviso"))


# -- a consulta das bases ------------------------------------------------------

def test_a_consulta_com_as_bases_vazias_nao_quebra():
    tela = consulta.ler()
    assert tela["portal"][0]["periodo"] == "vazio"
    assert tela["mercadorias"][0]["importado_em"] == "nunca importada"
    assert all(s.get("somente_leitura") for s in consulta.secoes())


def test_a_consulta_mostra_o_historico_do_portal():
    memoria = historico.Historico(
        parceiros={"12345678000190": {"codigo": "7007", "nome": "ANTIGO LTDA",
                                      "numero_unico": 10.0,
                                      "visto_em": "2025-12-15"}},
        pedidos={"12345678000190": {"numero_unico": 10.0, "comprador": "ANA",
                                    "data": "2025-12-15"}})
    historico.gravar(memoria, "teste")
    tela = consulta.ler()
    assert tela["portal"][0]["parceiros"] == 1
    assert tela["portal_parceiros"][0]["cnpj"] == "12.345.678/0001-90"
    pedido = tela["portal_pedidos"][0]
    assert pedido["parceiro"] == "7007 — ANTIGO LTDA"
    assert pedido["numero_unico"] == 10


def test_a_consulta_mostra_a_base_de_mercadorias_com_o_grau():
    base = conhecido.Conhecimento(
        parceiros={"4": {"nome": "FORNECEDOR ALFA",
                         "guardiao": {"proposto": "Suprimentos",
                                      "evidencia": {"valor": "Suprimentos",
                                                    "notas": 5, "apoio": 5,
                                                    "semanas": 3}},
                         "categoria": {"proposto": "Indiretos"}}},
        importado_em="2026-09-22 10:00:00")
    conhecido.gravar(base)
    linha = consulta.ler()["mercadorias_parceiros"][0]
    assert linha["guardiao"] == "Suprimentos" and linha["grau_guardiao"] == "firme"
    assert linha["categoria"] == "Indiretos"
    assert linha["grau_categoria"] == "sugestao"
