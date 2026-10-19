"""O painel desenhado: duas abas, três gráficos e nenhuma fórmula.

### Por que valores e não fórmulas

O arquivo de origem é feito de `CONT.SES` e `SOMASES` apontando para
`Pendentes!$D$2:$D$68`. Aqui as contas já foram feitas em Python, e o que vai
para a célula é o número. Três motivos, nesta ordem:

* o intervalo `$2:$68` é a semana 38 e mais nenhuma. Fórmula com intervalo
  fixo é a mesma armadilha do índice de coluna fixo que o porte tirou do VBA:
  na semana seguinte ela aponta para o lugar errado **sem errar**;
* fórmula só mostra número depois que o Excel abre e calcula. Quem recebe o
  arquivo por e-mail e olha no celular vê o painel montado;
* o valor gravado é o valor que a ferramenta afirma. Se ele estiver errado, o
  erro é reproduzível — não depende de quem abriu, com qual versão.

O que se perde é o painel se corrigir sozinho quando alguém edita uma linha
depois. É deliberado: o resumo é gerado **depois** da classificação fechar, e
editar o relatório depois disso pede rodar o resumo de novo, não confiar num
recálculo silencioso.

### O desenho é o do painel da semana 38

`[FATO]` Cores e bordas foram medidas no print do painel da semana 38, pixel
a pixel: barras de título e cabeçalhos em cinza-escuro `393939` com letra
branca; cada categoria com a sua cor — Diretos `AB99D5`, Indiretos `193A62`,
Serviços `8EACC3` — na fatia, na barra e na célula da tabela; a grade das
tabelas em `D0D0D0`; a moldura e as linhas de grade dos gráficos em `898989`,
de canto reto. A cor mora aqui e não num parâmetro porque não é regra: é o
desenho que o time já reconhece.

Cada gráfico é preso às células pelos dois cantos. Medido em centímetro, como
era, a pizza passava da linha 12 e cobria a tabela por categoria.

### O que o arquivo perde ao passar por aqui

`[FATO]` O openpyxl não preserva gráfico nem imagem das abas que ele apenas
relê. O relatório da semana, como a ferramenta o gera, não tem nenhum dos
dois — mas um gráfico que alguém tenha colado à mão em outra aba não
sobrevive. Está dito na tela, contado, em vez de sumir calado.
"""
from __future__ import annotations

from typing import Sequence

from openpyxl.chart import BarChart, PieChart, Reference
from openpyxl.chart.axis import ChartLines
from openpyxl.chart.data_source import NumFmt
from openpyxl.chart.label import DataLabelList
from openpyxl.chart.layout import Layout, ManualLayout
from openpyxl.chart.marker import DataPoint
from openpyxl.chart.shapes import GraphicalProperties
from openpyxl.chart.text import RichText
from openpyxl.drawing.line import LineProperties
from openpyxl.drawing.spreadsheet_drawing import AnchorMarker, TwoCellAnchor
from openpyxl.drawing.text import (CharacterProperties, Font as FonteDoGrafico,
                                   Paragraph, ParagraphProperties,
                                   RichTextProperties)
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side

from . import colunas as col
from .fontes import Pendencia
from .painel import Corte, Painel

#: A fonte do painel é a mesma do resto da planilha.
FONTE = "Aptos Narrow"
TAMANHO = 10

# -- as cores, medidas no print da semana 38 -------------------------------

#: Barras de título, cabeçalhos e a linha do total.
COR_ESCURA = "393939"
BRANCO = "FFFFFF"
PRETO = "000000"
#: A grade das tabelas.
COR_DA_GRADE = "D0D0D0"
#: A moldura dos gráficos e as linhas de grade dentro deles.
COR_DA_MOLDURA = "898989"
#: A cor de cada categoria — a mesma na pizza, nas barras e na tabela.
COR_DA_CATEGORIA = {
    col.DIRETOS: "AB99D5",
    col.INDIRETOS: "193A62",
    col.SERVICOS: "8EACC3",
}
#: Sobre o azul-escuro de Indiretos o rótulo é branco; nas outras duas, preto.
LETRA_SOBRE_A_CATEGORIA = {
    col.DIRETOS: PRETO,
    col.INDIRETOS: BRANCO,
    col.SERVICOS: PRETO,
}

