"""As abas de conferência: o que elas prometem ao time fiscal."""
from __future__ import annotations

import openpyxl
import pytest

from apurabot.apuracao import apurar
from apurabot.conferencia import ROTULO_DA_ATIVIDADE, _parcela, _rotulo_atividade
from apurabot.nucleo import atividade as ativ
from apurabot.saida import ORDEM_DAS_ABAS, escrever

CENTAVO = 0.005


@pytest.fixture(scope="module")
def apuracao(base_julho):
    return apurar(base_julho)


@pytest.fixture(scope="module")
def planilha(base_julho, apuracao, tmp_path_factory):
    destino = tmp_path_factory.mktemp("saida") / "conferencia.xlsx"
    escrever(base_julho, destino, apuracao)
    return openpyxl.load_workbook(destino, data_only=True)


# -- o CHECK é a promessa da aba -------------------------------------------

def test_toda_linha_apurada_fecha_o_check(apuracao):
    """a estornar + a apropriar = ICMS creditado, linha a linha.

    É o que a coluna CHECK mostra. Se falhar aqui, a aba mostra vermelho — e
    o vermelho é erro de motor, não de escrituração.
    """
    quebradas = [
        a for f in apuracao.filiais.values() for a in f.apuradas if not a.confere
    ]
    assert not quebradas, f"{len(quebradas)} linha(s) não fecham o CHECK"


def test_a_soma_das_linhas_apuradas_e_o_total_da_filial(apuracao):
    for filial in apuracao.filiais.values():
        assert sum(a.resultado.credito_bruto for a in filial.apuradas) == pytest.approx(
            filial.credito_bruto, abs=CENTAVO
        )
        assert sum(a.credito_a_apropriar for a in filial.apuradas) == pytest.approx(
            filial.credito_mantido, abs=CENTAVO
        )
        assert sum(a.resultado.debito for a in filial.apuradas) == pytest.approx(
            filial.debito, abs=CENTAVO
        )


def test_a_parcela_nao_tributada_e_a_fracao_estornada(apuracao):
    """A coluna é a conta, não um número solto: parcela × crédito = estorno."""
    for filial in apuracao.filiais.values():
        for a in filial.apuradas:
            parcela = _parcela(a)
            if parcela is None:
                assert not a.resultado.credito_bruto
                continue
            assert 0.0 <= parcela <= 1.0
            assert a.resultado.credito_bruto * parcela == pytest.approx(
                a.credito_a_estornar, abs=CENTAVO
            )


# -- rótulos ----------------------------------------------------------------

def test_a_atividade_aparece_com_o_nome_que_o_fiscal_usa(apuracao):
    rb = apuracao.filiais["HINOVE (RIO BRILHANTE)"]
    industriais = [a for a in rb.apuradas if a.atividade == ativ.INDUSTRIAL]
    assert industriais
    assert _rotulo_atividade(industriais[0]) == "Produção"
    assert ROTULO_DA_ATIVIDADE[ativ.COMERCIAL] == "Comercial"


def test_onde_a_uf_nao_segrega_o_rotulo_e_a_categoria_da_equalizacao(apuracao):
    guara = apuracao.filiais["HINOVE (FILIAL GUARÁ)"]
    assert not guara.segrega_por_atividade
    rotulos = {_rotulo_atividade(a) for a in guara.apuradas}
    assert rotulos
    assert not rotulos & set(ROTULO_DA_ATIVIDADE.values())


# -- a planilha -------------------------------------------------------------

def test_a_planilha_traz_as_tres_abas_de_conferencia(planilha):
    assert {"APURAÇÃO EFETIVA", "REGISTRO", "TRANSFERÊNCIAS"} <= set(
        planilha.sheetnames
    )


def test_as_abas_saem_da_conclusao_para_o_detalhe(planilha):
    """Quem abre o arquivo cai no resumo, não em seis mil linhas de base."""
    assert planilha.sheetnames == [
        nome for nome in ORDEM_DAS_ABAS if nome in planilha.sheetnames
    ]
    assert planilha.sheetnames[0] == "RESUMO"


def test_a_aba_de_transferencias_diz_o_que_emitir(planilha):
    texto = "\n".join(
        str(c.value)
        for linha in planilha["TRANSFERÊNCIAS"].iter_rows()
        for c in linha
        if c.value
    )
    assert "HINOVE (REGISTRO)" in texto and "HINOVE (FILIAL GUARÁ)" in texto
    assert "HINOVE (CORUMBÁ- MS)" in texto and "HINOVE (RIO BRILHANTE)" in texto
    assert "NF-e" in texto and "Registro de Apuração" in texto


def test_a_aba_de_pendencias_nao_cobra_mais_a_nota_de_transferencia(planilha):
    texto = "\n".join(
        str(c.value)
        for linha in planilha["PENDÊNCIAS"].iter_rows()
        for c in linha
        if c.value
    )
    assert "sem NF-e escriturada" not in texto


def test_o_registro_tem_um_bloco_por_filial_e_o_totalizador(planilha, apuracao):
    primeira = [linha[0].value for linha in planilha["REGISTRO"].iter_rows(max_col=1)]
    for nome in apuracao.filiais:
        assert nome in primeira
    assert any(
        str(v or "").startswith("TOTALIZADOR") for v in primeira
    ), "falta o totalizador que o PDF por filial não tem"
