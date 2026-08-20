"""Perfil do Livro Fiscal: volume, estabelecimentos, CFOPs, CSTs e cargas."""
import collections
from _comum import abrir, leitor

CAMPOS = ["Nome Fantasia (Empresa)", "Entrada/Saída", "Carga efetiva",
          "Cód. de tributação", "Espécie do documento", "Modelo do Documento"]


def main():
    livro = abrir()
    for nome in livro.sheet_names():
        aba = livro.sheet_by_name(nome)
        if "Nro único Nota" not in {str(aba.cell(0, c).value).strip()
                                    for c in range(aba.ncols)}:
            continue
        v = leitor(aba)
        print(f"\n===== {nome}: {aba.nrows - 1} linhas, {aba.ncols} colunas =====")

        contagens = {c: collections.Counter() for c in CAMPOS}
        cfops, notas, produtos, cancelados = collections.Counter(), set(), set(), 0
        for r in range(1, aba.nrows):
            for c in CAMPOS:
                contagens[c][v(r, c)] += 1
            cfops[v(r, "CFOP")] += 1
            if v(r, "Nro único Nota"):
                notas.add(v(r, "Nro único Nota"))
            if v(r, "Produto"):
                produtos.add(v(r, "Produto"))
            if v(r, "Dt. Cancelamento"):
                cancelados += 1

        print(f"  notas distintas: {len(notas)} | produtos distintos: {len(produtos)}"
              f" | CFOPs distintos: {len(cfops)} | cancelados: {cancelados}")
        for c in CAMPOS:
            itens = sorted(contagens[c].items(), key=lambda kv: -kv[1])[:12]
            print(f"  {c}: " + ", ".join(f"{k}={n}" for k, n in itens))
        print("  CFOPs mais frequentes: " +
              ", ".join(f"{int(k)}={n}" for k, n in cfops.most_common(15) if k))


if __name__ == "__main__":
    main()
