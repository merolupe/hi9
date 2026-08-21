"""O extrato "Movimento Livros Fiscais" — padrão a partir de 08/2026.

Ele traz a coluna TOP (Tipo de Operação), que nomeia a operação como ela foi
lançada, e abre com duas linhas de metadados antes do cabeçalho. Estes testes
garantem que o motor lê os dois layouts e chega no mesmo resultado.

Como o de Julho/2026, o arquivo tem dado fiscal real e não é versionado.
"""
from __future__ import annotations

import os
from pathlib import Path

import pytest

from apurabot.apuracao import apurar
from apurabot.base_tratada import tratar
from apurabot.ingestao import ler_livro_fiscal

CENTAVO = 0.005


@pytest.fixture(scope="module")
def arquivo_movimento() -> Path:
    caminho = os.environ.get("APURABOT_FIXTURE_MOVIMENTO_JULHO")
    if not caminho or not Path(caminho).is_file():
        pytest.skip(
            "extrato Movimento Livros Fiscais não encontrado — defina "
            "APURABOT_FIXTURE_MOVIMENTO_JULHO. Tem dado fiscal real e por isso "
            "não é versionado."
        )
    return Path(caminho)


@pytest.fixture(scope="module")
def livro_movimento(arquivo_movimento):
    return ler_livro_fiscal(arquivo_movimento)


def test_encontra_o_cabecalho_fora_da_primeira_linha(livro_movimento):
    """O extrato abre com título, data de emissão e usuário antes do cabeçalho."""
    assert len(livro_movimento) > 6_000
    assert livro_movimento.competencias == {"2026-07"}
    for essencial in ("Nro único Nota", "CFOP", "Vlr. do ICMS"):
        assert essencial not in livro_movimento.colunas_ausentes


def test_traz_o_tipo_de_operacao(livro_movimento):
    com_top = [linha for linha in livro_movimento if linha.top]
    assert len(com_top) > 6_000
    tops = {linha.top for linha in com_top}
    # Os TOPs que nomeiam o que o motor hoje deduz por heurística.
    assert {2310, 3217, 2316, 2103, 2108}.issubset(tops)


def test_inclui_documentos_cancelados_que_o_extrato_antigo_filtrava(livro_movimento):
    """São 51 em Julho/2026, todos com ICMS zero — o motor os descarta."""
    cancelados = [linha for linha in livro_movimento if linha.cancelado]
    assert len(cancelados) == 51
    assert all(not (linha.dados.get("valor_icms") or 0) for linha in cancelados)


def test_produz_a_mesma_apuracao_que_o_extrato_antigo(arquivo_movimento, arquivo_julho):
    """A prova de que trocar de extração não muda um centavo da apuração."""
    antiga = apurar(tratar(arquivo_julho))
    nova = apurar(tratar(arquivo_movimento))

    assert set(nova.filiais) == set(antiga.filiais)
    for nome, filial in antiga.filiais.items():
        outra = nova.filiais[nome]
        for campo in ("credito_bruto", "estorno", "credito_indevido",
                      "credito_mantido", "debito"):
            assert getattr(outra, campo) == pytest.approx(
                getattr(filial, campo), abs=CENTAVO
            ), f"{nome}.{campo}"


def test_mesma_base_tratada_nos_dois_extratos(arquivo_movimento, arquivo_julho):
    antiga, nova = tratar(arquivo_julho), tratar(arquivo_movimento)
    assert len(nova.relevantes) == len(antiga.relevantes) == 2345
    assert len(nova.com_pendencia) == len(antiga.com_pendencia) == 0
    assert len(nova.com_alerta) == len(antiga.com_alerta) == 36
