"""Um Livro Fiscal sintético de Rio Brilhante, para teste — sem dado real.

Uma venda que gera débito e benefício, e a NF-e de recebimento do crédito
transferido (CFOP 1601). Os valores são inventados; só o formato é o do
extrato do Sankhya.
"""
from __future__ import annotations

import datetime as dt

import openpyxl

from apurabot.ingestao import COLUNAS

RB = "HINOVE (RIO BRILHANTE)"
CHAVE = "50260800000000000000550050002445641100000000"
RECEBIDO = 62_720.00


def livro(destino, mes: int = 8):
    """Um Livro de Rio Brilhante com uma venda e a nota do crédito recebido."""
    cabecalho = list(COLUNAS)

    def linha(**campos):
        valores = {
            "Nome Fantasia (Empresa)": RB, "Empresa": 2,
            "Dt. do movimento": dt.datetime(2026, mes, 10),
            "Dt. do documento": dt.datetime(2026, mes, 10),
            "Cód. de tributação": "00", "Vlr. contábil": 0, "Base do ICMS": 0,
            "Alíquota ICMS": 0, "Vlr. do ICMS": 0, "UF de Origem": "MS",
            "UF de Destino": "MS", "Espécie do documento": "NFE",
            "Produto": 100000001, "Modelo do Documento": "55",
        }
        valores.update(campos)
        return [valores.get(c) for c in cabecalho]

    wb = openpyxl.Workbook()
    aba = wb.active
    aba.append(cabecalho)
    aba.append(linha(**{
        "Nro único Nota": 1, "Nro. da nota": 10, "CFOP": 5101,
        "Descrição da CFOP": "Vda prod do estab",
        "Entrada/Saída": "Saída", "Vlr. contábil": 100_000,
        "Base do ICMS": 100_000, "Alíquota ICMS": 17, "Vlr. do ICMS": 17_000,
    }))
    aba.append(linha(**{
        "Nro único Nota": 2, "Nro. da nota": 244564, "CFOP": 1601,
        "Entrada/Saída": "Entrada", "Vlr. contábil": RECEBIDO,
        "Cód. de tributação": "90", "Produto": 701000701,
        "Descrição (Produto)": "Recebimento, por transferência, de crédito de ICMS",
        "Descrição Parceiro/Empresa": "EMITENTE DO CRÉDITO", "Chave NF-e": CHAVE,
    }))
    wb.save(destino)
    return destino
