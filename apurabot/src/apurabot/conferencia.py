"""As abas de conferência da apuração.

Três visões da mesma competência, cada uma respondendo a uma pergunta diferente:

`APURAÇÃO EFETIVA`   por que cada crédito foi estornado ou apropriado — CFOP,
                     alíquota e produto, com a conta à vista e o CHECK fechando
                     linha a linha.

`REGISTRO`           o espelho do Registro de Apuração do ICMS, um bloco por
                     estabelecimento e um totalizador no fim — que é o que o
                     PDF do ERP, emitido filial a filial, não mostra.

`TRANSFERÊNCIAS`     o que precisa ser transferido para a centralizadora depois
                     que a competência fechar.
"""
from __future__ import annotations

from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

from .apuracao import Apuracao, LinhaApurada
from .nucleo import atividade as ativ
from .nucleo import centralizacao as centr
from .nucleo import registro as reg

TITULO = Font(bold=True, color="FFFFFF")
FUNDO = PatternFill("solid", fgColor="1F3864")
FUNDO_CLARO = PatternFill("solid", fgColor="D9E2F3")
FUNDO_ATENCAO = PatternFill("solid", fgColor="FFF2CC")
MOEDA = "#,##0.00"
PERCENTUAL = "0.00%"
VERMELHO = Font(bold=True, color="B00020")
VERDE = Font(bold=True, color="1E7B34")

ROTULO_SEM_ATIVIDADE = "(não segregada)"

#: Como a atividade aparece na conferência — os nomes que o time fiscal usa.
ROTULO_DA_ATIVIDADE = {
    ativ.INDUSTRIAL: "Produção",
    ativ.COMERCIAL: "Comercial",
    ativ.IMPORTADOS: "Importados",
    ativ.PRESTACIONAL: "Prestacional / Outras",
}


# --------------------------------------------------------------------------
# Utilitários de escrita
# --------------------------------------------------------------------------

def _larguras(aba, larguras: list[int]) -> None:
    for i, largura in enumerate(larguras, start=1):
        aba.column_dimensions[get_column_letter(i)].width = largura


def _titulo(aba, texto: str, ate: int, *, fundo=FUNDO, fonte=TITULO) -> int:
    linha = aba.max_row + 1
    aba.cell(row=linha, column=1, value=texto)
    for coluna in range(1, ate + 1):
        celula = aba.cell(row=linha, column=coluna)
        celula.fill, celula.font = fundo, fonte
    return linha


def _cabecalho(aba, rotulos: list[str]) -> int:
    linha = aba.max_row + 1
    for i, rotulo in enumerate(rotulos, start=1):
        celula = aba.cell(row=linha, column=i, value=rotulo)
        celula.font, celula.fill = TITULO, FUNDO
        celula.alignment = Alignment(vertical="center", wrap_text=True)
    return linha


def _moeda(aba, linha: int, colunas: range) -> None:
    for coluna in colunas:
        aba.cell(row=linha, column=coluna).number_format = MOEDA


def _vazio(aba) -> None:
    aba.append([])


# --------------------------------------------------------------------------
# APURAÇÃO EFETIVA
# --------------------------------------------------------------------------

COLUNAS_EFETIVA = [
    "CFOP", "Descrição", "Alíquota", "Produto",
    "Vlr. contábil", "BC ICMS", "Vlr. ICMS",
    "Operação", "Parcela não tributada", "ICMS a estornar", "ICMS a apropriar",
    "CHECK",
]


def _parcela(apurada: LinhaApurada) -> float | None:
    """Fração do crédito que a regra manda estornar."""
    bruto = apurada.resultado.credito_bruto
    return (apurada.credito_a_estornar / bruto) if bruto else None


def _rotulo_atividade(apurada: LinhaApurada) -> str:
    if not apurada.atividade:
        # A UF não segrega por atividade: mostra a categoria da equalização,
        # que é o corte que faz sentido ali.
        return apurada.tratada.classificacao.categoria or ROTULO_SEM_ATIVIDADE
    return ROTULO_DA_ATIVIDADE.get(apurada.atividade, apurada.atividade)


