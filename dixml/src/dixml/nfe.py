"""A NF-e vira uma linha por item, com os dados da nota repetidos.

Uma linha por item, e não por nota, porque a conferência fiscal é por item:
CFOP, NCM, CST e alíquota mudam dentro da mesma nota. O que é da nota — chave,
emitente, totais — se repete em todas as linhas dela, para a planilha poder ser
filtrada por qualquer coluna sem perder o contexto.

## Reforma Tributária

Os grupos IBS/CBS e Imposto Seletivo são lidos por achatamento dinâmico, então
qualquer tag que a SEFAZ acrescentar aparece sozinha como coluna nova. As
listas abaixo são **sementes**: garantem que a coluna exista na planilha mesmo
quando nenhuma nota do lote traz o grupo — é o que deixa a planilha comparável
entre um mês e outro, e o que permite montar tabela dinâmica sem quebrar
quando o campo começa a ser preenchido.

Base: NT 2025.002-RTC (grupos UB / UT / totais W), conferida em julho de 2026.
Grupos raros — `gIBSCBSMono` (combustíveis), `gTransfCred`, `gCredPresIBSZFM`,
`gEstornoCred` — não são semeados, mas são capturados se aparecerem.
"""
from __future__ import annotations

from typing import Any
from xml.etree.ElementTree import Element

from .campos import achar, achatar, numero, texto

#: Colunas do item, na ordem em que a conferência as lê.
COLUNAS_BASE = [
    "Arquivo", "Chave", "Numero NF", "Serie", "Emissao", "Tipo operacao", "Natureza",
    "Emitente", "Emitente Doc", "Emitente Tipo",
    "Destinatario", "Destinatario Doc", "Destinatario Tipo",
    "Item", "Produto", "NCM", "CFOP", "Qtd", "Valor Unit", "Valor Item",
    "cBenef",
    "CST ICMS Item", "BC ICMS Item", "Aliquota ICMS Item", "Valor ICMS Item",
    "BC ICMS-ST Item", "Valor ICMS-ST Item", "Aliquota ICMS-ST Item",
    "PIS CST", "PIS Base", "PIS Aliquota", "PIS Valor", "PIS-ST Item",
    "COFINS CST", "COFINS Base", "COFINS Aliquota", "COFINS Valor", "COFINS-ST Item",
    "IPI CST", "IPI Aliquota", "IPI Base", "IPI Valor",
    "Pagamento", "Desconto NF", "Tipo Frete", "Seguro NF", "Outras Despesas NF",
    "BC ICMS NF", "BC ICMS-ST NF", "ICMS-ST NF",
    "PIS NF", "COFINS NF", "PIS-ST NF", "COFINS-ST NF",
    "IPI NF", "Valor NF", "Observacao",
]

