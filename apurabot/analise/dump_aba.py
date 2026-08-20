"""Imprime o conteúdo de uma aba com as letras das colunas.

    python dump_aba.py <apuracao.xls> "ESTORNO" 0 97
"""
import sys
from _comum import abrir, valor


def letra(i):
    nome, i = "", i + 1
    while i:
        i, resto = divmod(i - 1, 26)
        nome = chr(65 + resto) + nome
    return nome


def formatar(aba, linha, coluna, datemode):
    import xlrd
    c = aba.cell(linha, coluna)
    if c.ctype == 3:
        try:
            return str(xlrd.xldate.xldate_as_datetime(c.value, datemode).date())
        except Exception:
            return str(c.value)
    if c.ctype == 2:
        return str(int(c.value)) if c.value == int(c.value) else f"{c.value:.4f}"
    if c.ctype == 4:
        return "TRUE" if c.value else "FALSE"
    v = valor(aba, linha, coluna)
    return "" if v is None else str(v).strip()


def main():
    if len(sys.argv) < 3:
        sys.exit('uso: python dump_aba.py <apuracao.xls> "<aba>" [linha_ini] [linha_fim]')
    livro = abrir(sys.argv[1])
    aba = livro.sheet_by_name(sys.argv[2])
    ini = int(sys.argv[3]) if len(sys.argv) > 3 else 0
    fim = int(sys.argv[4]) if len(sys.argv) > 4 else aba.nrows

    for r in range(ini, min(fim, aba.nrows)):
        celulas = [f"{letra(c)}={t}" for c in range(aba.ncols)
                   if (t := formatar(aba, r, c, livro.datemode)) != ""]
        if celulas:
            print(f"r{r + 1}: " + " ; ".join(celulas))


if __name__ == "__main__":
    main()
