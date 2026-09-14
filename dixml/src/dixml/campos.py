"""Como um pedaço de XML vira coluna de planilha.

Duas regras atravessam o arquivo inteiro:

1. **Namespace não importa.** A NF-e e o CT-e declaram namespace no elemento
   raiz; as buscas usam `{*}` para ignorá-lo e continuar funcionando quando a
   SEFAZ publicar uma versão nova do esquema.

2. **Só vira número o que é decimal.** Chave de acesso, CNPJ, número da nota,
   NCM e CFOP são códigos: viram número, viram notação científica, perdem zero
   à esquerda e deixam de casar com o resto. Ficam texto, de propósito.
"""
from __future__ import annotations

import re
from typing import Any
from xml.etree.ElementTree import Element

#: Decimal do padrão da NF-e: `9999.99`. Sem ponto decimal não é valor.
PADRAO_DECIMAL = re.compile(r"^-?\d+\.\d+$")

#: O bloco de assinatura digital não tem informação fiscal e tem centenas de
#: caracteres por tag. Fica fora da planilha.
IGNORADAS = ("Signature",)


def sem_namespace(tag: str) -> str:
    """`{http://...}ide` vira `ide`."""
    return tag.split("}")[-1] if "}" in tag else tag


def valor(texto: str | None) -> Any:
    """Converte para número **somente** o que é decimal; o resto fica texto."""
    if texto is None:
        return ""
    texto = texto.strip()
    if PADRAO_DECIMAL.match(texto):
        try:
            return float(texto)
        except ValueError:
            return texto
    return texto


def numero(texto: str | None) -> Any:
    """Converte para número um campo que se sabe numérico.

    Diferente de `valor`: aqui a coluna é sabidamente de valor ou quantidade
    (`vNF`, `qCom`, `pICMS`…), então `1000` também vira número. É por isso que
    as duas funções existem — a distinção é entre "campo numérico" e "campo
    que por acaso parece número".
    """
    if texto is None or texto == "":
        return ""
    try:
        return float(texto)
    except ValueError:
        return texto


def achar(elemento: Element | None, tag: str) -> Element | None:
    """O primeiro descendente com esta tag, em qualquer namespace."""
    if elemento is None:
        return None
    return elemento.find(f".//{{*}}{tag}")


def texto(elemento: Element | None, tag: str) -> str:
    """O conteúdo do primeiro descendente com esta tag, ou vazio."""
    if elemento is None:
        return ""
    achado = elemento.find(f".//{{*}}{tag}")
    return achado.text.strip() if achado is not None and achado.text else ""


def achatar(elemento: Element, caminho: str, saida: dict[str, Any]) -> None:
    """Achata um ramo do XML em `{caminho/da/tag: valor}`.

    É o que permite capturar grupo que ainda não existe: tudo o que a SEFAZ
    acrescentar ao XML aparece como coluna nova, sem alteração de código. As
    colunas-semente da Reforma (`nfe.py`) existem para o contrário — garantir
    que a coluna apareça mesmo quando nenhuma nota do lote traz o grupo.

    Tag repetida no mesmo caminho ganha sufixo `_2`, `_3`…
    """
    if sem_namespace(elemento.tag) in IGNORADAS:
        return
    filhos = list(elemento)
    if filhos:
        for filho in filhos:
            achatar(filho, caminho + "/" + sem_namespace(filho.tag), saida)
        return

    conteudo = (elemento.text or "").strip()
    if not conteudo:
        return
    chave, i = caminho, 2
    while chave in saida:
        chave = f"{caminho}_{i}"
        i += 1
    saida[chave] = valor(conteudo)
