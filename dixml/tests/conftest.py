"""Notas fictícias para os testes.

Nenhum XML real da empresa entra no repositório — a regra nº 1 do `CLAUDE.md`.
As notas aqui são montadas no próprio teste, com CNPJ e chave inventados, e
trazem só o que cada teste precisa exercitar.
"""
from __future__ import annotations

import sys
import zipfile
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "dixml" / "src"))

CHAVE_NFE = "35260612345678000199550010000001231000001234"
CHAVE_CTE = "35260611222333000144570010000000771000000778"


def nfe(itens: str = "", reforma: bool = False, chave: str = CHAVE_NFE) -> str:
    """Uma NF-e de venda. `itens` substitui os itens padrão quando informado."""
    padrao = """
      <det nItem="1">
        <prod><xProd>ADUBO NPK</xProd><NCM>31051000</NCM><CFOP>5101</CFOP>
          <qCom>10.0000</qCom><vUnCom>25.5000</vUnCom><vProd>255.00</vProd></prod>
        <imposto>
          <ICMS><ICMS00><orig>0</orig><CST>00</CST><vBC>255.00</vBC>
            <pICMS>18.00</pICMS><vICMS>45.90</vICMS></ICMS00></ICMS>
          <PIS><PISAliq><CST>01</CST><vBC>255.00</vBC>
            <pPIS>1.65</pPIS><vPIS>4.21</vPIS></PISAliq></PIS>
          <COFINS><COFINSAliq><CST>01</CST><vBC>255.00</vBC>
            <pCOFINS>7.60</pCOFINS><vCOFINS>19.38</vCOFINS></COFINSAliq></COFINS>
        </imposto>
      </det>
      <det nItem="2">
        <prod><xProd>DEFENSIVO</xProd><NCM>38089329</NCM><CFOP>5102</CFOP>
          <qCom>2.0000</qCom><vUnCom>100.0000</vUnCom><vProd>200.00</vProd></prod>
        <imposto>
          <ICMS><ICMS20><orig>0</orig><CST>20</CST><vBC>120.00</vBC>
            <pICMS>18.00</pICMS><vICMS>21.60</vICMS></ICMS20></ICMS>
        </imposto>
      </det>
    """
    grupos_reforma = """
        <IBSCBS><CST>000</CST><cClassTrib>000001</cClassTrib>
          <gIBSCBS><vBC>255.00</vBC>
            <gIBSUF><pIBSUF>0.1000</pIBSUF><vIBSUF>0.26</vIBSUF></gIBSUF>
            <gCBS><pCBS>0.9000</pCBS><vCBS>2.30</vCBS></gCBS>
            <vIBS>0.26</vIBS>
          </gIBSCBS></IBSCBS>
    """ if reforma else ""
    item_reforma = f"""
      <det nItem="1">
        <prod><xProd>ADUBO NPK</xProd><NCM>31051000</NCM><CFOP>5101</CFOP>
          <qCom>10.0000</qCom><vUnCom>25.5000</vUnCom><vProd>255.00</vProd></prod>
        <imposto>
          <ICMS><ICMS00><CST>00</CST><vBC>255.00</vBC>
            <pICMS>18.00</pICMS><vICMS>45.90</vICMS></ICMS00></ICMS>
          {grupos_reforma}
        </imposto>
        <vItem>255.00</vItem>
      </det>
    """ if reforma else ""

    corpo = itens or (item_reforma if reforma else padrao)
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<nfeProc xmlns="http://www.portalfiscal.inf.br/nfe" versao="4.00">
  <NFe>
    <infNFe Id="NFe{chave}" versao="4.00">
      <ide><cUF>35</cUF><nNF>123</nNF><serie>1</serie>
        <dhEmi>2026-06-01T10:30:00-03:00</dhEmi>
        <tpNF>1</tpNF><natOp>VENDA DE PRODUCAO DO ESTABELECIMENTO</natOp></ide>
      <emit><CNPJ>12345678000199</CNPJ><xNome>EMPRESA EXEMPLO LTDA</xNome></emit>
      <dest><CNPJ>98765432000188</CNPJ><xNome>CLIENTE EXEMPLO SA</xNome></dest>
      {corpo}
      <total><ICMSTot><vBC>375.00</vBC><vICMS>67.50</vICMS><vBCST>0.00</vBCST>
        <vST>0.00</vST><vProd>455.00</vProd><vDesc>0.00</vDesc><vSeg>0.00</vSeg>
        <vOutro>0.00</vOutro><vIPI>0.00</vIPI><vPIS>4.21</vPIS>
        <vCOFINS>19.38</vCOFINS><vNF>455.00</vNF></ICMSTot></total>
      <transp><modFrete>0</modFrete></transp>
      <pag><detPag><tPag>01</tPag></detPag></pag>
      <infAdic><infCpl>PEDIDO 4567</infCpl></infAdic>
    </infNFe>
    <Signature xmlns="http://www.w3.org/2000/09/xmldsig#">
      <SignatureValue>ASSINATURA-QUE-NAO-DEVE-VIRAR-COLUNA</SignatureValue>
    </Signature>
  </NFe>
