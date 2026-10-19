"""A APURAÇÃO EFETIVA de MS mostra de onde a carga efetiva veio.

Alíquota da nota → redução de base → carga efetiva → % do crédito estornado.
Livro sintético de Rio Brilhante, sem dado real.
"""
from __future__ import annotations

import datetime as dt

import openpyxl
import pytest

from apurabot.apuracao import apurar
from apurabot.base_tratada import tratar
from apurabot.ingestao import COLUNAS
from apurabot.saida import escrever

RB = "HINOVE (RIO BRILHANTE)"


@pytest.fixture(scope="module")
def planilha(parametros, tmp_path_factory):
    pasta = tmp_path_factory.mktemp("reducao")
    cabecalho = list(COLUNAS)
    wb = openpyxl.Workbook()
    aba = wb.active
    aba.append(cabecalho)
    notas = [
        # produto, código, cfop, valor, base, alíquota
        ("ZINCO 15 GR", 110000001, 2101, 82_500.00, 47_140.50, 7),
        ("SACO SOLD. 50KG", 201000001, 2101, 47_880.00, 47_880.00, 7),
        ("CLORETO DE AMONIO", 110000002, 2906, 416_010.43, 138_656.02, 12),
    ]
    for n, (desc, prod, cfop, vc, base, aliq) in enumerate(notas, start=1):
        valores = {
            "Nro único Nota": n, "Nro. da nota": n, "Empresa": 2,
            "Nome Fantasia (Empresa)": RB,
            "Dt. do movimento": dt.datetime(2026, 9, 10),
            "Dt. do documento": dt.datetime(2026, 9, 10),
            "CFOP": cfop, "Entrada/Saída": "Entrada",
            "Cód. de tributação": "20" if base < vc else "00",
            "Vlr. contábil": vc, "Base do ICMS": base, "Alíquota ICMS": aliq,
            "Vlr. do ICMS": round(base * aliq / 100, 2),
            "UF de Origem": "SP", "UF de Destino": "MS",
            "Espécie do documento": "NFE", "Modelo do Documento": "55",
            "Produto": prod, "Descrição (Produto)": desc,
        }
        aba.append([valores.get(c) for c in cabecalho])
    livro = pasta / "livro.xlsx"
    wb.save(livro)
    base = tratar(livro, parametros=parametros)
    destino = escrever(base, pasta / "saida.xlsx", apurar(base, parametros))
    return openpyxl.load_workbook(destino)


def _linhas_de_produto(planilha):
    aba = planilha["APURAÇÃO EFETIVA"]
    # A coluna A é a filial; o resto vem uma casa à direita.
    return {
        linha[4]: linha[1:] for linha in aba.iter_rows(values_only=True)
        if linha[4] and linha[1] in (None, "") and linha[3]
    }


def test_ms_mostra_aliquota_e_reducao_no_fim_da_tabela(planilha):
    aba = planilha["APURAÇÃO EFETIVA"]
    cabecalho = next(linha for linha in aba.iter_rows(values_only=True)
                     if linha[1] == "CFOP")
    assert list(cabecalho[12:14]) == ["Alíquota da nota", "Redução de base"]


@pytest.mark.parametrize("produto, carga, aliquota, reducao", [
    ("ZINCO 15 GR", "4%", "7%", 0.4286),
    ("SACO SOLD. 50KG", "7%", "7%", 0.0),
    ("CLORETO DE AMONIO", "4%", "12%", 0.6667),
])
def test_a_reducao_explica_a_carga(planilha, produto, carga, aliquota, reducao):
    linha = _linhas_de_produto(planilha)[produto]
    assert linha[2] == carga
    assert linha[11] == aliquota
    assert linha[12] == pytest.approx(reducao, abs=0.00005)


def test_o_estorno_e_pela_aliquota_mesmo_com_a_base_reduzida(planilha):
    """Zinco reduzido a 4% estorna como o saco cheio: os dois são de 7%."""
    linhas = _linhas_de_produto(planilha)
    assert linhas["ZINCO 15 GR"][9] == pytest.approx(3_299.84 * 0.4286, abs=0.01)
    assert linhas["SACO SOLD. 50KG"][9] == pytest.approx(3_351.60 * 0.4286, abs=0.01)
    assert linhas["CLORETO DE AMONIO"][9] == pytest.approx(16_638.72 * 0.6667,
                                                            abs=0.01)


def test_cada_linha_da_aba_diz_a_filial_e_o_filtro_esta_nela(planilha):
    """Escolher a filial no filtro de A2 mostra o bloco inteiro dela."""
    aba = planilha["APURAÇÃO EFETIVA"]
    assert aba["A2"].value == "Filial"
    assert aba.auto_filter.ref == f"A2:A{aba.max_row}"
    for numero in range(3, aba.max_row + 1):
        assert aba.cell(row=numero, column=1).value == RB, numero


def test_as_formulas_andam_junto_com_a_coluna(planilha):
    """Os totais somam as mesmas linhas, agora uma coluna à direita."""
    aba = planilha["APURAÇÃO EFETIVA"]
    total = next(c.row for c in aba["B"] if c.value == "TOTAL")
    assert str(aba[f"H{total}"].value).startswith("=SUM(H")
    assert str(aba[f"L{total}"].value) == f"=H{total}-K{total}"