#: Rótulo de barra que dá zero não é escrito: a terceira seção do formato é
#: o zero, e vazia ela some. Sem isso, cada unidade sem Diretos ganharia um
#: "R$ 0" flutuando no pé da coluna.
FORMATO_DO_ROTULO_DE_VALOR = '"R$" #,##0;-"R$" #,##0;;'
FORMATO_DO_EIXO_DE_VALOR = '"R$" #,##0'
FORMATO_DO_ROTULO_DE_QUANTIDADE = "0;-0;;"

_FINA = Side(style="thin", color=COR_DA_GRADE)
GRADE = Border(left=_FINA, right=_FINA, top=_FINA, bottom=_FINA)


# -- células ----------------------------------------------------------------

def _barra(aba, linha: int, coluna: int, largura: int, texto: str,
           tamanho: int = TAMANHO - 1) -> None:
    """Uma barra de título: fundo escuro, letra branca, mesclada no bloco."""
    for j in range(largura):
        celula = aba.cell(linha, coluna + j)
        celula.fill = PatternFill("solid", fgColor=COR_ESCURA)
        celula.border = GRADE
    celula = aba.cell(linha, coluna, texto)
    celula.font = Font(name=FONTE, size=tamanho, bold=True, color=BRANCO)
    celula.alignment = Alignment(horizontal="center", vertical="center")
    if largura > 1:
        aba.merge_cells(start_row=linha, start_column=coluna,
                        end_row=linha, end_column=coluna + largura - 1)


def _cabecalho(aba, linha: int, coluna: int, rotulos: Sequence[str]) -> None:
    """Cabeçalho de tabela: como a barra de título, uma célula por rótulo."""
    for i, rotulo in enumerate(rotulos):
        celula = aba.cell(linha, coluna + i, rotulo)
        celula.font = Font(name=FONTE, size=TAMANHO - 1, bold=True,
                           color=BRANCO)
        celula.fill = PatternFill("solid", fgColor=COR_ESCURA)
        celula.border = GRADE
        celula.alignment = Alignment(horizontal="center", vertical="center",
                                     wrap_text=True)


def _celula(aba, linha: int, coluna: int, valor, formato: str | None = None,
            *, alinhar: str | None = None, grade: bool = False):
    celula = aba.cell(linha, coluna, valor)
    celula.font = Font(name=FONTE, size=TAMANHO)
    if formato:
        celula.number_format = formato
    if alinhar:
        celula.alignment = Alignment(horizontal=alinhar, vertical="center")
    if grade:
        celula.border = GRADE
    return celula


# -- a aba auxiliar ---------------------------------------------------------

def _cabecalho_auxiliar(aba, coluna: int, rotulos: Sequence[str]) -> None:
    negrito = Font(name=FONTE, size=TAMANHO, bold=True)
    for i, rotulo in enumerate(rotulos):
        aba.cell(1, coluna + i, rotulo).font = negrito


def escrever_auxiliar(livro, painel: Painel):
    """`_AuxResumo` — o intervalo para onde os três gráficos apontam.

    Ela existe pelo mesmo motivo que existe no arquivo de origem: gráfico de
    Excel aponta para células, não para uma lista. Nasce oculta.
    """
    aba = livro.create_sheet(col.ABA_AUXILIAR)
    aba.sheet_state = "hidden"

    # A:C — as três categorias, que é o que a pizza mostra.
    _cabecalho_auxiliar(aba, col.BLOCO_DAS_CATEGORIAS,
                        (col.TABELA_DE_CATEGORIAS[0],
                         col.CABECALHO_DA_QUANTIDADE, col.CABECALHO_DO_VALOR))
    for i, linha in enumerate(painel.categorias, start=2):
        _celula(aba, i, 1, linha.categoria)
        _celula(aba, i, 2, linha.quantidade)
        _celula(aba, i, 3, linha.valor, col.FORMATO_DE_VALOR)

    # D:G e H:K — a unidade contada e a unidade somada, todas as cadastradas.
    # AI:AL — só as que têm pendência, que é o que o gráfico mostra.
    for bloco, cortes, somar in (
            (col.BLOCO_DA_CONTAGEM_POR_UNIDADE, painel.unidades, False),
            (col.BLOCO_DO_VALOR_POR_UNIDADE, painel.unidades, True),
            (col.BLOCO_DO_GRAFICO_DE_UNIDADES, painel.unidades_do_grafico,
             True)):
        _cabecalho_auxiliar(aba, bloco,
                            (col.CABECALHO_DA_UNIDADE,
                             *col.CATEGORIAS_DO_GRAFICO))
        _escrever_cortes(aba, bloco, cortes, somar)

    # L:O — todos os guardiões; AD:AG — só os que entram no gráfico.
    for bloco, cortes in (
            (col.BLOCO_DOS_GUARDIOES, painel.guardioes),
            (col.BLOCO_DO_GRAFICO_DE_GUARDIOES, painel.guardioes_do_grafico)):
        _cabecalho_auxiliar(aba, bloco,
                            (col.CABECALHO_DO_GUARDIAO,
                             *col.CATEGORIAS_DO_GRAFICO))
        _escrever_cortes(aba, bloco, cortes, False)
    return aba


