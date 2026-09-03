"""Camada 5 — segregação por atividade.

A GIA de Mato Grosso do Sul não aceita uma apuração só por estabelecimento:
exige o resultado separado por atividade — Industrial, Comercial, Importados e
Prestacional/Outras.

Isso não é formalidade de declaração. É a segregação que dimensiona o benefício
fiscal, porque o crédito presumido do Termo de Acordo n. 1.190/2018 incide
exclusivamente sobre o saldo devedor da atividade industrial. Sem esta camada
não existe "crédito da parcela incentivada", e o benefício não tem como ser
calculado.

Ordem de avaliação: descrição primeiro, CFOP depois. O que não casar em nenhuma
regra recebe `SEM REGRA` e bloqueia o encerramento da competência.

Uma regra de descrição pode declarar `vigencia_inicio` e `vigencia_fim`: aí é a
data do movimento do documento que decide se ela se aplica. É o que permite
mudar a classificação de agosto em diante sem alterar o que julho já declarou.

As listas de CFOP e as finalidades de frete vêm de `parametros/regimes.yaml`.
"""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Any

from ..ingestao import LinhaLivro
from ..parametros import Parametros

INDUSTRIAL = "industrial"
COMERCIAL = "comercial"
IMPORTADOS = "importados"
PRESTACIONAL = "prestacional_outras"
SEM_REGRA = "SEM REGRA"

# Ordem em que as atividades aparecem no relatório — a mesma da GIA.
ORDEM = (INDUSTRIAL, COMERCIAL, IMPORTADOS, PRESTACIONAL)

INTRAESTADUAL = "intraestadual"
INTERESTADUAL = "interestadual"
EXTERIOR = "exterior"


class MapaDeAtividadeAusente(Exception):
    """A UF exige segregação por atividade e o mapa não está parametrizado."""


@dataclass(frozen=True)
class ResultadoAtividade:
    atividade: str
    regra: str
    destino: str | None = None      # só faz sentido nas saídas

    @property
    def e_pendencia(self) -> bool:
        return self.atividade == SEM_REGRA


def mapa_da_uf(uf: str, params: Parametros) -> dict[str, Any] | None:
    """Devolve o mapa de atividades da UF, ou None se ela não segrega."""
    mapas = params.regimes.get("atividades") or {}
    return mapas.get(str(uf or "").strip().casefold())


def classificar(
    linha: LinhaLivro, mapa: dict[str, Any]
) -> ResultadoAtividade:
    """Determina a atividade de uma linha do Livro Fiscal."""
    cfop = linha.cfop_int
    destino = _destino(cfop, mapa)
    entrada = str(linha.dados.get("entrada_saida") or "") != "Saída"
    lado = "credito" if entrada else "debito"

    # 1. A descrição vence o CFOP.
    #
    # O CFOP do serviço de transporte diz quem contratou o frete, não o que o
    # frete carrega — e é o que ele carrega que define a atividade. Frete de
    # insumo é industrial; frete de venda é comercial, no mesmo CFOP 2352.
    descricao = str(linha.dados.get("produto_descricao") or "").casefold()
    data = linha.dados.get("data_movimento")
    for regra in mapa.get("por_descricao") or []:
        if not _vigente(regra, data):
            continue
        alvos = set(regra.get("cfop") or [])
        if alvos and cfop not in alvos:
            continue
        agulha = str(regra.get("contem") or "").casefold()
        if agulha and agulha in descricao:
            return ResultadoAtividade(
                atividade=regra["atividade"],
                regra=f"descrição contém {regra['contem']!r}",
                destino=destino,
            )

    # 2. CFOP.
    for atividade, lados in (mapa.get("por_cfop") or {}).items():
        if cfop in set((lados or {}).get(lado) or []):
            return ResultadoAtividade(
                atividade=atividade,
                regra=f"CFOP {cfop} de {lado} — atividade {atividade}",
                destino=destino,
            )

    return ResultadoAtividade(
        atividade=SEM_REGRA,
        regra=(
            f"CFOP {cfop} de {lado} não está em nenhuma atividade do mapa — "
            "cadastre-o em regimes.yaml, bloco `atividades`"
        ),
        destino=destino,
    )


def _vigente(regra: dict[str, Any], data) -> bool:
    """A regra vale na data do movimento do documento?

    Regra sem vigência declarada vale sempre — é o caso da maioria. Onde há
    `vigencia_inicio` ou `vigencia_fim`, é a data do documento que decide, para
    que competência antiga continue reproduzível depois de a regra mudar. É a
    regra 3 do repositório, e o que separa "a classificação mudou de agosto em
    diante" de "a apuração de julho passou a dar outro número".
    """
    if not isinstance(data, dt.date):
        return True
    inicio, fim = _data(regra.get("vigencia_inicio")), _data(regra.get("vigencia_fim"))
    if inicio and data < inicio:
        return False
    if fim and data > fim:
        return False
    return True


def _data(valor) -> dt.date | None:
    if isinstance(valor, dt.datetime):
        return valor.date()
    if isinstance(valor, dt.date):
        return valor
    if isinstance(valor, str) and valor.strip():
        return dt.date.fromisoformat(valor.strip())
    return None


def _destino(cfop: int | None, mapa: dict[str, Any]) -> str | None:
    """Intra, inter ou exterior, pelo primeiro dígito do CFOP.

    É a definição do próprio sistema de CFOP, e é o corte que a GIA usa para
    separar as saídas de 67% das de 80%.
    """
    if cfop is None:
        return None
    por_prefixo = {int(k): v for k, v in (mapa.get("destino_por_prefixo_cfop") or {}).items()}
    return por_prefixo.get(cfop // 1000)


@dataclass
class TotaisAtividade:
    """Somas de uma atividade dentro de um estabelecimento."""

    atividade: str
    credito_bruto: float = 0.0
    credito_mantido: float = 0.0
    estorno: float = 0.0
    credito_indevido: float = 0.0
    debito: float = 0.0
    linhas: int = 0
    debito_por_destino: dict[str, float] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.debito_por_destino is None:
            self.debito_por_destino = {}

    def debito_de(self, destino: str) -> float:
        return self.debito_por_destino.get(destino, 0.0)

    @property
    def saldo(self) -> float:
        """Positivo = devedor. É o saldo da atividade, antes do benefício."""
        return self.debito - self.credito_mantido

    @property
    def confere(self) -> bool:
        soma = self.credito_mantido + self.estorno + self.credito_indevido
        return abs(soma - self.credito_bruto) < 0.005
