"""A janela da central: o menu, a execução de uma ferramenta e as travas."""
from __future__ import annotations

import io
import zipfile
from pathlib import Path

import openpyxl

from central import ferramentas

RAIZ = Path(__file__).resolve().parents[2]


# -- o menu ----------------------------------------------------------------

def test_o_menu_traz_todas_as_ferramentas_do_setor(janela):
    codigo, dados = janela.pedir("/ferramentas")
    assert codigo == 200
    por_id = {f["id"]: f for f in dados["ferramentas"]}
    assert set(por_id) == {
        "apurabot", "dixml", "fiscalbot", "gerarpendentes",
        "gerarservpend", "faturabot",
    }


def test_ferramenta_ainda_nao_importada_aparece_apagada_em_vez_de_sumir(janela):
    """O time enxerga o que falta, em vez de descobrir quando precisar."""
    _, dados = janela.pedir("/ferramentas")
    por_id = {f["id"]: f for f in dados["ferramentas"]}
    assert por_id["gerarpendentes"]["estado"] == ferramentas.A_IMPORTAR
    assert por_id["gerarpendentes"]["resumo"]
    assert por_id["dixml"]["estado"] == ferramentas.DISPONIVEL
    assert por_id["fiscalbot"]["estado"] == ferramentas.DISPONIVEL
    assert por_id["apurabot"]["estado"] == ferramentas.JANELA_PROPRIA


def test_so_quem_guarda_estado_declara_configuracao(janela):
    """O Fiscalbot é a primeira com regras próprias; as outras não têm o que salvar."""
    _, dados = janela.pedir("/ferramentas")
    por_id = {f["id"]: f for f in dados["ferramentas"]}
    assert por_id["fiscalbot"]["tem_configuracao"] is True
    assert por_id["dixml"]["tem_configuracao"] is False


def test_quem_roda_na_janela_declara_o_que_pede(janela):
    _, dados = janela.pedir("/ferramentas")
    dixml = next(f for f in dados["ferramentas"] if f["id"] == "dixml")
    assert dixml["entrada"]["extensoes"] == [".zip"]
    assert dixml["entrada"]["varios"] is True


def test_a_pagina_e_servida(janela):
    codigo, corpo = janela.pedir("/")
    assert codigo == 200
    assert b"Central" in corpo


# -- a trava de sessão -----------------------------------------------------

def test_sem_a_chave_da_sessao_nada_responde(janela):
    """Outra pessoa logada na mesma máquina também alcança 127.0.0.1."""
    for rota in ("/", "/ferramentas", "/baixar"):
        codigo, _ = janela.pedir(rota, chave="chave-errada")
        assert codigo == 403, rota


# -- o DiXML de ponta a ponta ---------------------------------------------

def _enviar_e_executar(janela, lote, nome="lote.zip"):
    codigo, envio = janela.pedir("/enviar", corpo=lote, ferramenta="dixml", nome=nome)
    assert codigo == 200, envio
    return janela.postar("/executar", ferramenta="dixml")


def test_o_lote_entra_pela_janela_e_sai_planilha(janela, lote):
    codigo, dados = _enviar_e_executar(janela, lote)
    assert codigo == 200, dados

    fichas = {f["rotulo"]: f["valor"] for f in dados["fichas"]}
    assert fichas["Notas (NF-e)"] == "1"
    assert fichas["Linhas de item"] == "1"
    assert dados["planilha"].startswith("DiXML_")

    codigo, corpo = janela.pedir("/baixar")
    assert codigo == 200
    livro = openpyxl.load_workbook(io.BytesIO(corpo))
    assert livro.sheetnames == ["NFe", "CTe"]
    aba = livro["NFe"]
    cabecalho = [c.value for c in aba[1]]
    assert aba.cell(row=2, column=cabecalho.index("Chave") + 1).value == (
        "35260612345678000199550010000001231000001234"
    )


