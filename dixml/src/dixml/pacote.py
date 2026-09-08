"""De um `.zip` até cada XML lá dentro — inclusive `.zip` dentro de `.zip`.

O lote que a contabilidade baixa costuma vir aninhado: um `.zip` do mês com um
`.zip` por filial, com os XMLs dentro. Descer sozinho poupa a pessoa de
descompactar em cascata antes de usar a ferramenta.

Descer sozinho também abre uma porta: um `.zip` pode se expandir muito além do
próprio tamanho, de propósito ou por acidente. Por isso a descida tem teto de
profundidade e teto de bytes descompactados — a ferramenta agora recebe arquivo
pela janela do navegador, e o que entra por ali é conferido.

Zip aninhado corrompido não derruba a execução: fica registrado e a leitura
continua. Num lote de milhares de notas, parar tudo por causa de um arquivo
ilegível é pior do que seguir e avisar.
"""
from __future__ import annotations

import io
import zipfile
from collections.abc import Iterator
from pathlib import Path

#: Quantos `.zip` dentro de `.zip` a leitura aceita descer.
PROFUNDIDADE_MAXIMA = 8

#: Teto de bytes já descompactados numa execução (2 GB). Um lote mensal inteiro
#: fica muito abaixo disso; passar daí é engano de arquivo, não lote de notas.
TETO_DESCOMPACTADO = 2 * 1024 * 1024 * 1024


class PacoteGrandeDemais(Exception):
    """O conteúdo descompactado passou do teto."""


class Orcamento:
    """Quanto ainda pode ser descompactado nesta execução."""

    def __init__(self, teto: int = TETO_DESCOMPACTADO) -> None:
        self.teto = teto
        self.gasto = 0

    def gastar(self, bytes_: int) -> None:
        self.gasto += bytes_
        if self.gasto > self.teto:
            raise PacoteGrandeDemais(
                f"O conteúdo descompactado passou de "
                f"{self.teto // (1024 * 1024)} MB. Se o lote é este mesmo, "
                f"divida-o em partes; se não, confira se o arquivo é o certo."
            )


def _percorrer(
    zf: zipfile.ZipFile,
    prefixo: str,
    erros: list[str],
    orcamento: Orcamento,
    profundidade: int,
) -> Iterator[tuple[str, bytes]]:
    for nome in zf.namelist():
        if nome.endswith("/"):
            continue                                  # entrada de diretório
        minusculo = nome.lower()
        if minusculo.endswith(".xml"):
            try:
                orcamento.gastar(zf.getinfo(nome).file_size)
                yield prefixo + nome, zf.read(nome)
            except PacoteGrandeDemais:
                raise
            except Exception as erro:                 # noqa: BLE001
                erros.append(f"{prefixo}{nome} (leitura do XML: {erro})")
        elif minusculo.endswith(".zip"):
            if profundidade >= PROFUNDIDADE_MAXIMA:
                erros.append(
                    f"{prefixo}{nome} (zip aninhado além de "
                    f"{PROFUNDIDADE_MAXIMA} níveis: não foi aberto)"
                )
                continue
            try:
                orcamento.gastar(zf.getinfo(nome).file_size)
                interno = zipfile.ZipFile(io.BytesIO(zf.read(nome)), "r")
            except PacoteGrandeDemais:
                raise
            except Exception as erro:                 # noqa: BLE001
                erros.append(f"{prefixo}{nome} (zip aninhado ilegível: {erro})")
                continue
            with interno:
                yield from _percorrer(
                    interno, f"{prefixo}{nome}::", erros, orcamento, profundidade + 1
                )
        # qualquer outro tipo de arquivo dentro do zip é ignorado


def xmls(
    caminhos: list[Path], erros: list[str], orcamento: Orcamento | None = None
) -> Iterator[tuple[str, bytes]]:
    """Cada XML de cada `.zip`, como `(nome_de_exibição, conteúdo)`.

    O nome de exibição carrega o caminho dentro dos pacotes
    (`externo.zip::interno.zip::nota.xml`) — é o que permite achar a origem de
    uma linha da planilha meses depois.
    """
    orcamento = orcamento or Orcamento()
    for caminho in caminhos:
        base = Path(caminho).name
        try:
            zf = zipfile.ZipFile(caminho, "r")
        except Exception as erro:                     # noqa: BLE001
            erros.append(f"{base} (abertura do zip: {erro})")
            continue
        with zf:
            yield from _percorrer(zf, f"{base}::", erros, orcamento, 1)
