"""O CT-e vira uma linha por documento, com todas as tags que ele trouxer.

Diferente da NF-e, aqui não há lista de colunas escolhida a dedo: o documento
inteiro é achatado. O motivo é prático — o CT-e tem muitas variantes (normal,
complementar, substituição, anulação, multimodal) e cada uma preenche um
conjunto diferente de grupos. Escolher colunas deixaria de fora justamente a
variante rara, que é a que costuma precisar de conferência.

A consequência é que as colunas do CT-e mudam conforme o lote. É esperado.
"""
from __future__ import annotations

from typing import Any
from xml.etree.ElementTree import Element

from .campos import achar, achatar, sem_namespace


def processar(raiz: Element, arquivo: str) -> dict[str, Any] | None:
    """A linha deste CT-e, ou `None` se o XML não for um CT-e."""
    inf = achar(raiz, "infCte")
    if inf is None:
        return None

    linha: dict[str, Any] = {
        "Arquivo": arquivo,
        "Chave CT-e": inf.attrib.get("Id", "").replace("CTe", ""),
        "Versao": inf.attrib.get("versao", ""),
    }

    # ide, emit, rem, dest, vPrest, imp (com os grupos IBS/CBS do CT-e,
    # quando houver), infCTeNorm e o que mais vier.
    for filho in inf:
        achatar(filho, sem_namespace(filho.tag), linha)

    # Protocolo de autorização, presente quando o XML é o `cteProc`.
    protocolo = achar(raiz, "protCTe")
    if protocolo is not None:
        inf_prot = achar(protocolo, "infProt")
        if inf_prot is not None:
            for filho in inf_prot:
                achatar(filho, "protocolo/" + sem_namespace(filho.tag), linha)

    return linha
