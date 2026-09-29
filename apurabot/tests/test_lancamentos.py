"""AJUSTES A LANÇAR e REGISTRO 1200 — o que se digita no Sankhya e na EFD.

A maior parte dos testes roda sobre um Livro Fiscal sintético de Rio Brilhante,
sem dado real: uma venda que gera débito e benefício, e a NF-e de recebimento
do crédito transferido (CFOP 1601). O último confere julho/2026 contra o
Registro do ERP e é pulado quando o arquivo real não está na máquina.
"""
from __future__ import annotations

from types import SimpleNamespace

import openpyxl
import pytest

from apurabot import ajustes as aj
from apurabot import controle_de_creditos as cc
from apurabot import lancamentos as lanc
from apurabot.apuracao import apurar, ler_ajustes
from apurabot.base_tratada import tratar
from apurabot.saida import ORDEM_DAS_ABAS, escrever
from sintetico import CHAVE, RB, RECEBIDO
from sintetico import livro as _livro

CENTAVO = 0.005
ABERTURA_DE_AGOSTO = 86_091.65          # parametros/saldos.yaml
UTILIZADO = 108_858.68                  # Ajuste de Apuração do Sankhya, 08/2026


def _linhas(aba) -> list[list]:
    return [[c for c in linha if c is not None]
            for linha in aba.iter_rows(values_only=True)
            if any(c is not None for c in linha)]


@pytest.fixture(scope="module")
def agosto(parametros, tmp_path_factory):
    base = tratar(_livro(tmp_path_factory.mktemp("livro") / "livro.xlsx"),
                  parametros=parametros)
    return base, apurar(base, parametros)


def _devolver(base, apuracao, pasta, valor=UTILIZADO, codigo="87"):
    """A planilha devolvida com o uso do crédito declarado na aba AJUSTES."""
    destino = escrever(base, pasta / "saida.xlsx", apuracao)
    wb = openpyxl.load_workbook(destino)
    aba = wb[aj.ABA]
    titulo = next(celulas[0].row for celulas in aba.iter_rows(max_col=1)
                  if str(celulas[0].value or "").upper() == aj.TITULO_PARCELAS)
    for coluna, v in enumerate(
        [RB, "Produção", "006", valor, "crédito do art. 68 do RICMS/MS",
         "Fulano", "Ciclano", codigo], start=1,
    ):
        aba.cell(row=titulo + 2, column=coluna, value=v)
    devolvido = pasta / "devolvido.xlsx"
    wb.save(devolvido)
    return devolvido


@pytest.fixture(scope="module")
def reapurado(agosto, parametros, tmp_path_factory):
    base, apuracao = agosto
    devolvido = _devolver(base, apuracao, tmp_path_factory.mktemp("volta"))
    base = tratar(devolvido, parametros=parametros)
    return base, apurar(base, parametros, ajustes=ler_ajustes(devolvido))


# -- AJUSTES A LANÇAR -------------------------------------------------------

def test_as_duas_abas_vem_logo_depois_do_registro(agosto, tmp_path):
    base, apuracao = agosto
    planilha = openpyxl.load_workbook(escrever(base, tmp_path / "x.xlsx", apuracao))
    nomes = planilha.sheetnames
    assert nomes.index("AJUSTES A LANÇAR") == nomes.index("REGISTRO") + 1
    assert nomes.index("REGISTRO 1200") == nomes.index("AJUSTES A LANÇAR") + 1
    assert [n for n in ORDEM_DAS_ABAS if n in nomes] == nomes


def test_o_calculado_entra_sem_ninguem_declarar(agosto, parametros):
    """O benefício é conta da apuração: vira lançamento com o código 37."""
    base, apuracao = agosto
    roteiro = lanc.montar(apuracao, parametros)
    beneficio = [x for x in roteiro.lancamentos if x.parcela == "beneficio"]
    assert len(beneficio) == 1
    assert beneficio[0].tipo == "Deduções do imposto apurado"
    assert beneficio[0].observacao_padrao == "37"
    assert "1190/2018" in beneficio[0].texto
    assert beneficio[0].valor == pytest.approx(
        apuracao.filiais[RB].credito_presumido, abs=CENTAVO)


