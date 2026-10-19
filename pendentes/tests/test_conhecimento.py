"""A base que propõe: o cruzamento entre a lista curada e o histórico medido.

Os dois arquivos de entrada são montados aqui, com parceiro e área
inventados — regra nº 1. O que estes testes provam é a fronteira que dá nome
ao módulo: **propor não é classificar**. Só o que a lista e o histórico
afirmam juntos, com lastro, pode preencher célula; todo o resto é sugestão, e
a sugestão carrega o motivo de não ser mais do que isso.

A medição contra o relatório real da semana 38 está em
`docs/pendentes/08-base-de-conhecimento.md` — ela não cabe em teste porque
depende de arquivo que não entra no repositório.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from pendentes.conhecimento import base as bc
from pendentes.conhecimento import simulacao
from pendentes.conhecimento.importacao import (ArquivoNaoReconhecido,
                                               cfop_normalizado, importar)
from pendentes.mercadorias import colunas as merc

CABECALHO = ("Código parceiro;Parceiro;Unidade (vazio = geral);"
             "Guardião sugerido;Gestor atual;Categoria sugerida;"
             "Notas guardião;Notas categoria;Concordância categoria")


def csv_de(linhas, caminho: Path) -> Path:
    caminho.write_text("﻿" + "\n".join([CABECALHO, *linhas]),
                       encoding="utf-8")
    return caminho


def regra(**campos) -> dict:
    padrao = {"tipo": "parceiro", "campo": "guardiao", "codigo_parceiro": "1",
              "unidade": "", "valor": "", "total": 1, "apoio": 1,
              "semanas": 1, "alternativas": "", "status": ""}
    return {**padrao, **campos}


def json_de(regras, caminho: Path, **extras) -> Path:
    caminho.write_text(json.dumps(
        {"versao": "2026-09-17", "ultimo_relatorio_classificado": 37,
         "regras": regras, **extras}, ensure_ascii=False), encoding="utf-8")
    return caminho


@pytest.fixture()
def base(tmp_path) -> bc.Conhecimento:
    """Um parceiro com histórico firme, um com evidência curta, um em conflito."""
    lista = csv_de([
        "1;ALFA COMERCIO LTDA;;Almoxarifado;Tavares;Indiretos;9;9;1.0",
        "2;BETA INDUSTRIA SA;;Manutenção;Gleyson;Diretos;1;1;1.0",
        "3;GAMA SERVICOS ME;;Suprimentos;Anderson;Indiretos;8;8;1.0",
    ], tmp_path / "parceiros.csv")
    regras = [
        # 1 — a lista e o histórico dizem o mesmo, com lastro de sobra
        regra(codigo_parceiro="1", campo="guardiao", valor="Almoxarifado",
              total=9, apoio=9, semanas=4, alternativas="Almoxarifado: 9"),
        regra(codigo_parceiro="1", campo="categoria", valor="Indiretos",
              total=9, apoio=9, semanas=4, alternativas="Indiretos: 9"),
        # 2 — concordam, mas com uma nota só
        regra(codigo_parceiro="2", campo="guardiao", valor="Manutenção",
              total=1, apoio=1, semanas=1, alternativas="Manutenção: 1"),
        regra(codigo_parceiro="2", campo="categoria", valor="Diretos",
              total=1, apoio=1, semanas=1, alternativas="Diretos: 1"),
        # 3 — o histórico guarda o nome de uma pessoa, a lista propõe a área
        regra(codigo_parceiro="3", campo="guardiao", valor="Joana M.",
              total=8, apoio=5, semanas=3,
              alternativas="Joana M.: 5 | Almoxarifado: 3"),
        regra(codigo_parceiro="3", campo="categoria", valor="Indiretos",
              total=8, apoio=8, semanas=3, alternativas="Indiretos: 8"),
    ]
    relato = importar([lista, json_de(regras, tmp_path / "regras.json")],
                      raiz=tmp_path / "dados")
    return relato.conhecimento


# -- o cruzamento -----------------------------------------------------------

def test_lista_e_historico_de_acordo_com_lastro_podem_preencher(base):
    proposta = base.propor("1", "guardiao")
    assert proposta.valor == "Almoxarifado"
    assert proposta.confianca == bc.FIRME
    assert proposta.lastro == bc.LASTRO_CONFIRMA
    assert proposta.pode_preencher


def test_de_acordo_mas_com_evidencia_curta_e_so_sugestao(base):
    proposta = base.propor("2", "guardiao")
    assert proposta.valor == "Manutenção"
    assert proposta.confianca == bc.SUGESTAO
    assert proposta.lastro == bc.LASTRO_CURTO
    assert not proposta.pode_preencher


def test_proposta_que_o_historico_contradiz_nunca_preenche(base):
    """O caso do nome de pessoa trocado pela área: a proposta é boa, o
    histórico não a sustenta, e por isso ela não entra sozinha na planilha."""
    proposta = base.propor("3", "guardiao")
    assert proposta.valor == "Suprimentos"
    assert proposta.confianca == bc.SUGESTAO
    assert proposta.evidencia.valor == "Joana M."
    assert proposta.evidencia.alternativas == {"Joana M.": 5, "Almoxarifado": 3}


def test_parceiro_desconhecido_responde_que_nao_sabe(base):
    proposta = base.propor("999", "guardiao")
    assert not proposta
    assert proposta.confianca == bc.SEM_PROPOSTA


def test_tres_notas_em_duas_semanas_e_o_limiar_e_esta_escrito(tmp_path):
    """O limiar da fonte, em números: três notas distintas, em duas semanas."""
    def firme(total, semanas):
        lista = csv_de([f"1;ALFA;;Almoxarifado;Tavares;Indiretos;{total};{total};1.0"],
                       tmp_path / "p.csv")
        regras = [regra(campo="guardiao", valor="Almoxarifado", total=total,
                        apoio=total, semanas=semanas,
                        alternativas=f"Almoxarifado: {total}")]
        conhecimento = importar([lista, json_de(regras, tmp_path / "r.json")],
                                raiz=tmp_path / "dados").conhecimento
        return conhecimento.propor("1", "guardiao").confianca

    assert firme(3, 2) == bc.FIRME
    assert firme(2, 2) == bc.SUGESTAO      # notas de menos
    assert firme(3, 1) == bc.SUGESTAO      # semanas de menos


# -- a precedência ----------------------------------------------------------

def test_parceiro_mais_unidade_vence_parceiro(tmp_path):
    lista = csv_de([
        "1;ALFA;;Almoxarifado;Tavares;Indiretos;9;9;1.0",
        "1;ALFA;HINOVE  (REGISTRO);Balança Registro;Tavares;Diretos;9;9;1.0",
    ], tmp_path / "p.csv")
    regras = [
        regra(campo="guardiao", valor="Almoxarifado", total=9, apoio=9,
              semanas=4, alternativas="Almoxarifado: 9"),
        regra(tipo="parceiro_unidade", unidade="HINOVE  (REGISTRO)",
              campo="guardiao", valor="Balança Registro", total=9, apoio=9,
              semanas=4, alternativas="Balança Registro: 9"),
    ]
    base = importar([lista, json_de(regras, tmp_path / "r.json")],
                    raiz=tmp_path / "dados").conhecimento

    especifica = base.propor("1", "guardiao", "Hinove (Registro)")
    assert especifica.valor == "Balança Registro"
    assert especifica.nivel == "parceiro + unidade"
    # O espaço duplo do relatório não impede o casamento.
    assert base.propor("1", "guardiao", "HINOVE  (REGISTRO)").valor == \
        "Balança Registro"
    # Outra unidade cai na regra geral do parceiro.
    assert base.propor("1", "guardiao", "HINOVE (MATRIZ)").valor == "Almoxarifado"


def test_o_conjunto_de_cfop_casa_por_correspondencia_exata(tmp_path):
    regras = [
        regra(tipo="operacao", campo="operacao", nivel="CFOP", cfop="5102",
              codigo_parceiro="", valor="Compra Uso e Consumo", total=20,
              apoio=20, semanas=9, alternativas="Compra Uso e Consumo: 20"),
        regra(tipo="operacao", campo="operacao", nivel="CFOP", cfop="5102+5405",
              codigo_parceiro="", valor="Compra Embalagem", total=5, apoio=5,
              semanas=3, alternativas="Compra Embalagem: 5"),
    ]
    base = importar([json_de(regras, tmp_path / "r.json")],
                    raiz=tmp_path / "dados").conhecimento

    assert base.propor_operacao("5102").valor == "Compra Uso e Consumo"
    # A nota com dois CFOP não herda a regra de um deles.
    assert base.propor_operacao(cfop_normalizado("5405, 5102")).valor == \
        "Compra Embalagem"
    assert not base.propor_operacao("6102")


def test_o_cfop_do_relatorio_chega_em_duas_formas_e_sai_numa(tmp_path):
    assert cfop_normalizado(5102) == "5102"
    assert cfop_normalizado("5405, 5102") == "5102+5405"
    assert cfop_normalizado("5102+5405") == "5102+5405"
    assert cfop_normalizado("") == ""


def test_o_nivel_mais_especifico_de_operacao_vence(tmp_path):
    regras = [
        regra(tipo="operacao", campo="operacao", cfop="5102", codigo_parceiro="",
              valor="Compra Uso e Consumo", total=20, apoio=20, semanas=9,
              alternativas="Compra Uso e Consumo: 20"),
        regra(tipo="operacao", campo="operacao", cfop="5102",
              codigo_parceiro="7", valor="Compra MP", total=6, apoio=6,
              semanas=3, alternativas="Compra MP: 6"),
    ]
    base = importar([json_de(regras, tmp_path / "r.json")],
                    raiz=tmp_path / "dados").conhecimento
    assert base.propor_operacao("5102", "7").nivel == "CFOP + parceiro"
    assert base.propor_operacao("5102", "7").valor == "Compra MP"
    assert base.propor_operacao("5102", "9").nivel == "CFOP"


# -- o gestor ---------------------------------------------------------------

def test_o_gestor_vigente_firma_por_ausencia_de_empate(tmp_path):
    regras = [
        regra(tipo="guardiao_gestor_atual", campo="gestor",
              guardiao_condicao="Manutenção Guará", valor="Gleyson",
              total=18, apoio=17, semanas=1,
              alternativas="Gleyson: 17 | Anderson: 1"),
        regra(tipo="guardiao_gestor_atual", campo="gestor",
              guardiao_condicao="Facilities", valor="Ana", total=2, apoio=1,
              semanas=1, alternativas="Ana: 1 | Bruno: 1"),
    ]
    base = importar([json_de(regras, tmp_path / "r.json")],
                    raiz=tmp_path / "dados").conhecimento

    # Minoritário não bloqueia: 17 contra 1 é escolha, não empate.
    assert base.gestor_de("Manutenção Guará").confianca == bc.FIRME
    assert base.gestor_de("manutencao guara").valor == "Gleyson"
    # Empate, sim, bloqueia.
    assert base.gestor_de("Facilities").confianca == bc.SUGESTAO


# -- o que a importação recusa ---------------------------------------------

def test_categoria_fora_das_duas_nao_vira_proposta_e_vira_aviso(tmp_path):
    lista = csv_de(["1;ALFA;;Almoxarifado;Tavares;Serviços;9;9;1.0"],
                   tmp_path / "p.csv")
    relato = importar([lista], raiz=tmp_path / "dados")
    assert not relato.conhecimento.propor("1", "categoria")
    assert any("categoria fora de" in aviso for aviso in relato.avisos)


def test_a_lista_de_guardioes_que_valida_a_semana_nao_e_preenchida_daqui(base):
    """Encher a lista de validação daqui faria a semana seguinte bloquear em
    cima de nome que ninguém conferiu. Os observados ficam registrados."""
    assert base.guardioes_observados == ["Almoxarifado", "Manutenção",
                                         "Suprimentos"]


def test_arquivo_que_nao_e_nem_um_nem_outro_aborta_dizendo_o_que_esperava(tmp_path):
    qualquer = tmp_path / "qualquer.txt"
    qualquer.write_text("nada disso", encoding="utf-8")
    with pytest.raises(ArquivoNaoReconhecido) as erro:
        importar([qualquer], raiz=tmp_path / "dados")
    assert "lista de parceiros" in str(erro.value)


def test_sem_o_historico_nada_chega_a_firme(tmp_path):
    lista = csv_de(["1;ALFA;;Almoxarifado;Tavares;Indiretos;9;9;1.0"],
                   tmp_path / "p.csv")
    relato = importar([lista], raiz=tmp_path / "dados")
    assert relato.conhecimento.propor("1", "guardiao").confianca == bc.SUGESTAO
    assert any("regras medidas não vieram" in aviso for aviso in relato.avisos)


def test_a_importacao_carimba_de_onde_veio_e_com_que_impressao(base, tmp_path):
    assert base.versao_da_fonte == "2026-09-17"
    assert base.ultimo_relatorio_classificado == 37
    assert base.importado_em and base.importado_por
    assert {f["nome"] for f in base.fontes} == {"parceiros.csv", "regras.json"}
    assert all(len(f["sha256"]) == 64 for f in base.fontes)


def test_a_base_vai_para_fora_do_git_e_volta_igual(tmp_path):
    lista = csv_de(["1;ALFA;;Almoxarifado;Tavares;Indiretos;9;9;1.0"],
                   tmp_path / "p.csv")
    regras = [regra(campo="guardiao", valor="Almoxarifado", total=9, apoio=9,
                    semanas=4, alternativas="Almoxarifado: 9")]
    relato = importar([lista, json_de(regras, tmp_path / "r.json")],
                      raiz=tmp_path / "dados")
    assert relato.caminho.parts[-3:] == ("pendentes", "conhecimento",
                                         "mercadorias.json")
    relida = bc.carregar(raiz=tmp_path / "dados")
    assert relida.propor("1", "guardiao").confianca == bc.FIRME


def test_sem_base_no_disco_nada_e_proposto(tmp_path):
    vazia = bc.carregar(raiz=tmp_path / "nao-existe")
    assert len(vazia) == 0
    assert not vazia.propor("1", "guardiao")
    assert not vazia.gestor_de("Almoxarifado")


# -- a medição --------------------------------------------------------------

def relatorio_classificado(caminho: Path, linhas) -> Path:
    import openpyxl

    livro = openpyxl.Workbook()
    livro.remove(livro.active)
    aba = livro.create_sheet("Pendentes")
    rotulos = [c.rotulo for c in merc.pendentes(38)]
    aba.append(rotulos)
    for dados in linhas:
        linha = ["" for _ in rotulos]
        for rotulo, valor in dados.items():
            linha[rotulos.index(rotulo)] = valor
        aba.append(linha)
    livro.save(str(caminho))
    return caminho


def test_a_simulacao_separa_acerto_firme_de_acerto_sugerido(base, tmp_path):
    arquivo = relatorio_classificado(tmp_path / "Pendentes38.xlsx", [
        {merc.X_NRO_NOTA: "1", merc.X_COD_PARCEIRO: 1,
         merc.C_GUARDIAO: "Almoxarifado", merc.C_CATEGORIA: "Indiretos"},
        {merc.X_NRO_NOTA: "2", merc.X_COD_PARCEIRO: 2,
         merc.C_GUARDIAO: "Manutenção", merc.C_CATEGORIA: "Diretos"},
    ])
    medida = simulacao.simular([arquivo], base, semana=38)
    assert medida.linhas == 2
    assert medida.placares["guardiao"].acertos == {bc.FIRME: 1, bc.SUGESTAO: 1}
    assert medida.placares["guardiao"].taxa(bc.FIRME) == 1.0


def test_a_simulacao_avisa_quando_mede_a_base_contra_semana_que_ela_viu(
        base, tmp_path):
    arquivo = relatorio_classificado(tmp_path / "Pendentes37.xlsx", [
        {merc.X_NRO_NOTA: "1", merc.X_COD_PARCEIRO: 1,
         merc.C_GUARDIAO: "Almoxarifado", merc.C_CATEGORIA: "Indiretos"},
    ])
    medida = simulacao.simular([arquivo], base, semana=37)
    assert any("já viu" in aviso for aviso in medida.avisos)


def test_a_simulacao_nomeia_o_erro_cometido_com_evidencia_firme(base, tmp_path):
    arquivo = relatorio_classificado(tmp_path / "Pendentes38.xlsx", [
        {merc.X_NRO_NOTA: "77", merc.X_COD_PARCEIRO: 1,
         merc.C_GUARDIAO: "Facilities", merc.C_CATEGORIA: "Indiretos"},
    ])
    medida = simulacao.simular([arquivo], base, semana=38)
    assert medida.placares["guardiao"].erros == {bc.FIRME: 1}
    assert "nota 77" in medida.placares["guardiao"].erros_firmes[0]


def test_linha_sem_o_campo_preenchido_nao_e_gabarito_de_nada(base, tmp_path):
    arquivo = relatorio_classificado(tmp_path / "Pendentes38.xlsx", [
        {merc.X_NRO_NOTA: "1", merc.X_COD_PARCEIRO: 1, merc.C_GUARDIAO: "",
         merc.C_CATEGORIA: "Indiretos"},
    ])
    medida = simulacao.simular([arquivo], base, semana=38)
    assert medida.placares["guardiao"].total(bc.FIRME) == 0
    assert medida.placares["categoria"].total(bc.FIRME) == 1


def test_sem_relatorio_classificado_a_simulacao_aborta(base, tmp_path):
    arquivo = relatorio_classificado(tmp_path / "Pendentes38.xlsx", [])
    with pytest.raises(simulacao.SemRelatorioClassificado):
        simulacao.simular([arquivo], base)