def aba_apuracao_efetiva(wb, apuracao: Apuracao) -> None:
    """Conferência do crédito, do estorno e da apropriação, linha a linha."""
    aba = wb.create_sheet("APURAÇÃO EFETIVA")
    _larguras(aba, [10, 32, 10, 44, 16, 16, 15, 14, 12, 16, 16, 11])

    aba.append(["APURAÇÃO EFETIVA — crédito, estorno e apropriação por CFOP e produto"])
    aba.cell(row=1, column=1).font = Font(bold=True, size=14)
    aba.append([
        "Um bloco por estabelecimento. CHECK = a estornar + a apropriar − ICMS "
        "creditado; qualquer valor diferente de zero é erro de motor."
    ])

    for filial in sorted(
        apuracao.filiais.values(), key=lambda f: (f.uf, f.estabelecimento)
    ):
        _bloco_efetiva(aba, filial)

    aba.freeze_panes = "A3"


def _bloco_efetiva(aba, filial) -> None:
    _vazio(aba)
    _titulo(
        aba,
        f"{filial.estabelecimento}  —  {filial.uf}  —  regime {filial.regime}",
        len(COLUNAS_EFETIVA),
    )
    entradas = [a for a in filial.apuradas if a.resultado.credito_bruto]
    if not entradas:
        aba.append(["", "Sem crédito de entrada nesta competência."])
        _blocos_de_fechamento(aba, filial)
        return

    _cabecalho(aba, COLUNAS_EFETIVA)

    for cfop, do_cfop in _por_cfop(entradas):
        _linha_agrupadora(aba, do_cfop, nivel=0, chave=cfop or "(sem CFOP)",
                          descricao=_descricao_cfop(do_cfop))
        for aliquota, do_grupo in _por_aliquota(do_cfop):
            _linha_agrupadora(aba, do_grupo, nivel=1, aliquota=aliquota)
            for apurada in sorted(do_grupo, key=_nome_do_produto):
                _linha_de_produto(aba, apurada, aliquota)

    _linha_agrupadora(aba, entradas, nivel=0, chave="TOTAL", negrito=True)
    _blocos_de_fechamento(aba, filial)


def _nome_do_produto(apurada: LinhaApurada) -> str:
    return str(apurada.tratada.origem.dados.get("produto_descricao") or "")


def _descricao_cfop(apuradas: list[LinhaApurada]) -> str:
    return str(apuradas[0].tratada.origem.dados.get("cfop_descricao") or "").strip()


def _por_cfop(apuradas: list[LinhaApurada]):
    grupos: dict = {}
    for a in apuradas:
        grupos.setdefault(a.tratada.origem.cfop_int, []).append(a)
    return sorted(grupos.items(), key=lambda kv: (kv[0] is None, kv[0] or 0))


def _por_aliquota(apuradas: list[LinhaApurada]):
    grupos: dict = {}
    for a in apuradas:
        try:
            aliquota = float(a.tratada.origem.dados.get("aliquota_icms") or 0.0)
        except (TypeError, ValueError):
            aliquota = 0.0
        grupos.setdefault(aliquota, []).append(a)
    return sorted(grupos.items())


def _somas(apuradas: list[LinhaApurada]) -> tuple[float, float, float, float, float]:
    contabil = base = icms = estornar = apropriar = 0.0
    for a in apuradas:
        dados = a.tratada.origem.dados
        contabil += _numero(dados.get("valor_contabil"))
        base += _numero(dados.get("base_icms"))
        icms += a.resultado.credito_bruto
        estornar += a.credito_a_estornar
        apropriar += a.credito_a_apropriar
    return contabil, base, icms, estornar, apropriar


def _numero(valor) -> float:
    try:
        return float(valor or 0.0)
    except (TypeError, ValueError):
        return 0.0


def _linha_agrupadora(
    aba, apuradas, *, nivel: int, chave=None, descricao: str = "",
    aliquota: float | None = None, negrito: bool = False,
) -> None:
    contabil, base, icms, estornar, apropriar = _somas(apuradas)
    aba.append([
        chave if nivel == 0 else "", descricao,
        f"{aliquota:g}%" if aliquota is not None else "", "",
        contabil, base, icms, "", None, estornar, apropriar,
        round(estornar + apropriar - icms, 2) + 0.0,
    ])
    linha = aba.max_row
    _moeda(aba, linha, range(5, 8))
    _moeda(aba, linha, range(10, 13))
    for celula in aba[linha]:
        celula.font = Font(bold=True)
        if nivel == 0 and not negrito:
            celula.fill = FUNDO_CLARO
    if nivel:
        aba.row_dimensions[linha].outlineLevel = 1


