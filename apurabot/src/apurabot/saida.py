"""Escrita da base tratada em .xlsx.

O time fiscal continua recebendo uma planilha — o Python é o motor, não a
interface. Toda linha carrega a rastreabilidade exigida pelo Anexo B do escopo.
"""
from __future__ import annotations

from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

from . import __version__
from .ajustes import ABA as ABA_AJUSTES
from .apuracao import Apuracao, apurar
from .conferencia import (ABAS_COM_FILIAL, ABA_1200, ABA_EFETIVA, ABA_LANCAMENTOS, ABA_REGISTRO,
                          ABA_TRANSFERENCIAS, aba_apuracao_efetiva,
                          aba_lancamentos, aba_registro, aba_registro_1200,
                          aba_transferencias)
from .nucleo.atividade import INDUSTRIAL, INTERESTADUAL, INTRAESTADUAL
from .nucleo.atividade import ORDEM as ATIVIDADES_EM_ORDEM
from .base_tratada import BaseTratada
from .formato import reais

#: Procedência — o que a ferramenta escreve, não o Livro.
COLUNAS_DE_PROCEDENCIA = [
    ("arquivo_origem", 22), ("linha_origem", 12), ("competencia", 12),
]

#: Campos do Livro que abrem a aba: são os que se olha primeiro.
COLUNAS_EM_DESTAQUE = [
    ("estabelecimento", 30), ("uf_origem", 10), ("uf_destino", 10),
    ("entrada_saida", 13), ("nro_unico", 12), ("numero_nota", 12),
    ("cfop", 8), ("cfop_descricao", 30), ("cst", 10), ("especie", 9),
    ("produto", 12), ("produto_descricao", 38),
    ("valor_contabil", 15), ("base_icms", 15), ("aliquota_icms", 12),
    ("valor_icms", 15),
]

#: O que o motor concluiu sobre a linha. Na releitura estas colunas são
#: ignoradas e recalculadas: se alguém as editar, a edição não vale.
COLUNAS_CALCULADAS = [
    ("carga_bruta", 13), ("carga_efetiva", 13), ("situacao", 22),
    ("categoria", 26), ("regra_carga", 60), ("regra_classificacao", 60),
    ("alerta", 24), ("pendencia", 60),
]

#: As colunas que o time fiscal preenche. Ver `ajustes.py`.
COLUNAS_DE_AJUSTE = [
    ("ajuste_linha", 14), ("ajuste_valor", 15), ("ajuste_motivo", 46),
    ("ajuste_responsavel", 20), ("ajuste_aprovador", 20),
    ("atividade_ajustada", 18), ("atividade_motivo", 46),
    ("atividade_responsavel", 20), ("atividade_aprovador", 20),
]


def _demais_campos_do_livro() -> list[tuple[str, int]]:
    """Todo campo do Livro que não está em destaque, na ordem do extrato.

    Eles saem porque a conferência precisa deles — parceiro, datas, série,
    chave, observação, TOP — e porque é o que torna o arquivo devolvido
    autossuficiente: com o Livro inteiro dentro, realimentar é arrastar um
    arquivo só.
    """
    from .ingestao import COLUNAS

    destaque = {nome for nome, _ in COLUNAS_EM_DESTAQUE}
    vistos: set[str] = set()
    colunas = []
    for campo in COLUNAS.values():
        if campo in destaque or campo in vistos:
            continue
        vistos.add(campo)
        colunas.append((campo, max(12, min(30, len(campo) + 4))))
    return colunas


CABECALHO_BASE = (
    COLUNAS_DE_PROCEDENCIA
    + COLUNAS_EM_DESTAQUE
    + COLUNAS_CALCULADAS
    + COLUNAS_DE_AJUSTE
    + _demais_campos_do_livro()
)

#: Onde começam as colunas de ajuste (1-based), para pintá-las de outra cor.
PRIMEIRA_DE_AJUSTE = (
    len(COLUNAS_DE_PROCEDENCIA) + len(COLUNAS_EM_DESTAQUE)
    + len(COLUNAS_CALCULADAS) + 1
)

TITULO = Font(bold=True, color="FFFFFF")
FUNDO = PatternFill("solid", fgColor="1F3864")
MOEDA = "#,##0.00"
PERCENTUAL = "0.00%"

ABA_BASE = "BASE TRATADA"
ABA_PENDENCIAS = "PENDÊNCIAS"
ABA_RESUMO = "RESUMO"
ABA_POR_CARGA = "POR ESTABELECIMENTO E CARGA"
ABA_DETALHES = "RESUMO E DETALHES"