def test_o_declarado_entra_com_o_codigo_que_veio_na_aba(reapurado, parametros):
    _, apuracao = reapurado
    roteiro = lanc.montar(apuracao, parametros)
    declarado = [x for x in roteiro.lancamentos if x.parcela == "declarado"]
    assert len(declarado) == 1
    x = declarado[0]
    assert (x.linha, x.tipo, x.observacao_padrao) == (6, "Outros créditos", "87")
    assert x.valor == pytest.approx(UTILIZADO, abs=CENTAVO)
    assert "ART. 68" in x.texto
    assert x.complemento == "crédito do art. 68 do RICMS/MS"


def test_os_lancamentos_fecham_com_o_registro(reapurado, parametros):
    _, apuracao = reapurado
    roteiro = lanc.montar(apuracao, parametros)
    assert roteiro.conferencia
    assert roteiro.divergencias == []


def test_o_codigo_da_linha_volta_na_planilha(reapurado, tmp_path):
    """Quem reenvia a planilha não perde o código que digitou."""
    base, apuracao = reapurado
    planilha = openpyxl.load_workbook(escrever(base, tmp_path / "y.xlsx", apuracao))
    parcelas = [linha for linha in planilha[aj.ABA].iter_rows(values_only=True)
                if linha[0] == RB and linha[2] == "006"]
    assert len(parcelas) == 1
    assert str(parcelas[0][7]) == "87"


@pytest.mark.parametrize(
    "parcela, regime, uf, beneficio, esperado",
    [
        ("estorno", "sp_equilibrio_fiscal", "SP", "", "83"),
        ("estorno", "ms_beneficio_rio_brilhante", "MS", "ms_rio_brilhante", "62"),
        ("estorno", "ms_estorno_proporcional", "MS", "", "61"),
        ("estorno", "mt_diferimento", "MT", "", "29"),
        ("credito_indevido", "ms_estorno_proporcional", "MS", "", "34"),
        ("difal", "sp_equilibrio_fiscal", "SP", "", "33"),
        ("centralizacao_recebe_debito", "sp_equilibrio_fiscal", "SP", "", "82"),
        ("centralizacao_transfere_debito", "ms_estorno_proporcional", "MS", "", "79"),
        ("beneficio", "ms_beneficio_rio_brilhante", "MS", "ms_rio_brilhante", "37"),
        # Sem regra cadastrada: sai sem código, não com um parecido.
        ("estorno", "pr_diferimento", "PR", "", ""),
        ("difal", "ms_estorno_proporcional", "MS", "", ""),
        ("credito_indevido", "sp_equilibrio_fiscal", "SP", "", ""),
    ],
)
def test_o_codigo_de_cada_parcela_vem_do_parametro(
    parametros, parcela, regime, uf, beneficio, esperado
):
    """Os códigos do relatório de Ajuste de Apuração do Sankhya de 08/2026."""
    filial = SimpleNamespace(regime=regime, uf=uf)
    assert lanc._codigo_da_parcela(
        parametros, parcela, filial, beneficio, "2026-08") == esperado


def test_o_codigo_tem_vigencia(parametros):
    """Os códigos foram vistos a partir de 08/2026: julho não os herda."""
    filial = SimpleNamespace(regime="sp_equilibrio_fiscal", uf="SP")
    assert lanc._codigo_da_parcela(parametros, "estorno", filial, "", "2026-07") == ""


# -- REGISTRO 1200 ----------------------------------------------------------

