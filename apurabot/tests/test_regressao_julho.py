"""Regressão contra a apuração manual de Julho/2026.

O critério de aceite da Entrega 1: a base tratada reproduz a aba `ICMS` da
planilha manual (as linhas relevantes para ICMS) e os totais por
estabelecimento × entrada/saída × carga batem com a aba `Dinamica`.

O arquivo de referência tem dado fiscal real e não é versionado — ver conftest.
"""
from __future__ import annotations

import pytest
import xlrd

from apurabot.nucleo.carga import Situacao

CENTAVO = 0.005


# --------------------------------------------------------------------------
# Leitura da planilha manual, que é a fonte da verdade destes testes
# --------------------------------------------------------------------------

def _abrir(caminho):
    return xlrd.open_workbook(caminho, on_demand=True)


def _celula(aba, r, c):
    cel = aba.cell(r, c)
    return None if cel.ctype in (0, 5, 6) else cel.value


@pytest.fixture(scope="module")
def aba_icms(arquivo_julho):
    """A aba ICMS é o Livro Fiscal filtrado pelas linhas com carga efetiva."""
    return _abrir(arquivo_julho).sheet_by_name("ICMS")


@pytest.fixture(scope="module")
def dinamica(arquivo_julho):
    """Totais manuais por estabelecimento × entrada/saída × carga efetiva.

    A aba `Dinamica` é uma tabela dinâmica com subtotais; aqui só interessam
    as linhas de detalhe, que são as que têm os três níveis preenchidos.
    """
    aba = _abrir(arquivo_julho).sheet_by_name("Dinamica")
    esperado: dict[tuple, dict[str, float]] = {}
    estabelecimento = entrada_saida = None
    for r in range(4, aba.nrows):
        a, b, c = (_celula(aba, r, i) for i in range(3))
        if isinstance(a, str) and a.strip() and not a.endswith("Total"):
            estabelecimento = a.strip()
        if isinstance(b, str) and b.strip():
            if b.strip().endswith("Total"):
                continue
            entrada_saida = b.strip()
        if c is None or estabelecimento is None or entrada_saida is None:
            continue
        if "(vazio)" in (estabelecimento, entrada_saida):
            continue                     # linha em branco da tabela dinâmica
        if c == "(vazio)":
            carga = None                 # linha sem ICMS
        elif isinstance(c, str):
            carga = c.strip()            # "CIAP"
        else:
            carga = float(c)
        esperado[(estabelecimento, entrada_saida, carga)] = {
            "valor_contabil": _celula(aba, r, 3) or 0.0,
            "base_icms": _celula(aba, r, 4) or 0.0,
            "valor_icms": _celula(aba, r, 5) or 0.0,
        }
    return esperado


# --------------------------------------------------------------------------
# Testes
# --------------------------------------------------------------------------

def test_le_o_livro_inteiro(base_julho):
    assert len(base_julho.livro) == 6504
    assert base_julho.competencia == "2026-07"

    # A extração da apuração é anterior ao extrato "Movimento Livros Fiscais" e
    # não traz as colunas dele. Nenhuma é essencial — a apuração roda sem elas,
    # como as demais asserções deste arquivo comprovam.
    assert set(base_julho.livro.colunas_ausentes) == {
        "Tipo Operação", "Descrição (Tipo de Operação)", "Observação",
        "Vlr. DIFAL UF Remet.", "Vlr. DIFAL UF Destino",
        "Nro. único pedido", "Origem",
    }


def test_reproduz_a_quantidade_de_linhas_relevantes(base_julho, aba_icms):
    """A aba ICMS da planilha manual tem uma linha por linha relevante.

    Contamos as linhas com carga efetiva preenchida em vez de usar o total de
    linhas da aba: a última linha do arquivo (2347) carrega só um total solto
    na coluna E, sem documento.
    """
    coluna_carga = 23                                  # X — Carga efetiva
    manuais = sum(
        1
        for r in range(1, aba_icms.nrows)
        if _celula(aba_icms, r, coluna_carga) is not None
    )
    assert manuais == 2345
    assert len(base_julho.relevantes) == manuais


def test_linhas_descartadas_nao_tem_icms(base_julho):
    """Nenhuma linha fora da apuração pode carregar ICMS."""
    for tratada in base_julho.linhas:
        if tratada.carga.situacao is Situacao.SEM_ICMS:
            assert not (tratada.origem.dados.get("valor_icms") or 0)


def test_carga_efetiva_bate_com_a_classificacao_manual(base_julho):
    """A equalização reproduz a coluna preenchida à mão.

    As três divergências aceitas são as notas da ICL Aditivos em Rio Brilhante
    (CST 00, alíquota 7%), reclassificadas manualmente para 4% ao aplicar a
    regra de MS de limitar o crédito mantido. São intervenção, não erro de
    algoritmo — ver docs/apurabot/05-achados-julho-2026.md.
    """
    iguais, divergentes = 0, []
    for t in base_julho.linhas:
        manual = t.origem.dados.get("carga_efetiva_origem")
        if isinstance(manual, float):
            if t.carga.carga is not None and abs(t.carga.carga - manual) < 1e-9:
                iguais += 1
            else:
                divergentes.append((t.origem.linha_origem, manual, t.carga.carga))
        elif manual == "CIAP":
            assert t.carga.situacao is Situacao.CIAP
            iguais += 1

    assert len(divergentes) == 3, f"divergências inesperadas: {divergentes}"
    assert all(manual == 4.0 and calculado == 7.0 for _, manual, calculado in divergentes)
    assert iguais == 2342


