"""Leitura do relatório extraído, seja `.xls` ou `.xlsx`.

O Sankhya entrega `.xls` antigo; alguém pode reabrir e salvar como `.xlsx`.
As duas coisas chegam aqui e saem iguais: uma matriz de valores onde número é
número e texto é texto. Essa distinção importa — o CFOP vem numérico e o CST
vem como texto (`41-Não tributada`), e cada um é tratado de um jeito.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

EXTENSOES = (".xls", ".xlsx", ".xlsm")


class LayoutInvalido(Exception):
    """O arquivo não parece o relatório Movimento Livros Fiscais."""


def _ler_xls(caminho: Path) -> list[list[Any]]:
    import xlrd

    livro = xlrd.open_workbook(str(caminho))
    aba = livro.sheet_by_index(0)
    return [[aba.cell_value(r, c) for c in range(aba.ncols)]
            for r in range(aba.nrows)]


def _ler_xlsx(caminho: Path) -> list[list[Any]]:
    import openpyxl

    livro = openpyxl.load_workbook(str(caminho), data_only=True, read_only=True)
    try:
        aba = livro.worksheets[0]
        return [[c if c is not None else "" for c in linha]
                for linha in aba.iter_rows(values_only=True)]
    finally:
        livro.close()


def ler(caminho: Path) -> list[list[Any]]:
    """A primeira aba do arquivo, como matriz de valores."""
    caminho = Path(caminho)
    if not caminho.is_file():
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho}")
    sufixo = caminho.suffix.lower()
    if sufixo == ".xls":
        return _ler_xls(caminho)
    if sufixo in (".xlsx", ".xlsm"):
        return _ler_xlsx(caminho)
    raise LayoutInvalido(
        f"{caminho.name} não é uma planilha que o Fiscalbot leia. "
        f"Esperado {', '.join(EXTENSOES)}."
    )