def test_o_recebido_vem_da_nota_do_livro(agosto, parametros):
    _, apuracao = agosto
    (controle,) = cc.montar(apuracao, parametros)
    assert (controle.estabelecimento, controle.cod_aj_apur) == (RB, "MS090004")
    assert controle.recebido == pytest.approx(RECEBIDO)
    assert [n.chave for n in controle.notas] == [CHAVE]
    assert controle.saldo_inicial == pytest.approx(ABERTURA_DE_AGOSTO)


def test_sem_uso_declarado_o_estoque_so_cresce(agosto, parametros):
    """Quanto usar é decisão do fiscal: sem declaração, nada é utilizado."""
    _, apuracao = agosto
    (controle,) = cc.montar(apuracao, parametros)
    assert controle.utilizado == 0
    assert controle.saldo_final == pytest.approx(ABERTURA_DE_AGOSTO + RECEBIDO)
    assert controle.linha_1210() is None


def test_agosto_fecha_como_o_resumo_do_sped(reapurado, parametros):
    """86.091,65 + 62.720,00 − 108.858,68 = 39.952,97."""
    _, apuracao = reapurado
    (controle,) = cc.montar(apuracao, parametros)
    assert controle.utilizado == pytest.approx(UTILIZADO)
    assert controle.saldo_final == pytest.approx(39_952.97, abs=CENTAVO)
    assert controle.pendencias == []
    assert controle.linha_1200() == (
        "|1200|MS090004|86091,65|0|62720|108858,68|39952,97|")
    assert controle.linha_1210() == f"|1210|MS03||108858,68|{CHAVE}|"


def test_uso_acima_do_estoque_fica_pendente(agosto, parametros, tmp_path):
    base, apuracao = agosto
    devolvido = _devolver(base, apuracao, tmp_path, valor=200_000.00)
    base = tratar(devolvido, parametros=parametros)
    apuracao = apurar(base, parametros, ajustes=ler_ajustes(devolvido))
    (controle,) = cc.montar(apuracao, parametros)
    assert controle.saldo_final < 0
    assert any("negativo" in p for p in controle.pendencias)


def test_competencia_sem_saldo_declarado_fica_pendente(parametros, tmp_path):
    """Setembro ainda não tem abertura em saldos.yaml: não é zero, é aberto."""
    base = tratar(_livro(tmp_path / "setembro.xlsx", mes=9), parametros=parametros)
    (controle,) = cc.montar(apurar(base, parametros), parametros)
    assert controle.saldo_inicial is None
    assert any("não declarado" in p for p in controle.pendencias)


def test_a_aba_traz_as_linhas_da_efd(reapurado, tmp_path):
    base, apuracao = reapurado
    planilha = openpyxl.load_workbook(escrever(base, tmp_path / "z.xlsx", apuracao))
    texto = [c for linha in _linhas(planilha["REGISTRO 1200"]) for c in linha]
    assert "|1200|MS090004|86091,65|0|62720|108858,68|39952,97|" in texto
    assert f"|1210|MS03||108858,68|{CHAVE}|" in texto


@pytest.mark.parametrize("valor, esperado", [
    (0.0, "0"), (62720.0, "62720"), (46138.68, "46138,68"), (0.1, "0,10"),
])
def test_numero_no_formato_da_efd(valor, esperado):
    assert cc._efd(valor) == esperado


# -- julho/2026, contra o Registro do ERP ------------------------------------

def test_julho_desmonta_o_registro_de_rio_brilhante(base_julho, parametros):
    """Linha 003 = 331.236,11 do Livro; linha 002 = 99.412,10 recebidos."""
    apuracao = apurar(base_julho, parametros)
    roteiro = lanc.montar(apuracao, parametros)
    assert roteiro.divergencias == []
    rb = {(x.parcela, x.linha): x.valor for x in roteiro.lancamentos
          if x.estabelecimento == RB}
    assert rb[("estorno", 3)] == pytest.approx(331_236.11, abs=CENTAVO)
    assert rb[("centralizacao_recebe_debito", 2)] == pytest.approx(
        99_412.10, abs=CENTAVO)
