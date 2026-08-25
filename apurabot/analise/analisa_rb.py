"""Confere Rio Brilhante contra os documentos oficiais da competência.

Roda o motor sobre o Livro Fiscal e compara, linha a linha, com o que a GIA
retificadora e o Registro de Apuração declaram. Serve como verificação rápida no
fechamento mensal: se algum campo divergir, aparece aqui antes de virar problema.

    python analise/analisa_rb.py <livro_fiscal.xls>

Os alvos abaixo são de Julho/2026. Numa competência nova eles mudam — o que não
muda é a mecânica, que está em docs/apurabot/04-matriz-de-regras-icms.md.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from apurabot.apuracao import AjustesDaApuracao, apurar          # noqa: E402
from apurabot.base_tratada import tratar                          # noqa: E402
from apurabot.nucleo import atividade as ativ                     # noqa: E402

FILIAL = "HINOVE (RIO BRILHANTE)"

# Linha 003 do Registro de Apuração: "Estorno de créditos para ajuste de
# apuração do ICMS". Não nasce de documento no Livro Fiscal.
AJUSTE_ESTORNO_INDUSTRIAL = 3_865.30

# GIA retificadora, protocolo 36160E2, entregue em 25/08/2026.
GIA = [
    ("crédito industrial",              "credito_industrial",              327_834.95),
    ("estorno industrial",              "estorno_industrial",              245_987.17),
    ("crédito da parcela incentivada",  "credito_da_parcela_incentivada",   77_982.48),
    ("débito industrial",               "debito_beneficiado",              412_274.17),
    ("base do incentivo",               "base_do_incentivo",               334_291.69),
    ("benefício (67% + 80%)",           "credito_presumido",               261_431.90),
    ("FADEFE 2% — guia avulsa",         "fadefe",                            5_228.64),
]


def main():
    if len(sys.argv) < 2:
        sys.exit("uso: python analise/analisa_rb.py <livro_fiscal.xls>")

    base = tratar(sys.argv[1])
    apuracao = apurar(
        base,
        ajustes=AjustesDaApuracao(
            estorno_de_credito={FILIAL: {ativ.INDUSTRIAL: AJUSTE_ESTORNO_INDUSTRIAL}}
        ),
    )
    filial = apuracao.filiais.get(FILIAL)
    if filial is None:
        sys.exit(f"{FILIAL} não aparece no Livro Fiscal informado.")

    print(f"\n{FILIAL} — competência {base.competencia}\n")

    print("Segregação por atividade")
    print(f"  {'atividade':<22}{'crédito':>14}{'estorno':>14}{'débito':>14}")
    for nome in ativ.ORDEM:
        if nome not in filial.por_atividade:
            continue
        t = filial.por_atividade[nome]
        print(f"  {nome:<22}{t.credito_bruto:>14,.2f}{t.estorno:>14,.2f}{t.debito:>14,.2f}")
    if filial.atividades_sem_regra:
        t = filial.atividades_sem_regra
        print(f"  {'SEM REGRA':<22}{t.credito_bruto:>14,.2f}{t.estorno:>14,.2f}"
              f"{t.debito:>14,.2f}   <-- bloqueia o encerramento")

    print("\nConferência contra a GIA retificadora")
    print(f"  {'campo':<32}{'motor':>14}{'GIA':>14}{'diferença':>13}")
    divergencias = 0
    for rotulo, campo, alvo in GIA:
        obtido = getattr(filial.beneficio, campo)
        delta = obtido - alvo
        marca = "" if abs(delta) < 0.02 else "   <-- DIVERGE"
        if marca:
            divergencias += 1
        print(f"  {rotulo:<32}{obtido:>14,.2f}{alvo:>14,.2f}{delta:>+13,.2f}{marca}")

    print("\nMemória do benefício")
    for passo in filial.beneficio.memoria:
        print(f"  {passo}")

    print()
    if divergencias:
        print(f"{divergencias} campo(s) divergindo da declaração. Investigar antes de fechar.")
        return 1
    print("Todos os campos conferem com o declarado.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
