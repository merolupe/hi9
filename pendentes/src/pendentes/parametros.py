"""A carga de fábrica versionada e a base viva que fica fora do git.

Mesma arquitetura do Fiscalbot, pelo mesmo motivo. Dois endereços:

| Onde | O que tem | Versionado? |
|---|---|---|
| `pendentes/parametros_de_fabrica.yaml` | valores de partida, **sem dado da empresa** | sim |
| `dados/pendentes/parametros.yaml` | a base viva, editada pela tela | não |

Na primeira abertura a base é semeada da fábrica. Dali em diante quem manda é
a base: atualizar a fábrica não mexe em quem já está rodando.

**O que nunca entra na fábrica:** unidade, filial e guardião. São nome e CNPJ
reais — dado da empresa, regra nº 1. Numa máquina nova nascem vazios e são
cadastrados na tela, exatamente como as listas de parceiros do Fiscalbot.

A regra nº 2 do `CLAUDE.md` fala de **regra tributária**, e nada aqui é regra
tributária: não há alíquota, não há base, não há crédito. O que vale é o
princípio por trás dela — *o que o time fiscal muda sem precisar de
desenvolvedor não pode morar em `.py`* —, que é mais exigente, não menos.
"""
from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from . import cabecalho as cab
from . import papeis as pap
from .farol import tabela_de

#: A carga de fábrica, versionada, ao lado do projeto.
FABRICA = Path(__file__).resolve().parents[2] / "parametros_de_fabrica.yaml"

#: As seções que a tela edita em fatias — `gravar` mescla, nunca substitui.
SECOES = ("confronto_servicos", "semana", "farol", "roteamento", "categorias",
          "unidades", "filiais", "guardioes", "papeis", "colunas")


def _raiz() -> Path:
    for pasta in Path(__file__).resolve().parents:
        if (pasta / "vendor" / "openpyxl").is_dir():
            return pasta
    return Path(__file__).resolve().parents[3]


def caminho_da_base() -> Path:
    """A base viva do aplicativo. Fora do git, como `dados/fiscalbot/`."""
    return _raiz() / "dados" / "pendentes" / "parametros.yaml"


# -- carregar e gravar -----------------------------------------------------

def carregar_fabrica(caminho: Path | None = None) -> dict[str, Any]:
    caminho = Path(caminho) if caminho else FABRICA
    if not caminho.is_file():                            # pragma: no cover
        return {}
    return yaml.safe_load(caminho.read_text(encoding="utf-8")) or {}


def carregar(caminho: Path | None = None) -> dict[str, Any]:
    """A base viva. Semeia da carga de fábrica na primeira vez."""
    caminho = Path(caminho) if caminho else caminho_da_base()
    if caminho.is_file():
        dados = yaml.safe_load(caminho.read_text(encoding="utf-8")) or {}
        # A base de uma versão antiga pode não ter uma seção nova. Ela vem da
        # fábrica, e o que a base já tem continua valendo.
        de_fabrica = carregar_fabrica()
        for secao, valor in de_fabrica.items():
            dados.setdefault(secao, valor)
        return dados
    return carregar_fabrica()


def gravar(parcial: dict[str, Any], responsavel: str | None = None,
           caminho: Path | None = None) -> Path:
    """Mescla o que a tela mandou na base, e carimba quem gravou e quando.

    **Mescla, nunca substitui.** Cada tela edita uma fatia — a de mercadorias
    não conhece os TOPs de serviço, e mandar o arquivo inteiro de volta faria
    uma tela apagar o que a outra cadastrou.

    O carimbo é o que substitui, dentro do aplicativo, o histórico que o git
    daria: sem ele ninguém sabe de onde veio um parâmetro que mudou.
    """
    caminho = Path(caminho) if caminho else caminho_da_base()
    dados = carregar(caminho)
    for secao, valor in parcial.items():
        dados[secao] = valor
    dados["atualizado_em"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    dados["atualizado_por"] = (
        responsavel or os.environ.get("USERNAME") or os.environ.get("USER") or "?"
    )
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(
        yaml.safe_dump(dados, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    return caminho


# -- as vistas que o resto do projeto consome ------------------------------

def secao(dados: dict[str, Any], nome: str, padrao: Any = None) -> Any:
    valor = dados.get(nome)
    return padrao if valor is None else valor


def colunas_de(dados: dict[str, Any], fonte: str) -> tuple[cab.Exigencia, ...]:
    """As exigências de coluna de um relatório, com sinônimos e obrigatoriedade."""
    return cab.exigencias_de((dados.get("colunas") or {}).get(fonte) or [])


def papeis_de(dados: dict[str, Any], dominio: str = "") -> tuple[pap.Papel, ...]:
    """Os papéis de arquivo esperados, do domínio pedido."""
    return pap.papeis_de(dados.get("papeis") or [], dominio)


def farol_de(dados: dict[str, Any], qual: str):
    """A tabela de códigos de emoji: `pedido` ou `semaforo`."""
    return tabela_de((dados.get("farol") or {}).get(qual) or [])


def unidades(dados: dict[str, Any]) -> list[dict]:
    """A tabela de palavras-chave de unidade, na ordem em que foi cadastrada.

    Quem for aplicá-la passa por `tabelas.por_ordem` — a ordem é a regra,
    porque `CORUMB` tem de ser testado antes de `GUAR`.
    """
    return list(dados.get("unidades") or [])


def roteamento(dados: dict[str, Any]) -> list[dict]:
    """As condições de roteamento de mercadorias, como cadastradas."""
    return list(dados.get("roteamento") or [])
