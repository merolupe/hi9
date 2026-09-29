"""O Registro de Apuração como página de impressão — para salvar em PDF.

O Sankhya emite o Registro de Apuração do ICMS em PDF, estabelecimento a
estabelecimento: uma folha com as entradas e saídas por CFOP e outra com o
resumo em quatorze linhas. Esta página reproduz as duas folhas, no mesmo
desenho, para conferir o papel da ferramenta com o do ERP lado a lado.

Não se gera PDF aqui. A biblioteca de PDF precisaria de extensão compilada, que
a máquina sem administrador não instala (regra 6 do repositório). Quem gera o
PDF é o próprio navegador: a página abre a janela de impressão, e o destino
"Salvar como PDF" existe no Edge e no Chrome sem instalar nada.

O conteúdo é o mesmo `Registro` da aba REGISTRO da planilha — a página só
desenha, não calcula.
"""
from __future__ import annotations

import calendar
import datetime as dt
from html import escape

from ..nucleo import registro as reg

#: Linhas do resumo que o documento manda discriminar abaixo.
DISCRIMINADAS = {2, 3, 6, 7, 12}

#: Os três quadros do resumo, e a palavra que corre na vertical ao lado.
QUADROS = (
    ("DÉBITO DO IMPOSTO", "DÉBITO", (1, 2, 3, 4)),
    ("CRÉDITO DO IMPOSTO", "CRÉDITO", (5, 6, 7, 8, 9, 10)),
    ("APURAÇÃO DO SALDO", "SALDO", (11, 12, 13, 14)),
)

#: O número que o livro põe antes de cada subtotal: o primeiro dígito do CFOP.
PREFIXO = {
    **{grupo: f"{digito}.00" for digito, grupo in reg.GRUPOS_ENTRADA.items()},
    **{grupo: f"{digito}.00" for digito, grupo in reg.GRUPOS_SAIDA.items()},
}


def montar(registros: list[reg.Registro], params, emissao: dt.datetime | None = None
           ) -> str:
    """A página inteira: duas folhas por estabelecimento, sem o totalizador.

    O totalizador fica de fora porque não é documento fiscal — o papel que se
    confere com o do ERP é o de cada estabelecimento.
    """
    emissao = emissao or dt.datetime.now()
    firma = str(params.filiais.get("razao_social") or "")
    documentos = [r for r in registros if not r.gerencial]

    opcoes = "".join(
        f'<option value="{i}">{escape(r.estabelecimento)}</option>'
        for i, r in enumerate(documentos)
    )
    folhas = "".join(
        f'<div class="documento" data-i="{i}">'
        f"{_folha_movimento(r, firma, emissao)}{_folha_resumo(r, firma, emissao)}"
        "</div>"
        for i, r in enumerate(documentos)
    )
    competencia = documentos[0].competencia if documentos else ""
    return PAGINA.format(
        titulo=escape(f"Registro de Apuração do ICMS — {competencia}"),
        opcoes=opcoes, folhas=folhas or "<p>Nenhum estabelecimento apurado.</p>",
    )


# --------------------------------------------------------------------------
# Folha 1 — entradas e saídas por CFOP
# --------------------------------------------------------------------------

def _folha_movimento(r: reg.Registro, firma: str, emissao: dt.datetime) -> str:
    return (
        '<section class="folha">'
        '<h1>Registro de Apuração do ICMS</h1>'
        f"{_cabecalho(r, firma, emissao, folha=1)}"
        f"{_bloco(r.entradas, 'ENTRADAS', 'crédito', 'Imposto Creditado')}"
        f"{_bloco(r.saidas, 'SAÍDAS', 'débito', 'Imposto Debitado')}"
        "</section>"
    )