def test_o_nome_do_pacote_chega_a_planilha(janela, lote):
    """É por ele que se acha a origem de uma linha meses depois."""
    _enviar_e_executar(janela, lote, nome="XMLs_junho_filial_02.zip")
    _, corpo = janela.pedir("/baixar")
    aba = openpyxl.load_workbook(io.BytesIO(corpo))["NFe"]
    assert aba.cell(row=2, column=1).value == "XMLs_junho_filial_02.zip::nota.xml"


def test_dois_pacotes_de_mesmo_nome_nao_se_atropelam(janela, lote):
    for _ in range(2):
        codigo, envio = janela.pedir(
            "/enviar", corpo=lote, ferramenta="dixml", nome="lote.zip"
        )
        assert codigo == 200, envio
    codigo, dados = janela.postar("/executar", ferramenta="dixml")
    assert codigo == 200, dados
    assert {f["rotulo"]: f["valor"] for f in dados["fichas"]}["Linhas de item"] == "2"


def test_os_arquivos_enviados_somem_depois_de_rodar(janela, lote):
    _enviar_e_executar(janela, lote)
    assert janela.sessao.recebidos_de("dixml") == []


def test_o_que_nao_e_nota_aparece_na_tela_em_vez_de_sumir(janela, tmp_path):
    caminho = tmp_path / "com_evento.zip"
    with zipfile.ZipFile(caminho, "w") as zf:
        zf.writestr("evento.xml", "<procEventoNFe><evento/></procEventoNFe>")
    _, dados = _enviar_e_executar(janela, caminho.read_bytes())
    titulos = " ".join(l["titulo"] for l in dados["listas"])
    assert "Não entraram na planilha" in titulos


# -- o que a janela recusa -------------------------------------------------

def test_arquivo_do_tipo_errado_e_recusado_com_o_motivo(janela):
    codigo, dados = janela.pedir(
        "/enviar", corpo=b"conteudo", ferramenta="dixml", nome="livro.xlsx"
    )
    assert codigo == 400
    assert ".zip" in dados["erro"]


def test_arquivo_vazio_e_recusado(janela):
    codigo, dados = janela.pedir(
        "/enviar", corpo=b"", ferramenta="dixml", nome="lote.zip"
    )
    assert codigo == 400
    assert "vazio" in dados["erro"]


def test_executar_sem_arquivo_avisa_em_vez_de_estourar(janela):
    codigo, dados = janela.postar("/executar", ferramenta="dixml")
    assert codigo == 400
    assert "Nenhum arquivo" in dados["erro"]


def test_ferramenta_desconhecida_nao_derruba_a_janela(janela):
    codigo, dados = janela.postar("/executar", ferramenta="naoexiste")
    assert codigo == 404
    assert "erro" in dados


def test_ferramenta_ainda_nao_importada_nao_finge_que_roda(janela):
    codigo, dados = janela.postar("/executar", ferramenta="gerarpendentes")
    assert codigo == 400
    assert "ainda não roda" in dados["erro"]


def test_o_nome_do_arquivo_nao_escapa_da_pasta_temporaria(janela, lote):
    """O nome vem do navegador e vai para o disco: fica só o nome."""
    codigo, _ = janela.pedir(
        "/enviar", corpo=lote, ferramenta="dixml",
        nome="..%2F..%2Fescapou.zip",
    )
    assert codigo == 200
    recebido = janela.sessao.recebidos_de("dixml")[0]
    assert recebido.name == "escapou.zip"
    assert janela.sessao.pasta in recebido.parents


def test_zip_corrompido_vira_recado_em_vez_de_traceback(janela):
    codigo, dados = janela.pedir(
        "/enviar", corpo=b"isto nao e um zip", ferramenta="dixml", nome="lote.zip"
    )
    assert codigo == 200
    codigo, dados = janela.postar("/executar", ferramenta="dixml")
    assert codigo == 200
    titulos = " ".join(l["titulo"] for l in dados["listas"])
    assert "ilegíveis" in titulos


# -- a tela de configuração ------------------------------------------------