#: Saem no arquivo, mas escondidas: os números do RESUMO estão na tela, e a
#: visão por carga é insumo de conferência, não leitura.
ABAS_OCULTAS = {ABA_RESUMO, ABA_POR_CARGA}

#: Cinza médio em volta de tudo que é dado ou tabela.
_CINZA = Side(style="thin", color="808080")
BORDA = Border(left=_CINZA, right=_CINZA, top=_CINZA, bottom=_CINZA)


def _escreve_cabecalho(aba, colunas):
    aba.append([nome for nome, _ in colunas])
    for i, (_, largura) in enumerate(colunas, start=1):
        aba.column_dimensions[get_column_letter(i)].width = largura
        celula = aba.cell(row=1, column=i)
        celula.font, celula.fill = TITULO, FUNDO
        celula.alignment = Alignment(vertical="center", wrap_text=False)


#: Fundo das colunas que o time fiscal preenche — para não se confundirem com
#: as que a ferramenta escreve.
FUNDO_DE_AJUSTE = PatternFill("solid", fgColor="7B3F00")


def _aba_base(wb, base: BaseTratada) -> None:
    aba = wb.create_sheet(ABA_BASE)
    _escreve_cabecalho(aba, CABECALHO_BASE)
    for i in range(PRIMEIRA_DE_AJUSTE, PRIMEIRA_DE_AJUSTE + len(COLUNAS_DE_AJUSTE)):
        aba.cell(row=1, column=i).fill = FUNDO_DE_AJUSTE

    competencia = base.competencia
    demais = [nome for nome, _ in _demais_campos_do_livro()]
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
            # O que foi informado volta como está: realimentar o arquivo não
            # pode apagar o ajuste de quem o escreveu.
            d.get("ajuste_linha"), d.get("ajuste_valor"), d.get("ajuste_motivo"),
            d.get("ajuste_responsavel"), d.get("ajuste_aprovador"),
            d.get("atividade_ajustada"), d.get("atividade_motivo"),
            d.get("atividade_responsavel"), d.get("atividade_aprovador"),
            *(d.get(campo) for campo in demais),
        ])
    primeira_moeda = len(COLUNAS_DE_PROCEDENCIA) + 13      # valor_contabil
    for linha in aba.iter_rows(min_row=2, min_col=primeira_moeda,
                               max_col=primeira_moeda + 3):
        for celula in linha:
            celula.number_format = MOEDA
    for linha in aba.iter_rows(min_row=2, min_col=PRIMEIRA_DE_AJUSTE + 1,
                               max_col=PRIMEIRA_DE_AJUSTE + 1):
        for celula in linha:
            celula.number_format = MOEDA
    aba.auto_filter.ref = aba.dimensions


def _aba_pendencias(wb, base: BaseTratada, apuracao: Apuracao) -> None:
    """Tudo que bloqueia o encerramento, inclusive o que não vem de uma linha.

    Atividade indefinida é pendência da apuração, não da base: ela não tem
    linha de origem, e por isso já ficou de fora daqui uma vez. Quem trabalha
    pela planilha não pode deixar de ver um bloqueio que a tela mostra.
    """
    if not (base.com_pendencia or apuracao.sem_regra_de_atividade
            or apuracao.bloqueios_de_ajuste):
        return                          # a aba só existe quando tem o que mostrar
    aba = wb.create_sheet(ABA_PENDENCIAS)
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
    for filial in apuracao.sem_regra_de_atividade:
        somas = filial.atividades_sem_regra
        aba.append([
            "", filial.estabelecimento, "", "", "", "", somas.credito_bruto,
            f"ATIVIDADE INDEFINIDA: {somas.linhas} linha(s) não casaram com "
            "nenhuma atividade — cadastre o CFOP em regimes.yaml, bloco "
            "`atividades`",
        ])
    for motivo in apuracao.bloqueios_de_ajuste:
        aba.append(["", "", "", "", "", "", None, f"AJUSTE INCOMPLETO: {motivo}"])
    for linha in aba.iter_rows(min_row=2, min_col=7, max_col=7):
        for celula in linha:
            celula.number_format = MOEDA
    aba.auto_filter.ref = aba.dimensions