#: Sementes da Reforma no item — ver o cabeçalho do módulo.
COLUNAS_RTC_ITEM = [
    "cBenef",
    "vItem",                                    # novo total do item (NT 2025.002)
    "IBSCBS/CST",
    "IBSCBS/cClassTrib",
    "IBSCBS/gIBSCBS/vBC",
    # --- IBS UF ---
    "IBSCBS/gIBSCBS/gIBSUF/pIBSUF",
    "IBSCBS/gIBSCBS/gIBSUF/gDif/pDif",
    "IBSCBS/gIBSCBS/gIBSUF/gDif/vDif",
    "IBSCBS/gIBSCBS/gIBSUF/gDevTrib/vDevTrib",
    "IBSCBS/gIBSCBS/gIBSUF/gRed/pRedAliq",      # redução de alíquota (ex.: insumo agro)
    "IBSCBS/gIBSCBS/gIBSUF/gRed/pAliqEfet",
    "IBSCBS/gIBSCBS/gIBSUF/vIBSUF",
    # --- IBS Município ---
    "IBSCBS/gIBSCBS/gIBSMun/pIBSMun",
    "IBSCBS/gIBSCBS/gIBSMun/gDif/pDif",
    "IBSCBS/gIBSCBS/gIBSMun/gDif/vDif",
    "IBSCBS/gIBSCBS/gIBSMun/gDevTrib/vDevTrib",
    "IBSCBS/gIBSCBS/gIBSMun/gRed/pRedAliq",
    "IBSCBS/gIBSCBS/gIBSMun/gRed/pAliqEfet",
    "IBSCBS/gIBSCBS/gIBSMun/vIBSMun",
    "IBSCBS/gIBSCBS/vIBS",
    # --- CBS ---
    "IBSCBS/gIBSCBS/gCBS/pCBS",
    "IBSCBS/gIBSCBS/gCBS/gDif/pDif",
    "IBSCBS/gIBSCBS/gCBS/gDif/vDif",
    "IBSCBS/gIBSCBS/gCBS/gDevTrib/vDevTrib",
    "IBSCBS/gIBSCBS/gCBS/gRed/pRedAliq",
    "IBSCBS/gIBSCBS/gCBS/gRed/pAliqEfet",
    "IBSCBS/gIBSCBS/gCBS/vCBS",
    # --- tributação regular (quando há suspensão ou diferimento) ---
    "IBSCBS/gIBSCBS/gTribRegular/CSTReg",
    "IBSCBS/gIBSCBS/gTribRegular/cClassTribReg",
    "IBSCBS/gIBSCBS/gTribRegular/pAliqEfetRegIBSUF",
    "IBSCBS/gIBSCBS/gTribRegular/vTribRegIBSUF",
    "IBSCBS/gIBSCBS/gTribRegular/pAliqEfetRegIBSMun",
    "IBSCBS/gIBSCBS/gTribRegular/vTribRegIBSMun",
    "IBSCBS/gIBSCBS/gTribRegular/pAliqEfetRegCBS",
    "IBSCBS/gIBSCBS/gTribRegular/vTribRegCBS",
    # --- créditos presumidos ---
    "IBSCBS/gIBSCBS/gIBSCredPres/cCredPres",
    "IBSCBS/gIBSCBS/gIBSCredPres/pCredPres",
    "IBSCBS/gIBSCBS/gIBSCredPres/vCredPres",
    "IBSCBS/gIBSCBS/gIBSCredPres/vCredPresCondSus",
    "IBSCBS/gIBSCBS/gCBSCredPres/cCredPres",
    "IBSCBS/gIBSCBS/gCBSCredPres/pCredPres",
    "IBSCBS/gIBSCBS/gCBSCredPres/vCredPres",
    "IBSCBS/gIBSCBS/gCBSCredPres/vCredPresCondSus",
    # --- Imposto Seletivo (grupo IS do item) ---
    "IS/CSTIS",
    "IS/cClassTribIS",
    "IS/vBCIS",
    "IS/pIS",
    "IS/pISEspec",
    "IS/uTrib",
    "IS/qTrib",
    "IS/vIS",
]

#: Sementes no nível da nota: compras governamentais, grupo dentro de `<ide>`.
COLUNAS_RTC_NOTA = [
    "gCompraGov/tpEnteGov",
    "gCompraGov/pRedutor",
    "gCompraGov/tpOperGov",
]

#: Sementes dos totais da nota.
COLUNAS_RTC_TOTAL = [
    "IBSCBSTot/vBCIBSCBS",
    "IBSCBSTot/gIBS/gIBSUF/vDif",
    "IBSCBSTot/gIBS/gIBSUF/vDevTrib",
    "IBSCBSTot/gIBS/gIBSUF/vIBSUF",
    "IBSCBSTot/gIBS/gIBSMun/vDif",
    "IBSCBSTot/gIBS/gIBSMun/vDevTrib",
    "IBSCBSTot/gIBS/gIBSMun/vIBSMun",
    "IBSCBSTot/gIBS/vIBS",
    "IBSCBSTot/gIBS/vCredPres",
    "IBSCBSTot/gIBS/vCredPresCondSus",
    "IBSCBSTot/gCBS/vDif",
    "IBSCBSTot/gCBS/vDevTrib",
    "IBSCBSTot/gCBS/vCBS",
    "IBSCBSTot/gCBS/vCredPres",
    "IBSCBSTot/gCBS/vCredPresCondSus",
    "ISTot/vIS",
    "vNFTot",                                   # novo total da nota, com IBS/CBS
]