def test_a_tela_de_configuracao_traz_secoes_e_dados(janela):
    codigo, dados = janela.pedir("/configuracao", ferramenta="fiscalbot")
    assert codigo == 200, dados
    ids = [s["id"] for s in dados["secoes"]]
    assert "regras" in ids and "parceiros_sn" in ids
    assert dados["dados"]["regras"], "a carga de fábrica tem que vir preenchida"
    for secao in dados["secoes"]:
        assert secao["explicacao"]
        assert secao["campos"]


def test_ferramenta_sem_configuracao_diz_isso(janela):
    codigo, dados = janela.pedir("/configuracao", ferramenta="dixml")
    assert codigo == 400
    assert "não tem o que configurar" in dados["erro"]


def test_gravar_configuracao_com_erro_nao_grava(janela):
    """Base inconsistente auditaria o mês inteiro errado."""
    import json
    corpo = json.dumps({"dados": {
        "regras": [{"id": "X1", "cfop": "5101", "ativa": True},
                   {"id": "X1", "cfop": "5102", "ativa": True}],
        "parametros": [{"tolerancia_carga": "0.05",
                        "cst_exigem_icms_positivo": "00"}],
    }}).encode("utf-8")
    codigo, dados = janela.pedir("/configuracao", corpo=corpo, ferramenta="fiscalbot")
    assert codigo == 200
    assert dados["gravou"] is False
    assert any(p["gravidade"] == "erro" for p in dados["problemas"])


def test_a_tela_devolve_os_problemas_para_a_pessoa_ler(janela):
    import json
    corpo = json.dumps({"dados": {"regras": [], "parametros": [{}]}}).encode("utf-8")
    codigo, dados = janela.pedir("/configuracao", corpo=corpo, ferramenta="fiscalbot")
    assert codigo == 200
    assert dados["gravou"] is False
    assert dados["problemas"], "recusar sem dizer o motivo não ajuda ninguém"
    for problema in dados["problemas"]:
        assert problema["onde"] and problema["mensagem"]


# -- o Apurabot, que tem tela própria --------------------------------------

def test_o_apurabot_abre_em_janela_propria_sem_ser_reescrito(janela):
    codigo, dados = janela.pedir("/abrir", ferramenta="apurabot")
    assert codigo == 200, dados
    assert dados["endereco"].startswith("http://127.0.0.1:")
    assert "chave=" in dados["endereco"]


def test_clicar_duas_vezes_no_apurabot_reaproveita_a_mesma_janela(janela):
    _, primeira = janela.pedir("/abrir", ferramenta="apurabot")
    _, segunda = janela.pedir("/abrir", ferramenta="apurabot")
    assert primeira["endereco"] == segunda["endereco"]


def test_ferramenta_sem_tela_propria_nao_finge_ter(janela):
    codigo, dados = janela.pedir("/abrir", ferramenta="dixml")
    assert codigo == 400
    assert "janela própria" in dados["erro"]


# -- o encerramento --------------------------------------------------------

def test_encerrar_avisa_a_janela_e_limpa_o_que_ficou(janela, lote):
    janela.pedir("/enviar", corpo=lote, ferramenta="dixml", nome="lote.zip")
    pasta = janela.sessao.pasta
    codigo, _ = janela.pedir("/encerrar")
    assert codigo == 200
    assert janela.sessao.encerrar.is_set()
    janela.sessao.limpar()
    assert not pasta.exists()


# -- o lançador ------------------------------------------------------------

def test_o_lancador_da_central_pergunta_ao_python_em_vez_de_adivinhar():
    """Escolher `py -3` por vir primeiro na lista foi o defeito de antes."""
    bat = (RAIZ / "Hinove.bat").read_text(encoding="cp1252")
    assert "verificar.py" in bat
    for candidato in ("python", "py -3"):
        assert f'"{candidato}"' in bat


def test_os_arquivos_de_entrada_estao_na_raiz():
    for arquivo in ("Hinove.bat", "Apurabot.bat", "rodar.py", "verificar.py"):
        assert (RAIZ / arquivo).is_file(), arquivo
