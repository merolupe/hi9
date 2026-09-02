"""A série do ano — o resultado de cada competência, lado a lado."""
from __future__ import annotations

import json
import threading
import urllib.error
import urllib.request

import pytest

from apurabot import serie as ser
from apurabot.apuracao import apurar

CENTAVO = 0.005


@pytest.fixture
def pasta(tmp_path):
    return tmp_path / "competencias"


# -- o arquivo --------------------------------------------------------------

def test_o_ano_nasce_com_doze_meses_vazios(pasta):
    serie = ser.ler(2026, pasta)
    assert len(serie) == 12
    assert all(m.vazio for m in serie.values())
    assert serie["2026-07"].nome == "julho"


def test_mes_vazio_nao_e_gravado(pasta):
    """Vazio não é zero: um mês que ninguém preencheu não pode virar 0,00."""
    serie = ser.ler(2026, pasta)
    serie["2026-01"].saldo = -1_200_000.0
    arquivo = ser.gravar(2026, serie, pasta)

    guardado = arquivo.read_text(encoding="utf-8")
    assert "2026-01" in guardado
    assert "2026-02" not in guardado

    relido = ser.ler(2026, pasta)
    assert relido["2026-01"].saldo == pytest.approx(-1_200_000.0)
    assert relido["2026-02"].saldo is None


def test_a_serie_fica_fora_do_git():
    """Resultado de apuração é dado fiscal: `competencias/`, não `parametros/`.

    É a regra 1 do repositório. O `.gitignore` cuida da pasta; o teste cuida de
    ninguém mover o arquivo de lugar sem perceber.
    """
    assert ser.PASTA_PADRAO.name == "competencias"
    assert ser.caminho(2026).name == "serie-2026.yaml"


def test_arquivo_ilegivel_nao_derruba_a_janela(pasta):
    pasta.mkdir(parents=True, exist_ok=True)
    ser.caminho(2026, pasta).write_text("isto: [não é: yaml", encoding="utf-8")
    assert all(m.vazio for m in ser.ler(2026, pasta).values())


def test_o_que_a_janela_manda_chega_no_formato_brasileiro():
    serie = ser.de_dados(2026, [
        {"competencia": "2026-01", "saldo": "1.200.000,00", "a_recolher": "R$ 350.000,00"},
        {"competencia": "2026-02", "saldo": "", "a_recolher": ""},
        {"competencia": "1999-13", "saldo": "1"},          # fora do ano, ignorado
    ])
    assert serie["2026-01"].saldo == pytest.approx(1_200_000.0)
    assert serie["2026-01"].a_recolher == pytest.approx(350_000.0)
    assert serie["2026-02"].vazio


# -- o mês que está sendo apurado ------------------------------------------

def test_a_competencia_apurada_vem_preenchida(base_julho, parametros, pasta):
    """Quem acabou de rodar o mês tem o número mais novo dele."""
    apuracao = apurar(base_julho, parametros)
    serie = ser.com_a_apuracao(2026, apuracao, pasta)

    julho = serie["2026-07"]
    assert julho.da_apuracao
    assert julho.saldo == pytest.approx(apuracao.total.saldo, abs=CENTAVO)
    assert not serie["2026-06"].da_apuracao


def test_a_recolher_nao_e_o_saldo_com_o_sinal_trocado(base_julho, parametros, pasta):
    """Filial credora não paga a conta de outra devedora fora da centralização.

    Em julho o grupo fecha credor e mesmo assim recolhe: são as duas colunas.
    """
    apuracao = apurar(base_julho, parametros)
    julho = ser.com_a_apuracao(2026, apuracao, pasta)["2026-07"]
    assert julho.saldo > 0
    assert julho.a_recolher > 0
    assert julho.a_recolher == pytest.approx(
        sum(f.a_recolher for f in apuracao.filiais.values()), abs=CENTAVO
    )


def test_o_painel_publica_a_serie(base_julho, parametros, monkeypatch, pasta):
    from apurabot.nucleo import registro as reg
    from apurabot.web import painel

    monkeypatch.setattr(ser, "PASTA_PADRAO", pasta)
    apuracao = apurar(base_julho, parametros)
    dados = painel.montar(base_julho, apuracao, reg.montar(apuracao, parametros))

    serie = dados["serie"]
    assert serie["ano"] == 2026
    assert [m["nome"] for m in serie["meses"]][:2] == ["janeiro", "fevereiro"]
    assert len(serie["meses"]) == 12
    julho = next(m for m in serie["meses"] if m["competencia"] == "2026-07")
    assert julho["da_apuracao"] is True
    json.dumps(dados, ensure_ascii=False)


# -- a janela grava ---------------------------------------------------------

@pytest.fixture
def janela(monkeypatch, pasta):
    from apurabot.web.servidor import Manipulador, Servidor, Sessao

    monkeypatch.setattr(ser, "PASTA_PADRAO", pasta)
    sessao = Sessao()
    manipulador = type("ManipuladorDeTeste", (Manipulador,), {"sessao": sessao})
    servidor = Servidor(("127.0.0.1", 0), manipulador)
    thread = threading.Thread(target=servidor.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{servidor.server_address[1]}", sessao
    finally:
        servidor.shutdown()
        servidor.server_close()
        sessao.limpar()


def _mandar(base, chave, corpo):
    pedido = urllib.request.Request(
        f"{base}/serie?chave={chave}",
        data=json.dumps(corpo).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(pedido, timeout=20) as resposta:  # noqa: S310
        return json.loads(resposta.read())


def test_a_janela_grava_o_que_foi_preenchido(janela, pasta):
    base, sessao = janela
    resposta = _mandar(base, sessao.chave, {"ano": 2026, "meses": [
        {"competencia": "2026-01", "saldo": "1.200.000,00",
         "a_recolher": "350.000,00", "observacao": "fechado"},
    ]})
    assert resposta["ok"] is True

    relido = ser.ler(2026, pasta)
    assert relido["2026-01"].saldo == pytest.approx(1_200_000.0)
    assert relido["2026-01"].observacao == "fechado"


def test_a_serie_sobrevive_ao_encerramento_da_janela(janela, pasta):
    """A pasta temporária some no fim; a série não pode sumir com ela."""
    base, sessao = janela
    _mandar(base, sessao.chave, {"ano": 2026, "meses": [
        {"competencia": "2026-03", "saldo": "10,00"},
    ]})
    sessao.limpar()
    assert not sessao.pasta.exists()
    assert ser.ler(2026, pasta)["2026-03"].saldo == pytest.approx(10.0)


def test_sem_a_chave_a_janela_nao_grava(janela, pasta):
    base, _ = janela
    with pytest.raises(urllib.error.HTTPError) as erro:
        _mandar(base, "chute", {"ano": 2026, "meses": []})
    assert erro.value.code == 403
    assert not ser.caminho(2026, pasta).exists()


def test_corpo_sem_ano_e_recusado_com_explicacao(janela):
    base, sessao = janela
    with pytest.raises(urllib.error.HTTPError) as erro:
        _mandar(base, sessao.chave, {"meses": []})
    assert erro.value.code == 400
    assert "tabela" in json.loads(erro.value.read())["erro"]