def _escrever_cortes(aba, coluna: int, cortes: Sequence[Corte],
                     somar: bool) -> None:
    for i, corte in enumerate(cortes, start=2):
        _celula(aba, i, coluna, corte.nome)
        for j, categoria in enumerate(col.CATEGORIAS_DO_GRAFICO, start=1):
            valor = (corte.valor[categoria] if somar
                     else corte.quantidade[categoria])
            _celula(aba, i, coluna + j, valor,
                    col.FORMATO_DE_VALOR if somar else None)


# -- os três gráficos -------------------------------------------------------

def _texto(tamanho: float = 9, *, negrito: bool = False,
           cor: str = PRETO) -> RichText:
    """A fonte de um pedaço do gráfico — rótulo, eixo ou legenda."""
    letra = CharacterProperties(latin=FonteDoGrafico(typeface=FONTE),
                                sz=int(tamanho * 100), b=negrito,
                                solidFill=cor)
    return RichText(bodyPr=RichTextProperties(),
                    p=[Paragraph(pPr=ParagraphProperties(defRPr=letra),
                                 endParaRPr=letra)])


def _linha(cor: str = COR_DA_MOLDURA) -> LineProperties:
    return LineProperties(solidFill=cor, w=9525)          # 0,75 pt


def _sem_linha() -> LineProperties:
    return LineProperties(noFill=True)


def _moldura(grafico) -> None:
    """Fundo branco, moldura cinza fina e canto reto — não arredondado."""
    grafico.roundedCorners = False
    grafico.graphical_properties = GraphicalProperties(solidFill=BRANCO,
                                                       ln=_linha())
    grafico.plot_area.graphicalProperties = GraphicalProperties(
        noFill=True, ln=_sem_linha())


class _Rotulos(DataLabelList):
    """Os rótulos de dado, com dois reparos na hora de gravar.

    `[FATO]` O openpyxl grava o separador como `<separator val=" "/>`, que o
    esquema do Excel não prevê — o texto vai **dentro** do elemento. E grava o
    formato do rótulo sem `sourceLinked="0"`, e aí o rótulo herda o formato
    da célula: sai `233122,19` em vez de `R$ 233.122`, e o zero aparece.
    """

    tagname = "dLbls"
    # O openpyxl monta a lista do que gravar só com o que a própria classe
    # declara; sem repetir a da mãe, o rótulo sairia vazio.
    __attrs__ = DataLabelList.__attrs__
    __nested__ = DataLabelList.__nested__
    __elements__ = DataLabelList.__elements__

    def to_tree(self, tagname=None, idx=None, namespace=None):
        arvore = super().to_tree(tagname, idx, namespace)
        for filho in arvore:
            nome = filho.tag.rsplit("}", 1)[-1]
            if nome == "separator":
                filho.text = filho.attrib.pop("val", None)
            elif nome == "numFmt":
                filho.set("sourceLinked", "0")
        return arvore


def _rotulos(**mostrar) -> DataLabelList:
    """Rótulos de dado com tudo desligado, menos o que foi pedido.

    O Excel lê o que falta como ligado em alguns casos — por isso cada um é
    escrito, e não deixado de fora.
    """
    rotulos = _Rotulos()
    for nome in ("showLegendKey", "showVal", "showCatName", "showSerName",
                 "showPercent", "showBubbleSize", "showLeaderLines"):
        setattr(rotulos, nome, bool(mostrar.get(nome, False)))
    return rotulos


def _ancorar(grafico, coluna: int, linha: int, largura: int,
             ate_a_linha: int) -> None:
    """Prende o gráfico do canto de `coluna, linha` ao começo de `ate_a_linha`.

    Notação do openpyxl nos argumentos (1 = A); o marcador conta do zero.
    """
    grafico.anchor = TwoCellAnchor(
        _from=AnchorMarker(col=coluna - 1, row=linha - 1),
        to=AnchorMarker(col=coluna - 1 + largura, row=ate_a_linha - 1))


