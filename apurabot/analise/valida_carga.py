"""Afere o algoritmo de equalização de carga efetiva contra a classificação manual.

A carga bruta (ICMS / valor contábil) traz artefatos porque o valor contábil
inclui parcelas fora da base do ICMS. A equalização traz o valor para a carga
nominal mais próxima, limitada pela alíquota do ICMS.

Resultado em Julho/2026: 2.333 de 2.336 linhas (99,87%).
"""
import collections
from _comum import abrir, leitor

CARGAS_NOMINAIS = [4, 7, 12, 17, 18, 19, 20.5, 25]


def equalizar(carga_bruta_pct, aliquota):
    """Carga nominal mais próxima da bruta, nunca acima da alíquota."""
    teto = aliquota if aliquota else 100
    candidatas = [c for c in CARGAS_NOMINAIS if c <= teto + 1e-9] or CARGAS_NOMINAIS
    return min(candidatas, key=lambda c: abs(c - carga_bruta_pct))


def main():
    aba = abrir().sheet_by_name("Livro Fiscal")
    v = leitor(aba)
    acertos = divergencias = 0
    detalhe = []

    for r in range(1, aba.nrows):
        manual = v(r, "Carga efetiva")
        if not isinstance(manual, float):
            continue                      # sem carga, ou marcada como "CIAP"
        contabil = v(r, "Vlr. contábil") or 0
        if not contabil:
            continue
        icms = v(r, "Vlr. do ICMS") or 0
        aliquota = v(r, "Alíquota ICMS") or 0
        previsto = equalizar(icms / contabil * 100, aliquota)

        if abs(previsto - manual) < 1e-9:
            acertos += 1
        else:
            divergencias += 1
            detalhe.append((str(v(r, "Cód. de tributação")), aliquota,
                            v(r, "Base do ICMS"), contabil, icms, manual, previsto))

    total = acertos + divergencias
    print(f"Aderência: {acertos}/{total} = {acertos / total * 100:.2f}%\n")
    if detalhe:
        print("Divergências (esperadas apenas onde houve reclassificação manual):")
        for cst, aliq, base, cont, icms, man, prev in detalhe:
            print(f"  CST {cst[:2]} aliq {aliq:>5} base {base:>12,.2f} "
                  f"contábil {cont:>12,.2f} ICMS {icms:>10,.2f} "
                  f"manual {man} previsto {prev}")

    print("\nCruzamento CST x alíquota -> carga efetiva:")
    tab = collections.Counter()
    for r in range(1, aba.nrows):
        manual = v(r, "Carga efetiva")
        if isinstance(manual, float):
            tab[(str(v(r, "Cód. de tributação"))[:2], v(r, "Alíquota ICMS"), manual)] += 1
    for (cst, aliq, carga), n in sorted(tab.items(), key=lambda kv: (kv[0][0], kv[0][1] or 0)):
        print(f"  CST {cst}  alíquota {aliq:>5}  ->  carga {carga:>5}  ({n} linhas)")


if __name__ == "__main__":
    main()
