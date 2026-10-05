#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Gera o slide 'Faturamento x Meta' do KPI semanal a partir dos quatro numeros da semana.

Uso tipico (uma linha por semana):

    python3 kpi/gerar_faturamento.py \\
        --base       competencias/kpi/modelo.pptx \\
        --historico  competencias/kpi/faturamento.json \\
        --semana 41 --orc-acum 1120431,0 --real-acum 942118,3 \\
        --orc-sem 41827,8 --real-sem 11262,7 \\
        --saida "competencias/kpi/REUNIAO_SEMANAL_-_S42_2026.pptx"

Tudo em R$ mil, no formato da planilha (ponto de milhar, virgula decimal).
O historico e atualizado no lugar; rodar duas vezes a mesma semana nao duplica.

Formato visual: ver kpi/PADRAO-FATURAMENTO.md.
Dado fiscal nao entra no git — modelo, historico e saida ficam em competencias/.
"""
import argparse
import html
import json
import os
import re
import shutil
import sys
import tempfile
import zipfile

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, 'vendor'))

EMU = 914400
def emu(v): return int(round(v * EMU))

# ----------------------------------------------------------------- paleta
NAVY, BORDER, BODY = '1F3864', 'BFCDE4', '333F50'
ROW_LBL, ROW_ALT, WHITE = 'DCE6F5', 'F5F8FD', 'FFFFFF'
MUTED = '7B8AA3'
VERM_BG, VERM_TX = 'B3121F', 'FFFFFF'       # realizado semanal abaixo da meta
AMAR_BG, AMAR_TX = 'FFD100', '1F1F1F'       # realizado semanal a partir de 95%
VERDE, VERMELHO = '018965', 'C00000'        # anotacoes dentro do grafico

LIMITE_AMARELO = 0.95                        # a partir daqui a celula fica amarela


# ================================================================= numeros
def ler(txt):
    """'1.078.603,2' ou '1078603.2' -> float."""
    if isinstance(txt, (int, float)):
        return float(txt)
    t = txt.strip().replace(' ', '')
    if ',' in t:
        t = t.replace('.', '').replace(',', '.')
    return float(t)


def br(v, casas=1):
    """1078603.2 -> '1.078.603,2'"""
    s = ('%.*f' % (casas, v)).replace('.', ',')
    inteiro, _, dec = s.partition(',')
    neg = inteiro.startswith('-')
    inteiro = inteiro.lstrip('-')
    grupos = []
    while len(inteiro) > 3:
        grupos.insert(0, inteiro[-3:])
        inteiro = inteiro[:-3]
    grupos.insert(0, inteiro)
    return ('-' if neg else '') + '.'.join(grupos) + (',' + dec if dec else '')


def dinheiro(mil):
    """Valor em R$ mil -> 'R$ 930,9 mi' ou 'R$ 1,08 Bi'."""
    if abs(mil) >= 1_000_000:
        return 'R$ %s Bi' % br(mil / 1_000_000, 2)
    return 'R$ %s mi' % br(mil / 1_000, 1)


def pct(x, casas=2):
    return '%s%%' % br(x * 100, casas)


# ================================================================= pacote
class Pacote:
    """Um .pptx aberto como arvore de arquivos em disco."""

    def __init__(self, caminho):
        self.tmp = tempfile.mkdtemp(prefix='kpi-')
        with zipfile.ZipFile(caminho) as z:
            self.nomes = z.namelist()
            z.extractall(self.tmp)

    def ler(self, parte):
        with open(os.path.join(self.tmp, parte), encoding='utf-8') as f:
            return f.read()

    def grava(self, parte, texto):
        with open(os.path.join(self.tmp, parte), 'w', encoding='utf-8') as f:
            f.write(texto)

    def salvar(self, destino):
        tmp_zip = destino + '.parcial'
        with zipfile.ZipFile(tmp_zip, 'w', zipfile.ZIP_DEFLATED) as z:
            # [Content_Types].xml precisa ser a primeira entrada do pacote
            ordem = sorted(self.nomes, key=lambda n: n != '[Content_Types].xml')
            for nome in ordem:
                z.write(os.path.join(self.tmp, nome), nome)
        os.replace(tmp_zip, destino)

    def fechar(self):
        shutil.rmtree(self.tmp, ignore_errors=True)


# ================================================================= formas
def formas(xml):
    return list(re.finditer(r'<p:sp>.*?</p:sp>', xml, re.S))


def caixa(sp):
    o = re.search(r'<a:off x="(-?\d+)" y="(-?\d+)"/><a:ext cx="(\d+)" cy="(\d+)"/>', sp)
    return tuple(int(v) / EMU for v in o.groups()) if o else None


def achar(xml, x, y, tol=0.06):
    """Localiza a forma pela posicao — sobrevive a idas e vindas no PowerPoint."""
    for m in formas(xml):
        c = caixa(m.group())
        if c and abs(c[0] - x) <= tol and abs(c[1] - y) <= tol:
            return m
    raise KeyError('forma em (%.2f, %.2f) nao encontrada' % (x, y))


def troca_runs(bloco, novo):
    """Poe o texto no primeiro run e esvazia os demais, preservando a formatacao."""
    ts = list(re.finditer(r'<a:t>[^<]*</a:t>', bloco))
    if not ts:
        return bloco
    saida, pos = [], 0
    for n, t in enumerate(ts):
        saida.append(bloco[pos:t.start()])
        saida.append('<a:t>%s</a:t>' % html.escape(novo, quote=False) if n == 0 else '<a:t></a:t>')
        pos = t.end()
    saida.append(bloco[pos:])
    return ''.join(saida)


def set_texto(xml, x, y, novo, par=0):
    m = achar(xml, x, y)
    sp = m.group()
    paras = list(re.finditer(r'<a:p>.*?</a:p>', sp, re.S))
    p = paras[par]
    sp = sp[:p.start()] + troca_runs(p.group(), novo) + sp[p.end():]
    return xml[:m.start()] + sp + xml[m.end():]


def set_geometria(xml, m, x, y, w, h):
    sp = m.group()
    o = re.search(r'<a:off x="(-?\d+)" y="(-?\d+)"/><a:ext cx="(\d+)" cy="(\d+)"/>', sp)
    novo = '<a:off x="%d" y="%d"/><a:ext cx="%d" cy="%d"/>' % (emu(x), emu(y), emu(w), emu(h))
    sp = sp[:o.start()] + novo + sp[o.end():]
    return xml[:m.start()] + sp + xml[m.end():]


ESTILO = ('<p:style><a:lnRef idx="1"><a:schemeClr val="accent1"/></a:lnRef>'
          '<a:fillRef idx="3"><a:schemeClr val="accent1"/></a:fillRef>'
          '<a:effectRef idx="2"><a:schemeClr val="accent1"/></a:effectRef>'
          '<a:fontRef idx="minor"><a:schemeClr val="lt1"/></a:fontRef></p:style>')


def celula(ident, x, y, w, h, fundo, texto, cor, negrito, tam):
    return ('<p:sp><p:nvSpPr><p:cNvPr id="%d" name="Rectangle %d"/><p:cNvSpPr/><p:nvPr/>'
            '</p:nvSpPr><p:spPr><a:xfrm><a:off x="%d" y="%d"/><a:ext cx="%d" cy="%d"/></a:xfrm>'
            '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom>'
            '<a:solidFill><a:srgbClr val="%s"/></a:solidFill>'
            '<a:ln w="6350"><a:solidFill><a:srgbClr val="%s"/></a:solidFill></a:ln>'
            '<a:effectLst/></p:spPr>%s'
            '<p:txBody><a:bodyPr wrap="square" lIns="4572" tIns="0" rIns="4572" bIns="0" '
            'rtlCol="0" anchor="ctr"/><a:lstStyle/><a:p><a:pPr algn="ctr"/><a:r>'
            '<a:rPr lang="pt-BR" sz="%d" b="%d" dirty="0">'
            '<a:solidFill><a:srgbClr val="%s"/></a:solidFill><a:latin typeface="Lato"/>'
            '</a:rPr><a:t>%s</a:t></a:r></a:p></p:txBody></p:sp>') % (
        ident, ident, emu(x), emu(y), emu(w), emu(h), fundo,
        NAVY if fundo == NAVY else BORDER, ESTILO, tam, 1 if negrito else 0, cor,
        html.escape(texto, quote=False))


# ================================================================= historico
def carregar(caminho):
    with open(caminho, encoding='utf-8') as f:
        d = json.load(f)
    d.setdefault('colunas', [])
    for chave in ('orcado_acumulado', 'realizado_acumulado'):
        d.setdefault(chave, [])
    for chave in ('orcado_semanal', 'realizado_semanal'):
        d[chave] = {str(k): v for k, v in d.get(chave, {}).items()}
    return d


def aplicar_semana(d, rotulo, orc_acum, real_acum, orc_sem, real_sem):
    """Acrescenta (ou corrige) a coluna da semana."""
    if rotulo in d['colunas']:
        i = d['colunas'].index(rotulo)
    else:
        i = len(d['colunas'])
        d['colunas'].append(rotulo)
        d['orcado_acumulado'].append(0.0)
        d['realizado_acumulado'].append(0.0)
    d['orcado_acumulado'][i] = orc_acum
    d['realizado_acumulado'][i] = real_acum
    if orc_sem is not None:
        d['orcado_semanal'][str(i)] = orc_sem
    if real_sem is not None:
        d['realizado_semanal'][str(i)] = real_sem
    d['semana_atual'] = rotulo
    return i


# ================================================================= slide
def slide_do_faturamento(pac):
    for nome in sorted(n for n in pac.nomes if re.match(r'ppt/slides/slide\d+\.xml$', n)):
        if 'Faturamento x Meta' in pac.ler(nome):
            return nome
    raise SystemExit('slide "Faturamento x Meta" nao encontrado no modelo')


def monta_tabela(d, atual):
    """Devolve o XML das celulas da tabela, dimensionado para o numero de colunas."""
    X0, LBL, X1, H, TOPO = 0.50, 1.40, 12.83, 0.24, 5.42
    n = len(d['colunas'])
    CW = (X1 - (X0 + LBL)) / n

    # a fonte dos valores encolhe junto com a coluna; 7,2pt coube em 0,64"
    tam_valor = max(600, min(720, int(720 * CW / 0.643)))
    tam_rotulo, tam_cab = 820, 900

    def col(i): return X0 + LBL + i * CW

    ident = [600]
    def novo():
        ident[0] += 1
        return ident[0]

    t = [celula(novo(), X0, TOPO, LBL, H, NAVY, 'Semanas', WHITE, True, tam_cab)]
    for i, s in enumerate(d['colunas']):
        t.append(celula(novo(), col(i), TOPO, CW, H, NAVY, s, WHITE, True, tam_cab))

    for linha, (rot, vals, fundo) in enumerate([
            ('Orçado Acumulado', d['orcado_acumulado'], WHITE),
            ('Realizado Acumulado', d['realizado_acumulado'], ROW_ALT)]):
        y = TOPO + (linha + 1) * H
        t.append(celula(novo(), X0, y, LBL, H, ROW_LBL, rot, NAVY, True, tam_rotulo))
        for i, v in enumerate(vals):
            t.append(celula(novo(), col(i), y, CW, H, fundo, br(v), BODY, False, tam_valor))

    # as duas linhas semanais comecam depois do 1ºQ/2ºQ: o rotulo cobre essas colunas
    vazias = sum(1 for i in range(n) if str(i) not in d['orcado_semanal']
                 and d['colunas'][i] in ('1ºQ', '2ºQ'))
    for linha, chave in enumerate(('orcado_semanal', 'realizado_semanal')):
        y = TOPO + (linha + 3) * H
        rot = 'Orçado Semanal' if chave == 'orcado_semanal' else 'Realizado Semanal'
        t.append(celula(novo(), X0, y, LBL + vazias * CW, H, ROW_LBL, rot, NAVY, True, tam_rotulo))
        for i in range(vazias, n):
            v = d[chave].get(str(i))
            if v is None:                      # fechamento de trimestre: nao se aplica
                t.append(celula(novo(), col(i), y, CW, H, ROW_LBL, '–', MUTED, False, tam_valor))
            elif chave == 'orcado_semanal':
                t.append(celula(novo(), col(i), y, CW, H, WHITE, br(v), BODY, False, tam_valor))
            else:
                orc = d['orcado_semanal'].get(str(i))
                bom = orc and v / orc >= LIMITE_AMARELO
                fundo, cor = (AMAR_BG, AMAR_TX) if bom else (VERM_BG, VERM_TX)
                t.append(celula(novo(), col(i), y, CW, H, fundo, br(v), cor, True, tam_valor))
    return ''.join(t)


def atualiza_grafico(pac, slide, d):
    """Recarrega o cache do grafico e a planilha de apoio."""
    rels = pac.ler(re.sub(r'slides/(slide\d+)\.xml', r'slides/_rels/\1.xml.rels', slide))
    alvo = re.search(r'Target="\.\./charts/(chart\d+\.xml)"', rels).group(1)
    c = pac.ler('ppt/charts/' + alvo)

    n = len(d['colunas'])
    def pontos(vals, fmt=lambda v: v):
        return ''.join('<c:pt idx="%d"><c:v>%s</c:v></c:pt>' % (i, fmt(v))
                       for i, v in enumerate(vals))

    def troca(bloco, conteudo):
        bloco = re.sub(r'<c:ptCount val="\d+"/>', '<c:ptCount val="%d"/>' % n, bloco, count=1)
        bloco = re.sub(r'<c:pt idx="\d+"><c:v>[^<]*</c:v></c:pt>', '', bloco)
        tag = '</c:strCache>' if '<c:strCache>' in bloco else '</c:numCache>'
        return bloco.replace(tag, conteudo + tag, 1)

    series = [d['realizado_acumulado'], d['orcado_acumulado']]
    sers = list(re.finditer(r'<c:ser>.*?</c:ser>', c, re.S))
    for k in reversed(range(len(sers))):
        sp = sers[k].group()
        m = re.search(r'<c:cat>.*?</c:cat>', sp, re.S)
        sp = sp[:m.start()] + troca(m.group(), pontos(d['colunas'])) + sp[m.end():]
        m = re.search(r'<c:val>.*?</c:val>', sp, re.S)
        sp = sp[:m.start()] + troca(m.group(), pontos(series[k], lambda v: repr(v))) + sp[m.end():]
        sp = re.sub(r'(\$[A-Z]\$2:\$[A-Z]\$)\d+', r'\g<1>%d' % (n + 1), sp)
        c = c[:sers[k].start()] + sp + c[sers[k].end():]

    # o eixo acompanha a meta, em degraus de 200.000
    teto = max(d['orcado_acumulado'] + d['realizado_acumulado'])
    maximo = 200000 * (int(teto // 200000) + 1)
    c = re.sub(r'<c:max val="[^"]+"/>', '<c:max val="%d"/>' % maximo, c, count=1)
    pac.grava('ppt/charts/' + alvo, c)

    # planilha de apoio (o "Editar dados" do PowerPoint abre ela)
    try:
        from openpyxl import Workbook
    except ImportError:
        return alvo, maximo
    crels = pac.ler('ppt/charts/_rels/%s.rels' % alvo)
    emb = re.search(r'Target="\.\./embeddings/([^"]+)"', crels)
    if emb:
        wb = Workbook()
        ws = wb.active
        ws.title = 'Sheet1'
        ws.append(['', 'Faturamento realizado', 'Meta acumulada'])
        for i, rot in enumerate(d['colunas']):
            ws.append([rot, d['realizado_acumulado'][i], d['orcado_acumulado'][i]])
        wb.save(os.path.join(pac.tmp, 'ppt/embeddings/' + emb.group(1)))
    return alvo, maximo


def posicao_destaque(pac, slide, grafico, maximo, d):
    """Retangulo tracejado sobre a ultima categoria, na escala atual do eixo."""
    sx = pac.ler(slide)
    gf = re.search(r'<p:graphicFrame>.*?</p:graphicFrame>', sx, re.S).group()
    o = re.search(r'<a:off x="(-?\d+)" y="(-?\d+)"/><a:ext cx="(\d+)" cy="(\d+)"/>', gf)
    fx, fy, fw, fh = (int(v) / EMU for v in o.groups())

    c = pac.ler('ppt/charts/' + grafico)
    lay = re.search(r'<c:manualLayout>.*?</c:manualLayout>', c, re.S).group()
    def val(tag):
        return float(re.search(r'<c:%s val="([^"]+)"/>' % tag, lay).group(1))
    px, py, pw, ph = val('x'), val('y'), val('w'), val('h')

    n = len(d['colunas'])
    centro = fx + px * fw + (n - 0.5) * (pw * fw) / n
    base, altura = fy + (py + ph) * fh, ph * fh
    def alt(v): return base - (v / maximo) * altura
    topo = alt(max(d['orcado_acumulado'][-1], d['realizado_acumulado'][-1]))
    fundo = alt(min(d['orcado_acumulado'][-1], d['realizado_acumulado'][-1]))
    return centro - 0.32, topo - 0.09, 0.64, (fundo - topo) + 0.18


def gerar(base, historico, saida, semana, orc_acum, real_acum, orc_sem, real_sem,
          meta_3q=None, meta_anual=None, capa=None):
    d = carregar(historico)
    idx = aplicar_semana(d, semana, orc_acum, real_acum, orc_sem, real_sem)
    if meta_3q:
        d['meta_3q'] = meta_3q
    if meta_anual:
        d['meta_anual'] = meta_anual

    pac = Pacote(base)
    try:
        slide = slide_do_faturamento(pac)
        x = pac.ler(slide)

        # ---- tabela
        antigas = [m for m in formas(x)
                   if caixa(m.group()) and 5.35 <= caixa(m.group())[1] <= 6.70
                   and 'name="Rectangle' in m.group()]
        for m in reversed(antigas):
            x = x[:m.start()] + x[m.end():]
        x = x.replace('</p:spTree>', monta_tabela(d, idx) + '</p:spTree>')

        # ---- cartoes
        oa, ra = d['orcado_acumulado'][idx], d['realizado_acumulado'][idx]
        os_, rs = d['orcado_semanal'][str(idx)], d['realizado_semanal'][str(idx)]
        at_ac, at_se = ra / oa, rs / os_
        df_ac, df_se = oa - ra, os_ - rs

        # o atingimento do trimestre congela na coluna de fechamento, se ela existir
        ref_q = ra
        for i, rot in enumerate(d['colunas']):
            if rot.endswith('ºQ') and i >= 2:
                ref_q = d['realizado_acumulado'][i]

        x = set_texto(x, 8.90, 1.33, '%s de %s' % (dinheiro(ra), dinheiro(oa)))
        x = set_texto(x, 11.08, 1.08, pct(at_ac))
        x = set_texto(x, 8.97, 2.00, '%s abaixo da meta' % dinheiro(df_ac))
        x = set_texto(x, 11.18, 1.73, '▼ %s' % pct(1 - at_ac))
        x = set_texto(x, 8.90, 3.60, 'DÉFICIT SEMANAL · S%s' % semana)
        x = set_texto(x, 8.91, 3.20, '%s de %s' % (dinheiro(rs), dinheiro(os_)))
        x = set_texto(x, 11.26, 3.61, '▼ %s' % pct(1 - at_se))
        x = set_texto(x, 11.08, 2.90, pct(at_se))
        x = set_texto(x, 8.91, 3.85, '%s abaixo da meta' % dinheiro(df_se))
        if d.get('meta_3q'):
            x = set_texto(x, 10.09, 4.46, '%s atingido' % pct(ref_q / d['meta_3q'], 1))
        if d.get('meta_anual'):
            x = set_texto(x, 10.13, 5.02, '%s atingido' % pct(ra / d['meta_anual'], 1))

        # ---- anotacoes dentro do grafico
        # as duas caixas sao alinhadas a direita e terminam em 8,50", antes dos cartoes
        m = achar(x, 6.36, 2.41)
        x = set_geometria(x, m, 5.60, 2.41, 2.90, 0.60)
        x = set_texto(x, 5.60, 2.41, 'Orçado Sem.: %s' % br(os_), par=0)
        x = set_texto(x, 5.60, 2.41, 'Realizado Sem.: %s' % br(rs), par=1)
        m = achar(x, 7.14, 2.90)
        x = set_geometria(x, m, 4.40, 3.08, 4.10, 0.30)
        x = set_texto(x, 4.40, 3.08,
                      'Diferença S%s  ·  ▼ %s  (%s)' % (semana, dinheiro(df_se), pct(1 - at_se)))

        pac.grava(slide, x)

        # ---- grafico e destaque tracejado
        grafico, maximo = atualiza_grafico(pac, slide, d)
        bx, by, bw, bh = posicao_destaque(pac, slide, grafico, maximo, d)
        x = pac.ler(slide)
        for m in formas(x):
            if '<a:prstDash val="dash"/>' in m.group():
                x = set_geometria(x, m, bx, by, bw, bh)
                break
        pac.grava(slide, x)

        # ---- capa
        if capa:
            for nome in sorted(n for n in pac.nomes if re.match(r'ppt/slides/slide\d+\.xml$', n)):
                s = pac.ler(nome)
                novo = re.sub(r'KPI SEMANAL – S\d+', 'KPI SEMANAL – S%s' % capa, s)
                if novo != s:
                    pac.grava(nome, novo)
                    break

        pac.salvar(saida)
    finally:
        pac.fechar()

    with open(historico, 'w', encoding='utf-8') as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    return saida


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--base', required=True, help='pptx modelo (o deck da semana anterior)')
    p.add_argument('--historico', required=True, help='json com a serie acumulada')
    p.add_argument('--saida', required=True)
    p.add_argument('--semana', required=True, help='rotulo da coluna: 41, 3ºQ, ...')
    p.add_argument('--orc-acum', required=True)
    p.add_argument('--real-acum', required=True)
    p.add_argument('--orc-sem', default=None, help='vazio em coluna de fechamento')
    p.add_argument('--real-sem', default=None)
    p.add_argument('--meta-3q', default=None)
    p.add_argument('--meta-anual', default=None)
    p.add_argument('--capa', default=None, help='numero da semana da reuniao, ex.: 42')
    a = p.parse_args()

    destino = gerar(
        a.base, a.historico, a.saida, a.semana,
        ler(a.orc_acum), ler(a.real_acum),
        ler(a.orc_sem) if a.orc_sem else None,
        ler(a.real_sem) if a.real_sem else None,
        ler(a.meta_3q) if a.meta_3q else None,
        ler(a.meta_anual) if a.meta_anual else None,
        a.capa)
    print('gerado: %s' % destino)


if __name__ == '__main__':
    main()