def test_totais_por_estabelecimento_e_carga_batem_com_a_dinamica(base_julho, dinamica):
    """Os totais reproduzem a aba Dinamica, com uma exceção conhecida.

    A exceção é a mesma das três notas da ICL Aditivos: a planilha manual as
    moveu de 7% para 4% ao aplicar a regra de MS de limitar o crédito mantido.
    Isso desloca exatamente R$ 9.019,01 de ICMS entre os dois grupos de entrada
    de Rio Brilhante. O teste exige que a diferença seja essa e só essa — se
    aparecer em outro grupo, ou com outro valor, ele falha.
    """
    ICL = 9_019.01
    calculado = base_julho.por_estabelecimento_carga()

    # A planilha manual grafa Corumbá sem espaço antes de "MS" e Registro com
    # espaço duplo; comparamos por nome normalizado.
    def normalizar(nome):
        return " ".join(str(nome).split()).replace("- MS", "-MS").casefold()

    por_chave = {
        (normalizar(estab), es, carga): valores
        for (estab, es, carga), valores in calculado.items()
    }

    faltando, divergentes = [], {}
    for (estab, es, carga), esperado in dinamica.items():
        chave = (normalizar(estab), es, carga)
        obtido = por_chave.get(chave)
        if obtido is None:
            faltando.append(chave)
            continue
        for campo in ("valor_contabil", "base_icms", "valor_icms"):
            delta = obtido[campo] - esperado[campo]
            if abs(delta) > CENTAVO:
                divergentes.setdefault(chave, {})[campo] = delta

    assert not faltando, f"grupos da Dinamica sem correspondência: {faltando}"

    esperadas = {
        ("hinove (rio brilhante)", "Entrada", 4.0),
        ("hinove (rio brilhante)", "Entrada", 7.0),
    }
    assert set(divergentes) == esperadas, (
        "divergências fora do esperado:\n  "
        + "\n  ".join(f"{k}: {v}" for k, v in divergentes.items() if k not in esperadas)
    )

    # O ICMS sai de um grupo e entra no outro, sem sobrar nem faltar.
    saiu = divergentes[("hinove (rio brilhante)", "Entrada", 4.0)]["valor_icms"]
    entrou = divergentes[("hinove (rio brilhante)", "Entrada", 7.0)]["valor_icms"]
    assert abs(saiu + ICL) < CENTAVO
    assert abs(entrou - ICL) < CENTAVO


def test_ciap_e_complemento_conferem(base_julho):
    """Os lançamentos sem valor contábil, que a planilha marcava à mão."""
    por_categoria = base_julho.por_categoria()
    assert por_categoria["ciap"]["linhas"] == 3
    assert abs(por_categoria["ciap"]["valor_icms"] - 24_903.24) < CENTAVO
    assert por_categoria["complemento_icms"]["linhas"] == 6
    assert abs(por_categoria["complemento_icms"]["valor_icms"] - 17_490.73) < CENTAVO


def test_enxofre_de_revenda_bate_com_a_aba_estorno(base_julho):
    """A aba ESTORNO traz "Enxofre - Revenda" com R$ 474.416,28 e estorno zero."""
    revenda = base_julho.por_categoria()["revenda"]
    assert abs(revenda["valor_icms"] - 474_416.28) < CENTAVO


def test_retorno_de_industrializacao_bate_com_a_aba_estorno(base_julho):
    """A aba ESTORNO traz "Retorno MP Ind" a 12% com R$ 6.967,37 e estorno zero."""
    total = sum(
        t.origem.dados.get("valor_icms") or 0.0
        for t in base_julho.relevantes
        if t.classificacao.categoria == "retorno_industrializacao"
        and t.carga.carga == 12.0
        and t.origem.dados.get("entrada_saida") == "Entrada"
    )
    assert abs(total - 6_967.37) < CENTAVO


def test_julho_fecha_sem_pendencia(base_julho):
    """Com o COMPLEMENTO DE PREÇO classificado, não sobra nada bloqueando.

    Era a última pendência da competência: 22 linhas, R$ 2.181,70 de ICMS.
    A decisão de 21/08/2026 é que o complemento acompanha a nota complementada.
    """
    assert base_julho.com_pendencia == []
    assert base_julho.pode_encerrar


def test_cargas_toleradas_alertam_sem_bloquear(base_julho):
    """As 30 linhas de 20,5% e as 6 de complemento de ICMS avisam, não travam."""
    alertas = base_julho.com_alerta
    assert len(alertas) == 36
    assert all(not t.pendencias for t in alertas)


def test_regua_homologada_nao_tem_dezenove_nem_vinte_e_cinco(parametros):
    """Decisão de 21/08/2026: 19 e 25 saem das homologadas e viram toleradas."""
    assert parametros.cargas_nominais == [4.0, 7.0, 12.0, 17.0, 18.0]
    assert set(parametros.cargas_toleradas) == {19.0, 20.5, 25.0}