def _pizza(auxiliar, categorias: Sequence[str]) -> PieChart:
    """A proporção de notas pendentes por categoria.

    Cada fatia recebe a cor da sua categoria pelo nome, não pela posição: a
    ordem da aba auxiliar pode mudar sem a cor trocar de dono.
    """
    grafico = PieChart()
    quantas = len(categorias)
    grafico.add_data(Reference(auxiliar, min_col=2, min_row=1,
                               max_row=1 + quantas), titles_from_data=True)
    grafico.set_categories(Reference(auxiliar, min_col=1, min_row=2,
                                     max_row=1 + quantas))
    _moldura(grafico)

    serie = grafico.series[0]
    for i, categoria in enumerate(categorias):
        cor = COR_DA_CATEGORIA.get(categoria)
        if cor:
            serie.dPt.append(DataPoint(idx=i, spPr=GraphicalProperties(
                solidFill=cor, ln=_linha(BRANCO))))
    # "10 7%": a quantidade e a proporção, fora da fatia.
    serie.dLbls = _rotulos(showVal=True, showPercent=True)
    serie.dLbls.separator = " "
    serie.dLbls.position = "outEnd"
    serie.dLbls.txPr = _texto(10, negrito=True)

    grafico.legend.position = "r"
    grafico.legend.txPr = _texto(9, negrito=True)
    # A pizza à esquerda, a legenda no terço da direita.
    grafico.plot_area.layout = Layout(manualLayout=ManualLayout(
        x=0.12, y=0.1, w=0.48, h=0.84, xMode="edge", yMode="edge"))
    return grafico


def _barras(auxiliar, coluna: int, quantas: int, *, deitada: bool,
            formato_do_rotulo: str,
            formato_do_eixo: str | None = None) -> BarChart:
    """Uma barra empilhada por categoria — as três somam o total do corte."""
    grafico = BarChart()
    grafico.type = "bar" if deitada else "col"
    grafico.grouping = "stacked"
    grafico.overlap = 100
    grafico.gapWidth = 40 if deitada else 50
    grafico.add_data(
        Reference(auxiliar, min_col=coluna + 1, max_col=coluna + 3,
                  min_row=1, max_row=1 + quantas),
        titles_from_data=True)
    grafico.set_categories(Reference(auxiliar, min_col=coluna, min_row=2,
                                     max_row=1 + quantas))
    _moldura(grafico)

    for serie, categoria in zip(grafico.series, col.CATEGORIAS_DO_GRAFICO):
        serie.graphicalProperties = GraphicalProperties(
            solidFill=COR_DA_CATEGORIA[categoria], ln=_sem_linha())
        serie.dLbls = _rotulos(showVal=True)
        serie.dLbls.numFmt = formato_do_rotulo
        serie.dLbls.position = "ctr"
        serie.dLbls.txPr = _texto(9, negrito=True,
                                  cor=LETRA_SOBRE_A_CATEGORIA[categoria])

    # Eixo de categoria: o nome da unidade ou do guardião, em negrito.
    categorias, valores = grafico.x_axis, grafico.y_axis
    categorias.delete = False
    categorias.txPr = _texto(9, negrito=True)
    categorias.majorTickMark = "none"
    categorias.spPr = GraphicalProperties(ln=_linha())
    if deitada:
        # O maior no alto, como se lê um ranking. Com o eixo invertido, a
        # escala de valor vai para cima do gráfico — onde ela está no print.
        categorias.scaling.orientation = "maxMin"

    # Eixo de valor: a escala, e as linhas de grade que saem dela.
    valores.delete = False
    valores.txPr = _texto(9)
    valores.scaling.min = 0
    valores.majorTickMark = "none"
    valores.spPr = GraphicalProperties(ln=_sem_linha())
    valores.majorGridlines = ChartLines(
        spPr=GraphicalProperties(ln=_linha()))
    if formato_do_eixo:
        valores.numFmt = NumFmt(formatCode=formato_do_eixo, sourceLinked=False)

    grafico.legend.position = "b"
    grafico.legend.txPr = _texto(9, negrito=True)
    return grafico


# -- o painel ---------------------------------------------------------------