def _linha_de_produto(aba, apurada: LinhaApurada, aliquota: float) -> None:
    dados = apurada.tratada.origem.dados
    parcela = _parcela(apurada)
    icms = apurada.resultado.credito_bruto
    aba.append([
        "", "", f"{aliquota:g}%", _nome_do_produto(apurada),
        _numero(dados.get("valor_contabil")), _numero(dados.get("base_icms")), icms,
        _rotulo_atividade(apurada), parcela,
        apurada.credito_a_estornar, apurada.credito_a_apropriar,
        round(apurada.credito_a_estornar + apurada.credito_a_apropriar - icms, 2) + 0.0,
    ])
    linha = aba.max_row
    _moeda(aba, linha, range(5, 8))
    _moeda(aba, linha, range(10, 13))
    aba.cell(row=linha, column=9).number_format = PERCENTUAL
    aba.row_dimensions[linha].outlineLevel = 2
    if not apurada.confere:
        aba.cell(row=linha, column=12).font = VERMELHO


def _blocos_de_fechamento(aba, filial) -> None:
    """Créditos e débitos por atividade — o fechamento que a GIA pede."""
    por_atividade: dict[str, dict[str, float]] = {}
    for a in filial.apuradas:
        chave = _rotulo_atividade(a)
        alvo = por_atividade.setdefault(
            chave, {"bc_credito": 0.0, "credito": 0.0, "estorno": 0.0,
                    "bc_debito": 0.0, "debito": 0.0}
        )
        base = _numero(a.tratada.origem.dados.get("base_icms"))
        if a.resultado.credito_bruto:
            alvo["bc_credito"] += base
            alvo["credito"] += a.resultado.credito_bruto
            alvo["estorno"] += a.credito_a_estornar
        if a.resultado.debito:
            alvo["bc_debito"] += base
            alvo["debito"] += a.resultado.debito

    _vazio(aba)
    _titulo(aba, "CRÉDITOS", 6, fundo=FUNDO_CLARO, fonte=Font(bold=True))
    _cabecalho(aba, ["", "Atividade", "BC ICMS", "VLR ICMS", "ESTORNO ICMS",
                     "A APROPRIAR"])
    soma = [0.0, 0.0, 0.0]
    for nome in sorted(por_atividade):
        v = por_atividade[nome]
        if not v["credito"]:
            continue
        aba.append(["", nome, v["bc_credito"], v["credito"], v["estorno"],
                    v["credito"] - v["estorno"]])
        _moeda(aba, aba.max_row, range(3, 7))
        soma = [soma[0] + v["bc_credito"], soma[1] + v["credito"],
                soma[2] + v["estorno"]]
    aba.append(["", "TOTAL", soma[0], soma[1], soma[2], soma[1] - soma[2]])
    _moeda(aba, aba.max_row, range(3, 7))
    for celula in aba[aba.max_row]:
        celula.font = Font(bold=True)

    _vazio(aba)
    _titulo(aba, "DÉBITOS", 6, fundo=FUNDO_CLARO, fonte=Font(bold=True))
    _cabecalho(aba, ["", "Atividade", "BC ICMS", "VLR ICMS"])
    soma_debito = [0.0, 0.0]
    for nome in sorted(por_atividade):
        v = por_atividade[nome]
        if not v["debito"]:
            continue
        aba.append(["", nome, v["bc_debito"], v["debito"]])
        _moeda(aba, aba.max_row, range(3, 5))
        soma_debito = [soma_debito[0] + v["bc_debito"], soma_debito[1] + v["debito"]]
    aba.append(["", "TOTAL", soma_debito[0], soma_debito[1]])
    _moeda(aba, aba.max_row, range(3, 5))
    for celula in aba[aba.max_row]:
        celula.font = Font(bold=True)

    if filial.beneficio:
        _vazio(aba)
        _titulo(aba, "BENEFÍCIO FISCAL", 6, fundo=FUNDO_CLARO, fonte=Font(bold=True))
        for passo in filial.beneficio.memoria:
            aba.append(["", passo])


