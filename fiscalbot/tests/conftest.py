"""Registros fictícios e a localização do padrão-ouro.

Nenhum dado fiscal real entra no repositório — a regra nº 1 do `CLAUDE.md`.
Os registros aqui são montados no próprio teste. O teste de regressão procura
o relatório real por, nesta ordem:

  1. a variável de ambiente FISCALBOT_PADRAO_OURO
  2. competencias/fiscalbot/ na raiz do repositório

Sem ele, a regressão é pulada com a mensagem explicando o motivo; os testes de
unidade continuam rodando.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

import pytest

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "fiscalbot" / "src"))

from fiscalbot.leitura import MapaDeColunas  # noqa: E402
from fiscalbot.modelo import (BaseDeRegras, Parametros, Parceiro,  # noqa: E402
                              Regra)

PASTA_PADRAO_OURO = RAIZ / "competencias" / "fiscalbot"

#: As colunas do relatório, na ordem em que o teste as monta.
COLUNAS = ("ES", "CST", "ICMS", "CFOP", "UFO", "UFD", "PROD", "ALIQ", "VCONT",
           "ESP", "PARC", "PARCNOME", "ORIGEM", "DESCPROD", "DESCTIPO",
           "NUNOTA", "NOMEFANT", "DESCCFOP")

PADRAO = {
    "ES": "Saída", "CST": "00-Tributada integralmente", "ICMS": 18.0,
    "CFOP": 5101.0, "UFO": "SP", "UFD": "SP", "PROD": 101060223.0,
    "ALIQ": 18.0, "VCONT": 100.0, "ESP": "NF", "PARC": 4.0,
    "PARCNOME": "CLIENTE EXEMPLO", "ORIGEM": "Estoque",
    "DESCPROD": "PRODUTO EXEMPLO", "DESCTIPO": "Venda", "NUNOTA": 1.0,
    "NOMEFANT": "HINOVE (MATRIZ)", "DESCCFOP": "Venda de producao",
}


@pytest.fixture()
def mapa() -> MapaDeColunas:
    return MapaDeColunas({campo: i for i, campo in enumerate(COLUNAS)})


def registro(**alteracoes: Any) -> list[Any]:
    """Uma linha do relatório, com os campos que o teste quiser trocar.

    Aceita o nome do campo em minúscula (`cst=`, `cfop=`) — é como o teste lê
    melhor. Um nome que não seja campo do relatório é erro de teste, não algo
    a ignorar em silêncio.
    """
    desconhecidos = {c for c in alteracoes if c.upper() not in PADRAO}
    if desconhecidos:
        raise KeyError(f"campo(s) que o relatório não tem: {sorted(desconhecidos)}")
    valores = {**PADRAO, **{c.upper(): v for c, v in alteracoes.items()}}
    return [valores[campo] for campo in COLUNAS]


def base_com(*regras: Regra, **ajustes: Any) -> BaseDeRegras:
    """Uma base mínima com as regras informadas."""
    parametros = Parametros(
        tolerancia_carga=ajustes.pop("tolerancia_carga", 0.05),
        cst_exigem_icms_positivo=ajustes.pop("cst_exigem_icms_positivo", ("00", "20")),
        tabelas=ajustes.pop("tabelas", {}),
        sinonimos={},
    )
    return BaseDeRegras(
        regras=list(regras),
        parametros=parametros,
        aliquotas=ajustes.pop("aliquotas", {}),
        parceiros_simples_nacional=[
            Parceiro(c) for c in ajustes.pop("simples_nacional", ())
        ],
        parceiros_cavaco=[Parceiro(c) for c in ajustes.pop("cavaco", ())],
    )


def regra(identificador: str = "T01", **campos: Any) -> Regra:
    campos.setdefault("operacao", "Operacao de teste")
    cfop = campos.pop("cfop", ("5101",))
    if isinstance(cfop, str):
        cfop = tuple(cfop.split(";"))
    return Regra(id=identificador, cfop=tuple(cfop), **campos)


def _localizar_padrao_ouro() -> Path | None:
    do_ambiente = os.environ.get("FISCALBOT_PADRAO_OURO")
    if do_ambiente and Path(do_ambiente).is_file():
        return Path(do_ambiente)
    if PASTA_PADRAO_OURO.is_dir():
        for padrao in ("*.xls", "*.xlsx"):
            achados = sorted(PASTA_PADRAO_OURO.glob(padrao))
            if achados:
                return achados[0]
    return None


@pytest.fixture(scope="session")
def padrao_ouro() -> Path:
    """Um relatório real já auditado pela macro VBA, com as abas de saída."""
    caminho = _localizar_padrao_ouro()
    if caminho is None:
        pytest.skip(
            "relatório auditado pela macro não encontrado — defina "
            f"FISCALBOT_PADRAO_OURO ou coloque o arquivo em {PASTA_PADRAO_OURO}. "
            "Ele tem dado fiscal real e por isso não é versionado."
        )
    return caminho


@pytest.fixture(scope="session")
def base_de_fabrica() -> BaseDeRegras:
    from fiscalbot.base import carregar_fabrica

    return carregar_fabrica()
