"""A janela do navegador — o que ela promete e o que ela recusa."""
from __future__ import annotations

import json
import threading
import urllib.error
import urllib.request
from urllib.parse import quote

import pytest

from apurabot.apuracao import apurar
from apurabot.nucleo import registro as reg
from apurabot.web import painel
from apurabot.web.servidor import PAGINA, Manipulador, Servidor, Sessao

CENTAVO = 0.005
RB = "HINOVE (RIO BRILHANTE)"


# -- o painel ---------------------------------------------------------------

@pytest.fixture(scope="module")
def dados(base_julho, parametros):
    apuracao = apurar(base_julho, parametros)
    registros = reg.montar(apuracao, parametros)
    registros = registros + [reg.totalizador(registros, base_julho.competencia)]
    return painel.montar(base_julho, apuracao, registros)


def test_o_painel_e_serializavel(dados):
    """Vai virar JSON: nada de objeto do motor vazando para a página."""
    json.dumps(dados, ensure_ascii=False)


def test_o_painel_traz_o_que_a_janela_desenha(dados):
    assert dados["competencia"] == "2026-07"
    assert dados["filiais"] and dados["registros"] and dados["transferencias"]
    assert dados["pode_encerrar"] is True
    assert dados["pendencias"] == []


def test_o_saldo_do_painel_e_o_saldo_da_apuracao(dados):
    rb = next(f for f in dados["filiais"] if f["estabelecimento"] == RB)
    assert rb["debito"] == pytest.approx(505_991.41, abs=CENTAVO)
    assert rb["credito_mantido"] == pytest.approx(138_666.94, abs=CENTAVO)
    assert rb["beneficio"] == pytest.approx(258_409.05, abs=CENTAVO)


def test_o_registro_do_painel_reproduz_o_do_erp(dados):
    rb = next(r for r in dados["registros"] if r["estabelecimento"] == RB)
    assert rb["entradas"]["total"][2] == pytest.approx(469_903.05, abs=CENTAVO)
    assert rb["saidas"]["total"][2] == pytest.approx(505_991.41, abs=CENTAVO)
    linha = {i["codigo"]: i for i in rb["resumo"]}
    assert linha["001"]["valor"] == pytest.approx(505_991.41, abs=CENTAVO)
    assert linha["002"]["valor"] == pytest.approx(99_412.10, abs=CENTAVO)
    assert linha["003"]["aguarda_ajuste"] is True


def test_a_atividade_vem_com_o_nome_do_fiscal(dados):
    rb = next(f for f in dados["filiais"] if f["estabelecimento"] == RB)
    assert "Produção" in [a["nome"] for a in rb["atividades"]]


def test_o_totalizador_vem_marcado_como_gerencial(dados):
    assert dados["registros"][-1]["gerencial"] is True
    assert all(not r["gerencial"] for r in dados["registros"][:-1])


# -- o servidor -------------------------------------------------------------

@pytest.fixture
def janela():
    """Uma janela de verdade, em 127.0.0.1, numa porta livre."""
    sessao = Sessao()
    manipulador = type("ManipuladorDeTeste", (Manipulador,), {"sessao": sessao})
    servidor = Servidor(("127.0.0.1", 0), manipulador)
    thread = threading.Thread(target=servidor.serve_forever, daemon=True)
    thread.start()
    porta = servidor.server_address[1]
    try:
        yield f"http://127.0.0.1:{porta}", sessao
    finally:
        servidor.shutdown()
        servidor.server_close()
        sessao.limpar()


def _pegar(url):
    with urllib.request.urlopen(url, timeout=20) as resposta:  # noqa: S310
        return resposta.status, resposta.read()


def test_a_pagina_abre_com_a_chave(janela):
    base, sessao = janela
    status, corpo = _pegar(f"{base}/?chave={sessao.chave}")
    assert status == 200
    assert b"Arraste aqui o Livro Fiscal" in corpo


def test_sem_a_chave_a_janela_recusa(janela):
    """Outra pessoa logada na mesma máquina também alcança 127.0.0.1."""
    base, _ = janela
    with pytest.raises(urllib.error.HTTPError) as erro:
        _pegar(f"{base}/")
    assert erro.value.code == 403


def test_com_a_chave_errada_a_janela_recusa(janela):
    base, _ = janela
    with pytest.raises(urllib.error.HTTPError) as erro:
        _pegar(f"{base}/?chave=chute")
    assert erro.value.code == 403


