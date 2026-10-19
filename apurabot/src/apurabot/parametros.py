"""Carregamento dos parâmetros tributários.

A regra tributária vive em `apurabot/parametros/*.yaml`, nunca em código.
Este módulo só lê e valida — não interpreta.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

PASTA_PADRAO = Path(__file__).resolve().parents[2] / "parametros"

ARQUIVOS = ("filiais", "regimes", "cargas", "classificacao", "produtos", "saldos")

#: Lidos quando existem. Sem eles a apuração fecha igual — o que falta é só o
#: que o arquivo acrescenta, e isso sai marcado onde for usado.
OPCIONAIS = ("lancamentos_sankhya", "controle_de_creditos")


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
    #: Observação padrão do Sankhya de cada ajuste — ver `lancamentos.py`.
    lancamentos_sankhya: dict[str, Any] = field(default_factory=dict)
    #: Registros 1200/1210 — ver `controle_de_creditos.py`.
    controle_de_creditos: dict[str, Any] = field(default_factory=dict)

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

    # -- DIFAL ----------------------------------------------------------

    def difal_da_uf(self, uf: str) -> dict[str, Any]:
        """Como a UF trata o diferencial de alíquota.

        UF sem bloco cadastrado devolve vazio, e o DIFAL dela fica fora da
        conta gráfica: é a leitura conservadora, porque incluí-lo por conta
        própria aumentaria o imposto sem ninguém ter decidido.
        """
        return (self.regimes.get("difal") or {}).get(str(uf).lower()) or {}

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

    def saldo_do_controle(self, competencia: str, empresa: int,
                          codigo: str) -> float | None:
        """Saldo inicial de um crédito controlado (SLD_CRED do 1200).

        `None` quando a competência não o declara — diferente de zero, pelo
        mesmo motivo do saldo credor: ninguém disse quanto havia.
        """
        for item in self.saldos.get("creditos_controlados") or []:
            if str(item.get("competencia") or "") != competencia:
                continue
            por_codigo = (item.get("por_estabelecimento") or {}).get(empresa)
            if por_codigo is None:
                por_codigo = (item.get("por_estabelecimento") or {}).get(str(empresa))
            valor = (por_codigo or {}).get(codigo)
            return None if valor is None else float(valor)
        return None

    def recebido_do_controle(self, competencia: str, empresa: int,
                             codigo: str) -> float | None:
        """Crédito recebido no mês (CRÉD_RECEB), quando declarado.

        A NF-e de transferência vem com desconto, e o Livro Fiscal só traz o
        valor do documento. `None` quando não declarado: vale o Livro.
        """
        for item in self.saldos.get("creditos_controlados") or []:
            if str(item.get("competencia") or "") != competencia:
                continue
            declarados = item.get("recebido_por_estabelecimento") or {}
            por_codigo = declarados.get(empresa) or declarados.get(str(empresa))
            valor = (por_codigo or {}).get(codigo)
            return None if valor is None else float(valor)
        return None

    def transmitidos_do_controle(self, empresa: int,
                                 codigo: str) -> dict[str, dict[str, float]]:
        """O 1200 de cada mês já transmitido, por competência (AAAA-MM).

        Cada mês traz `sld_cred`, `cred_apr`, `cred_receb` e `cred_util`; o
        campo ausente é zero.
        """
        for item in self.saldos.get("creditos_controlados_transmitidos") or []:
            if int(item.get("empresa") or 0) != int(empresa):
                continue
            if str(item.get("cod_aj_apur") or "") != codigo:
                continue
            return {
                str(competencia): {
                    campo: float((valores or {}).get(campo) or 0.0)
                    for campo in ("sld_cred", "cred_apr", "cred_receb", "cred_util")
                }
                for competencia, valores in (item.get("meses") or {}).items()
            }
        return {}


def carregar(pasta: Path | str | None = None) -> Parametros:
    """Lê os arquivos de parâmetros de `pasta` — os obrigatórios e os opcionais."""
    pasta = Path(pasta) if pasta else PASTA_PADRAO
    if not pasta.is_dir():
        raise FileNotFoundError(f"pasta de parâmetros não encontrada: {pasta}")

    conteudo: dict[str, Any] = {}
    for nome in ARQUIVOS:
        caminho = pasta / f"{nome}.yaml"
        if not caminho.is_file():
            raise FileNotFoundError(f"parâmetro obrigatório ausente: {caminho}")
        conteudo[nome] = yaml.safe_load(caminho.read_text(encoding="utf-8")) or {}
    for nome in OPCIONAIS:
        caminho = pasta / f"{nome}.yaml"
        if caminho.is_file():
            conteudo[nome] = yaml.safe_load(caminho.read_text(encoding="utf-8")) or {}

    return Parametros(pasta=pasta, **conteudo)
