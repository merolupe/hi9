# -*- coding: utf-8 -*-
"""Edicao cirurgica de slides do KPI semanal.

Mexe no XML do .pptx direto, trocando texto e geometria de formas
identificadas **pela posicao**, nao pelo id. O PowerPoint embaralha os ids a
cada ida e volta do arquivo, mas preserva as coordenadas — por isso a posicao
e a ancora confiavel.

Uso tipico:

    from pptx_cirurgia import Pacote

    with Pacote('deck.pptx') as p:
        slide = p.slide_com('Agendamentos de Faturamento')
        x = p.ler(slide)
        x = set_texto(x, 0.60, 0.99, 'AGENDAMENTOS · S42')
        p.grava(slide, x)
        p.salvar('novo.pptx')

Depende so da biblioteca padrao. Para a planilha embutida dos graficos usa o
openpyxl de vendor/, que e Python puro (regra 6 do repositorio).
"""
import decimal
import html
import os
import re
import shutil
import tempfile
import zipfile

EMU = 914400


def emu(v):
    """Polegadas -> EMU, a unidade do OOXML."""
    return int(round(v * EMU))


# ===================================================================== pacote
class Pacote:
    """Um .pptx aberto como arvore de arquivos em disco."""

    def __init__(self, caminho):
        self.tmp = tempfile.mkdtemp(prefix='kpi-')
        with zipfile.ZipFile(caminho) as z:
            self.nomes = z.namelist()
            z.extractall(self.tmp)

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.fechar()

    def ler(self, parte):
        with open(os.path.join(self.tmp, parte), encoding='utf-8') as f:
            return f.read()

    def grava(self, parte, texto):
        with open(os.path.join(self.tmp, parte), 'w', encoding='utf-8') as f:
            f.write(texto)

    def slides(self):
        return sorted(n for n in self.nomes
                      if re.match(r'ppt/slides/slide\d+\.xml$', n))

    def slide_com(self, trecho):
        """Acha o slide pelo texto do titulo — id e numero de slide mudam, titulo nao."""
        for n in self.slides():
            if trecho in self.ler(n):
                return n
        raise KeyError('nenhum slide contem %r' % trecho)

    def grafico_do(self, slide, ordem=0):
        """Nome do arquivo de grafico que o slide usa (chartN.xml).

        O PowerPoint renumera os graficos ao salvar, entao nunca assuma
        chart1 = faturamento. Resolve sempre pelos relacionamentos.
        """
        rels = self.ler(re.sub(r'slides/(slide\d+)\.xml',
                               r'slides/_rels/\1.xml.rels', slide))
        pares = dict(re.findall(
            r'Id="(rId\d+)"[^>]*Target="\.\./charts/(chart\d+\.xml)"', rels))
        usados = re.findall(r'<c:chart [^>]*r:id="(rId\d+)"', self.ler(slide))
        return pares[usados[ordem]]

    def so_estes_slides(self, partes):
        """Deixa so os slides indicados na apresentacao.

        Util quando o pedido e 'me entrega so o slide X'. Depois disto rode
        scripts/clean.py da skill de pptx para remover os orfaos.
        """
        pres = self.ler('ppt/presentation.xml')
        rels = self.ler('ppt/_rels/presentation.xml.rels')
        manter = set()
        for p in partes:
            nome = os.path.basename(p)
            manter.add(re.search(
                r'Id="(rId\d+)"[^>]*Target="slides/%s"' % nome, rels).group(1))
        for m in re.finditer(r'<p:sldId id="\d+" r:id="(rId\d+)"/>', pres):
            if m.group(1) not in manter:
                pres = pres.replace(m.group(), '')
        self.grava('ppt/presentation.xml', pres)

    def salvar(self, destino):
        parcial = destino + '.parcial'
        with zipfile.ZipFile(parcial, 'w', zipfile.ZIP_DEFLATED) as z:
            # [Content_Types].xml precisa ser a primeira entrada do pacote
            for nome in sorted(self.nomes, key=lambda n: n != '[Content_Types].xml'):
                z.write(os.path.join(self.tmp, nome), nome)
        os.replace(parcial, destino)
        return destino

    def fechar(self):
        shutil.rmtree(self.tmp, ignore_errors=True)


# ===================================================================== formas
RE_XFRM = r'<a:off x="(-?\d+)" y="(-?\d+)"/><a:ext cx="(\d+)" cy="(\d+)"/>'


