"""Reproduz o crédito presumido de Rio Brilhante a partir do Livro Fiscal.

Pontos de Atenção: 67% de crédito sobre o saldo devedor nas saídas intraestaduais
e 80% nas interestaduais. Ver docs/apurabot/06-decisoes-pendentes.md, item 1.
"""
import collections
from _comum import abrir, leitor

FILIAL = "HINOVE (RIO BRILHANTE)"
CREDITO_MANTIDO = 138_666.94      # aba ESTORNO, Julho/2026
BF_LANCADO = 283_766.56           # aba ESTORNO, Julho/2026
PCT_INTRA, PCT_INTER = 0.67, 0.80


def main():
    aba = abrir().sheet_by_name("Livro Fiscal")
    v = leitor(aba)
    debito = collections.Counter()
    por_cfop = collections.Counter()

    for r in range(1, aba.nrows):
        if v(r, "Nome Fantasia (Empresa)") != FILIAL:
            continue
        if v(r, "Entrada/Saída") != "Saída":
            continue
        icms = v(r, "Vlr. do ICMS") or 0
        if not icms:
            continue
        tipo = "INTRA" if v(r, "UF de Origem") == v(r, "UF de Destino") else "INTER"
        debito[tipo] += icms
        por_cfop[(int(v(r, "CFOP")), tipo, str(v(r, "Descrição da CFOP"))[:32])] += icms

    d_intra, d_inter = debito["INTRA"], debito["INTER"]
    total = d_intra + d_inter

    print("Débito de saída por CFOP:")
    for (cfop, tipo, desc), val in sorted(por_cfop.items(), key=lambda kv: -kv[1]):
        print(f"  {cfop}  {tipo:5}  {desc:34}  {val:>14,.2f}")
    print(f"  {'TOTAL':49}  {total:>14,.2f}\n")

    saldo_devedor = total - CREDITO_MANTIDO
    p_intra = d_intra / total
    bf = saldo_devedor * (PCT_INTRA * p_intra + PCT_INTER * (1 - p_intra))

    print(f"débito INTRA        {d_intra:>14,.2f}  ({p_intra * 100:.2f}%)")
    print(f"débito INTER        {d_inter:>14,.2f}  ({(1 - p_intra) * 100:.2f}%)")
    print(f"crédito mantido     {CREDITO_MANTIDO:>14,.2f}")
    print(f"saldo devedor       {saldo_devedor:>14,.2f}")
    print(f"B.F. calculado      {bf:>14,.2f}")
    print(f"B.F. lançado        {BF_LANCADO:>14,.2f}")
    print(f"diferença           {bf - BF_LANCADO:>+14,.2f}  ({abs(bf / BF_LANCADO - 1) * 100:.2f}%)")


if __name__ == "__main__":
    main()