# --------------------------------------------------------------------------
# REGISTRO
# --------------------------------------------------------------------------

COLUNAS_REGISTRO = [12, 40, 18, 18, 18, 18, 18]

CABECALHO_VALORES = [
    "Valores Contábeis", "Base de Cálculo", "Imposto {verbo}",
    "Isentas / N. Trib.", "Outras",
]


def aba_registro(wb, apuracao: Apuracao, params, ajustes=None) -> list:
    """Espelho do Registro de Apuração — um bloco por filial e o totalizador."""
    aba = wb.create_sheet("REGISTRO")
    _larguras(aba, COLUNAS_REGISTRO)

    aba.append(["REGISTRO DE APURAÇÃO DO ICMS"])
    aba.cell(row=1, column=1).font = Font(bold=True, size=14)
    aba.append([
        "Espelho do livro por estabelecimento. As linhas do resumo marcadas "
        "AGUARDA AJUSTE dependem de lançamento aprovado que não nasce do Livro Fiscal."
    ])

    registros = reg.montar(apuracao, params, ajustes)
    for registro in registros:
        _bloco_registro(aba, registro)
    if len(registros) > 1:
        _bloco_registro(aba, reg.totalizador(registros, apuracao.base.competencia))

    aba.freeze_panes = "A3"
    return registros


def _bloco_registro(aba, registro: reg.Registro) -> None:
    _vazio(aba)
    _vazio(aba)
    _titulo(aba, registro.estabelecimento, 7)
    if registro.gerencial:
        aba.append([
            "", "Soma dos estabelecimentos. Não é documento fiscal: consolida "
            "UFs com contas gráficas distintas."
        ])
    else:
        aba.append(["FIRMA", registro.estabelecimento, "UF", registro.uf])
        aba.append([
            "CNPJ", registro.cnpj or "(não cadastrado)",
            "INSCRIÇÃO ESTADUAL", registro.inscricao_estadual or "(não cadastrado)",
        ])
        aba.append(["PERÍODO", registro.competencia])

    _bloco_de_valores(aba, registro.entradas, "Creditado")
    _bloco_de_valores(aba, registro.saidas, "Debitado")
    _bloco_de_resumo(aba, registro)


def _bloco_de_valores(aba, bloco: reg.Bloco, verbo: str) -> None:
    _vazio(aba)
    _titulo(aba, bloco.lado, 7, fundo=FUNDO_CLARO, fonte=Font(bold=True))
    _cabecalho(
        aba,
        ["CFOP", "Codificação Contábil-Fiscal"]
        + [c.format(verbo=verbo) for c in CABECALHO_VALORES],
    )
    for linha in bloco.linhas:
        aba.append([linha.cfop, linha.descricao, *linha.valores.as_tuple()])
        _moeda(aba, aba.max_row, range(3, 8))

    for grupo in bloco.grupos():
        valores = bloco.subtotal(grupo)
        aba.append(["", f"Subtotal {grupo}", *valores.as_tuple()])
        _moeda(aba, aba.max_row, range(3, 8))
        for celula in aba[aba.max_row]:
            celula.fill = FUNDO_CLARO

    aba.append(["", "TOTAL", *bloco.total.as_tuple()])
    _moeda(aba, aba.max_row, range(3, 8))
    for celula in aba[aba.max_row]:
        celula.font = Font(bold=True)


#: Linhas que consolidam as anteriores — vão na coluna "Somas".
LINHAS_DE_SOMA = {4, 8, 10, 11, 13, 14}


