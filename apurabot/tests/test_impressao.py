"""O Registro de Apuração como página de impressão — o PDF sai do navegador.

A página desenha o mesmo `Registro` da aba REGISTRO, nas duas folhas do
documento que o Sankhya emite: entradas e saídas por CFOP, e o resumo.
"""
from __future__ import annotations

import datetime as dt
import threading
import urllib.error
import urllib.request

import pytest

from apurabot.apuracao import apurar
from apurabot.base_tratada import tratar
from apurabot.nucleo import registro as reg
from apurabot.web import impressao
from apurabot.web.servidor import Manipulador, Servidor, Sessao
from sintetico import RB
from sintetico import livro as _livro

EMISSAO = dt.datetime(2026, 9, 29, 14, 52, 37)


@pytest.fixture(scope="module")
def pagina(parametros, tmp_path_factory):
    base = tratar(_livro(tmp_path_factory.mktemp("livro") / "livro.xlsx"),
                  parametros=parametros)
    registros = reg.montar(apurar(base, parametros), parametros)
    registros = registros + [reg.totalizador(registros, base.competencia)]
    return impressao.montar(registros, parametros, EMISSAO)


def test_as_duas_folhas_do_documento(pagina):
    assert "Registro de Apuração do ICMS" in pagina
    assert "Resumo da Apuração do Imposto (ICMS)" in pagina
    assert pagina.count('class="folha"') == 2


def test_o_cabecalho_e_o_do_erp(pagina):
    """Razão social, CNPJ e IE do cadastro; o período é o mês inteiro."""
    assert "HINOVE AGROCIÊNCIA S.A." in pagina
    assert "14031191000244" in pagina and "284280330" in pagina
    assert "01/08/2026 à 31/08/2026" in pagina
    assert "29/09/2026 14:52:37" in pagina
    assert "Ajuste de Apuração e Ajuste de Sub-Apuração" in pagina


def test_os_valores_saem_no_formato_do_documento(pagina):
    assert "5101" in pagina and "Vda prod do estab" in pagina
    assert "100.000,00" in pagina and "17.000,00" in pagina
    assert "1.00 do Estado" in pagina and "6.00 para outros Estados" in pagina


def test_o_resumo_traz_as_quatorze_linhas(pagina):
    for rotulo in ("001 por Saídas/Prestações com Débito do Imposto",
                   "002 Outros Débitos (Discriminar Abaixo)",
                   "012 DEDUÇÕES (Discriminar Abaixo)",
                   "014 SALDO CREDOR (Crédito menos Débito)"):
        assert rotulo in pagina


def test_o_beneficio_vem_discriminado_na_coluna_auxiliar(pagina):
    assert "Termo de Acordo n. 1.190/2018" in pagina


def test_linha_que_aguarda_ajuste_sai_marcada(pagina):
    """O papel não pode parecer final quando não é."""
    assert "o valor impresso não é o final" in pagina


def test_o_totalizador_nao_vira_documento(pagina):
    """Soma de UFs diferentes não é documento fiscal de ninguém."""
    assert "TOTALIZADOR" not in pagina
    assert RB in pagina


def test_nome_com_caractere_de_html_e_escapado(parametros):
    bloco = reg.Bloco(reg.ENTRADAS)
    registro = reg.Registro(
        estabelecimento="A <b>&</b> B", uf="SP", cnpj="", inscricao_estadual="",
        competencia="2026-08", entradas=bloco, saidas=reg.Bloco(reg.SAIDAS),
        resumo=[reg.LinhaResumo(c, "x") for c in range(1, 15)],
    )
    html = impressao.montar([registro], parametros, EMISSAO)
    assert "<b>&</b>" not in html
    assert "A &lt;b&gt;&amp;&lt;/b&gt; B" in html


@pytest.mark.parametrize("valor, esperado", [
    (0, "0,00"), (1234567.8, "1.234.567,80"), (0.005, "0,01"), (-5.5, "-5,50"),
])
def test_reais(valor, esperado):
    assert impressao._reais(valor) == esperado


# -- a rota na janela --------------------------------------------------------

@pytest.fixture
def janela():
    sessao = Sessao()
    manipulador = type("ManipuladorDeTeste", (Manipulador,), {"sessao": sessao})
    servidor = Servidor(("127.0.0.1", 0), manipulador)
    threading.Thread(target=servidor.serve_forever, daemon=True).start()
    try:
        yield f"http://127.0.0.1:{servidor.server_address[1]}", sessao
    finally:
        servidor.shutdown()
        servidor.server_close()
        sessao.limpar()


def test_a_janela_serve_a_pagina_depois_de_apurar(janela, tmp_path):
    base, sessao = janela
    with pytest.raises(urllib.error.HTTPError) as erro:
        urllib.request.urlopen(f"{base}/imprimir?chave={sessao.chave}", timeout=20)  # noqa: S310
    assert erro.value.code == 404

    pedido = urllib.request.Request(
        f"{base}/apurar?chave={sessao.chave}&nome=livro.xlsx",
        data=_livro(tmp_path / "livro.xlsx").read_bytes(),
        headers={"Content-Type": "application/octet-stream"},
    )
    with urllib.request.urlopen(pedido, timeout=60) as resposta:  # noqa: S310
        assert resposta.status == 200

    with urllib.request.urlopen(f"{base}/imprimir?chave={sessao.chave}", timeout=20) as r:  # noqa: S310
        corpo = r.read().decode("utf-8")
    assert "Resumo da Apuração do Imposto (ICMS)" in corpo


def test_sem_a_chave_a_pagina_de_impressao_e_recusada(janela):
    base, _ = janela
    with pytest.raises(urllib.error.HTTPError) as erro:
        urllib.request.urlopen(f"{base}/imprimir?chave=chute", timeout=20)  # noqa: S310
    assert erro.value.code == 403
