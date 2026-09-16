"""O livro de classificação: a leitura por cabeçalho e as cinco regras da ingestão."""
from __future__ import annotations

import pytest

from conftest import CHAVE, COLUNAS_DE_CLASSIFICACAO
from pendentes import estado
from pendentes.cabecalho import ColunasFaltando
from pendentes.chaves import chave_de_acesso

CABECALHO = COLUNAS_DE_CLASSIFICACAO + ["Retorno semana 29", "Chave Acesso"]
LINHA = ["Compra direta", "Suprimentos", "Maria", "Diretos",
         "aguardando fornecedor", CHAVE]


def extrair(cabecalho, linhas, semana=None):
    return estado.extrair_da_planilha(
        cabecalho, linhas,
        colunas_da_chave=["Chave Acesso"],
        montar_chave=lambda valores: chave_de_acesso(valores[0]),
        semana=semana,
    )


# -- a leitura -------------------------------------------------------------

def test_a_classificacao_e_lida_por_cabecalho_e_nao_por_posicao():
    """O VBA lê as colunas 1 a 5 por posição fixa; uma coluna nova embaralha tudo."""
    deslocado = ["Coluna nova"] + CABECALHO
    lidas = extrair(deslocado, [["qualquer coisa", *LINHA]])

    assert lidas[0].guardiao == "Suprimentos"
    assert lidas[0].categoria == "Diretos"
    assert lidas[0].chave == CHAVE


def test_a_coluna_de_retorno_traz_a_semana_no_proprio_rotulo():
    """`Retorno semana 29` é o retorno da semana 29, e não o da corrente."""
    lidas = extrair(CABECALHO, [LINHA], semana=30)
    assert lidas[0].retornos == {29: "aguardando fornecedor"}


def test_coluna_da_chave_ausente_aborta_nomeando_a_coluna():
    with pytest.raises(ColunasFaltando) as erro:
        extrair(COLUNAS_DE_CLASSIFICACAO, [["a", "b", "c", "d"]])
    assert "Chave Acesso" in str(erro.value)


def test_linha_sem_chave_e_ignorada():
    assert extrair(CABECALHO, [["", "", "", "", "", ""]]) == []


# -- as cinco regras da ingestão -------------------------------------------

def test_chave_nova_entra_no_livro_carimbada():
    livro = estado.Livro("mercadorias")
    relato = estado.ingerir(livro, extrair(CABECALHO, [LINHA]),
                            origem="retorno da semana 29", responsavel="luan")

    assert relato.novas == 1 and relato.alteradas == 0
    registro = livro.obter(CHAVE)
    assert registro.guardiao == "Suprimentos"
    assert registro.origem == "retorno da semana 29"
    assert registro.gravado_por == "luan"
    assert registro.gravado_em


def test_onde_o_arquivo_diverge_o_arquivo_vence_e_a_divergencia_e_contada():
    livro = estado.Livro("mercadorias")
    estado.ingerir(livro, extrair(CABECALHO, [LINHA]), responsavel="luan")

    corrigida = list(LINHA)
    corrigida[1] = "Manutenção"
    relato = estado.ingerir(livro, extrair(CABECALHO, [corrigida]),
                            responsavel="ana")

    assert relato.alteradas == 1
    assert livro.obter(CHAVE).guardiao == "Manutenção"
    assert livro.obter(CHAVE).gravado_por == "ana"
    assert any("guardiao" in detalhe for detalhe in relato.detalhes)


def test_onde_o_arquivo_esta_vazio_o_livro_vence():
    """A planilha devolvida em branco não apaga o que o time já classificou."""
    livro = estado.Livro("mercadorias")
    estado.ingerir(livro, extrair(CABECALHO, [LINHA]))

    em_branco = ["", "", "", "", "", CHAVE]
    relato = estado.ingerir(livro, extrair(CABECALHO, [em_branco]))

    assert relato.alteradas == 0
    assert relato.preservadas == 4
    assert livro.obter(CHAVE).guardiao == "Suprimentos"


def test_a_ingestao_e_idempotente():
    livro = estado.Livro("mercadorias")
    estado.ingerir(livro, extrair(CABECALHO, [LINHA]), responsavel="luan")
    antes = livro.obter(CHAVE).gravado_em

    relato = estado.ingerir(livro, extrair(CABECALHO, [LINHA]), responsavel="ana")

    assert (relato.novas, relato.alteradas, relato.retornos) == (0, 0, 0)
    assert relato.inalteradas == 1
    assert livro.obter(CHAVE).gravado_em == antes
    assert livro.obter(CHAVE).gravado_por == "luan"


def test_o_livro_guarda_os_retornos_semana_a_semana():
    livro = estado.Livro("mercadorias")
    estado.ingerir(livro, extrair(CABECALHO, [LINHA]))

    semana_seguinte = [c if c != "Retorno semana 29" else "Retorno semana 30"
                       for c in CABECALHO]
    nova = list(LINHA)
    nova[4] = "nota substituída"
    estado.ingerir(livro, extrair(semana_seguinte, [nova]))

    assert livro.obter(CHAVE).retornos == {
        29: "aguardando fornecedor", 30: "nota substituída",
    }


# -- o defeito que o livro conserta ----------------------------------------

def test_a_classificacao_sobrevive_a_semana_em_que_a_nota_sai_de_pendentes():
    """O defeito de hoje, em três semanas.

    Semana 29: a nota é classificada. Semana 30: ela foi lançada, some da aba
    `Pendentes` e por isso o PROCX da macro não a lê. Semana 31: ela volta —
    e, no VBA, volta **vazia**, porque a herança só enxerga a planilha da
    semana imediatamente anterior. O livro guarda todo mundo, para sempre.
    """
    livro = estado.Livro("mercadorias")
    estado.ingerir(livro, extrair(CABECALHO, [LINHA]))          # semana 29

    estado.ingerir(livro, extrair(CABECALHO, []))               # semana 30: sumiu

    assert livro.de(CHAVE).guardiao == "Suprimentos"            # semana 31: voltou
    assert livro.de("chave que nunca existiu").guardiao == ""


# -- ida e volta ao disco --------------------------------------------------

def test_o_livro_vai_e_volta_do_disco_inteiro(tmp_path):
    livro = estado.Livro("mercadorias")
    estado.ingerir(livro, extrair(CABECALHO, [LINHA]), origem="semeadura")
    caminho = estado.gravar(livro, "luan", tmp_path / "mercadorias.yaml")

    relido = estado.carregar("mercadorias", caminho)

    assert relido.atualizado_por == "luan"
    assert relido.obter(CHAVE).categoria == "Diretos"
    assert relido.obter(CHAVE).retornos == {29: "aguardando fornecedor"}
    assert relido.obter(CHAVE).origem == "semeadura"


def test_livro_que_ainda_nao_existe_nasce_vazio_sem_erro(tmp_path):
    """Primeira execução não é caso de erro — e o VBA abortava."""
    livro = estado.carregar("servicos", tmp_path / "nao-existe.yaml")
    assert len(livro) == 0
    assert livro.dominio == "servicos"


def test_a_semana_do_rotulo_e_lida_do_proprio_titulo():
    assert estado.semana_do_rotulo("Retorno semana 30") == 30
    assert estado.semana_do_rotulo("Retorno", 31) == 31
