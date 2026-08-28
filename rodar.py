#!/usr/bin/env python3
"""Roda o Apurabot sem instalar nada.

Em máquina corporativa sem elevação de administrador, `pip install` pode falhar
e o executável `apurabot.exe` pode ser barrado pela política de segurança —
o sintoma é "Acesso negado" ao rodar o comando.

Este arquivo contorna as duas coisas: não instala nada e não cria executável.
É o próprio Python, que já está aprovado na máquina, rodando o código da pasta.

**Quem não usa terminal não precisa deste arquivo:** dê dois cliques em
`Apurabot.bat`, na mesma pasta. Ele abre a janela do Apurabot no navegador.

    python rodar.py                    abre a janela no navegador
    python rodar.py apurar "caminho\\do\\livro.xls" --saida "pasta\\de\\saida"
    python rodar.py --help

As três bibliotecas de que o Apurabot depende continuam necessárias:

    pip install --user openpyxl "xlrd==2.0.1" PyYAML
"""
from __future__ import annotations

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
sys.path.insert(0, str(RAIZ / "apurabot" / "src"))

FALTANDO = """
Falta a biblioteca {nome!r} — neste Python:

    {executavel}

A máquina costuma ter mais de um Python instalado, e um `pip install`
sozinho pode instalar em outro. Instale neste, que é o que está rodando:

    "{executavel}" -m pip install --user openpyxl "xlrd==2.0.1" PyYAML

O `--user` instala na sua conta, sem precisar de administrador.
"""

try:
    from apurabot.cli import main
except ModuleNotFoundError as erro:  # dependência ausente
    nome = getattr(erro, "name", "?")
    if nome and nome.startswith("apurabot"):
        raise
    print(FALTANDO.format(nome=nome, executavel=sys.executable), file=sys.stderr)
    raise SystemExit(2) from None

if __name__ == "__main__":
    raise SystemExit(main())
