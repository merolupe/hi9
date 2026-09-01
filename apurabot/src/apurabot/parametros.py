"""Carregamento dos parâmetros tributários.

A regra tributária vive em `apurabot/parametros/*.yaml`, nunca em código.
Este módulo só lê e valida — não interpreta.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

PASTA_PADRAO = Path(__file__).resolve().parents[2] / "parametros"

ARQUIVOS = ("filiais", "regimes", "cargas", "classificacao", "produtos", "saldos")


@dataclass(frozen=True)
class Parametros:
    """Todos os parâmetros tributários de uma competência, já carregados."""

    filiais: dict[str, Any]
    regimes: dict[str, Any]
    cargas: dict[str, Any]
    classificacao: dict[str, Any]
    produtos: dict[str, Any]
    saldos: dict[str, Any]
    pasta: Path

    # -- atalhos usados pelo núcleo ------------------------------------

    @property
    def cargas_nominais(self) -> list[float]:
        return [float(c) for c in self.cargas["equalizacao"]["cargas_nominais"]]

    @property
    def cargas_toleradas(self) -> dict[float, dict[str, Any]]:
        """Cargas reconhecidas mas não homologadas, indexadas pelo valor."""
        itens = self.cargas["equalizacao"].get("cargas_toleradas") or []
        return {float(i["carga"]): i for i in itens}

    @property
    def regua_completa(self) -> list[float]:
        """Régua efetiva da equalização: homologadas + toleradas."""
        return sorted(set(self.cargas_nominais) | set(self.cargas_toleradas))

    @property
    def tolerancia(self) -> float:
        return float(self.cargas["equalizacao"]["tolerancia_percentual"])

    @property
    def limite_teto_aliquota(self) -> bool:
        return bool(self.cargas["equalizacao"]["limite_teto_aliquota"])

    # -- saldo credor de abertura ---------------------------------------

    def saldos_credores(self, competencia: str) -> dict[int, float] | None:
        """Saldo credor de abertura de cada estabelecimento da competência.

        Indexado pelo código da empresa. Devolve `None` quando a competência
        não foi declarada — o que é diferente de declará-la com todos zerados:
        no primeiro caso o registro marca a linha 009 como pendente, no segundo
        ele a dá por fechada em zero.
        """
        for item in self.saldos.get("saldos_credores") or []:
            if str(item.get("competencia") or "") != competencia:
                continue
            declarados = item.get("por_estabelecimento") or {}
            return {int(k): float(v) for k, v in declarados.items()}
        return None


def carregar(pasta: Path | str | None = None) -> Parametros:
    """Lê os cinco arquivos de parâmetros de `pasta`."""
    pasta = Path(pasta) if pasta else PASTA_PADRAO
    if not pasta.is_dir():
        raise FileNotFoundError(f"pasta de parâmetros não encontrada: {pasta}")

    conteudo: dict[str, Any] = {}
    for nome in ARQUIVOS:
        caminho = pasta / f"{nome}.yaml"
        if not caminho.is_file():
            raise FileNotFoundError(f"parâmetro obrigatório ausente: {caminho}")
        conteudo[nome] = yaml.safe_load(caminho.read_text(encoding="utf-8")) or {}

    return Parametros(pasta=pasta, **conteudo)