def _bloco(bloco: reg.Bloco, titulo: str, natureza: str, coluna_imposto: str) -> str:
    linhas = []
    for linha in bloco.linhas:
        codigo = "" if linha.cfop is None else str(linha.cfop)
        descricao = "" if linha.cfop is None else linha.descricao
        linhas.append(
            f'<tr><td class="cfop">{codigo}</td><td>{escape(descricao)}</td>'
            f"{_valores(linha.valores)}</tr>"
        )

    subtotais = [
        f'<tr><td></td><td class="recuo">{PREFIXO[g]} {escape(g)}</td>'
        f"{_valores(bloco.subtotal(g))}</tr>"
        for g in bloco.grupos()
    ]
    return f"""
<table class="movimento">
  <colgroup><col class="c-cfop"><col><col class="c-valor"><col class="c-valor">
    <col class="c-valor"><col class="c-valor"><col class="c-valor"></colgroup>
  <thead>
    <tr class="faixa"><th colspan="2"></th><th colspan="5" class="lado">{titulo}</th></tr>
    <tr>
      <th colspan="2" class="esq" rowspan="3">Codificação<br>Contábil-Fiscal</th>
      <th rowspan="3">Valores<br>Contábeis</th>
      <th colspan="4" class="grupo">ICMS - Valores Fiscais</th>
    </tr>
    <tr>
      <th colspan="2" class="sub">Operações com {natureza} do Imposto</th>
      <th colspan="2" class="sub">Operações sem {natureza} do Imposto</th>
    </tr>
    <tr class="colunas">
      <th>Base Cálculo</th><th class="forte">{coluna_imposto}</th>
      <th>Isentas / N.Trib.</th><th>Outras</th>
    </tr>
  </thead>
  <tbody>
    {"".join(linhas)}
    <tr><td></td><td class="rotulo">Subtotais {"Entradas" if titulo == "ENTRADAS" else "Saídas"}</td><td colspan="5"></td></tr>
    {"".join(subtotais)}
    <tr class="totais"><td></td><td class="recuo">Totais</td>{_valores(bloco.total)}</tr>
  </tbody>
</table>"""


def _valores(v: reg.ValoresFiscais) -> str:
    return "".join(f'<td class="num">{_reais(x)}</td>' for x in v.as_tuple())


# --------------------------------------------------------------------------
# Folha 2 — o resumo da apuração
# --------------------------------------------------------------------------

def _folha_resumo(r: reg.Registro, firma: str, emissao: dt.datetime) -> str:
    quadros = []
    for titulo, vertical, codigos in QUADROS:
        linhas = []
        for codigo in codigos:
            linha = r.linha(codigo)
            rotulo = f"{codigo:03d} {linha.rotulo}"
            if codigo in DISCRIMINADAS:
                rotulo += " (Discriminar Abaixo)"
            marca = ' <span class="aguarda">*</span>' if linha.aguarda_ajuste else ""
            linhas.append(
                f'<tr class="linha"><td>{escape(rotulo)}{marca}</td>'
                f'<td class="num"></td><td class="num">{_reais(linha.valor)}</td></tr>'
            )
            for texto, valor in linha.discriminacao:
                if abs(valor) < 0.005:
                    continue
                linhas.append(
                    f'<tr class="discriminacao"><td>{escape(texto)}</td>'
                    f'<td class="num">{_reais(valor)}</td><td></td></tr>'
                )
        letras = "<br>".join(vertical)
        quadros.append(f"""
<tr class="quadro"><td class="vertical"></td><td class="titulo-quadro">{titulo}</td>
  <td class="num aux">{'Coluna Auxiliar' if codigos[0] == 1 else ''}</td>
  <td class="num aux">{'Somas' if codigos[0] == 1 else ''}</td></tr>
<tr><td class="vertical" rowspan="{len(linhas) + 1}">{letras}</td></tr>
{"".join(linhas)}""")

    pendentes = [f"{item.codigo:03d}" for item in r.resumo if item.aguarda_ajuste]
    observacao = (
        "* Linha que depende de ajuste ainda não conferido na aba AJUSTES "
        f"({', '.join(pendentes)}): o valor impresso não é o final."
        if pendentes else ""
    )
    return (
        '<section class="folha">'
        '<h1>Resumo da Apuração do Imposto (ICMS)</h1>'
        f"{_cabecalho(r, firma, emissao, folha=2, ajuste=True)}"
        '<table class="resumo">'
        '<colgroup><col class="c-vertical"><col><col class="c-valor">'
        '<col class="c-valor"></colgroup>'
        '<tr class="valores"><td></td><td></td>'
        '<td colspan="2" class="centro">Valores</td></tr>'
        f"{''.join(quadros)}"
        "</table>"
        '<div class="complementares">INFORMAÇÕES COMPLEMENTARES</div>'
        f'<div class="observacoes">Observações: {escape(observacao)}</div>'
        "</section>"
    )


