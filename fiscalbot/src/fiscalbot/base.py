"""Onde a base de regras mora, e como ela é lida e gravada.

A base **não é versionada**. Ela é do aplicativo, editada pela tela da Central,
e mora em `dados/fiscalbot/base.yaml`, na raiz do repositório — pasta ignorada
pelo git, como `competencias/`. O motivo é duplo: as listas de parceiros
trazem código e nome de fornecedor real (dado da empresa, regra nº 1), e o time
fiscal precisa alterar regra sem passar por commit.

O que **é** versionado é a **carga de fábrica** (`regras_de_fabrica.yaml`, ao
lado deste pacote): as 64 regras, os parâmetros e a matriz de alíquotas, sem
nenhum dado de empresa. Ela existe para a ferramenta funcionar na primeira vez
que abre numa máquina nova — sem ela, o Fiscalbot nasceria sem nenhuma regra e
alguém teria que redigitar 64.

Na primeira abertura a base é semeada a partir da carga de fábrica. Dali em
diante quem manda é a base: atualizar a carga de fábrica não mexe em quem já
está rodando.

**As listas de parceiros não vêm na carga de fábrica.** Numa máquina nova elas
nascem vazias e precisam ser preenchidas na tela — são os únicos dados que o
repositório não pode carregar por você.
"""
from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from .modelo import BaseDeRegras, Parametros, Parceiro, Regra

#: A carga de fábrica, versionada, ao lado do projeto.
FABRICA = Path(__file__).resolve().parents[2] / "regras_de_fabrica.yaml"


def _raiz() -> Path:
    for pasta in Path(__file__).resolve().parents:
        if (pasta / "vendor" / "openpyxl").is_dir():
            return pasta
    return Path(__file__).resolve().parents[3]


#: A base viva do aplicativo. Fora do git.
def caminho_da_base() -> Path:
    return _raiz() / "dados" / "fiscalbot" / "base.yaml"


# -- de dicionário para objeto e de volta ----------------------------------

def _regra_de(d: dict[str, Any]) -> Regra:
    cfop = d.get("cfop") or []
    if isinstance(cfop, str):
        cfop = cfop.split(";")
    return Regra(
        id=str(d.get("id", "")).strip(),
        operacao=str(d.get("operacao", "")).strip(),
        ativa=bool(d.get("ativa", True)),
        es=str(d.get("es", "") or "").strip(),
        especie=str(d.get("especie", "") or "").strip(),
        cfop=tuple(str(c).strip() for c in cfop),
        cond_produto=str(d.get("cond_produto", "") or "").strip(),
        cond_par_uf=str(d.get("cond_par_uf", "") or "").strip(),
        cond_parceiro=str(d.get("cond_parceiro", "") or "").strip(),
        esp_cst=str(d.get("esp_cst", "") or "").strip(),
        esp_icms=str(d.get("esp_icms", "") or "").strip(),
        esp_aliq=str(d.get("esp_aliq", "") or "").strip(),
        esp_carga=str(d.get("esp_carga", "") or "").strip(),
        esp_outros=str(d.get("esp_outros", "") or "").strip(),
        base_legal=str(d.get("base_legal", "") or "").strip(),
        ultima_revisao=str(d.get("ultima_revisao", "") or "").strip(),
    )


def _dicionario_de(regra: Regra) -> dict[str, Any]:
    return {
        "id": regra.id,
        "operacao": regra.operacao,
        "ativa": regra.ativa,
        "es": regra.es,
        "especie": regra.especie,
        "cfop": list(regra.cfop),
        "cond_produto": regra.cond_produto,
        "cond_par_uf": regra.cond_par_uf,
        "cond_parceiro": regra.cond_parceiro,
        "esp_cst": regra.esp_cst,
        "esp_icms": regra.esp_icms,
        "esp_aliq": regra.esp_aliq,
        "esp_carga": regra.esp_carga,
        "esp_outros": regra.esp_outros,
        "base_legal": regra.base_legal,
        "ultima_revisao": regra.ultima_revisao,
    }


