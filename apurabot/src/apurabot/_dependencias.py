"""Faz as bibliotecas de terceiros funcionarem sem instalação.

O Apurabot roda em máquina corporativa sem elevação de administrador, onde
`pip install` já falhou de duas maneiras: barrado pela política de segurança, e
acertando um Python diferente do que a ferramenta abre. As duas vezes a pessoa
tinha feito tudo certo e mesmo assim não rodava.

As três bibliotecas de que o Apurabot depende são **Python puro**, então elas
viajam junto com o código, em `vendor/`. Baixar a pasta e dar dois cliques
passa a bastar: nada é instalado, nada é baixado, e o Python que abrir a
ferramenta é indiferente.

`vendor/` entra no **fim** do `sys.path`, nunca no começo: uma biblioteca que
o administrador tenha instalado na máquina continua tendo precedência. A cópia
local é a rede de segurança, não a preferência.
"""
from __future__ import annotations

import sys
from pathlib import Path

VENDOR = Path(__file__).resolve().parent / "vendor"

#: O que `vendor/` carrega, para a mensagem de erro saber o que citar.
EMBARCADAS = ("openpyxl", "et_xmlfile", "xlrd", "yaml")


def preparar() -> None:
    """Põe `vendor/` ao alcance do import, sem tirar a vez de quem já existe."""
    caminho = str(VENDOR)
    if VENDOR.is_dir() and caminho not in sys.path:
        sys.path.append(caminho)


preparar()
