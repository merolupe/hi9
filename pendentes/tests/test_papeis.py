"""O reconhecimento de papel: ordem trocada, papel duplicado, papel ausente."""
from __future__ import annotations

import pytest

from conftest import escrever
from pendentes import parametros
from pendentes.papeis import (PapelAmbiguo, PapelAusente, PapelDuplicado,
                              ler_e_reconhecer)

PAPEIS = parametros.papeis_de(parametros.carregar_fabrica(), "mercadorias")


def test_a_ordem_de_arrastar_nao_importa(arquivo_xml, arquivo_ce,
                                         arquivo_semana_anterior):
    """É o problema que o desenho resolve por construção."""
    direta = [arquivo_xml, arquivo_ce, arquivo_semana_anterior]
    trocada = [arquivo_semana_anterior, arquivo_ce, arquivo_xml]

    primeira, _ = ler_e_reconhecer(direta, PAPEIS)
    segunda, _ = ler_e_reconhecer(trocada, PAPEIS)

    for reconhecimento in (primeira, segunda):
        assert reconhecimento["xml"].arquivo.nome == arquivo_xml.name
        assert reconhecimento["conferencia_de_entradas"].arquivo.nome == \
            arquivo_ce.name
        assert reconhecimento["semana_anterior_mercadorias"].arquivo.nome == \
            arquivo_semana_anterior.name


def test_a_planilha_da_semana_anterior_nao_e_confundida_com_o_xml(
        arquivo_semana_anterior):
    """Ela tem todas as colunas do XML; só a ausência de `Guardião` separa."""
    reconhecimento, _ = ler_e_reconhecer([arquivo_semana_anterior],
                                         [p for p in PAPEIS
                                          if not p.obrigatorio])
    assert reconhecimento.tem("semana_anterior_mercadorias")
    assert not reconhecimento.tem("xml")


def test_o_cabecalho_e_achado_fora_da_primeira_linha(arquivo_xml, arquivo_ce):
    """Os dois relatórios do Sankhya trazem título e data antes do cabeçalho."""
    reconhecimento, _ = ler_e_reconhecer([arquivo_xml, arquivo_ce], PAPEIS)
    assert reconhecimento["xml"].linha_do_cabecalho == 2
    assert reconhecimento["xml"].cabecalho[0] == "Nro Nota"
    assert len(reconhecimento["xml"].dados) == 2


def test_dois_arquivos_com_o_mesmo_papel_abortam_nomeando_os_dois(
        tmp_path, arquivo_xml, arquivo_ce):
    copia = tmp_path / "XML30 (1).xlsx"
    copia.write_bytes(arquivo_xml.read_bytes())

    with pytest.raises(PapelDuplicado) as erro:
        ler_e_reconhecer([arquivo_xml, copia, arquivo_ce], PAPEIS)

    assert "XML30.xlsx" in str(erro.value)
    assert "XML30 (1).xlsx" in str(erro.value)


def test_papel_obrigatorio_ausente_aborta_dizendo_quais_colunas_procurou(
        arquivo_xml):
    with pytest.raises(PapelAusente) as erro:
        ler_e_reconhecer([arquivo_xml], PAPEIS)

    mensagem = str(erro.value)
    assert "Conferência de Entradas" in mensagem
    assert "Motivo Incongruência" in mensagem


def test_papel_opcional_ausente_degrada_com_aviso_contado(arquivo_xml,
                                                          arquivo_ce):
    """Rodar sem a semana anterior deixou de ser erro — o livro guarda o estado."""
    reconhecimento, _ = ler_e_reconhecer([arquivo_xml, arquivo_ce], PAPEIS)

    assert reconhecimento.tem("xml")
    assert not reconhecimento.tem("semana_anterior_mercadorias")
    assert [p.id for p in reconhecimento.ausentes] == \
        ["semana_anterior_mercadorias"]
    assert any("planilha da semana anterior" in aviso
               for aviso in reconhecimento.avisos)


def test_arquivo_que_nao_casa_com_papel_nenhum_entra_na_lista_de_avisos(
        tmp_path, arquivo_xml, arquivo_ce):
    estranho = escrever(tmp_path / "Relatorio.xlsx",
                        {"Plan1": [["Coluna A", "Coluna B"], [1, 2]]})

    reconhecimento, _ = ler_e_reconhecer([arquivo_xml, arquivo_ce, estranho],
                                         PAPEIS)

    assert reconhecimento.nao_reconhecidos == ("Relatorio.xlsx",)
    assert any("Relatorio.xlsx" in aviso for aviso in reconhecimento.avisos)


