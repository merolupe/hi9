#!/usr/bin/env python3
"""Roda as ferramentas fiscais sem instalar nada.

Em máquina corporativa sem elevação de administrador, `pip install` pode falhar
e um executável novo pode ser barrado pela política de segurança — o sintoma é
"Acesso negado" ao rodar o comando.

Este arquivo contorna as duas coisas: não instala nada e não cria executável.
É o próprio Python, que já está aprovado na máquina, rodando o código da pasta.

**Quem não usa terminal não precisa deste arquivo:** dê dois cliques em
`Hinove.bat`, na mesma pasta. Ele abre a Central Fiscal no navegador, com as
ferramentas para escolher.

    python rodar.py                    abre a Central no navegador
    python rodar.py dixml lote.zip --saida "pasta\\de\\saida"
    python rodar.py apurabot apurar "caminho\\do\\livro.xls"
    python rodar.py --help

As bibliotecas de que as ferramentas dependem **viajam junto com o código**, em
`vendor/`. Não é preciso instalar nada.
"""
from __future__ import annotations

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent

# Cada ferramenta vive em `<projeto>/src/<pacote>`. A central acha todas
# sozinha; aqui basta ela, que é a porta de entrada.
sys.path.insert(0, str(RAIZ / "central" / "src"))

#: Comandos antigos, de quando o repositório era só o Apurabot. Continuam
#: valendo: `rodar.py apurar livro.xls` é `rodar.py apurabot apurar livro.xls`.
ALIAS_DO_APURABOT = ("apurar", "base-tratada", "janela")

AJUDA = """
Central de Ferramentas Fiscais — Hinove Agrociência S.A.

    python rodar.py                       abre a Central no navegador
    python rodar.py central --help        opções da janela
    python rodar.py dixml --help          lote de XML para planilha
    python rodar.py apurabot --help       apuração de ICMS

Sem argumento nenhum, abre a Central: é o mesmo que dois cliques em
Hinove.bat.
"""

FALTANDO = """
Falta a biblioteca {nome!r} — neste Python:

    {executavel}

Ela deveria ter vindo junto com o código, em `vendor/`, na raiz da pasta. Se a
pasta não está lá, o download veio incompleto: baixe o ZIP de novo e extraia
inteiro.

Para o diagnóstico completo:

    "{executavel}" verificar.py
"""


def main(argv: list[str]) -> int:
    if argv and argv[0] in ("-h", "--help"):
        print(AJUDA)
        return 0

    if not argv:
        ferramenta, resto = "central", []
    elif argv[0] in ALIAS_DO_APURABOT:
        ferramenta, resto = "apurabot", argv
    else:
        ferramenta, resto = argv[0], argv[1:]

    if ferramenta == "central":
        from central.cli import main as rodar
    elif ferramenta == "apurabot":
        import central                       # põe as ferramentas no sys.path
        from apurabot.cli import main as rodar
    elif ferramenta == "dixml":
        import central                       # idem
        from dixml.cli import main as rodar
    else:
        print(f"Não conheço a ferramenta {ferramenta!r}.\n{AJUDA}", file=sys.stderr)
        return 2

    return rodar(resto)


if __name__ == "__main__":
    try:
        codigo = main(sys.argv[1:])
    except ModuleNotFoundError as erro:      # dependência ausente
        nome = getattr(erro, "name", "?")
        if nome and nome.split(".")[0] in ("central", "apurabot", "dixml"):
            raise
        print(FALTANDO.format(nome=nome, executavel=sys.executable), file=sys.stderr)
        raise SystemExit(2) from None
    raise SystemExit(codigo)
