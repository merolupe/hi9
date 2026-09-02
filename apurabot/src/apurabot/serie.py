"""A série do ano — o resultado de cada competência, lado a lado.

A apuração enxerga um mês de cada vez. Quem responde pela empresa precisa do
ano: quanto saiu do caixa mês a mês, e quanto de crédito ficou acumulado. É o
que este módulo guarda.

Dois números por competência, porque um não deriva do outro quando há mais de
um estabelecimento:

    saldo         o resultado do grupo, no sinal do caixa — positivo é credor
    a recolher    a soma do que cada estabelecimento recolhe, que não é
                  `max(-saldo, 0)`: uma filial credora não paga a conta de
                  outra devedora fora da centralização

**Onde fica.** Em `competencias/serie-<ano>.yaml`, e não em `parametros/`. A
distinção é a regra 1 do repositório: `parametros/` é a regra declarada, que se
versiona; `competencias/` é dado fiscal da empresa, que o git ignora. A série é
resultado de apuração — dado —, então fica fora do git.

O mês da apuração que está rodando entra preenchido; os demais vêm do arquivo,
que alguém preencheu pela janela. Nada aqui é calculado por conta própria: mês
sem valor fica vazio, e vazio se lê como "ninguém preencheu".
"""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from .formato import numero

#: `apurabot/src/apurabot/serie.py` → raiz do repositório.
PASTA_PADRAO = Path(__file__).resolve().parents[3] / "competencias"

MESES = (
    "janeiro", "fevereiro", "março", "abril", "maio", "junho",
    "julho", "agosto", "setembro", "outubro", "novembro", "dezembro",
)


@dataclass
class Mes:
    """Uma competência da série."""

    competencia: str                      # AAAA-MM
    saldo: float | None = None
    a_recolher: float | None = None
    observacao: str = ""
    #: Veio da apuração que está rodando agora, e não do arquivo.
    da_apuracao: bool = False

    @property
    def nome(self) -> str:
        return MESES[int(self.competencia[5:7]) - 1]

    @property
    def vazio(self) -> bool:
        return self.saldo is None and self.a_recolher is None and not self.observacao


def caminho(ano: int, pasta: Path | str | None = None) -> Path:
    return Path(pasta or PASTA_PADRAO) / f"serie-{ano}.yaml"


def ler(ano: int, pasta: Path | str | None = None) -> dict[str, Mes]:
    """A série gravada. Arquivo ausente ou ilegível devolve a série vazia."""
    arquivo = caminho(ano, pasta)
    conteudo: dict[str, Any] = {}
    if arquivo.is_file():
        try:
            conteudo = yaml.safe_load(arquivo.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError:
            conteudo = {}

    guardados = conteudo.get("meses") or {}
    serie: dict[str, Mes] = {}
    for m in range(1, 13):
        competencia = f"{ano:04d}-{m:02d}"
        dados = guardados.get(competencia) or {}
        serie[competencia] = Mes(
            competencia=competencia,
            saldo=numero(dados.get("saldo")),
            a_recolher=numero(dados.get("a_recolher")),
            observacao=str(dados.get("observacao") or ""),
        )
    return serie


def gravar(ano: int, meses: dict[str, Mes], pasta: Path | str | None = None) -> Path:
    """Grava a série. Mês vazio não é escrito — vazio não é zero."""
    arquivo = caminho(ano, pasta)
    arquivo.parent.mkdir(parents=True, exist_ok=True)

    guardados: dict[str, dict[str, Any]] = {}
    for competencia in sorted(meses):
        mes = meses[competencia]
        if mes.vazio:
            continue
        registro: dict[str, Any] = {}
        if mes.saldo is not None:
            registro["saldo"] = round(mes.saldo, 2)
        if mes.a_recolher is not None:
            registro["a_recolher"] = round(mes.a_recolher, 2)
        if mes.observacao:
            registro["observacao"] = mes.observacao
        guardados[competencia] = registro

    texto = yaml.safe_dump(
        {"ano": ano, "atualizado_em": dt.datetime.now().strftime("%d/%m/%Y %H:%M"),
         "meses": guardados},
        allow_unicode=True, sort_keys=False, default_flow_style=False,
    )
    arquivo.write_text(
        "# Série de saldos do ano, preenchida pela janela do Apurabot.\n"
        "# Dado fiscal da empresa: fica em `competencias/`, fora do git.\n"
        "# Mês ausente é mês que ninguém preencheu — não é mês zerado.\n\n"
        + texto,
        encoding="utf-8",
    )
    return arquivo


def com_a_apuracao(
    ano: int, apuracao, pasta: Path | str | None = None
) -> dict[str, Mes]:
    """A série gravada, com o mês que está sendo apurado já preenchido.

    O valor calculado prevalece sobre o que estiver no arquivo: quem acabou de
    rodar a competência tem o número mais novo dela.
    """
    serie = ler(ano, pasta)
    competencia = apuracao.competencia
    if competencia in serie:
        serie[competencia] = Mes(
            competencia=competencia,
            saldo=apuracao.total.saldo,
            a_recolher=sum(f.a_recolher for f in apuracao.filiais.values()),
            observacao=serie[competencia].observacao,
            da_apuracao=True,
        )
    return serie


def de_dados(ano: int, recebidos: list[dict[str, Any]]) -> dict[str, Mes]:
    """Monta a série a partir do que a janela mandou de volta."""
    serie = {f"{ano:04d}-{m:02d}": Mes(competencia=f"{ano:04d}-{m:02d}")
             for m in range(1, 13)}
    for item in recebidos or []:
        competencia = str(item.get("competencia") or "")
        if competencia not in serie:
            continue
        serie[competencia] = Mes(
            competencia=competencia,
            saldo=numero(item.get("saldo")),
            a_recolher=numero(item.get("a_recolher")),
            observacao=str(item.get("observacao") or "").strip()[:200],
        )
    return serie