# --------------------------------------------------------------------------
# Comum às duas folhas
# --------------------------------------------------------------------------

def _cabecalho(r: reg.Registro, firma: str, emissao: dt.datetime, *, folha: int,
               ajuste: bool = False) -> str:
    tipo_ajuste = (
        '<div><span class="rot">TIPO AJUSTE:</span> Ajuste de Apuração e '
        "Ajuste de Sub-Apuração</div>" if ajuste else ""
    )
    return f"""
<div class="cabecalho">
  <div class="col">
    <div><span class="rot">FIRMA:</span> {escape(firma or r.estabelecimento)}</div>
    <div><span class="rot">INSCRIÇÃO ESTADUAL:</span> {escape(r.inscricao_estadual or "(não cadastrada)")}</div>
    {tipo_ajuste}
    <div><span class="rot">FOLHA:</span> {folha}</div>
  </div>
  <div class="col">
    <div><span class="rot">CPF/CNPJ:</span> {escape(r.cnpj or "(não cadastrado)")}</div>
    <div><span class="rot">MÊS OU PERIODO/ANO:</span> {_periodo(r.competencia)}</div>
    <div><span class="rot">EMISSÃO:</span> {emissao.strftime("%d/%m/%Y %H:%M:%S")}</div>
  </div>
  <div class="estab">{escape(r.estabelecimento)} — {escape(r.uf)}</div>
</div>"""


def _periodo(competencia: str) -> str:
    """'2026-08' → '01/08/2026 à 31/08/2026'."""
    try:
        ano, mes = int(competencia[:4]), int(competencia[5:7])
    except (ValueError, IndexError):
        return escape(competencia)
    ultimo = calendar.monthrange(ano, mes)[1]
    return f"01/{mes:02d}/{ano} à {ultimo:02d}/{mes:02d}/{ano}"


def _reais(valor: float) -> str:
    """1234567.8 → '1.234.567,80', como o documento do ERP."""
    texto = f"{round(valor or 0.0, 2):,.2f}"
    return texto.replace(",", "_").replace(".", ",").replace("_", ".")


