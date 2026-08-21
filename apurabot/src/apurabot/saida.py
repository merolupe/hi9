"""Escrita da base tratada em .xlsx.

O time fiscal continua recebendo uma planilha — o Python é o motor, não a
interface. Toda linha carrega a rastreabilidade exigida pelo Anexo B do escopo.
"""
from __future__ import annotations

from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

from .apuracao import Apuracao, apurar
from .base_tratada import BaseTratada

CABECALHO_BASE = [
    ("arquivo_origem", 22), ("linha_origem", 12), ("competencia", 12),
    ("estabelecimento", 30), ("uf_origem", 10), ("uf_destino", 10),
    ("entrada_saida", 13), ("nro_unico", 12), ("numero_nota", 12),
    ("cfop", 8), ("cfop_descricao", 30), ("cst", 10), ("especie", 9),
    ("produto", 12), ("produto_descricao", 38),
    ("valor_contabil", 15), ("base_icms", 15), ("aliquota_icms", 12),
    ("valor_icms", 15),
    ("carga_bruta", 13), ("carga_efetiva", 13), ("situacao", 22),
    ("categoria", 26), ("regra_carga", 60), ("regra_classificacao", 60),
    ("alerta", 24), ("pendencia", 60),
]

TITULO = Font(bold=True, color="FFFFFF")
FUNDO = PatternFill("solid", fgColor="1F3864")
MOEDA = "#,##0.00"


def _escreve_cabecalho(aba, colunas):
    aba.append([nome for nome, _ in colunas])
    for i, (_, largura) in enumerate(colunas, start=1):
        aba.column_dimensions[get_column_letter(i)].width = largura
        celula = aba.cell(row=1, column=i)
        celula.font, celula.fill = TITULO, FUNDO
        celula.alignment = Alignment(vertical="center", wrap_text=False)
    aba.freeze_panes = "A2"


def _aba_base(wb, base: BaseTratada) -> None:
    aba = wb.create_sheet("BASE TRATADA")
    _escreve_cabecalho(aba, CABECALHO_BASE)
    competencia = base.competencia
    for t in base.linhas:
        d = t.origem.dados
        aba.append([
            t.origem.arquivo_origem, t.origem.linha_origem, competencia,
            d.get("estabelecimento"), d.get("uf_origem"), d.get("uf_destino"),
            d.get("entrada_saida"), d.get("nro_unico"), d.get("numero_nota"),
            t.origem.cfop_int, d.get("cfop_descricao"), d.get("cst"), d.get("especie"),
            t.origem.produto_codigo, d.get("produto_descricao"),
            d.get("valor_contabil"), d.get("base_icms"), d.get("aliquota_icms"),
            d.get("valor_icms"),
            t.carga.carga_bruta, t.carga.carga, t.carga.situacao.value,
            t.classificacao.categoria, t.carga.regra, t.classificacao.regra,
            "; ".join(t.alertas), "; ".join(t.pendencias),
        ])
    for linha in aba.iter_rows(min_row=2, min_col=16, max_col=19):
        for celula in linha:
            celula.number_format = MOEDA
    aba.auto_filter.ref = aba.dimensions


def _aba_pendencias(wb, base: BaseTratada) -> None:
    aba = wb.create_sheet("PENDÊNCIAS")
    colunas = [
        ("linha_origem", 12), ("estabelecimento", 30), ("nro_unico", 12),
        ("cfop", 8), ("produto", 12), ("produto_descricao", 38),
        ("valor_icms", 15), ("pendencia", 90),
    ]
    _escreve_cabecalho(aba, colunas)
    for t in base.com_pendencia:
        d = t.origem.dados
        aba.append([
            t.origem.linha_origem, d.get("estabelecimento"), d.get("nro_unico"),
            t.origem.cfop_int, t.origem.produto_codigo, d.get("produto_descricao"),
            d.get("valor_icms"), " | ".join(t.pendencias),
        ])
    for linha in aba.iter_rows(min_row=2, min_col=7, max_col=7):
        for celula in linha:
            celula.number_format = MOEDA
    aba.auto_filter.ref = aba.dimensions