</nfeProc>
"""


def cte(chave: str = CHAVE_CTE) -> str:
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<cteProc xmlns="http://www.portalfiscal.inf.br/cte" versao="4.00">
  <CTe>
    <infCte Id="CTe{chave}" versao="4.00">
      <ide><cUF>35</cUF><nCT>77</nCT><serie>1</serie>
        <dhEmi>2026-06-02T08:00:00-03:00</dhEmi><CFOP>5353</CFOP>
        <natOp>PRESTACAO DE SERVICO DE TRANSPORTE</natOp></ide>
      <emit><CNPJ>11222333000144</CNPJ><xNome>TRANSPORTADORA EXEMPLO</xNome></emit>
      <rem><CNPJ>12345678000199</CNPJ><xNome>EMPRESA EXEMPLO LTDA</xNome></rem>
      <dest><CNPJ>98765432000188</CNPJ><xNome>CLIENTE EXEMPLO SA</xNome></dest>
      <vPrest><vTPrest>500.00</vTPrest><vRec>500.00</vRec></vPrest>
      <imp><ICMS><ICMS00><CST>00</CST><vBC>500.00</vBC>
        <pICMS>12.00</pICMS><vICMS>60.00</vICMS></ICMS00></ICMS></imp>
    </infCte>
    <protCTe><infProt><nProt>135260000112233</nProt>
      <dhRecbto>2026-06-02T09:00:00-03:00</dhRecbto><cStat>100</cStat></infProt></protCTe>
  </CTe>
</cteProc>
"""


def evento() -> str:
    """Um evento de carta de correção: nem NF-e, nem CT-e."""
    return """<?xml version="1.0" encoding="UTF-8"?>
<procEventoNFe xmlns="http://www.portalfiscal.inf.br/nfe" versao="1.00">
  <evento versao="1.00"><infEvento Id="ID1101101"><tpEvento>110110</tpEvento>
    <xCorrecao>CORRECAO DO CFOP</xCorrecao></infEvento></evento>
</procEventoNFe>
"""


def zipar(destino: Path, arquivos: dict[str, str | bytes]) -> Path:
    with zipfile.ZipFile(destino, "w", zipfile.ZIP_DEFLATED) as zf:
        for nome, conteudo in arquivos.items():
            zf.writestr(nome, conteudo)
    return destino


@pytest.fixture()
def lote(tmp_path) -> Path:
    """Um `.zip` com duas NF-e, um CT-e e um evento."""
    return zipar(tmp_path / "lote.zip", {
        "nota1.xml": nfe(),
        "nota2.xml": nfe(chave=CHAVE_NFE.replace("123100", "999100")),
        "conhecimento.xml": cte(),
        "evento.xml": evento(),
    })
