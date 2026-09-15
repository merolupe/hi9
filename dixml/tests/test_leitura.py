"""O que a leitura precisa garantir para a planilha servir para conferência."""
from __future__ import annotations

import zipfile
from datetime import date

import pytest
from conftest import CHAVE_NFE, cte, evento, nfe, zipar

from dixml import pacote
from dixml.extracao import extrair


# -- NF-e ------------------------------------------------------------------

def test_uma_linha_por_item_com_os_dados_da_nota_repetidos(tmp_path, lote):
    r = extrair([lote])
    assert r.notas == 2, "duas notas distintas"
    assert len(r.nfe) == 4, "duas notas de dois itens cada"
    for linha in r.nfe.linhas:
        assert linha["Emitente"] == "EMPRESA EXEMPLO LTDA"
        assert linha["Natureza"] == "VENDA DE PRODUCAO DO ESTABELECIMENTO"


def test_codigos_continuam_texto_e_valores_viram_numero(lote):
    """Chave em coluna numérica vira notação científica e perde o PROCV."""
    linha = extrair([lote]).nfe.linhas[0]
    assert linha["Chave"] == CHAVE_NFE
    for codigo in ("Chave", "Numero NF", "NCM", "CFOP", "Emitente Doc", "CST ICMS Item"):
        assert isinstance(linha[codigo], str), codigo
    for valor in ("Qtd", "Valor Unit", "Valor Item", "Valor ICMS Item", "Valor NF"):
        assert isinstance(linha[valor], float), valor
    assert linha["Valor Item"] == 255.00
    assert linha["Valor NF"] == 455.00


def test_o_icms_e_lido_seja_qual_for_o_nome_do_grupo(lote):
    """ICMS00, ICMS20, ICMSSN102… o CST está no nome da tag, não numa lista."""
    itens = {linha["Produto"]: linha for linha in extrair([lote]).nfe.linhas}
    assert itens["ADUBO NPK"]["CST ICMS Item"] == "00"
    assert itens["DEFENSIVO"]["CST ICMS Item"] == "20"
    assert itens["DEFENSIVO"]["BC ICMS Item"] == 120.00


def test_a_assinatura_digital_nao_vira_coluna(lote):
    colunas = " ".join(extrair([lote]).nfe.colunas)
    assert "Signature" not in colunas


def test_o_arquivo_de_origem_fica_registrado_em_cada_linha(lote):
    linhas = extrair([lote]).nfe.linhas
    assert all(linha["Arquivo"].startswith("lote.zip::") for linha in linhas)


# -- Reforma Tributária ----------------------------------------------------

def test_as_colunas_da_reforma_existem_mesmo_sem_nota_que_as_use(lote):
    """É o que deixa a planilha comparável de um mês para o outro."""
    colunas = extrair([lote]).nfe.colunas
    for semente in ("IBSCBS/CST", "IBSCBS/gIBSCBS/gCBS/vCBS", "IS/vIS", "vNFTot"):
        assert semente in colunas


def test_o_grupo_ibs_cbs_e_lido_quando_a_nota_traz(tmp_path):
    lote = zipar(tmp_path / "reforma.zip", {"nota.xml": nfe(reforma=True)})
    linha = extrair([lote]).nfe.linhas[0]
    assert linha["IBSCBS/CST"] == "000"
    assert linha["IBSCBS/gIBSCBS/gIBSUF/vIBSUF"] == 0.26
    assert linha["IBSCBS/gIBSCBS/gCBS/vCBS"] == 2.30
    assert linha["vItem"] == 255.00


def test_grupo_novo_do_xml_aparece_como_coluna_sem_mexer_no_codigo(tmp_path):
    """A SEFAZ acrescenta grupo; a planilha acompanha sozinha."""
    item = """
      <det nItem="1">
        <prod><xProd>X</xProd><NCM>31051000</NCM><CFOP>5101</CFOP><vProd>10.00</vProd></prod>
        <imposto><IBSCBS><gIBSCBSMono><vIBSMono>1.23</vIBSMono></gIBSCBSMono></IBSCBS></imposto>
      </det>
    """
    lote = zipar(tmp_path / "novo.zip", {"nota.xml": nfe(itens=item)})
    r = extrair([lote])
    assert "IBSCBS/gIBSCBSMono/vIBSMono" in r.nfe.colunas
    assert r.nfe.linhas[0]["IBSCBS/gIBSCBSMono/vIBSMono"] == 1.23


# -- CT-e ------------------------------------------------------------------

