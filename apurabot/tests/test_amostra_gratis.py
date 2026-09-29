"""Entrada de amostra grátis (CFOP 1911/2911) — sem crédito, em todo regime.

A primeira caiu em SEM REGRA em 08/2026: produto 401002431, "amostra grátis
fertilizante sólido". O prefixo 4 não diz o que o produto é, e o CFOP 1911 não
estava em regra nenhuma. Ver decisão pendente nº 18.
"""
from __future__ import annotations

import datetime as dt

import openpyxl
import pytest

from apurabot.apuracao import apurar
from apurabot.base_tratada import tratar
from apurabot.ingestao import COLUNAS

ICMS = 1_200.00

#: Um estabelecimento de cada regime (filiais.yaml).
FILIAIS = [
    (1, "HINOVE (MATRIZ)", "SP"),
    (2, "HINOVE (RIO BRILHANTE)", "MS"),
    (9, "HINOVE (CORUMBÁ- MS)", "MS"),
    (8, "HINOVE (BARRA DO GARÇAS - MT)", "MT"),
    (7, "HINOVE (LONDRINA)", "PR"),
]


@pytest.fixture(scope="module")
def apuracao(parametros, tmp_path_factory):
    cabecalho = list(COLUNAS)
    wb = openpyxl.Workbook()
    aba = wb.active
    aba.append(cabecalho)
    for n, (codigo, nome, uf) in enumerate(FILIAIS, start=1):
        valores = {
            "Nro único Nota": n, "Nro. da nota": n, "Empresa": codigo,
            "Nome Fantasia (Empresa)": nome,
            "Dt. do movimento": dt.datetime(2026, 8, 10),
            "Dt. do documento": dt.datetime(2026, 8, 10),
            "CFOP": 1911 if n % 2 else 2911,
            "Descrição da CFOP": "Ent amostra grátis",
            "Entrada/Saída": "Entrada", "Cód. de tributação": "00",
            "Vlr. contábil": 10_000, "Base do ICMS": 10_000,
            "Alíquota ICMS": 12, "Vlr. do ICMS": ICMS,
            "UF de Origem": uf, "UF de Destino": uf,
            "Espécie do documento": "NF", "Modelo do Documento": "55",
            "Produto": 401002431,
            "Descrição (Produto)": "AMOSTRA GRATIS FERTILIZANTE SOLIDO",
        }
        aba.append([valores.get(c) for c in cabecalho])
    destino = tmp_path_factory.mktemp("amostra") / "livro.xlsx"
    wb.save(destino)
    base = tratar(destino, parametros=parametros)
    return base, apurar(base, parametros)


def test_amostra_gratis_nao_cai_mais_em_sem_regra(apuracao):
    base, _ = apuracao
    for linha in base.linhas:
        assert linha.classificacao.categoria == "amostra_gratis"
        assert not linha.classificacao.e_pendencia


@pytest.mark.parametrize("nome", [nome for _, nome, _ in FILIAIS])
def test_o_credito_vai_inteiro_para_indevido_em_todo_regime(apuracao, nome):
    """Nem mantido (PR mantém 100%), nem só o excedente (SP estorna acima de 4%)."""
    _, apuracao = apuracao
    filial = apuracao.filiais[" ".join(nome.split())]
    assert filial.credito_bruto == pytest.approx(ICMS)
    assert filial.credito_indevido == pytest.approx(ICMS)
    assert filial.credito_mantido == pytest.approx(0.0)
    assert filial.estorno == pytest.approx(0.0)


def test_em_ms_a_amostra_tem_atividade(apuracao):
    """A GIA de MS segrega por atividade: sem ela, a linha bloquearia."""
    _, apuracao = apuracao
    assert apuracao.sem_regra_de_atividade == []
