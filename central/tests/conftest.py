"""Uma janela de verdade, subida numa porta livre, para os testes conversarem."""
from __future__ import annotations

import json
import sys
import threading
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "central" / "src"))

import central  # noqa: E402  (põe `vendor/` e as ferramentas no sys.path)
from central import servidor as srv  # noqa: E402


class Janela:
    """O endereço da janela e os atalhos para falar com ela."""

    def __init__(self, base: str, chave: str, sessao) -> None:
        self.base = base
        self.chave = chave
        self.sessao = sessao

    def url(self, rota: str, **parametros) -> str:
        partes = "".join(f"&{k}={v}" for k, v in parametros.items())
        return f"{self.base}{rota}?chave={self.chave}{partes}"

    def pedir(self, rota: str, corpo: bytes | None = None, chave: str | None = None,
              **parametros):
        """Devolve `(codigo, conteúdo)`; o conteúdo vem decodificado se for JSON."""
        endereco = self.url(rota, **parametros)
        if chave is not None:
            endereco = endereco.replace(f"chave={self.chave}", f"chave={chave}")
        pedido = urllib.request.Request(
            endereco, data=corpo, method="POST" if corpo is not None else "GET"
        )
        try:
            with urllib.request.urlopen(pedido, timeout=60) as resposta:
                return resposta.status, _ler(resposta)
        except urllib.error.HTTPError as erro:
            return erro.code, _ler(erro)

    def postar(self, rota: str, **parametros):
        return self.pedir(rota, corpo=b"", **parametros)


def _ler(resposta):
    bruto = resposta.read()
    if "json" in (resposta.headers.get("Content-Type") or ""):
        return json.loads(bruto)
    return bruto


@pytest.fixture()
def janela():
    sessao = srv.Sessao()
    manipulador = type("ManipuladorDoTeste", (srv.Manipulador,), {"sessao": sessao})
    servidor = srv.Servidor(("127.0.0.1", 0), manipulador)
    threading.Thread(target=servidor.serve_forever, daemon=True).start()
    porta = servidor.server_address[1]
    try:
        yield Janela(f"http://127.0.0.1:{porta}", sessao.chave, sessao)
    finally:
        servidor.shutdown()
        servidor.server_close()
        sessao.limpar()


NOTA = """<?xml version="1.0" encoding="UTF-8"?>
<nfeProc xmlns="http://www.portalfiscal.inf.br/nfe" versao="4.00"><NFe>
  <infNFe Id="NFe35260612345678000199550010000001231000001234" versao="4.00">
    <ide><nNF>123</nNF><serie>1</serie><dhEmi>2026-06-01T10:30:00-03:00</dhEmi>
      <tpNF>1</tpNF><natOp>VENDA</natOp></ide>
    <emit><CNPJ>12345678000199</CNPJ><xNome>EMPRESA EXEMPLO LTDA</xNome></emit>
    <dest><CNPJ>98765432000188</CNPJ><xNome>CLIENTE EXEMPLO SA</xNome></dest>
    <det nItem="1"><prod><xProd>ADUBO</xProd><NCM>31051000</NCM><CFOP>5101</CFOP>
      <qCom>10.0000</qCom><vUnCom>25.5000</vUnCom><vProd>255.00</vProd></prod>
      <imposto><ICMS><ICMS00><CST>00</CST><vBC>255.00</vBC>
        <pICMS>18.00</pICMS><vICMS>45.90</vICMS></ICMS00></ICMS></imposto></det>
    <total><ICMSTot><vBC>255.00</vBC><vNF>255.00</vNF></ICMSTot></total>
  </infNFe>
</NFe></nfeProc>
"""


@pytest.fixture()
def lote(tmp_path) -> bytes:
    caminho = tmp_path / "lote.zip"
    with zipfile.ZipFile(caminho, "w") as zf:
        zf.writestr("nota.xml", NOTA)
    return caminho.read_bytes()
