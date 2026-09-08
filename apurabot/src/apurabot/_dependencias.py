"""Faz as bibliotecas de terceiros funcionarem sem instalação.

O Apurabot roda em máquina corporativa sem elevação de administrador, onde
`pip install` já falhou de duas maneiras: barrado pela política de segurança, e
acertando um Python diferente do que a ferramenta abre. As duas vezes a pessoa
tinha feito tudo certo e mesmo assim não rodava.

As quatro bibliotecas de que as ferramentas dependem são **Python puro**, então
elas viajam junto com o código, em `vendor/`, na raiz do repositório. Baixar a
pasta e dar dois cliques passa a bastar: nada é instalado, nada é baixado, e o
Python que abrir a ferramenta é indiferente.

`vendor/` fica na raiz, e não dentro de um projeto, porque não é do Apurabot:
é do repositório. O DiXML e as ferramentas que vierem carregam as mesmas
cópias — ver `vendor/LEIA-ME.md`.

`vendor/` entra no **fim** do `sys.path`, nunca no começo: uma biblioteca que
o administrador tenha instalado na máquina continua tendo precedência. A cópia
local é a rede de segurança, não a preferência.
"""
from __future__ import annotations

import sys
from pathlib import Path

#: O que `vendor/` carrega, para a mensagem de erro saber o que citar.
EMBARCADAS = ("openpyxl", "et_xmlfile", "xlrd", "yaml")


def _localizar() -> Path:
    """Procura `vendor/` subindo a partir daqui.

    Subir em vez de fixar o caminho mantém a pasta encontrável se o projeto for
    movido ou aninhado — o que importa é onde `vendor/` está, não a distância.
    """
    for pasta in Path(__file__).resolve().parents:
        candidata = pasta / "vendor"
        if (candidata / "openpyxl").is_dir():
            return candidata
    return Path(__file__).resolve().parents[3] / "vendor"   # o lugar esperado


VENDOR = _localizar()


def preparar() -> None:
    """Põe `vendor/` ao alcance do import, sem tirar a vez de quem já existe."""
    caminho = str(VENDOR)
    if VENDOR.is_dir() and caminho not in sys.path:
        sys.path.append(caminho)


preparar()