def test_o_cte_vira_uma_linha_com_o_documento_inteiro(lote):
    r = extrair([lote])
    assert r.conhecimentos == 1
    linha = r.cte.linhas[0]
    assert linha["emit/xNome"] == "TRANSPORTADORA EXEMPLO"
    assert linha["vPrest/vTPrest"] == 500.00
    assert linha["imp/ICMS/ICMS00/vICMS"] == 60.00
    assert linha["protocolo/nProt"] == "135260000112233"


# -- datas -----------------------------------------------------------------

def test_data_e_hora_viram_colunas_separadas(lote):
    r = extrair([lote])
    linha = r.nfe.linhas[0]
    assert "Emissao" not in r.nfe.colunas
    assert linha["Emissao Data"] == date(2026, 6, 1)
    assert linha["Emissao Hora"] == "10:30:00"
    assert "Emissao Data" in r.nfe.colunas_de_data
    assert r.cte.linhas[0]["ide/dhEmi Data"] == date(2026, 6, 2)


def test_coluna_de_codigo_nao_e_confundida_com_data(lote):
    r = extrair([lote])
    assert "Chave Data" not in r.nfe.colunas


# -- o que não é nota ------------------------------------------------------

def test_evento_e_contado_a_parte_em_vez_de_virar_erro(lote):
    r = extrair([lote])
    assert len(r.nao_reconhecidos) == 1
    assert "evento.xml" in r.nao_reconhecidos[0]


def test_xml_quebrado_nao_derruba_o_lote(tmp_path):
    lote = zipar(tmp_path / "quebrado.zip", {
        "boa.xml": nfe(),
        "ruim.xml": "<nfeProc><infNFe> sem fechar",
    })
    r = extrair([lote])
    assert len(r.nfe) == 2, "a nota boa entrou"
    assert len(r.com_erro) == 1


# -- pacotes ---------------------------------------------------------------

def test_desce_em_zip_dentro_de_zip(tmp_path):
    interno = zipar(tmp_path / "filial.zip", {"nota.xml": nfe(), "frete.xml": cte()})
    externo = tmp_path / "mes.zip"
    with zipfile.ZipFile(externo, "w") as zf:
        zf.write(interno, "filial.zip")
    r = extrair([externo])
    assert len(r.nfe) == 2 and r.conhecimentos == 1
    assert r.nfe.linhas[0]["Arquivo"] == "mes.zip::filial.zip::nota.xml", (
        "o caminho dentro dos pacotes é o que permite achar a origem depois"
    )


def test_zip_aninhado_corrompido_nao_derruba_a_execucao(tmp_path):
    lote = zipar(tmp_path / "misto.zip", {
        "nota.xml": nfe(),
        "corrompido.zip": b"isto nao e um zip",
    })
    r = extrair([lote])
    assert len(r.nfe) == 2
    assert len(r.pacotes_com_erro) == 1


def test_varios_zips_vao_para_a_mesma_planilha(tmp_path):
    a = zipar(tmp_path / "a.zip", {"nota.xml": nfe()})
    b = zipar(tmp_path / "b.zip", {"frete.xml": cte()})
    r = extrair([a, b])
    assert len(r.nfe) == 2 and r.conhecimentos == 1
    assert r.pacotes == ["a.zip", "b.zip"]


def test_zip_que_nao_abre_e_registrado_sem_parar_o_resto(tmp_path):
    ruim = tmp_path / "ruim.zip"
    ruim.write_bytes(b"nao sou zip")
    bom = zipar(tmp_path / "bom.zip", {"nota.xml": nfe()})
    r = extrair([ruim, bom])
    assert len(r.nfe) == 2
    assert len(r.pacotes_com_erro) == 1


def test_a_expansao_tem_teto(tmp_path):
    """A ferramenta recebe arquivo pela janela; o que entra por ali é conferido."""
    lote = zipar(tmp_path / "grande.zip", {"nota.xml": nfe()})
    erros: list[str] = []
    with pytest.raises(pacote.PacoteGrandeDemais):
        list(pacote.xmls([lote], erros, pacote.Orcamento(teto=50)))


def test_zip_aninhado_fundo_demais_nao_e_aberto(tmp_path):
    atual = zipar(tmp_path / "n0.zip", {"nota.xml": nfe()})
    for nivel in range(1, pacote.PROFUNDIDADE_MAXIMA + 2):
        proximo = tmp_path / f"n{nivel}.zip"
        with zipfile.ZipFile(proximo, "w") as zf:
            zf.write(atual, atual.name)
        atual = proximo
    r = extrair([atual])
    assert len(r.nfe) == 0
    assert any("além de" in erro for erro in r.pacotes_com_erro)


def test_resumo_conta_o_que_entrou_e_o_que_ficou_de_fora(lote):
    texto = " | ".join(extrair([lote]).resumo())
    assert "NF-e: 2 nota(s), 4 linha(s) de item" in texto
    assert "CT-e: 1 documento(s)" in texto
