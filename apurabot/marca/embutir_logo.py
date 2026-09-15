#!/usr/bin/env python3
"""Embute a arte oficial do logo da Hinove dentro da janela.

A janela é um arquivo só e abre com a máquina desconectada da internet: o
servidor local entrega apenas `pagina.html` e nenhuma imagem é buscada por
URL. Então o PNG entra como `data:` URI, dentro do próprio HTML.

    python3 marca/embutir_logo.py

Rode de novo sempre que trocar o `marca/hinove.png`. Para voltar ao logo
desenhado em SVG:

    git checkout src/apurabot/web/pagina.html
"""
from __future__ import annotations

import base64
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
PNG = AQUI / "hinove.png"
PAGINA = AQUI.parent / "src" / "apurabot" / "web" / "pagina.html"

INICIO = "<!-- logo:inicio -->"
FIM = "<!-- logo:fim -->"

LARGURA_MINIMA = 1200          # a janela mostra em 280 px, em HiDPI dobra
PESO_MAXIMO = 300 * 1024       # base64 engorda uns 33% dentro do HTML


def _largura_do_png(dados: bytes) -> int | None:
    """A largura sai do cabeçalho IHDR, sem depender de biblioteca."""
    if dados[:8] != b"\x89PNG\r\n\x1a\n" or dados[12:16] != b"IHDR":
        return None
    return int.from_bytes(dados[16:20], "big")


def main() -> int:
    if not PNG.exists():
        print(f"não achei {PNG}.\n")
        print("Ponha a arte oficial ali com esse nome — PNG, fundo")
        print(f"transparente, pelo menos {LARGURA_MINIMA} px de largura.")
        print("Enquanto ela não existir, a janela desenha o logo em SVG.")
        return 1

    dados = PNG.read_bytes()
    largura = _largura_do_png(dados)
    if largura is None:
        print(f"{PNG.name} não é um PNG. Converta antes de embutir.")
        return 1
    if largura < LARGURA_MINIMA:
        print(f"{PNG.name} tem {largura} px de largura; o mínimo é "
              f"{LARGURA_MINIMA} px, senão sai borrado em tela HiDPI.")
        return 1

    html = PAGINA.read_text(encoding="utf-8")
    if INICIO not in html or FIM not in html:
        print(f"as marcas {INICIO} e {FIM} sumiram de pagina.html.")
        return 1

    uri = "data:image/png;base64," + base64.b64encode(dados).decode("ascii")
    novo = (
        f'{INICIO}\n'
        f'      <img src="{uri}"\n'
        f'           alt="Hinove Fertilizantes Especiais">\n'
        f'      {FIM}'
    )
    antes, resto = html.split(INICIO, 1)
    depois = resto.split(FIM, 1)[1]
    PAGINA.write_text(antes + novo + depois, encoding="utf-8")

    peso = len(uri)
    aviso = "" if peso <= PESO_MAXIMO else "  (pesado — considere reduzir)"
    print(f"logo embutido: {largura} px, {peso / 1024:.0f} KB no HTML{aviso}")
    print("Confira a janela e rode a suíte antes de subir.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
