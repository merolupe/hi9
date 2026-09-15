"""Data e hora do XML viram duas colunas, e a data vira data de verdade.

O XML traz `2026-06-01T10:30:00-03:00`. Deixado como texto, o Excel não filtra
por período, não ordena e não entra em tabela dinâmica por mês. Quebrar em
`Emissao Data` (data de verdade, exibida como `dd/mm/aaaa`) e `Emissao Hora`
(texto `hh:mm:ss`) resolve os três de uma vez.

A detecção é por conteúdo, não por nome de coluna: qualquer coluna cujos
valores preenchidos sejam **todos** data ISO é convertida. Assim vale para
`dhEmi`, `dhSaiEnt`, `dhRecbto` e para o que a SEFAZ criar depois, sem
manutenção de lista.

O fuso não é convertido: a data é a que está escrita no documento.
"""
from __future__ import annotations

import re
from datetime import date
from typing import Any

PADRAO_DATAHORA = re.compile(r"^(\d{4})-(\d{2})-(\d{2})T(\d{2}:\d{2}:\d{2})")
PADRAO_SO_DATA = re.compile(r"^(\d{4})-(\d{2})-(\d{2})$")


def _e_data(valor: Any) -> bool:
    return isinstance(valor, str) and valor != ""


def _para_data(texto: str) -> date | str:
    casou = PADRAO_DATAHORA.match(texto) or PADRAO_SO_DATA.match(texto)
    if not casou:
        return ""
    return date(int(casou.group(1)), int(casou.group(2)), int(casou.group(3)))


def _classificar(valores: list[str]) -> str:
    """`"datahora"`, `"data"` ou `""` quando a coluna não é de data."""
    if not valores:
        return ""
    if all(PADRAO_DATAHORA.match(v) for v in valores):
        return "datahora"
    if all(PADRAO_SO_DATA.match(v) for v in valores):
        return "data"
    return ""


def separar(
    colunas: list[str], linhas: list[dict[str, Any]]
) -> tuple[list[str], list[dict[str, Any]], list[str]]:
    """Devolve `(colunas, linhas, colunas_de_data)` com as datas separadas."""
    if not linhas:
        return colunas, linhas, []

    tipos: dict[str, str] = {}
    for coluna in colunas:
        preenchidos = [
            linha[coluna] for linha in linhas
            if _e_data(linha.get(coluna, ""))
        ]
        tipo = _classificar(preenchidos)
        if tipo:
            tipos[coluna] = tipo
    if not tipos:
        return colunas, linhas, []

    novas_colunas: list[str] = []
    colunas_de_data: list[str] = []
    for coluna in colunas:
        if coluna not in tipos:
            novas_colunas.append(coluna)
            continue
        novas_colunas.append(f"{coluna} Data")
        colunas_de_data.append(f"{coluna} Data")
        if tipos[coluna] == "datahora":
            novas_colunas.append(f"{coluna} Hora")

    for linha in linhas:
        for coluna, tipo in tipos.items():
            bruto = linha.pop(coluna, "")
            if not _e_data(bruto):
                linha[f"{coluna} Data"] = ""
                if tipo == "datahora":
                    linha[f"{coluna} Hora"] = ""
                continue
            linha[f"{coluna} Data"] = _para_data(bruto)
            if tipo == "datahora":
                casou = PADRAO_DATAHORA.match(bruto)
                linha[f"{coluna} Hora"] = casou.group(4) if casou else ""

    return novas_colunas, linhas, colunas_de_data
