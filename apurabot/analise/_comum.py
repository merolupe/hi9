"""Utilitários de leitura do arquivo de apuração (.xls) do Sankhya."""
import sys
import xlrd

ERROS = {0x00: "#NULL!", 0x07: "#DIV/0!", 0x0F: "#VALUE!", 0x17: "#REF!",
         0x1D: "#NAME?", 0x24: "#NUM!", 0x2A: "#N/A"}


def abrir(caminho=None):
    caminho = caminho or (sys.argv[1] if len(sys.argv) > 1 else None)
    if not caminho:
        sys.exit("uso: python <script>.py <apuracao.xls>")
    return xlrd.open_workbook(caminho, on_demand=True)


def indexar(aba):
    """Mapeia nome do cabeçalho -> índice da coluna."""
    return {str(aba.cell(0, c).value).strip(): c for c in range(aba.ncols)}


def valor(aba, linha, coluna_idx):
    c = aba.cell(linha, coluna_idx)
    if c.ctype in (0, 6):
        return None
    if c.ctype == 5:
        return ERROS.get(c.value, f"#ERR{c.value}")
    return c.value


def leitor(aba):
    """Devolve uma função valor(linha, nome_da_coluna)."""
    ix = indexar(aba)
    return lambda linha, nome: valor(aba, linha, ix[nome])