def formas(xml):
    """Todas as formas e molduras de grafico do slide, na ordem do XML."""
    return list(re.finditer(r'<p:(sp|graphicFrame)>.*?</p:\1>', xml, re.S))


def caixa(sp):
    """(x, y, largura, altura) em polegadas, ou None se a forma nao tiver xfrm."""
    o = re.search(RE_XFRM, sp)
    return tuple(int(v) / EMU for v in o.groups()) if o else None


def achar(xml, x, y, tol=0.06):
    """Localiza a forma pela posicao. Erga a tolerancia se o slide foi mexido a mao."""
    for m in formas(xml):
        c = caixa(m.group())
        if c and abs(c[0] - x) <= tol and abs(c[1] - y) <= tol:
            return m
    raise KeyError('nenhuma forma em (%.2f, %.2f) com tolerancia %.2f' % (x, y, tol))


def _troca_runs(bloco, novo):
    """Poe o texto no primeiro run e esvazia os demais.

    Preserva a formatacao original (fonte, corpo, cor) justamente por nao
    recriar os runs: o PowerPoint costuma quebrar um texto em varios runs,
    e reescrever tudo perderia negrito e cor.
    """
    ts = list(re.finditer(r'<a:t>[^<]*</a:t>', bloco))
    if not ts:
        return bloco
    saida, pos = [], 0
    for n, t in enumerate(ts):
        saida.append(bloco[pos:t.start()])
        saida.append('<a:t>%s</a:t>' % html.escape(novo, quote=False)
                     if n == 0 else '<a:t></a:t>')
        pos = t.end()
    saida.append(bloco[pos:])
    return ''.join(saida)


def set_texto(xml, x, y, novo, par=0, tol=0.06):
    """Troca o texto de um paragrafo da forma que esta em (x, y).

    `par` escolhe o paragrafo: o titulo do slide tem o nome no 0 e a semana no 1.
    """
    m = achar(xml, x, y, tol)
    sp = m.group()
    p = list(re.finditer(r'<a:p>.*?</a:p>', sp, re.S))[par]
    sp = sp[:p.start()] + _troca_runs(p.group(), novo) + sp[p.end():]
    return xml[:m.start()] + sp + xml[m.end():]


def set_fundo(xml, x, y, cor, tol=0.06):
    """Troca o preenchimento da forma (so o do spPr, nao o do texto)."""
    m = achar(xml, x, y, tol)
    sp = m.group()
    i, j = sp.index('</a:prstGeom>'), sp.index('</p:spPr>')
    trecho = re.sub(r'(<a:solidFill><a:srgbClr val=")[0-9A-Fa-f]{6}("/></a:solidFill>)',
                    r'\g<1>%s\g<2>' % cor, sp[i:j])
    return xml[:m.start()] + sp[:i] + trecho + sp[j:] + xml[m.end():]


def set_cor_texto(xml, x, y, cor, tol=0.06):
    """Troca a cor de todo o texto da forma."""
    m = achar(xml, x, y, tol)
    sp = m.group()
    i = sp.index('<p:txBody>')
    trecho = re.sub(r'(<a:srgbClr val=")[0-9A-Fa-f]{6}("/>)',
                    r'\g<1>%s\g<2>' % cor, sp[i:])
    return xml[:m.start()] + sp[:i] + trecho + xml[m.end():]


def set_corpo(xml, x, y, tamanho, tol=0.06):
    """Troca o corpo da fonte (centesimos de ponto: 1050 = 10,5pt)."""
    m = achar(xml, x, y, tol)
    sp = m.group()
    i = sp.index('<p:txBody>')
    trecho = re.sub(r'(<a:rPr[^>]*?)sz="\d+"', r'\g<1>sz="%d"' % tamanho, sp[i:])
    return xml[:m.start()] + sp[:i] + trecho + xml[m.end():]


def _reposiciona(sp, x, y, w, h):
    o = re.search(RE_XFRM, sp)
    vals = [int(v) for v in o.groups()]
    for k, v in enumerate([x, y, w, h]):
        if v is not None:
            vals[k] = emu(v)
    return (sp[:o.start()]
            + '<a:off x="%d" y="%d"/><a:ext cx="%d" cy="%d"/>' % tuple(vals)
            + sp[o.end():])