PAGINA = """<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{titulo}</title>
<style>
@page {{ size: A4 portrait; margin: 10mm 9mm; }}
* {{ box-sizing: border-box; }}
body {{ margin: 0; background: #e9e9e9; color: #000;
        font: 8.5pt Arial, Helvetica, sans-serif; }}
.barra {{ position: sticky; top: 0; z-index: 2; display: flex; gap: 12px;
          align-items: center; flex-wrap: wrap; padding: 10px 16px;
          background: #1f3864; color: #fff; font-size: 13px; }}
.barra select, .barra button {{ font: inherit; padding: 6px 10px; border-radius: 4px;
          border: 1px solid #c8d1e3; }}
.barra button {{ background: #fff; color: #1f3864; font-weight: bold; cursor: pointer; }}
.barra .dica {{ opacity: .85; font-size: 12px; }}
.folha {{ width: 210mm; min-height: 297mm; margin: 12px auto; padding: 10mm 9mm;
          background: #fff; box-shadow: 0 1px 4px rgba(0,0,0,.25);
          break-after: page; page-break-after: always; }}
h1 {{ margin: 0; padding-bottom: 3px; text-align: center; font-size: 11pt;
      border-bottom: 1.5px solid #000; }}
.cabecalho {{ display: grid; grid-template-columns: 1fr 1fr; padding: 4px 0 6px;
              border-bottom: 1.5px solid #000; margin-bottom: 4px; }}
.cabecalho .col {{ line-height: 1.45; }}
.cabecalho .col:first-child {{ padding-left: 10mm; }}
.cabecalho .col:last-child {{ padding-left: 22mm; }}
.cabecalho .rot {{ font-size: 7.5pt; }}
.cabecalho .estab {{ grid-column: 1 / -1; font-size: 7pt; color: #555; padding-left: 10mm; }}
table {{ width: 100%; border-collapse: collapse; }}
.movimento {{ margin-top: 4px; table-layout: fixed; }}
.movimento col.c-cfop {{ width: 9mm; }}
.movimento col.c-valor {{ width: 25mm; }}
.movimento thead th {{ font-weight: normal; font-size: 8pt; text-align: right;
                       padding: 1px 3px; vertical-align: bottom; }}
.movimento thead th.esq {{ text-align: left; vertical-align: top; padding-left: 5mm; }}
.movimento thead .faixa th {{ border-bottom: 1.5px solid #000; }}
.movimento thead .faixa th.lado {{ text-align: left; font-weight: bold; font-size: 10pt;
                                   padding-left: 0; border-bottom: none; }}
.movimento thead th.grupo {{ text-align: center; border-bottom: 1px solid #000; }}
.movimento thead th.sub {{ text-align: center; }}
.movimento thead .colunas th {{ border-top: 1px solid #000; border-bottom: 1.5px solid #000;
                               white-space: nowrap; }}
.movimento thead .colunas th.forte {{ font-weight: bold; }}
.movimento tbody td {{ padding: 1.6px 3px; white-space: nowrap; overflow: hidden;
                       text-overflow: ellipsis; }}
.movimento tbody tr:first-child td {{ padding-top: 6px; }}
.movimento td.cfop {{ text-align: right; padding-right: 4px; }}
.movimento td.rotulo {{ padding-top: 6px; }}
.movimento td.recuo {{ padding-left: 5mm; }}
.movimento tr.totais td {{ padding-top: 4px; }}
.num {{ text-align: right; font-variant-numeric: tabular-nums; }}
.resumo {{ margin-top: 4px; }}
.resumo col.c-vertical {{ width: 6mm; }}
.resumo col.c-valor {{ width: 32mm; }}
.resumo td {{ padding: 2px 3px; vertical-align: top; }}
.resumo tr.valores td {{ padding-top: 0; }}
.resumo .centro {{ text-align: center; }}
.resumo tr.quadro td {{ border-top: 1.5px solid #000; border-bottom: 1.5px solid #000;
                        padding: 3px; }}
.resumo td.titulo-quadro {{ padding-left: 20mm; }}
.resumo td.aux {{ font-size: 8pt; }}
.resumo td.vertical {{ text-align: center; line-height: 1.15; font-size: 8pt;
                       padding-top: 4px; }}
.resumo tr.linha td {{ padding-top: 5px; padding-bottom: 5px; }}
.resumo tr.discriminacao td {{ padding: 0 3px 3px 8mm; font-size: 7.5pt; }}
.resumo tr.discriminacao td.num {{ padding-left: 3px; }}
.aguarda {{ font-weight: bold; }}
.complementares {{ margin-top: 2px; padding: 3px 0; text-align: center;
                   border-top: 1.5px solid #000; border-bottom: 1.5px solid #000; }}
.observacoes {{ padding-top: 3px; }}
.oculto {{ display: none; }}
@media print {{
  body {{ background: #fff; }}
  .barra {{ display: none; }}
  .folha {{ width: auto; min-height: 0; margin: 0; padding: 0; box-shadow: none; }}
  .documento:last-child .folha:last-child {{ break-after: auto; page-break-after: auto; }}
}}
@media (max-width: 800px) {{
  .folha {{ width: auto; margin: 8px; overflow-x: auto; }}
}}
</style>
</head>
<body>
<div class="barra">
  <label>Estabelecimento
    <select id="estab"><option value="">Todos</option>{opcoes}</select></label>
  <button type="button" onclick="window.print()">Imprimir / Salvar como PDF</button>
  <span class="dica">Na janela de impressão, escolha o destino "Salvar como PDF".</span>
</div>
{folhas}
<script>
document.getElementById("estab").addEventListener("change", function (e) {{
  var escolhido = e.target.value;
  document.querySelectorAll(".documento").forEach(function (d) {{
    d.classList.toggle("oculto", escolhido !== "" && d.dataset.i !== escolhido);
  }});
}});
window.addEventListener("load", function () {{ setTimeout(window.print, 300); }});
</script>
</body>
</html>
"""