def escrever_painel(livro, painel: Painel, *, semana: int, posicao: int = 0):
    """`Resumo Executivo` — a aba que vai na frente do arquivo."""
    aba = livro.create_sheet(col.ABA_DO_PAINEL, posicao)
    aba.sheet_view.showGridLines = False
    for letra, largura in col.LARGURAS.items():
        aba.column_dimensions[letra].width = largura
    aba.row_dimensions[col.LINHA_DO_TITULO].height = 20

    esquerda, direita = col.COLUNA_DA_ESQUERDA, col.COLUNA_DA_DIREITA
    _barra(aba, col.LINHA_DO_TITULO, esquerda, col.LARGURA_DA_ESQUERDA,
           col.TITULO.format(semana=semana), tamanho=TAMANHO + 2)
    _barra(aba, col.LINHA_DA_PIZZA, esquerda, col.LARGURA_DA_ESQUERDA,
           col.TITULO_DA_PIZZA, tamanho=TAMANHO - 2)

    _tabela_de_categorias(aba, painel, esquerda)
    _tops(aba, painel, direita)
    _ajustes(aba, painel)

    _barra(aba, col.LINHA_DOS_GRAFICOS_DE_BAIXO, esquerda,
           col.LARGURA_DA_ESQUERDA, col.TITULO_DAS_UNIDADES,
           tamanho=TAMANHO - 1)
    _barra(aba, col.LINHA_DOS_GRAFICOS_DE_BAIXO, direita,
           col.LARGURA_DA_DIREITA, col.TITULO_DOS_GUARDIOES,
           tamanho=TAMANHO - 1)
    return aba


def _tabela_de_categorias(aba, painel: Painel, coluna: int) -> None:
    linha = col.LINHA_DA_TABELA
    _cabecalho(aba, linha, coluna, col.TABELA_DE_CATEGORIAS)
    for i, dados in enumerate([*painel.categorias, painel.total], start=1):
        if dados is None:                                # pragma: no cover
            continue
        valores = (
            (dados.categoria, None),
            (dados.quantidade, None),
            (dados.valor, col.FORMATO_DE_VALOR),
            ("" if dados.media_dias is None else dados.media_dias,
             col.FORMATO_DE_MEDIA),
        )
        for j, (valor, formato) in enumerate(valores):
            _celula(aba, linha + i, coluna + j, valor, formato,
                    alinhar="center", grade=True)
        if dados.categoria == col.TOTAL:
            # A linha do total é escura de ponta a ponta, como o cabeçalho.
            for j in range(len(valores)):
                celula = aba.cell(linha + i, coluna + j)
                celula.fill = PatternFill("solid", fgColor=COR_ESCURA)
                celula.font = Font(name=FONTE, size=TAMANHO, bold=True,
                                   color=BRANCO)
        elif dados.categoria in COR_DA_CATEGORIA:
            # O nome da categoria na cor dela — é a legenda da pizza.
            celula = aba.cell(linha + i, coluna)
            celula.fill = PatternFill(
                "solid", fgColor=COR_DA_CATEGORIA[dados.categoria])
            celula.font = Font(name=FONTE, size=TAMANHO, bold=True,
                               color=BRANCO)


def _tops(aba, painel: Painel, coluna: int) -> None:
    referencia = painel.referencia.strftime("%d/%m")
    cabecalho = tuple(r.format(referencia=referencia) for r in col.TABELA_DO_TOP)
    for titulo, linha_do_titulo, notas in (
            (col.TITULO_DO_TOP_DIAS, col.LINHA_DO_TOP_DIAS, painel.top_dias),
            (col.TITULO_DO_TOP_VALOR, col.LINHA_DO_TOP_VALOR, painel.top_valor)):
        _barra(aba, linha_do_titulo, coluna, len(cabecalho), titulo)
        _cabecalho(aba, linha_do_titulo + 1, coluna, cabecalho)
        primeira = linha_do_titulo + 2
        for i, nota in enumerate(notas, start=primeira):
            _escrever_nota(aba, i, coluna, nota, painel)
        _juntar_guardiao_sem_gestor(aba, primeira, notas, coluna + 1)


#: Como cada coluna do TOP N se alinha: o texto curto no centro, o nome do
#: parceiro à esquerda, o valor à direita — como no print.
_ALINHAMENTO_DO_TOP = ("center", "center", "center", "left", "right",
                       "center", "center")