def mover(xml, x, y, novo_x=None, novo_y=None, w=None, h=None, tol=0.06):
    """Reposiciona/redimensiona a forma que esta em (x, y). None mantem o valor."""
    m = achar(xml, x, y, tol)
    return xml[:m.start()] + _reposiciona(m.group(), novo_x, novo_y, w, h) + xml[m.end():]


def limpar(xml, x, y, tol=0.06):
    """Esvazia o texto da forma, deixando a caixa livre para preenchimento."""
    m = achar(xml, x, y, tol)
    sp = m.group()
    i = sp.index('<p:txBody>')
    j = sp.index('</p:txBody>') + len('</p:txBody>')
    corpo = ('<p:txBody><a:bodyPr wrap="square" lIns="128016" tIns="68580" '
             'rIns="109728" bIns="54864" rtlCol="0" anchor="t"/><a:lstStyle/>'
             '<a:p><a:endParaRPr lang="pt-BR" sz="950"/></a:p></p:txBody>')
    return xml[:m.start()] + sp[:i] + corpo + sp[j:] + xml[m.end():]


_PROX_ID = [900]


def clonar(xml, x, y, novo_x=None, novo_y=None, w=None, h=None, texto=None,
           origem=None, tol=0.06):
    """Duplica a forma de (x, y) numa nova posicao, com id novo.

    `origem` permite copiar de outro slide (passe o XML dele) — foi assim que
    a faixa de pontos de atencao nasceu num slide e foi para o outro.
    """
    sp = achar(origem if origem is not None else xml, x, y, tol).group()
    _PROX_ID[0] += 1
    sp = re.sub(r'<p:cNvPr id="\d+" name="[^"]*"',
                '<p:cNvPr id="%d" name="Shape %d"' % (_PROX_ID[0], _PROX_ID[0]),
                sp, count=1)
    sp = _reposiciona(sp, novo_x, novo_y, w, h)
    if texto is not None:
        sp = _troca_runs(sp, texto)
    return xml.replace('</p:spTree>', sp + '</p:spTree>')


# ==================================================================== grafico
def append_ponto(pac, arquivo, categoria, valores):
    """Acrescenta uma categoria e um ponto por serie, preservando a formatacao.

    Mexe so no cache do grafico — rotulos de dados, cores e legenda que o time
    ajustou a mao continuam onde estavam. `valores` segue a ordem das series
    no XML, que e a ordem da legenda.
    """
    x = pac.ler('ppt/charts/' + arquivo)
    sers = list(re.finditer(r'<c:ser>.*?</c:ser>', x, re.S))
    if len(sers) != len(valores):
        raise ValueError('%s tem %d series, recebi %d valores'
                         % (arquivo, len(sers), len(valores)))

    def amplia(bloco, valor):
        n = int(re.search(r'<c:ptCount val="(\d+)"/>', bloco).group(1))
        bloco = bloco.replace('<c:ptCount val="%d"/>' % n,
                              '<c:ptCount val="%d"/>' % (n + 1), 1)
        pt = '<c:pt idx="%d"><c:v>%s</c:v></c:pt>' % (n, valor)
        tag = '</c:strCache>' if '<c:strCache>' in bloco else '</c:numCache>'
        return bloco.replace(tag, pt + tag, 1), n

    for k in reversed(range(len(sers))):
        sp = sers[k].group()
        m = re.search(r'<c:cat>.*?</c:cat>', sp, re.S)
        novo, n = amplia(m.group(), categoria)
        sp = sp[:m.start()] + novo + sp[m.end():]
        m = re.search(r'<c:val>.*?</c:val>', sp, re.S)
        novo, _ = amplia(m.group(), valores[k])
        sp = sp[:m.start()] + novo + sp[m.end():]
        # a faixa da planilha de apoio acompanha o numero de linhas
        sp = re.sub(r'(\$[A-Z]\$2:\$[A-Z]\$)%d(?![0-9])' % (n + 1),
                    r'\g<1>%d' % (n + 2), sp)
        x = x[:sers[k].start()] + sp + x[sers[k].end():]
    pac.grava('ppt/charts/' + arquivo, x)


