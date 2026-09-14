"""Planilhas fictícias, montadas no próprio teste.

Nenhum relatório real da empresa entra no repositório — a regra nº 1 do
`CLAUDE.md`. As planilhas aqui são construídas na hora, com CNPJ, chave de
acesso e nome de fornecedor inventados, e trazem só as colunas que cada teste
precisa exercitar.

O padrão-ouro do porte — os arquivos de uma semana real e a saída que a macro
produziu a partir deles — fica em `competencias/pendentes/`, fora do git. Sem
ele, a prova de divergência zero não existe; o que existe são os invariantes
estruturais, que é o que estes testes cobrem.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "pendentes" / "src"))

import pendentes  # noqa: E402,F401  (põe `vendor/` no sys.path)

#: Onde o padrão-ouro moraria. Fora do git, como `competencias/fiscalbot/`.
PASTA_PADRAO_OURO = RAIZ / "competencias" / "pendentes"

#: Uma chave de acesso inventada, com os 44 dígitos que a de verdade tem.
CHAVE = "35260612345678000199550010000001231000001234"

#: As 27 colunas do relatório de importação de XML, na ordem do VBA.
COLUNAS_XML = [
    "Nro Nota", "Cód. Parceiro", "Nome Parceiro (Parceiro)", "Dh. Emissão",
    "CFOP's XML", "Valor da Nota", "Nome Fantasia", "Chave Acesso",
    "Dt. Vencimento", "Situação da manifestação", "Situação NF-e", "Tipo NF-e",
    "Último Evento DF-e", "Descrição Nat. Operação", "Entrada/Saida NF-e",
    "Tomador CT-e", "Dias Emissão Doc", "Dh. Importação", "Status",
    "Nome (Usuário)", "Papel no CT-e", "Código da Empresa", "Cnpj Parceiro",
    "Código", "Possui o XML", "Importado pelo DF-e", "Série Doc",
]

#: As 7 colunas da Conferência de Entradas.
COLUNAS_CE = [
    "Chave Acesso", "Conferência Física", "Conf. Fiscal",
    "Motivo Incongruência", "Dh. Conferência Física", "Nro. do Pedido",
    "Pedido confirmado?",
]

#: As 5 colunas de classificação da aba `Pendentes`, na ordem em que o VBA as
#: lê por posição — aqui elas são lidas por cabeçalho, de propósito.
COLUNAS_DE_CLASSIFICACAO = [
    "Tipo de Operação", "Guardião", "Gestor de apoio", "Categoria",
]


def escrever(caminho: Path, abas: dict[str, list[list]]) -> Path:
    """Um `.xlsx` com as abas e linhas informadas, na ordem informada."""
    from openpyxl import Workbook

    livro = Workbook()
    livro.remove(livro.active)
    for nome, linhas in abas.items():
        aba = livro.create_sheet(nome)
        for linha in linhas:
            aba.append(list(linha))
    caminho.parent.mkdir(parents=True, exist_ok=True)
    livro.save(str(caminho))
    return caminho


def cabecalho_com_titulo(colunas: list[str], linhas: list[list]) -> list[list]:
    """O relatório como o Sankhya entrega: duas linhas de título antes."""
    return [
        ["Relatório de exemplo"],
        ["Emitido em 14/09/2026 por fulano"],
        list(colunas),
        *linhas,
    ]


@pytest.fixture()
def arquivo_xml(tmp_path) -> Path:
    """O relatório de importação de XML, com duas notas."""
    linhas = [
        ["1001", "4", "FORNECEDOR EXEMPLO LTDA", "01/07/2026", "1102",
         "1500.00", "HINOVE MATRIZ", CHAVE, "30/07/2026", "Ciência",
         "NF-e autorizada", "NF-e Normal", "Autorizada", "COMPRA", "Saida",
         "Não se aplica", 12, "02/07/2026", "Importado", "fulano", "",
         "1", "12345678000199", "9001", "Sim", "Sim", "1"],
        ["1002", "5", "OUTRO FORNECEDOR SA", "02/07/2026", "1556",
         "320.50", "HINOVE CORUMBA", CHAVE[:-1] + "5", "01/08/2026",
         "Desconhecida", "NF-e autorizada", "NF-e Normal", "Autorizada",
         "USO E CONSUMO", "Entrada", "Não se aplica", 11, "03/07/2026",
         "Importado", "fulano", "", "1", "98765432000188", "9002", "Sim",
         "Sim", "1"],
    ]
    return escrever(tmp_path / "XML30.xlsx",
                    {"Plan1": cabecalho_com_titulo(COLUNAS_XML, linhas)})


@pytest.fixture()
def arquivo_ce(tmp_path) -> Path:
    """A Conferência de Entradas, com o farol nos três estados."""
    linhas = [
        [CHAVE, "Sim", "Sim", "", "05/07/2026", "7788",
         '<div><span>&#128994;</span></div>'],
        [CHAVE[:-1] + "5", "Sim", "não", "0,00", "06/07/2026", "7789",
         '<div><span>&#128308;</span></div>'],
        [CHAVE[:-1] + "7", "", "não", "", "", "", ""],
    ]
    return escrever(tmp_path / "CE30.xlsx",
                    {"Plan1": cabecalho_com_titulo(COLUNAS_CE, linhas)})


@pytest.fixture()
def arquivo_semana_anterior(tmp_path) -> Path:
    """A planilha da semana passada, com as 5 colunas de classificação.

    Ela carrega **todas** as colunas do XML, que é exatamente por que o
    reconhecimento de papel precisa de âncora ausente para separar as duas.
    """
    colunas = (COLUNAS_DE_CLASSIFICACAO + ["Retorno semana 29"]
               + COLUNAS_XML[:1] + ["Chave Acesso"] + COLUNAS_XML[9:16])
    linhas = [
        ["Compra direta", "Suprimentos", "Maria", "Diretos",
         "aguardando fornecedor", "1001", CHAVE, "Ciência", "NF-e autorizada",
         "NF-e Normal", "Autorizada", "COMPRA", "Saida", "Não se aplica"],
    ]
    return escrever(tmp_path / "Pendentes29.xlsx", {"Pendentes": [colunas, *linhas]})