def _escrever_nota(aba, linha: int, coluna: int, nota: Pendencia,
                   painel: Painel) -> None:
    dias = nota.dias(painel.referencia)
    valores = (
        (nota.categoria, None),
        (nota.guardiao, None),
        (nota.gestor, None),
        (nota.parceiro, None),
        (nota.valor, col.FORMATO_DE_VALOR),
        (nota.emissao, col.FORMATO_DE_DATA),
        ("" if dias is None else dias, col.FORMATO_DE_DIAS),
    )
    for j, ((valor, formato), alinhar) in enumerate(
            zip(valores, _ALINHAMENTO_DO_TOP)):
        _celula(aba, linha, coluna + j, valor, formato, alinhar=alinhar,
                grade=True)


def _sem_gestor(nota: Pendencia) -> bool:
    """O gestor não diz nada além do guardião: vazio, ou o mesmo texto.

    É o caso de `Guardião não encontrado`, que o relatório repete nas duas
    colunas. No print, as duas células viram uma só.
    """
    return not nota.gestor or nota.gestor == nota.guardiao


def _juntar_guardiao_sem_gestor(aba, primeira: int, notas: Sequence[Pendencia],
                                coluna: int) -> None:
    """Mescla `Guardião` com `Gestor` quando o gestor só repete o guardião.

    Linhas seguidas com o mesmo guardião nessa situação viram um bloco só,
    como no print da semana 38 — o texto aparece uma vez, no meio.
    """
    i = 0
    while i < len(notas):
        if not _sem_gestor(notas[i]):
            i += 1
            continue
        fim = i
        while (fim + 1 < len(notas) and _sem_gestor(notas[fim + 1])
               and notas[fim + 1].guardiao == notas[i].guardiao):
            fim += 1
        aba.cell(primeira + i, coluna + 1).value = None
        aba.merge_cells(start_row=primeira + i, start_column=coluna,
                        end_row=primeira + fim, end_column=coluna + 1)
        i = fim + 1


def _ajustes(aba, painel: Painel) -> None:
    """O rótulo do canto: a data contra a qual o tempo foi contado."""
    coluna = col.COLUNA_DOS_AJUSTES
    _celula(aba, col.LINHA_DO_TITULO, coluna, col.ROTULO_DA_REFERENCIA)
    _celula(aba, col.LINHA_DO_TITULO, coluna + 1, painel.referencia,
            col.FORMATO_DE_DATA)


def desenhar(aba, auxiliar, painel: Painel) -> None:
    """Prende os três gráficos ao painel, apontados para a aba auxiliar.

    Bloco vazio não vira gráfico vazio: sem unidade com pendência, o gráfico
    de unidades simplesmente não existe, e a tela diz por quê.
    """
    esquerda, direita = col.COLUNA_DA_ESQUERDA, col.COLUNA_DA_DIREITA
    abaixo = col.LINHA_DOS_GRAFICOS_DE_BAIXO + 1

    if painel.categorias:
        pizza = _pizza(auxiliar, [c.categoria for c in painel.categorias])
        # Da linha de baixo do título até o cabeçalho da tabela, sem cobri-lo.
        _ancorar(pizza, esquerda, col.LINHA_DA_PIZZA + 1,
                 col.LARGURA_DA_ESQUERDA, col.LINHA_DA_TABELA)
        aba.add_chart(pizza)
    if painel.unidades_do_grafico:
        unidades = _barras(auxiliar, col.BLOCO_DO_GRAFICO_DE_UNIDADES,
                           len(painel.unidades_do_grafico), deitada=False,
                           formato_do_rotulo=FORMATO_DO_ROTULO_DE_VALOR,
                           formato_do_eixo=FORMATO_DO_EIXO_DE_VALOR)
        _ancorar(unidades, esquerda, abaixo, col.LARGURA_DA_ESQUERDA,
                 col.LINHA_DO_FIM_DOS_GRAFICOS)
        aba.add_chart(unidades)
    if painel.guardioes_do_grafico:
        guardioes = _barras(auxiliar, col.BLOCO_DO_GRAFICO_DE_GUARDIOES,
                            len(painel.guardioes_do_grafico), deitada=True,
                            formato_do_rotulo=FORMATO_DO_ROTULO_DE_QUANTIDADE)
        _ancorar(guardioes, direita, abaixo, col.LARGURA_DA_DIREITA,
                 col.LINHA_DO_FIM_DOS_GRAFICOS)
        aba.add_chart(guardioes)
