"""Número, data e data-hora — como as fontes escrevem, não como o Excel adivinha.

Três fontes, três gramáticas, e nenhuma delas é a do Python:

* o **ASIS** exporta valor como texto com ponto decimal (`4369.14`);
* o **Sankhya** exporta valor como número, e data como texto `dd/mm/aaaa`;
* o **Excel** guarda data como número de série desde 30/12/1899.

O parse de data é **explícito**, nunca delegado. O comentário do VBA registra o
motivo e vale palavra por palavra: deixar o Excel interpretar a string faz ele
assumir `mm/dd` quando o valor permite, e o resultado é uma coluna com datas
misturadas que ninguém percebe.

Quando a data não é interpretável, `data_br` devolve **o texto original** — que
fica visível na planilha para tratamento manual. É a regra nº 4: não adivinhar.
"""
from __future__ import annotations

import re
from datetime import date, datetime, timedelta
from typing import Any

from .texto import texto_de

#: O zero do calendário do Excel. O dia 1 é 01/01/1900.
EPOCA_DO_EXCEL = datetime(1899, 12, 30)

_NUMERO_A_FRENTE = re.compile(r"^[+-]?(\d+\.?\d*|\.\d+)([eE][+-]?\d+)?")


def _val(texto: str) -> float:
    """O `Val` do VBA: lê o número do começo da string e ignora o resto.

    `Val("4369.14 (estimado)")` é `4369.14`; `Val("sem valor")` é `0`.
    """
    achado = _NUMERO_A_FRENTE.match(texto.replace(" ", ""))
    if not achado:
        return 0.0
    try:
        return float(achado.group(0))
    except ValueError:                                  # pragma: no cover
        return 0.0


def numero_br(valor: Any) -> float:
    """O valor da célula como número, nas três notações que chegam.

    | Entrada | Vem de | Sai |
    |---|---|---|
    | `4369.14` (texto) | ASIS | `4369.14` |
    | `4.369,14` (texto) | relatório em português | `4369.14` |
    | `4369,14` (texto) | idem, sem milhar | `4369.14` |
    | `4369.14` (número) | Sankhya | `4369.14` |
    | vazio | qualquer | `0.0` |
    """
    if valor is None:
        return 0.0
    if isinstance(valor, bool):
        return float(valor)
    if isinstance(valor, (int, float)):
        return float(valor)
    texto = texto_de(valor).strip()
    if not texto:
        return 0.0
    if "," in texto and "." in texto:
        return _val(texto.replace(".", "").replace(",", "."))
    if "," in texto:
        return _val(texto.replace(",", "."))
    return _val(texto)


def chave_de_valor(valor: Any) -> str:
    """O valor como chave de confronto: sempre duas casas, sempre com ponto.

    Comparar valor por texto de duas casas é o que o VBA faz, e é o que
    mantém o confronto de serviços reproduzível — `4369.1400000001` e
    `4369.14` são o mesmo pagamento. O preço é conhecido e está documentado:
    diferença de um centavo por arredondamento de fonte não casa.
    """
    return f"{numero_br(valor):.2f}"


def de_serial(numero: float) -> datetime:
    """Número de série do Excel para data."""
    return EPOCA_DO_EXCEL + timedelta(days=float(numero))


def data_br(valor: Any) -> Any:
    """`dd/mm/aaaa` para data de verdade. Não interpretável: **o texto original**.

    Aceita também a data que já chega como data (é o caso do `.xlsx`) e o
    número de série do Excel (é o caso de algumas colunas do `.xls`).
    """
    if isinstance(valor, datetime):
        return valor
    if isinstance(valor, date):
        return valor
    if valor is None:
        return ""
    if isinstance(valor, bool):
        return texto_de(valor)
    if isinstance(valor, (int, float)):
        return de_serial(valor) if valor > 0 else ""
    texto = texto_de(valor).strip()
    if not texto:
        return ""
    partes = texto.split("/")
    if len(partes) == 3:
        dia, mes, ano = (int(_val(p)) for p in partes)
        if 1 <= dia <= 31 and 1 <= mes <= 12 and 1900 <= ano <= 2100:
            try:
                return date(ano, mes, dia)
            except ValueError:                  # 31 de fevereiro e parentes
                return texto
    return texto


def data_hora(valor: Any) -> Any:
    """`dd/mm/aa hh:mm` para data-hora. Não interpretável: **vazio**.

    É o formato da Conferência de Serviços, e o ano de dois dígitos é lido
    como `20aa`.

    O vazio aqui é uma **assimetria conhecida** com `data_br`, que devolve o
    texto original: o mesmo dado ilegível some numa coluna e fica visível na
    outra. Uniformizar as duas é o defeito 12 do porte, e ele espera medição
    sobre arquivo real — até lá vale o comportamento de hoje, defeito e tudo.
    Ver `docs/pendentes/02-porte-do-vba.md`.
    """
    if isinstance(valor, (datetime, date)):
        return valor
    if valor is None or isinstance(valor, bool):
        return ""
    if isinstance(valor, (int, float)):
        return de_serial(valor) if valor > 0 else ""
    texto = texto_de(valor).strip()
    if not texto:
        return ""
    pedacos = texto.split(" ")
    partes = pedacos[0].split("/")
    if len(partes) != 3:
        return ""
    dia, mes, ano = (int(_val(p)) for p in partes)
    if ano < 100:
        ano += 2000
    hora = minuto = 0
    if len(pedacos) > 1:
        relogio = pedacos[1].split(":")
        if len(relogio) >= 2:
            hora, minuto = int(_val(relogio[0])), int(_val(relogio[1]))
    if not (1 <= dia <= 31 and 1 <= mes <= 12 and 1900 <= ano <= 2100):
        return ""
    try:
        return datetime(ano, mes, dia, hora, minuto)
    except ValueError:
        return ""


def zero_ou_vazio(valor: Any) -> bool:
    """Vazio, `0`, `0,00`, `000` — tudo isso é "não há incongruência".

    Texto como `não` devolve **False**, e não é detalhe: é por essa porta que
    a regra B1 deixa de disparar para a nota que nem estava na Conferência de
    Entradas, onde o VBA grava o literal `não`.
    """
    texto = texto_de(valor).strip()
    if not texto:
        return True
    limpo = texto.replace(".", "").replace(",", "").replace(" ", "")
    return bool(limpo) and set(limpo) == {"0"}