def _bloco_de_resumo(aba, registro: reg.Registro) -> None:
    _vazio(aba)
    _titulo(aba, "RESUMO DA APURAÇÃO DO IMPOSTO", 7,
            fundo=FUNDO_CLARO, fonte=Font(bold=True))
    _cabecalho(aba, ["Código", "Descrição", "Coluna Auxiliar", "Valores", "Somas",
                     "", "Situação"])
    if registro.gerencial:
        aba.append([
            "", "As linhas 011 a 014 são a soma do resultado de cada "
            "estabelecimento, não o recálculo sobre os totais: crédito de uma UF "
            "não abate débito de outra."
        ])
        aba.cell(row=aba.max_row, column=2).fill = FUNDO_ATENCAO

    for item in registro.resumo:
        soma = item.codigo in LINHAS_DE_SOMA
        aba.append([
            f"{item.codigo:03d}", item.rotulo, None,
            None if soma else item.valor,
            item.valor if soma else None, "",
            "AGUARDA AJUSTE" if item.aguarda_ajuste else "",
        ])
        linha = aba.max_row
        _moeda(aba, linha, range(3, 6))
        if soma:
            for celula in aba[linha]:
                celula.font = Font(bold=True)
        if item.aguarda_ajuste:
            aba.cell(row=linha, column=7).fill = FUNDO_ATENCAO
        if item.codigo == 13:
            aba.cell(row=linha, column=5).font = VERMELHO if item.valor else VERDE

        for descricao, valor in item.discriminacao:
            aba.append(["", f"    {descricao}", valor])
            aba.cell(row=aba.max_row, column=3).number_format = MOEDA
            aba.row_dimensions[aba.max_row].outlineLevel = 1


# --------------------------------------------------------------------------
# TRANSFERÊNCIAS
# --------------------------------------------------------------------------

def aba_transferencias(wb, apuracao: Apuracao) -> None:
    """O que transferir para a centralizadora depois de fechar a competência."""
    aba = wb.create_sheet("TRANSFERÊNCIAS")
    _larguras(aba, [34, 34, 18, 18, 18, 30, 22, 16])

    aba.append(["TRANSFERÊNCIAS DE SALDO A EMITIR"])
    aba.cell(row=1, column=1).font = Font(bold=True, size=14)
    aba.append([
        "A transferência é consequência da apuração: o documento que a formaliza "
        "só pode ser emitido depois do encerramento e vai escriturado na "
        "competência seguinte. Esta aba é a instrução, não uma conferência."
    ])

    if not apuracao.centralizacao:
        _vazio(aba)
        aba.append(["", "Nenhuma UF com apuração centralizada parametrizada."])
        return

    for grupo in apuracao.centralizacao:
        _vazio(aba)
        _titulo(aba, f"{grupo.uf} — centraliza em {grupo.centralizadora}", 8)
        if not grupo.homologado:
            aba.append([
                "", "REGRA NÃO HOMOLOGADA — falta a Gerência Fiscal/Tributária "
                "confirmar o que se transfere e por qual documento."
            ])
            aba.cell(row=aba.max_row, column=2).fill = FUNDO_ATENCAO

        _cabecalho(aba, [
            "Origem", "Destino", "Saldo do estabelecimento", "A transferir",
            "Saldo residual", "Mecanismo", "CFOP sugerido", "Confere",
        ])
        for t in grupo.transferencias:
            aba.append([
                t.origem, t.destino, t.saldo_individual, t.valor_transferido,
                t.saldo_residual,
                centr.MECANISMOS.get(t.mecanismo, t.mecanismo),
                ", ".join(str(c) for c in t.cfop_sugerido) if t.cfop_sugerido else "",
                "OK" if t.confere else "DIVERGE",
            ])
            _moeda(aba, aba.max_row, range(3, 6))

        _vazio(aba)
        for rotulo, valor in (
            ("Saldo próprio da centralizadora", grupo.saldo_proprio),
            ("Recebido dos centralizados", grupo.total_recebido),
            ("Saldo final do grupo", grupo.saldo_final),
        ):
            aba.append(["", rotulo, valor])
            aba.cell(row=aba.max_row, column=3).number_format = MOEDA
        for celula in aba[aba.max_row]:
            celula.font = Font(bold=True)

        _vazio(aba)
        aba.append(["", "O que emitir:"])
        aba.cell(row=aba.max_row, column=2).font = Font(bold=True)
        for instrucao in grupo.instrucoes:
            aba.append(["", instrucao])
        if not grupo.instrucoes:
            aba.append(["", "Nada a transferir nesta competência."])