def test_arquivo_que_nao_e_planilha_e_recusado_com_explicacao(janela):
    base, sessao = janela
    pedido = urllib.request.Request(
        f"{base}/apurar?chave={sessao.chave}&nome=contrato.pdf",
        data=b"nao sou uma planilha",
        headers={"Content-Type": "application/octet-stream"},
    )
    with pytest.raises(urllib.error.HTTPError) as erro:
        urllib.request.urlopen(pedido, timeout=20)  # noqa: S310
    assert erro.value.code == 400
    assert "planilha" in json.loads(erro.value.read())["erro"]


def test_antes_de_apurar_nao_ha_o_que_baixar(janela):
    base, sessao = janela
    with pytest.raises(urllib.error.HTTPError) as erro:
        _pegar(f"{base}/baixar?chave={sessao.chave}")
    assert erro.value.code == 404


def test_apurar_pela_janela_devolve_o_painel_e_a_planilha(janela, arquivo_julho):
    """O caminho inteiro: arrastar o arquivo, ver o resultado, baixar."""
    base, sessao = janela
    pedido = urllib.request.Request(
        f"{base}/apurar?chave={sessao.chave}&nome={quote(arquivo_julho.name)}",
        data=arquivo_julho.read_bytes(),
        headers={"Content-Type": "application/octet-stream"},
    )
    with urllib.request.urlopen(pedido, timeout=180) as resposta:  # noqa: S310
        dados = json.loads(resposta.read())
    assert dados["competencia"] == "2026-07"
    assert dados["pode_encerrar"] is True

    status, planilha = _pegar(f"{base}/baixar?chave={sessao.chave}")
    assert status == 200
    assert planilha[:2] == b"PK"          # .xlsx é um zip
    assert len(planilha) > 100_000


def test_o_arquivo_enviado_nao_fica_na_maquina(janela, arquivo_julho):
    """Só a planilha gerada sobrevive na pasta temporária, e ela some no fim."""
    base, sessao = janela
    pedido = urllib.request.Request(
        f"{base}/apurar?chave={sessao.chave}&nome={quote(arquivo_julho.name)}",
        data=arquivo_julho.read_bytes(),
        headers={"Content-Type": "application/octet-stream"},
    )
    urllib.request.urlopen(pedido, timeout=180).read()  # noqa: S310
    restantes = sorted(p.name for p in sessao.pasta.iterdir())
    assert restantes == ["Apuracao_2026-07.xlsx"]

    sessao.limpar()
    assert not sessao.pasta.exists()


# -- a página ---------------------------------------------------------------

def test_a_pagina_nao_busca_nada_fora_da_maquina():
    """Rede corporativa bloqueia CDN — e o dado não pode sair daqui.

    A janela tem que funcionar com a máquina desconectada da internet.
    """
    html = PAGINA.read_text(encoding="utf-8")
    for proibido in ("http://", "https://"):
        for trecho in html.split(proibido)[1:]:
            alvo = proibido + trecho[:60]
            assert "www.w3.org/2000/svg" in alvo or "127.0.0.1" in alvo, (
                f"a página busca recurso externo: {alvo!r}"
            )


def test_o_numero_da_instrucao_sai_no_formato_brasileiro():
    """`287,113.66` num relatório fiscal se lê como duzentos e oitenta e sete."""
    from apurabot.formato import reais

    assert reais(287_113.66) == "287.113,66"
    assert reais(-1_234_567.891) == "-1.234.567,89"
    assert reais(0.0) == "0,00"


# -- falta de parâmetro não é defeito ---------------------------------------

def test_filial_nao_cadastrada_manda_cadastrar_e_nao_abrir_chamado():
    """A regra 4 do repositório manda parar; a mensagem tem que dizer o quê.

    Quem fecha a competência resolve isto sozinho, editando um `.yaml`. Chamar
    de defeito da ferramenta mandaria a pessoa abrir chamado para um problema
    que é dela e que ela sabe resolver.
    """
    from apurabot.nucleo.estorno import RegimeDesconhecido
    from apurabot.web.servidor import _erro_amigavel

    texto = _erro_amigavel(RegimeDesconhecido(
        "estabelecimento 'HINOVE (NOVA)' não está em filiais.yaml — "
        "cadastre-o antes de apurar"
    ))
    assert "não é defeito da ferramenta" in texto
    assert "apurabot/parametros" in texto
    assert "RegimeDesconhecido" not in texto, "o nome da classe não diz nada a ninguém"


def test_defeito_de_verdade_continua_sendo_chamado_de_defeito():
    from apurabot.web.servidor import _erro_amigavel

    texto = _erro_amigavel(ZeroDivisionError("division by zero"))
    assert "defeito da ferramenta" in texto
    assert "não é defeito" not in texto