def teto_do_eixo(pac, arquivo, maior_valor, passo):
    """Sobe o maximo do eixo se o maior valor passar do topo.

    Vale conferir toda semana: um valor acima do maximo sai cortado e o rotulo
    some, sem nenhum aviso.
    """
    x = pac.ler('ppt/charts/' + arquivo)
    atual = re.search(r'<c:max val="([^"]+)"/>', x)
    if not atual:
        return None
    if maior_valor <= float(atual.group(1)):
        return float(atual.group(1))
    novo = passo * (int(maior_valor // passo) + 1)
    x = re.sub(r'<c:max val="[^"]+"/>', '<c:max val="%g"/>' % novo, x, count=1)
    pac.grava('ppt/charts/' + arquivo, x)
    return novo


def regrava_planilha(pac, arquivo, categorias, series):
    """Reescreve a planilha que o 'Editar dados' do PowerPoint abre.

    `series` e uma lista de (nome, lista de valores). Sem isso o grafico fica
    certo na tela mas a planilha de apoio mente, e quem abrir para conferir
    leva susto.
    """
    import sys
    raiz = os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.dirname(os.path.abspath(__file__)))))
    sys.path.insert(0, os.path.join(raiz, 'vendor'))
    try:
        from openpyxl import Workbook
    except ImportError:
        return None
    rels = pac.ler('ppt/charts/_rels/%s.rels' % arquivo)
    alvo = re.search(r'Target="\.\./embeddings/([^"]+)"', rels)
    if not alvo:
        return None
    wb = Workbook()
    ws = wb.active
    ws.title = 'Sheet1'
    ws.append([''] + [nome for nome, _ in series])
    for i, c in enumerate(categorias):
        ws.append([c] + [vals[i] for _, vals in series])
    wb.save(os.path.join(pac.tmp, 'ppt/embeddings/' + alvo.group(1)))
    return alvo.group(1)


def centros_das_categorias(pac, slide, grafico, n, ordem=0):
    """x (em polegadas) do centro de cada categoria do grafico.

    Serve para alinhar a linha TOTAL do slide de agendamentos com as colunas
    do grafico, que e o unico jeito de ela nao sair torta quando entra semana.
    """
    sx = pac.ler(slide)
    gf = list(re.finditer(r'<p:graphicFrame>.*?</p:graphicFrame>', sx, re.S))[ordem]
    o = re.search(RE_XFRM, gf.group())
    fx, _, fw, _ = (int(v) / EMU for v in o.groups())
    c = pac.ler('ppt/charts/' + grafico)
    lay = re.search(r'<c:manualLayout>.*?</c:manualLayout>', c, re.S)
    if lay:
        px = float(re.search(r'<c:x val="([^"]+)"/>', lay.group()).group(1))
        pw = float(re.search(r'<c:w val="([^"]+)"/>', lay.group()).group(1))
    else:
        px, pw = 0.13, 0.85
    x0, largura = fx + px * fw, pw * fw
    return [x0 + (i + 0.5) * largura / n for i in range(n)]


# ==================================================================== numeros
def ler_numero(txt):
    """'1.078.603,2' ou '1078603.2' -> float. Aceita os dois formatos."""
    if isinstance(txt, (int, float)):
        return float(txt)
    t = str(txt).strip().replace(' ', '')
    if ',' in t:
        t = t.replace('.', '').replace(',', '.')
    return float(t)


def br(v, casas=1):
    """1078603.2 -> '1.078.603,2' (ponto de milhar, virgula decimal).

    Arredondamento comercial: 56,25 vira 56,3 e nao 56,2. O `round` do Python
    desempata para o par e o time confere contra a planilha, onde o Excel
    desempata para cima — a diferenca de uma casa aparece na tabela e vira
    pergunta na reuniao.
    """
    q = decimal.Decimal(1).scaleb(-casas)
    d = decimal.Decimal(repr(float(v))).quantize(q, rounding=decimal.ROUND_HALF_UP)
    s = ('%.*f' % (casas, d)).replace('.', ',')
    inteiro, _, dec = s.partition(',')
    neg = inteiro.startswith('-')
    inteiro = inteiro.lstrip('-')
    grupos = []
    while len(inteiro) > 3:
        grupos.insert(0, inteiro[-3:])
        inteiro = inteiro[:-3]
    grupos.insert(0, inteiro)
    return ('-' if neg else '') + '.'.join(grupos) + (',' + dec if dec else '')


def pct(x, casas=2):
    """0.8569 -> '85,69%'"""
    return '%s%%' % br(x * 100, casas)
