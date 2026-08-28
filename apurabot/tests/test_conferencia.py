"""As abas de conferência: o que elas prometem ao time fiscal."""
from __future__ import annotations

import openpyxl
import pytest

from apurabot.apuracao import apurar
from apurabot.conferencia import (
    CHAVE_DA_REGRA,
    EXCEDENTE,
    PROPORCIONAL,
    ROTULO_DA_ATIVIDADE,
    _chave_do_regime,
    _rotulo_atividade,
)
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


def test_a_conferencia_agrupa_pela_chave_da_regra_de_cada_regime(apuracao, parametros):
    """Agrupar pela grandeza errada esconde o que se quer conferir.

    Em MS o estorno é fração da alíquota; em SP é o excedente da carga efetiva
    sobre a carga de saída. A coluna de agrupamento tem que seguir a regra.
    """
    rb = apuracao.filiais["HINOVE (RIO BRILHANTE)"]
    assert _chave_do_regime(rb, parametros) == CHAVE_DA_REGRA[PROPORCIONAL]
    assert _chave_do_regime(rb, parametros)[1] == "Alíquota"

    guara = apuracao.filiais["HINOVE (FILIAL GUARÁ)"]
    assert _chave_do_regime(guara, parametros) == CHAVE_DA_REGRA[EXCEDENTE]
    assert _chave_do_regime(guara, parametros)[1] == "Carga efetiva"


def test_a_parcela_de_ms_e_a_formula_da_regra(apuracao):
    """Em MS, estorno ÷ crédito é exatamente 1 − 4/alíquota.

    É a única UF em que o percentual da conferência coincide com um parâmetro
    da regra — por isso o rótulo da coluna é descritivo, e não normativo.
    """
    rb = apuracao.filiais["HINOVE (RIO BRILHANTE)"]
    conferidas = 0
    for a in rb.apuradas:
        if not a.resultado.credito_bruto or not a.credito_a_estornar:
            continue
        aliquota = float(a.tratada.origem.dados.get("aliquota_icms") or 0)
        if aliquota <= 4:
            continue
        assert a.credito_a_estornar / a.resultado.credito_bruto == pytest.approx(
            round(1 - 4 / aliquota, 4), abs=1e-6
        )
        conferidas += 1
    assert conferidas, "nenhuma linha de RB com estorno proporcional"


def test_em_sp_o_percentual_nao_e_parametro_da_regra(apuracao):
    """Em SP o estorno incide sobre o valor contábil, não sobre o ICMS.

    A razão estorno ÷ crédito varia dentro de uma mesma carga, porque a carga
    do documento foi equalizada para a régua nominal. Chamar isso de "parcela
    não tributada" — que é vocabulário de MS — ensinaria a regra errada.
    """
    guara = apuracao.filiais["HINOVE (FILIAL GUARÁ)"]
    razoes = {}
    for a in guara.apuradas:
        if not a.resultado.credito_bruto or not a.credito_a_estornar:
            continue
        carga = a.tratada.carga.carga
        razoes.setdefault(carga, set()).add(
            round(a.credito_a_estornar / a.resultado.credito_bruto, 4)
        )
    assert any(len(v) > 1 for v in razoes.values()), (
        "esperava razões diferentes dentro de uma mesma carga em SP"
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