def _parceiros_de(bruto: Any) -> list[Parceiro]:
    saida = []
    for item in bruto or []:
        if isinstance(item, dict):
            saida.append(Parceiro(str(item.get("codigo", "")).strip(),
                                  str(item.get("descricao", "") or "").strip()))
        else:
            saida.append(Parceiro(str(item).strip()))
    return saida


def de_dicionario(d: dict[str, Any]) -> BaseDeRegras:
    p = d.get("parametros") or {}
    parceiros = d.get("parceiros") or {}
    return BaseDeRegras(
        regras=[_regra_de(r) for r in (d.get("regras") or [])],
        parametros=Parametros(
            tolerancia_carga=float(p.get("tolerancia_carga", 0.05)),
            cst_exigem_icms_positivo=tuple(
                str(c).strip() for c in (p.get("cst_exigem_icms_positivo") or [])
            ),
            tabelas={
                str(nome).upper(): tuple(str(v).strip() for v in valores)
                for nome, valores in (p.get("tabelas") or {}).items()
            },
            sinonimos={
                str(campo).upper(): tuple(str(v).strip() for v in valores)
                for campo, valores in (p.get("sinonimos") or {}).items()
            },
        ),
        aliquotas={
            str(o).upper(): {str(dst).upper(): float(v) for dst, v in linha.items()}
            for o, linha in (d.get("aliquotas") or {}).items()
        },
        parceiros_simples_nacional=_parceiros_de(parceiros.get("simples_nacional")),
        parceiros_cavaco=_parceiros_de(parceiros.get("cavaco")),
        atualizado_em=str(d.get("atualizado_em", "") or ""),
        atualizado_por=str(d.get("atualizado_por", "") or ""),
    )


def para_dicionario(base: BaseDeRegras, *, com_parceiros: bool = True) -> dict[str, Any]:
    """`com_parceiros=False` produz o conteúdo publicável — sem dado da empresa."""
    d: dict[str, Any] = {
        "atualizado_em": base.atualizado_em,
        "atualizado_por": base.atualizado_por,
        "parametros": {
            "tolerancia_carga": base.parametros.tolerancia_carga,
            "cst_exigem_icms_positivo": list(base.parametros.cst_exigem_icms_positivo),
            "tabelas": {n: list(v) for n, v in base.parametros.tabelas.items()},
            "sinonimos": {c: list(v) for c, v in base.parametros.sinonimos.items()},
        },
        "aliquotas": {o: dict(linha) for o, linha in base.aliquotas.items()},
        "regras": [_dicionario_de(r) for r in base.regras],
    }
    if com_parceiros:
        d["parceiros"] = {
            "simples_nacional": [
                {"codigo": p.codigo, "descricao": p.descricao}
                for p in base.parceiros_simples_nacional
            ],
            "cavaco": [
                {"codigo": p.codigo, "descricao": p.descricao}
                for p in base.parceiros_cavaco
            ],
        }
    return d


# -- carregar e gravar -----------------------------------------------------

def carregar(caminho: Path | None = None) -> BaseDeRegras:
    """A base viva. Semeia da carga de fábrica na primeira vez."""
    caminho = caminho or caminho_da_base()
    if caminho.is_file():
        return de_dicionario(yaml.safe_load(caminho.read_text(encoding="utf-8")) or {})
    return carregar_fabrica()


def carregar_fabrica(caminho: Path | None = None) -> BaseDeRegras:
    caminho = caminho or FABRICA
    if not caminho.is_file():
        return BaseDeRegras()
    return de_dicionario(yaml.safe_load(caminho.read_text(encoding="utf-8")) or {})


def gravar(base: BaseDeRegras, caminho: Path | None = None,
           responsavel: str | None = None) -> Path:
    """Grava a base e carimba quem alterou e quando.

    O carimbo é o que substitui, dentro do aplicativo, o histórico que o git
    daria: sem ele ninguém sabe de onde veio uma regra que mudou.
    """
    caminho = caminho or caminho_da_base()
    base.atualizado_em = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    base.atualizado_por = responsavel or os.environ.get("USERNAME") or \
        os.environ.get("USER") or "?"
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(
        yaml.safe_dump(para_dicionario(base), allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    return caminho