def test_arquivo_que_serve_a_dois_papeis_aborta_em_vez_de_escolher(
        tmp_path, arquivo_ce):
    """Regra nº 4: nada é decidido por semelhança."""
    from pendentes.papeis import Papel

    dois = (
        Papel("um", "primeiro relatório", ("Chave Acesso",)),
        Papel("outro", "segundo relatório", ("Conf. Fiscal",)),
    )
    with pytest.raises(PapelAmbiguo) as erro:
        ler_e_reconhecer([arquivo_ce], dois)
    assert arquivo_ce.name in str(erro.value)


def test_o_papel_que_exige_aba_so_casa_naquela_aba(tmp_path):
    from pendentes.papeis import Papel

    papel = Papel("anterior", "planilha da semana anterior",
                  ("Chave Acesso", "Guardião"), obrigatorio=False,
                  aba="Pendentes")
    fora = escrever(tmp_path / "Outra.xlsx",
                    {"Resumo": [["Chave Acesso", "Guardião"], ["1", "Fiscal"]]})
    dentro = escrever(tmp_path / "Certa.xlsx",
                      {"Pendentes": [["Chave Acesso", "Guardião"], ["1", "Fiscal"]]})

    assert not ler_e_reconhecer([fora], [papel])[0].tem("anterior")
    assert ler_e_reconhecer([dentro], [papel])[0].tem("anterior")


# -- serviços: quatro papéis, dois obrigatórios ----------------------------

PAPEIS_DE_SERVICOS = parametros.papeis_de(parametros.carregar_fabrica(),
                                          "servicos")

COLUNAS_ASIS = ["Numero NFe", "Data Emissao NFe", "Data Cancelamento",
                "Prestador", "CNPJ/CPF Prestador", "Valor NFe",
                "Discriminacao", "CNPJ/CPF Tomador", "Numero RPS",
                "Codigo Verificador"]
COLUNAS_PC = ["Nro. Unico", "Nro. Nota", "Parceiro",
              "Nome Parceiro (Parceiro)", "Vlr. Nota", "Empresa",
              "Tipo Operacao", "CNPJ / CPF Parceiro", "CNPJ Empresa",
              "Dt. Neg."]
COLUNAS_PENDENTES_SERVICOS = ["Nro Nota", "Emissao", "Cod Parceiro",
                              "Parceiro", "Guardiao", "Gestor de apoio",
                              "Retorno", "Codigo Verificador"]


def test_os_quatro_papeis_de_servicos_sao_reconhecidos(tmp_path):
    asis = escrever(tmp_path / "ASIS.xlsx", {"Plan1": [COLUNAS_ASIS]})
    pc = escrever(tmp_path / "PC27.xlsx", {"Plan1": [COLUNAS_PC]})
    anterior = escrever(tmp_path / "Notas_Servico_Pendentes.xlsx",
                        {"Lancadas": [["Nro. Nota"]],
                         "Pendentes": [COLUNAS_PENDENTES_SERVICOS]})

    reconhecimento, _ = ler_e_reconhecer([anterior, pc, asis],
                                         PAPEIS_DE_SERVICOS)

    assert reconhecimento["asis"].arquivo.nome == "ASIS.xlsx"
    assert reconhecimento["portal_de_compras"].arquivo.nome == "PC27.xlsx"
    assert reconhecimento["semana_anterior_servicos"].aba.nome == "Pendentes"
    assert [p.id for p in reconhecimento.ausentes] == \
        ["conferencia_de_servicos"]


def test_a_semana_anterior_de_servicos_nao_e_confundida_com_o_asis(tmp_path):
    """Ela tem `Codigo Verificador`, mas não `Numero NFe` nem `Discriminacao`."""
    anterior = escrever(tmp_path / "Anterior.xlsx",
                        {"Pendentes": [COLUNAS_PENDENTES_SERVICOS]})
    reconhecimento, _ = ler_e_reconhecer(
        [anterior], [p for p in PAPEIS_DE_SERVICOS if not p.obrigatorio])
    assert reconhecimento.tem("semana_anterior_servicos")
    assert not reconhecimento.tem("asis")