def _aba_resumo(wb, base: BaseTratada) -> None:
    aba = wb.create_sheet(ABA_RESUMO)
    resumo = base.resumo()
    aba.column_dimensions["A"].width = 34
    aba.column_dimensions["B"].width = 30
    aba.column_dimensions["C"].width = 18
    aba.column_dimensions["D"].width = 18

    def secao(titulo: str) -> None:
        aba.append([None])   # linha em branco: `append([])` não avança no openpyxl
        aba.append([titulo])
        celula = aba.cell(row=aba.max_row, column=1)
        celula.font, celula.fill = TITULO, FUNDO

    aba.append(["APURAÇÃO DE ICMS — BASE TRATADA"])
    aba.cell(row=1, column=1).font = Font(bold=True, size=14)

    secao("PROCEDÊNCIA")
    aba.append(["Versão do Apurabot", __version__])
    for rotulo, chave in [
        ("Competência", "competencia"), ("Período do movimento", "periodo"),
        ("Arquivo de origem", "arquivo"),
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
    aba = wb.create_sheet(ABA_POR_CARGA)
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
    aba = wb.create_sheet(ABA_DETALHES)
    # `uf` e `linhas` são estreitas na tabela de cima, mas as memórias de
    # cálculo, mais abaixo, põem valor nessas colunas.
    colunas = [
        ("estabelecimento", 32), ("uf", 16), ("regime", 28), ("linhas", 16),
        ("credito_bruto", 16), ("estorno", 16), ("credito_indevido", 17),
        ("credito_mantido", 17), ("debito", 16), ("credito_presumido", 18),
        ("difal", 14), ("saldo credor anterior", 21), ("saldo (credor +)", 18),
        ("a recolher", 15), ("confere", 10),
    ]
    _escreve_cabecalho(aba, colunas)
    primeira = aba.max_row + 1
    for f in sorted(apuracao.filiais.values(), key=lambda f: (f.uf, f.estabelecimento)):
        aba.append([
            f.estabelecimento, f.uf, f.regime, f.linhas, f.credito_bruto,
            f.estorno, f.credito_indevido, f.credito_mantido, f.debito,
            f.credito_presumido, f.difal, f.saldo_credor_anterior, f.saldo,
            f.a_recolher, "OK" if f.confere else "DIVERGE",
        ])
    ultima = aba.max_row
    total = apuracao.total
    aba.append([
        "TOTAL", "", "", total.linhas, total.credito_bruto, total.estorno,
        total.credito_indevido, total.credito_mantido, total.debito,
        total.credito_presumido, total.difal, total.saldo_credor_anterior,
        total.saldo, apuracao.a_recolher, "OK" if total.confere else "DIVERGE",
    ])
    # O TOTAL soma as filiais na própria planilha, em vez de repetir o número
    # que o motor calculou — inclusive "a recolher", que é a soma do que cada
    # uma paga e não o saldo do grupo com o sinal trocado: filial credora não
    # paga a conta de outra devedora fora da centralização.
    linha = aba.max_row
    if ultima >= primeira:
        for coluna in range(4, 15):
            letra = get_column_letter(coluna)
            aba.cell(row=linha, column=coluna).value = (
                f"=SUM({letra}{primeira}:{letra}{ultima})"
            )
    for celula in aba[linha]:
        celula.font = Font(bold=True)
    for linha in aba.iter_rows(min_row=2, min_col=5, max_col=14):
        for celula in linha:
            celula.number_format = MOEDA

    _bloco_saldo_credor(aba, apuracao)
    _bloco_ajustes(aba, apuracao)

    _secao(aba, "Memória do benefício fiscal")
    # Uma linha em branco separa cada memória: é o que diz à borda onde uma
    # tabela acaba e a outra começa.
    fruido: dict[str, str] = {}
    for i, f in enumerate(sorted(
        (f for f in apuracao.filiais.values() if f.beneficio),
        key=lambda f: f.estabelecimento,
    )):
        if i:
            aba.append([None])
        fruido[f.estabelecimento] = _memoria_do_beneficio(aba, f)

    _secao(aba, "Centralização e transferência de saldo")
    for i, c in enumerate(apuracao.centralizacao):
        if i:
            aba.append([None])
        _memoria_da_centralizacao(aba, c)
    aba.append([None])
    aba.append(["", "As transferências a emitir estão na aba TRANSFERÊNCIAS."])

    _secao(aba, "Contribuição ao Pró-Desenvolve / FADEFE — GUIA AVULSA")
    aba.append(["", "Informativo: não entra na conta gráfica da apuração."])
    _cabecalho_de_bloco(aba, ["estabelecimento", "benefício fruído", "%",
                              "a recolher", "% adicional", "adicional a recolher"])
    for f in sorted(apuracao.filiais.values(), key=lambda f: f.estabelecimento):
        if not f.beneficio or not f.beneficio.percentual_fadefe:
            continue
        b = f.beneficio
        aba.append([
            f.estabelecimento, b.credito_presumido, b.percentual_fadefe / 100,
            b.fadefe, b.percentual_fadefe_adicional / 100, b.fadefe_adicional,
        ])
        n = aba.max_row
        if f.estabelecimento in fruido:
            # O benefício fruído é o total da memória, logo acima.
            aba.cell(row=n, column=2).value = f"={fruido[f.estabelecimento]}"
        aba.cell(row=n, column=4).value = f"=B{n}*C{n}"
        aba.cell(row=n, column=6).value = f"=B{n}*E{n}"
        for coluna in range(2, 7):
            aba.cell(row=n, column=coluna).number_format = (
                PERCENTUAL if coluna in (3, 5) else MOEDA
            )

    _secao(aba, "Segregação por atividade (exigida pela GIA de MS)")
    _cabecalho_de_bloco(aba, ["estabelecimento", "atividade", "linhas",
                              "credito_bruto", "estorno", "credito_mantido",
                              "debito", "debito_intra", "debito_inter", "saldo"])
    for f in sorted(apuracao.filiais.values(), key=lambda f: (f.uf, f.estabelecimento)):
        if not f.segrega_por_atividade:
            continue
        conhecidas = [a for a in ATIVIDADES_EM_ORDEM if a in f.por_atividade]
        restantes = [a for a in f.por_atividade if a not in conhecidas]
        for nome in conhecidas + sorted(restantes):
            t_ = f.por_atividade[nome]
            aba.append([
                f.estabelecimento, nome, t_.linhas, t_.credito_bruto, t_.estorno,
                t_.credito_mantido, t_.debito, t_.debito_de(INTRAESTADUAL),
                t_.debito_de(INTERESTADUAL), t_.saldo,
            ])
            n = aba.max_row
            aba.cell(row=n, column=10).value = f"=G{n}-F{n}"   # débito − mantido
            for coluna in range(4, 11):
                aba.cell(row=n, column=coluna).number_format = MOEDA

    _secao(aba, "Detalhe por carga efetiva")
    _cabecalho_de_bloco(aba, ["estabelecimento", "carga", "credito_bruto", "estorno",
                              "credito_indevido", "credito_mantido"])
    for f in sorted(apuracao.filiais.values(), key=lambda f: (f.uf, f.estabelecimento)):
        for carga, v in sorted(f.por_carga.items(), key=lambda kv: str(kv[0])):
            aba.append([
                f.estabelecimento, carga, v["credito_bruto"], v["estorno"],
                v["credito_indevido"], v["credito_mantido"],
            ])
            n = aba.max_row
            aba.cell(row=n, column=6).value = f"=C{n}-D{n}-E{n}"
            for coluna in (3, 4, 5, 6):
                aba.cell(row=n, column=coluna).number_format = MOEDA


def _secao(aba, titulo: str) -> None:
    aba.append([None])   # linha em branco: `append([])` não avança no openpyxl
    aba.append([titulo])
    aba.cell(row=aba.max_row, column=1).font = Font(bold=True)


def _cabecalho_de_bloco(aba, rotulos: list[str]) -> int:
    aba.append(rotulos)
    # Só as colunas da tabela: a linha inteira da aba levaria o fundo (e a
    # borda) até a última coluna da tabela de cima.
    for coluna in range(1, len(rotulos) + 1):
        celula = aba.cell(row=aba.max_row, column=coluna)
        celula.font, celula.fill = TITULO, FUNDO
    return aba.max_row


def _valor(aba, rotulo: str, valor, formato: str = MOEDA) -> int:
    """Uma linha da memória: o rótulo numa célula, o valor na do lado."""
    aba.append([rotulo, valor])
    aba.cell(row=aba.max_row, column=2).number_format = formato
    return aba.max_row


def _memoria_do_beneficio(aba, filial) -> str:
    """O crédito presumido passo a passo, com a conta em fórmula.

    Devolve a célula do crédito presumido total, que o quadro do FADEFE usa.
    As fórmulas refazem a conta do motor (`nucleo/beneficio.py`): o que elas
    resolvem tem que ser o que ele apurou.
    """
    b = filial.beneficio
    aba.append([filial.estabelecimento])
    aba.cell(row=aba.max_row, column=1).font = Font(bold=True)
    aba.append(["Termo", b.documento])
    aba.append(["Alcance", b.criterio])

    bruto = _valor(aba, "Crédito industrial bruto", b.credito_industrial)
    deducoes = [_valor(aba, "(−) estorno industrial", b.estorno_industrial)]
    # O mesmo total de atividade que o motor usou para calcular o benefício.
    indevido = filial.atividade(INDUSTRIAL).credito_indevido
    if indevido:
        deducoes.append(_valor(aba, "(−) crédito indevido industrial", indevido))
    if b.ajuste_de_credito:
        deducoes.append(
            _valor(aba, "(−) estorno de créditos (ajuste)", b.ajuste_de_credito)
        )
    credito = _valor(aba, "(=) crédito da parcela incentivada",
                     b.credito_da_parcela_incentivada)
    menos = "".join(f"-B{n}" for n in deducoes)
    aba.cell(row=credito, column=2).value = f"=MAX(B{bruto}{menos},0)"

    aba.append([None])                  # o quadro de rótulo e valor acaba aqui
    cabecalho = _cabecalho_de_bloco(aba, [
        "Saída", "Débito", "Crédito rateado", "Base do incentivo",
        "% presumido", "Crédito presumido",
    ])
    intra, inter = cabecalho + 1, cabecalho + 2
    for nome, parcela in (("intraestadual", b.intra), ("interestadual", b.inter)):
        aba.append([nome, parcela.debito, parcela.credito_rateado,
                    parcela.base_do_incentivo, parcela.percentual / 100,
                    parcela.credito_presumido])
        n = aba.max_row
        if b.debito_beneficiado:
            # O crédito se rateia pela participação de cada destino no débito.
            aba.cell(row=n, column=3).value = (
                f"=B{credito}*B{n}/(B{intra}+B{inter})"
            )
        aba.cell(row=n, column=4).value = f"=MAX(B{n}-C{n},0)"
        aba.cell(row=n, column=6).value = f"=D{n}*E{n}"
    aba.append(["Crédito presumido total", b.debito_beneficiado,
                b.credito_da_parcela_incentivada, b.base_do_incentivo, None,
                b.credito_presumido])
    total = aba.max_row
    for coluna in "BCDF":
        aba[f"{coluna}{total}"] = f"=SUM({coluna}{intra}:{coluna}{inter})"
    for celula in aba[total]:
        celula.font = Font(bold=True)
    for n in range(intra, total + 1):
        for coluna in range(2, 7):
            aba.cell(row=n, column=coluna).number_format = (
                PERCENTUAL if coluna == 5 else MOEDA
            )
    return f"F{total}"


def _memoria_da_centralizacao(aba, grupo) -> None:
    """Quem transfere quanto para a centralizadora, com a conta em fórmula."""
    from .nucleo.centralizacao import MECANISMOS

    aba.append([
        f"Centralização de {grupo.uf} em {grupo.centralizadora}"
        + ("" if grupo.homologado else "  (NÃO HOMOLOGADA)")
    ])
    aba.cell(row=aba.max_row, column=1).font = Font(bold=True)
    aba.append(["Regra de transferência",
                f"{grupo.regra} por "
                + MECANISMOS.get(grupo.mecanismo, grupo.mecanismo)])
    proprio = _valor(aba, "Saldo próprio da centralizadora", grupo.saldo_proprio)

    aba.append([None])
    cabecalho = _cabecalho_de_bloco(aba, ["Origem", "Saldo", "Transfere",
                                          "Residual", "Observação"])
    for t in grupo.transferencias:
        teto = (
            f"teto: {reais(t.retido_pelo_teto)} de crédito não coube no saldo "
            "devedor da centralizadora" if t.retido_pelo_teto else None
        )
        aba.append([t.origem, t.saldo_individual, t.valor_transferido,
                    t.saldo_residual, teto])
        n = aba.max_row
        aba.cell(row=n, column=4).value = f"=B{n}-C{n}"
        for coluna in (2, 3, 4):
            aba.cell(row=n, column=coluna).number_format = MOEDA
    ultima = aba.max_row

    aba.append([None])
    recebido = _valor(aba, "Recebido pela centralizadora", grupo.total_recebido)
    if ultima > cabecalho:
        aba.cell(row=recebido, column=2).value = (
            f"=SUM(C{cabecalho + 1}:C{ultima})"
        )
    final = _valor(aba, "Saldo final do grupo", grupo.saldo_final)
    aba.cell(row=final, column=2).value = f"=B{proprio}+B{recebido}"
    aba.cell(row=final, column=1).font = Font(bold=True)


def _bloco_ajustes(aba, apuracao: Apuracao) -> None:
    """A memória dos ajustes: o que entrou, de onde veio e quem aprovou.

    Junta as duas origens numa lista só — a aba AJUSTES MANUAIS é o formulário,
    esta é a prestação de contas. E traz o que ficou marcado sem ser lançado,
    que não muda número nenhum mas não pode sumir.
    """
    a = apuracao.ajustes
    _secao(aba, "Ajustes declarados")
    if not a.lancamentos:
        aba.append(["", "Nenhum ajuste declarado."])
    else:
        primeira = _cabecalho_de_bloco(aba, [
            "estabelecimento", "atividade", "linha", "valor", "motivo",
            "responsável", "aprovador", "onde foi informado",
        ]) + 1
        for x in a.lancamentos:
            aba.append([x.estabelecimento, x.atividade, f"{x.linha:03d}", x.valor,
                        x.motivo, x.responsavel, x.aprovador, x.onde])
        for linha in aba.iter_rows(min_row=primeira, max_row=aba.max_row,
                                   min_col=4, max_col=4):
            for celula in linha:
                celula.number_format = MOEDA

    if a.anotacoes:
        _secao(aba, f"Marcado, não lançado — {len(a.anotacoes)} linha(s)")
        aba.append(["", "Não entra na apuração; fica aqui para não se perder."])
        primeira = _cabecalho_de_bloco(aba, [
            "estabelecimento", "", "", "valor", "motivo", "responsável", "",
            "onde foi informado",
        ]) + 1
        for x in a.anotacoes:
            aba.append([x.estabelecimento, "", "", x.valor, x.motivo,
                        x.responsavel, "", x.onde])
        ultima = aba.max_row
        for linha in aba.iter_rows(min_row=primeira, max_row=ultima,
                                   min_col=4, max_col=4):
            for celula in linha:
                celula.number_format = MOEDA
        aba.append(["", "Total marcado e não lançado", "", a.marcado_nao_lancado])
        aba.cell(row=aba.max_row, column=4).value = f"=SUM(D{primeira}:D{ultima})"
        aba.cell(row=aba.max_row, column=4).number_format = MOEDA
        aba.cell(row=aba.max_row, column=2).font = Font(bold=True)


def _bloco_saldo_credor(aba, apuracao: Apuracao) -> None:
    """A conta gráfica atravessa a virada do mês — e a planilha mostra por onde.

    A última coluna é o que a competência seguinte tem que receber como
    abertura. Sai daqui pronta para o cadastro, para ninguém ter que subtrair
    duas linhas do registro à mão.
    """
    anterior, seguinte = apuracao.competencia_anterior, apuracao.competencia_seguinte
    _secao(aba, "Saldo credor — linhas 009 e 014 do Registro de Apuração")
    if not apuracao.saldos_declarados:
        aba.append([
            "",
            f"A abertura de {apuracao.competencia} não está declarada em "
            "parametros/saldos.yaml — a apuração rodou com todos os "
            "estabelecimentos abrindo o mês zerados.",
        ])
    _cabecalho_de_bloco(aba, [
        "estabelecimento", f"veio de {anterior}", "apurado no mês",
        f"vai para {seguinte}",
    ])
    for f in sorted(apuracao.filiais.values(), key=lambda f: (f.uf, f.estabelecimento)):
        if not (f.saldo_credor_anterior or f.credor):
            continue
        aba.append([f.estabelecimento, f.saldo_credor_anterior, f.saldo_do_periodo,
                    f.credor])
        n = aba.max_row
        # Só se transporta saldo credor: o devedor sai do caixa.
        aba.cell(row=n, column=4).value = f"=MAX(B{n}+C{n},0)"
        for coluna in (2, 3, 4):
            aba.cell(row=n, column=coluna).number_format = MOEDA
    aba.append([None])
    aba.append([
        "",
        f"A coluna \"vai para {seguinte}\" é a abertura da competência seguinte: "
        "cadastre-a em parametros/saldos.yaml.",
    ])


def _aba_ajustes(wb, apuracao: Apuracao) -> None:
    """O formulário dos ajustes que não têm documento, e a conferência.

    Duas coisas moram aqui. As **parcelas sem documento** são os lançamentos do
    Registro que não pertencem a nota nenhuma — o ajuste que tem dono vai na
    linha dele, na BASE TRATADA, e nem passa por aqui.

    A **conferência** é o que faz a marca `AGUARDA AJUSTE` sumir. Célula vazia
    diz ao mesmo tempo "não tem ajuste" e "ninguém olhou ainda", e a ferramenta
    não tem como escolher uma das duas: por isso alguém assina, e assinar sem
    nenhum ajuste também é resposta.
    """
    from .ajustes import ABA, TITULO_CONFERENCIA, TITULO_PARCELAS

    aba = wb.create_sheet(ABA)
    for coluna, largura in zip("ABCDEFGH", (32, 22, 10, 16, 52, 22, 22, 18)):
        aba.column_dimensions[coluna].width = largura

    aba.append([f"AJUSTES DA APURAÇÃO — competência {apuracao.competencia}"])
    aba.cell(row=1, column=1).font = Font(bold=True, size=14)
    for texto in (
        "Preencha, salve e arraste este mesmo arquivo de volta no Apurabot.",
        "O valor é sempre positivo: quem dá o sentido é a linha do Registro — "
        "002 e 003 aumentam o que se deve, 006 e 007 diminuem.",
        "Use ANOTAR na coluna `linha` para marcar sem lançar (ICMS em "
        "discussão, por exemplo): não muda a apuração e sai no relatório.",
        "Ajuste que pertence a uma nota vai na linha dela, na aba BASE "
        "TRATADA — aqui só o que não tem documento.",
        "A `observação padrão` é o código com que o ajuste entra no Sankhya "
        "(parametros/lancamentos_sankhya.yaml). Opcional: sem ela o ajuste "
        "vale igual, e sai sem código na aba AJUSTES NO SANKHYA.",
    ):
        aba.append(["", texto])

    aba.append([None])   # linha em branco: `append([])` não avança no openpyxl
    aba.append([TITULO_PARCELAS])
    aba.cell(row=aba.max_row, column=1).font = Font(bold=True)
    aba.append(["estabelecimento", "atividade", "linha", "valor", "motivo",
                "responsável", "aprovador", "observação padrão"])
    for celula in aba[aba.max_row]:
        celula.font, celula.fill = TITULO, FUNDO
    primeira = aba.max_row + 1
    for ajuste in apuracao.ajustes.lancamentos + apuracao.ajustes.anotacoes:
        if ajuste.onde.startswith("BASE TRATADA"):
            continue                    # esse tem dono; mora na linha dele
        aba.append([
            ajuste.estabelecimento, ajuste.atividade,
            "ANOTAR" if ajuste.anotacao else f"{ajuste.linha:03d}",
            ajuste.valor, ajuste.motivo, ajuste.responsavel, ajuste.aprovador,
            ajuste.observacao_padrao or None,
        ])
    for _ in range(12):                 # espaço para escrever
        aba.append([None])   # linha em branco: `append([])` não avança no openpyxl
    for linha in aba.iter_rows(min_row=primeira, max_row=aba.max_row,
                               min_col=1, max_col=8):
        for celula in linha:
            celula.border = BORDA       # a grade vazia é o formulário
            if celula.column == 4:
                celula.number_format = MOEDA

    aba.append([TITULO_CONFERENCIA])
    aba.cell(row=aba.max_row, column=1).font = Font(bold=True)
    aba.append(["estabelecimento", "conferido por", "conferido em", "observação"])
    for celula in aba[aba.max_row]:
        celula.font, celula.fill = TITULO, FUNDO
    for filial in sorted(
        apuracao.filiais.values(), key=lambda f: (f.uf, f.estabelecimento)
    ):
        assinada = apuracao.ajustes.conferencia.get(filial.estabelecimento)
        aba.append([
            filial.estabelecimento,
            assinada.por if assinada else None,
            assinada.em if assinada else None,
            assinada.observacao if assinada else None,
        ])
    aba.append([None])   # linha em branco: `append([])` não avança no openpyxl
    aba.append(["", "Estabelecimento com `conferido por` preenchido para de "
                    "mostrar AGUARDA AJUSTE — inclusive sem nenhum ajuste."])


#: Ordem das abas — por prioridade de leitura. O Registro abre o arquivo, a
#: APURAÇÃO EFETIVA é o coração da conta, e os ajustes do Sankhya vêm por
#: último, porque só se usam depois de fechados os ajustes manuais. As ocultas
#: ficam no fim.
ORDEM_DAS_ABAS = [
    ABA_REGISTRO, ABA_EFETIVA, ABA_DETALHES, ABA_1200, ABA_AJUSTES,
    ABA_TRANSFERENCIAS, ABA_PENDENCIAS, ABA_BASE, ABA_LANCAMENTOS,
    ABA_RESUMO, ABA_POR_CARGA,
]


def _ordenar_abas(wb) -> None:
    posicao = {nome: i for i, nome in enumerate(ORDEM_DAS_ABAS)}
    wb._sheets.sort(key=lambda aba: posicao.get(aba.title, len(posicao)))


def _acabamento(wb) -> None:
    """O que vale para o arquivo inteiro: nada congelado, bordas, abas ocultas."""
    for aba in wb.worksheets:
        aba.freeze_panes = None
        _bordas(aba)
        if aba.title in ABAS_OCULTAS:
            aba.sheet_state = "hidden"
    # Aba oculta não pode ser a ativa: o arquivo abre na primeira visível.
    visiveis = [i for i, aba in enumerate(wb.worksheets)
                if aba.sheet_state == "visible"]
    if visiveis:
        wb.active = visiveis[0]
        for i, aba in enumerate(wb.worksheets):
            aba.sheet_view.tabSelected = i == visiveis[0]


def _ocupada(celula) -> bool:
    return celula.value not in (None, "") or celula.fill.fill_type == "solid"


def _bordas(aba) -> None:
    """Cinza médio em volta de tudo que é dado ou tabela.

    Linha de tabela é a que tem mais de uma célula preenchida, a que tem fundo
    (os cabeçalhos e as faixas de título) e qualquer linha que venha depois de
    um cabeçalho, no mesmo bloco — é o caso da conferência, que só traz o nome
    do estabelecimento até alguém assinar. A borda vai da primeira à última
    coluna da tabela, para a grade sair inteira mesmo onde a linha tem célula
    vazia. Texto solto numa célula só antes da tabela — título da aba, nota,
    instrução — fica sem borda: riscado, ele só fica mais difícil de ler.
    """
    bloco: list[tuple[tuple, list[int]]] = []

    def fechar() -> None:
        tabela, depois_do_cabecalho = [], False
        for linha, ocupadas in bloco:
            fundo = any(c.fill.fill_type == "solid"
                        for c in linha if c.column in ocupadas)
            if fundo or len(ocupadas) > 1 or depois_do_cabecalho:
                tabela.append((linha, ocupadas))
            depois_do_cabecalho = depois_do_cabecalho or fundo
        if tabela:
            primeira = min(o[0] for _, o in tabela)
            ultima = max(o[-1] for _, o in tabela)
            for linha, _ in tabela:
                n = linha[0].row
                for coluna in range(primeira, ultima + 1):
                    aba.cell(row=n, column=coluna).border = BORDA
        bloco.clear()

    # Onde a coluna A é a filial de cada linha (o filtro), ela não conta: está
    # preenchida em toda linha, inclusive nas que separam as tabelas.
    filial = aba.title in ABAS_COM_FILIAL
    for linha in aba.iter_rows():
        ocupadas = [c.column for c in linha
                    if _ocupada(c) and not (filial and c.column == 1)]
        if ocupadas:
            bloco.append((linha, ocupadas))
        else:
            fechar()
    fechar()


def escrever(
    base: BaseTratada,
    destino: Path | str,
    apuracao: Apuracao | None = None,
    ajustes=None,
) -> Path:
    """Grava a base tratada, a apuração e as conferências em .xlsx."""
    destino = Path(destino)
    destino.parent.mkdir(parents=True, exist_ok=True)
    apuracao = apuracao if apuracao is not None else apurar(base)

    wb = Workbook()
    wb.remove(wb.active)
    _aba_base(wb, base)
    _aba_pendencias(wb, base, apuracao)
    _aba_por_carga(wb, base)
    _aba_apuracao(wb, apuracao)
    aba_apuracao_efetiva(wb, apuracao, base.parametros)
    registros = aba_registro(wb, apuracao, base.parametros, ajustes)
    aba_lancamentos(wb, apuracao, base.parametros, registros, ajustes)
    aba_registro_1200(wb, apuracao, base.parametros, ajustes)
    _aba_ajustes(wb, apuracao)
    aba_transferencias(wb, apuracao)
    _aba_resumo(wb, base)
    _ordenar_abas(wb)
    _acabamento(wb)
    wb.save(destino)
    return destino