def _aba_resumo(wb, base: BaseTratada) -> None:
    aba = wb.create_sheet("RESUMO", 0)
    resumo = base.resumo()
    aba.column_dimensions["A"].width = 34
    aba.column_dimensions["B"].width = 30
    aba.column_dimensions["C"].width = 18
    aba.column_dimensions["D"].width = 18

    def secao(titulo: str) -> None:
        aba.append([])
        aba.append([titulo])
        celula = aba.cell(row=aba.max_row, column=1)
        celula.font, celula.fill = TITULO, FUNDO

    aba.append(["APURAÇÃO DE ICMS — BASE TRATADA"])
    aba.cell(row=1, column=1).font = Font(bold=True, size=14)

    secao("PROCEDÊNCIA")
    for rotulo, chave in [
        ("Competência", "competencia"), ("Arquivo de origem", "arquivo"),
        ("SHA-256 do arquivo", "sha256"), ("Gerado em", "gerado_em"),
    ]:
        aba.append([rotulo, str(resumo[chave])])

    secao("VOLUME")
    for rotulo, chave in [
        ("Linhas no Livro Fiscal", "linhas_no_livro"),
        ("Linhas relevantes para ICMS", "linhas_relevantes"),
        ("Pendências (bloqueiam o encerramento)", "pendencias"),
        ("Alertas (não bloqueiam)", "alertas"),
    ]:
        aba.append([rotulo, resumo[chave]])
    aba.append([
        "Encerramento da competência",
        "LIBERADO" if base.pode_encerrar else "BLOQUEADO por pendência",
    ])
    aba.cell(row=aba.max_row, column=2).font = Font(
        bold=True, color="1E7B34" if base.pode_encerrar else "B00020"
    )

    secao("SITUAÇÃO DA EQUALIZAÇÃO")
    for nome, n in sorted(resumo["situacoes"].items(), key=lambda kv: -kv[1]):
        aba.append([nome, n])

    secao("CATEGORIAS DA OPERAÇÃO")
    aba.append(["categoria", "linhas", "ICMS (R$)"])
    for nome, dados in sorted(
        resumo["categorias"].items(), key=lambda kv: -kv[1]["valor_icms"]
    ):
        aba.append([nome, dados["linhas"], dados["valor_icms"]])
        aba.cell(row=aba.max_row, column=3).number_format = MOEDA


def _aba_por_carga(wb, base: BaseTratada) -> None:
    aba = wb.create_sheet("POR ESTABELECIMENTO E CARGA")
    colunas = [
        ("estabelecimento", 30), ("entrada_saida", 14), ("carga_efetiva", 14),
        ("linhas", 10), ("valor_contabil", 18), ("base_icms", 18), ("valor_icms", 18),
    ]
    _escreve_cabecalho(aba, colunas)
    somas = base.por_estabelecimento_carga()
    for (estab, es, carga), v in sorted(
        somas.items(), key=lambda kv: (str(kv[0][0]), str(kv[0][1]), str(kv[0][2]))
    ):
        aba.append([
            estab, es, "(vazio)" if carga is None else carga, v["linhas"],
            v["valor_contabil"], v["base_icms"], v["valor_icms"],
        ])
    for linha in aba.iter_rows(min_row=2, min_col=5, max_col=7):
        for celula in linha:
            celula.number_format = MOEDA
    aba.auto_filter.ref = aba.dimensions


def _aba_apuracao(wb, apuracao: Apuracao) -> None:
    aba = wb.create_sheet("APURAÇÃO POR FILIAL", 1)
    colunas = [
        ("estabelecimento", 32), ("uf", 6), ("regime", 28), ("linhas", 9),
        ("credito_bruto", 16), ("estorno", 16), ("credito_indevido", 17),
        ("credito_mantido", 17), ("debito", 16), ("saldo", 16), ("confere", 10),
    ]
    _escreve_cabecalho(aba, colunas)
    for f in sorted(apuracao.filiais.values(), key=lambda f: (f.uf, f.estabelecimento)):
        aba.append([
            f.estabelecimento, f.uf, f.regime, f.linhas, f.credito_bruto,
            f.estorno, f.credito_indevido, f.credito_mantido, f.debito, f.saldo,
            "OK" if f.confere else "DIVERGE",
        ])
    total = apuracao.total
    aba.append([
        "TOTAL", "", "", total.linhas, total.credito_bruto, total.estorno,
        total.credito_indevido, total.credito_mantido, total.debito, total.saldo,
        "OK" if total.confere else "DIVERGE",
    ])
    for celula in aba[aba.max_row]:
        celula.font = Font(bold=True)
    for linha in aba.iter_rows(min_row=2, min_col=5, max_col=10):
        for celula in linha:
            celula.number_format = MOEDA

    aba.append([])
    aba.append(["Detalhe por carga efetiva"])
    aba.cell(row=aba.max_row, column=1).font = Font(bold=True)
    aba.append(["estabelecimento", "carga", "credito_bruto", "estorno",
                "credito_indevido", "credito_mantido"])
    for celula in aba[aba.max_row]:
        celula.font, celula.fill = TITULO, FUNDO
    for f in sorted(apuracao.filiais.values(), key=lambda f: (f.uf, f.estabelecimento)):
        for carga, v in sorted(f.por_carga.items(), key=lambda kv: str(kv[0])):
            aba.append([
                f.estabelecimento, carga, v["credito_bruto"], v["estorno"],
                v["credito_indevido"], v["credito_mantido"],
            ])
            for coluna in (3, 4, 5, 6):
                aba.cell(row=aba.max_row, column=coluna).number_format = MOEDA


def escrever(base: BaseTratada, destino: Path | str) -> Path:
    """Grava a base tratada em .xlsx e devolve o caminho."""
    destino = Path(destino)
    destino.parent.mkdir(parents=True, exist_ok=True)

    wb = Workbook()
    wb.remove(wb.active)
    _aba_base(wb, base)
    _aba_pendencias(wb, base)
    _aba_por_carga(wb, base)
    _aba_apuracao(wb, apurar(base))
    _aba_resumo(wb, base)          # criada em posição 0, fica como primeira aba
    wb.save(destino)
    return destino