#: Todas as colunas garantidas, na ordem, antes das que o lote trouxer sozinho.
COLUNAS_SEMENTE = COLUNAS_RTC_ITEM + COLUNAS_RTC_NOTA + COLUNAS_RTC_TOTAL


def _totais(ide: Element | None, total: Element | None) -> dict[str, Any]:
    """Totais da nota que são lidos por achatamento — Reforma e Seletivo."""
    saida: dict[str, Any] = {}
    ibscbstot = achar(total, "IBSCBSTot")
    if ibscbstot is not None:
        achatar(ibscbstot, "IBSCBSTot", saida)
    istot = achar(total, "ISTot")
    if istot is not None:
        achatar(istot, "ISTot", saida)
    novo_total = texto(total, "vNFTot")
    if novo_total:
        saida["vNFTot"] = numero(novo_total)
    compra_gov = achar(ide, "gCompraGov")
    if compra_gov is not None:
        achatar(compra_gov, "gCompraGov", saida)
    return saida


def _reforma_do_item(det: Element) -> dict[str, Any]:
    """Grupos do item lidos por achatamento: IBS/CBS, Seletivo e `vItem`."""
    saida: dict[str, Any] = {}
    ibscbs = achar(det, "IBSCBS")
    if ibscbs is not None:
        achatar(ibscbs, "IBSCBS", saida)
    seletivo = achar(det, "IS")
    if seletivo is not None:
        achatar(seletivo, "IS", saida)
    # `vItem` é filho direto de `det`, não de um grupo de imposto.
    vitem = det.find("{*}vItem")
    if vitem is not None and vitem.text:
        saida["vItem"] = numero(vitem.text.strip())
    return saida


