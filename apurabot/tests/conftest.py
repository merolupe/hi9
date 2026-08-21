"""Fixtures comuns.

O arquivo de apuração de Julho/2026 contém dados fiscais reais e **não está no
repositório**. Os testes de regressão o localizam por, nesta ordem:

  1. a variável de ambiente APURABOT_FIXTURE_JULHO
  2. competencias/2026-07/entrada/ na raiz do repositório

Sem ele, os testes de regressão são pulados com mensagem explicando o motivo —
os testes de unidade continuam rodando.
"""
from __future__ import annotations

import os
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[2]
PASTA_COMPETENCIA = RAIZ / "competencias" / "2026-07" / "entrada"


def _localizar_julho() -> Path | None:
    do_ambiente = os.environ.get("APURABOT_FIXTURE_JULHO")
    if do_ambiente and Path(do_ambiente).is_file():
        return Path(do_ambiente)
    if PASTA_COMPETENCIA.is_dir():
        for padrao in ("*.xls", "*.xlsx"):
            achados = sorted(PASTA_COMPETENCIA.glob(padrao))
            if achados:
                return achados[0]
    return None


@pytest.fixture(scope="session")
def arquivo_julho() -> Path:
    caminho = _localizar_julho()
    if caminho is None:
        pytest.skip(
            "apuração de Julho/2026 não encontrada — defina APURABOT_FIXTURE_JULHO "
            f"ou coloque o arquivo em {PASTA_COMPETENCIA}. "
            "O arquivo tem dado fiscal real e por isso não é versionado."
        )
    return caminho


@pytest.fixture(scope="session")
def parametros():
    from apurabot.parametros import carregar

    return carregar()


@pytest.fixture(scope="session")
def base_julho(arquivo_julho, parametros):
    from apurabot.base_tratada import tratar

    return tratar(arquivo_julho, parametros=parametros)