def processar(raiz: Element, arquivo: str) -> list[dict[str, Any]] | None:
    """As linhas de itens desta NF-e, ou `None` se o XML não for uma NF-e."""
    inf = achar(raiz, "infNFe")
    if inf is None:
        return None

    ide = achar(inf, "ide")
    emit = achar(inf, "emit")
    dest = achar(inf, "dest")
    total = achar(inf, "total")
    icms_tot = achar(total, "ICMSTot")
    transp = achar(inf, "transp")
    pag = achar(inf, "pag")
    inf_adic = achar(inf, "infAdic")

    emitente_cnpj = texto(emit, "CNPJ")
    destinatario_cnpj = texto(dest, "CNPJ")

    pagamento = texto(achar(pag, "detPag"), "tPag") if pag is not None else ""

    #: O que é da nota e se repete em cada linha de item.
    da_nota: dict[str, Any] = {
        "Arquivo": arquivo,
        "Chave": inf.attrib.get("Id", "").replace("NFe", ""),
        "Numero NF": texto(ide, "nNF"),
        "Serie": texto(ide, "serie"),
        "Emissao": texto(ide, "dhEmi"),
        "Tipo operacao": texto(ide, "tpNF"),
        "Natureza": texto(ide, "natOp"),
        "Emitente": texto(emit, "xNome"),
        "Emitente Doc": emitente_cnpj or texto(emit, "CPF"),
        "Emitente Tipo": "cnpj" if emitente_cnpj else "cpf",
        "Destinatario": texto(dest, "xNome"),
        "Destinatario Doc": destinatario_cnpj or texto(dest, "CPF"),
        "Destinatario Tipo": "cnpj" if destinatario_cnpj else "cpf",
        "Pagamento": pagamento,
        "Desconto NF": numero(texto(icms_tot, "vDesc")),
        "Tipo Frete": texto(transp, "modFrete"),
        "Seguro NF": numero(texto(icms_tot, "vSeg")),
        "Outras Despesas NF": numero(texto(icms_tot, "vOutro")),
        "BC ICMS NF": numero(texto(icms_tot, "vBC")),
        "BC ICMS-ST NF": numero(texto(icms_tot, "vBCST")),
        "ICMS-ST NF": numero(texto(icms_tot, "vST")),
        "PIS NF": numero(texto(icms_tot, "vPIS")),
        "COFINS NF": numero(texto(icms_tot, "vCOFINS")),
        "PIS-ST NF": numero(texto(icms_tot, "vPISST")),
        "COFINS-ST NF": numero(texto(icms_tot, "vCOFINSST")),
        "IPI NF": numero(texto(icms_tot, "vIPI")),
        "Valor NF": numero(texto(icms_tot, "vNF")),
        "Observacao": texto(inf_adic, "infCpl"),
    }
    da_nota.update(_totais(ide, total))

    linhas = []
    for det in inf.findall(".//{*}det"):
        prod = achar(det, "prod")

        # O ICMS vem num filho cujo nome é o próprio CST (ICMS00, ICMS20,
        # ICMSSN102…). Não se procura pelo nome: pega-se o primeiro filho.
        icms = achar(det, "ICMS")
        icms_sub = icms[0] if icms is not None and len(icms) else None
        pis = achar(det, "PIS")
        pis_sub = pis[0] if pis is not None and len(pis) else None
        cofins = achar(det, "COFINS")
        cofins_sub = cofins[0] if cofins is not None and len(cofins) else None
        ipi = achar(det, "IPI")
        ipi_sub = achar(ipi, "IPITrib") if ipi is not None else None

        linha: dict[str, Any] = dict(da_nota)
        linha.update({
            "Item": det.attrib.get("nItem", ""),
            "Produto": texto(prod, "xProd"),
            "NCM": texto(prod, "NCM"),
            "CFOP": texto(prod, "CFOP"),
            "Qtd": numero(texto(prod, "qCom")),
            "Valor Unit": numero(texto(prod, "vUnCom")),
            "Valor Item": numero(texto(prod, "vProd")),
            "cBenef": texto(det, "cBenef"),
            "CST ICMS Item": texto(icms_sub, "CST") or texto(icms_sub, "CSOSN"),
            "BC ICMS Item": numero(texto(icms_sub, "vBC")),
            "Aliquota ICMS Item": numero(texto(icms_sub, "pICMS")),
            "Valor ICMS Item": numero(texto(icms_sub, "vICMS")),
            "BC ICMS-ST Item": numero(texto(icms_sub, "vBCST")),
            "Valor ICMS-ST Item": numero(texto(icms_sub, "vICMSST")),
            "Aliquota ICMS-ST Item": numero(texto(icms_sub, "pICMSST")),
            "PIS CST": texto(pis_sub, "CST"),
            "PIS Base": numero(texto(pis_sub, "vBC")),
            "PIS Aliquota": numero(texto(pis_sub, "pPIS")),
            "PIS Valor": numero(texto(pis_sub, "vPIS")),
            "PIS-ST Item": numero(texto(achar(det, "PISST"), "vPIS")),
            "COFINS CST": texto(cofins_sub, "CST"),
            "COFINS Base": numero(texto(cofins_sub, "vBC")),
            "COFINS Aliquota": numero(texto(cofins_sub, "pCOFINS")),
            "COFINS Valor": numero(texto(cofins_sub, "vCOFINS")),
            "COFINS-ST Item": numero(texto(achar(det, "COFINSST"), "vCOFINS")),
            "IPI CST": texto(ipi_sub, "CST"),
            "IPI Aliquota": numero(texto(ipi_sub, "pIPI")),
            "IPI Base": numero(texto(ipi_sub, "vBC")),
            "IPI Valor": numero(texto(ipi_sub, "vIPI")),
        })
        linha.update(_reforma_do_item(det))
        linhas.append(linha)

    return linhas
