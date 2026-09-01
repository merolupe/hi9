"""O que a janela do navegador mostra.

Traduz a apuração para estruturas simples — dicionários de texto e número —
que a página desenha. Nada de regra tributária aqui: se um valor precisa de
conta, a conta é de outra camada.
"""
from __future__ import annotations

from typing import Any

from .. import __version__
from ..apuracao import Apuracao
from ..base_tratada import BaseTratada
from ..conferencia import ROTULO_DA_ATIVIDADE
from ..nucleo import registro as reg


def montar(base: BaseTratada, apuracao: Apuracao, registros: list) -> dict[str, Any]:
    """O painel inteiro, pronto para virar JSON."""
    resumo = base.resumo()
    return {
        "versao": __version__,
        "competencia": resumo["competencia"],
        "periodo": resumo["periodo"],
        "arquivo": resumo["arquivo"],
        "sha256": resumo["sha256"],
        "gerado_em": resumo["gerado_em"],
        "linhas_no_livro": resumo["linhas_no_livro"],
        "linhas_relevantes": resumo["linhas_relevantes"],
        "alertas": resumo["alertas"],
        "pode_encerrar": _pode_encerrar(base, apuracao),
        "pendencias": _pendencias(base, apuracao),
        "filiais": [_filial(f) for f in _em_ordem(apuracao)],
        "registros": [_registro(r) for r in registros],
        "transferencias": _transferencias(apuracao),
        "beneficios": [_beneficio(f) for f in _em_ordem(apuracao) if f.beneficio],
    }


def _em_ordem(apuracao: Apuracao):
    return sorted(apuracao.filiais.values(), key=lambda f: (f.uf, f.estabelecimento))


def _pode_encerrar(base: BaseTratada, apuracao: Apuracao) -> bool:
    return base.pode_encerrar and not apuracao.sem_regra_de_atividade


def _pendencias(base: BaseTratada, apuracao: Apuracao) -> list[dict[str, Any]]:
    """O que bloqueia o encerramento, com onde olhar."""
    itens: list[dict[str, Any]] = []
    for tratada in base.com_pendencia[:50]:
        dados = tratada.origem.dados
        itens.append({
            "onde": f"linha {tratada.origem.linha_origem}",
            "estabelecimento": str(dados.get("estabelecimento") or ""),
            "detalhe": tratada.pendencias[0],
        })
    restantes = len(base.com_pendencia) - len(itens)
    if restantes > 0:
        itens.append({
            "onde": "",
            "estabelecimento": "",
            "detalhe": f"… e mais {restantes} na aba PENDÊNCIAS da planilha.",
        })
    for filial in apuracao.sem_regra_de_atividade:
        somas = filial.atividades_sem_regra
        itens.append({
            "onde": "atividade",
            "estabelecimento": filial.estabelecimento,
            "detalhe": (
                f"{somas.linhas} linha(s) não casaram com nenhuma atividade — "
                "cadastre o CFOP em regimes.yaml, bloco `atividades`"
            ),
        })
    return itens


def _filial(filial) -> dict[str, Any]:
    return {
        "estabelecimento": filial.estabelecimento,
        "uf": filial.uf,
        "regime": filial.regime,
        "credito_bruto": filial.credito_bruto,
        "estorno": filial.estorno + filial.credito_indevido,
        "credito_mantido": filial.credito_mantido,
        "debito": filial.debito,
        "beneficio": filial.credito_presumido,
        "saldo": filial.saldo,
        "a_recolher": filial.a_recolher,
        "atividades": [
            {
                "nome": ROTULO_DA_ATIVIDADE.get(nome, nome),
                "credito_bruto": totais.credito_bruto,
                "estorno": totais.estorno,
                "debito": totais.debito,
            }
            for nome, totais in _atividades_em_ordem(filial)
        ],
    }


def _atividades_em_ordem(filial):
    from ..nucleo.atividade import ORDEM

    conhecidas = [n for n in ORDEM if n in filial.por_atividade]
    restantes = sorted(n for n in filial.por_atividade if n not in conhecidas)
    return [(n, filial.por_atividade[n]) for n in conhecidas + restantes]


def _registro(registro: reg.Registro) -> dict[str, Any]:
    return {
        "estabelecimento": registro.estabelecimento,
        "uf": registro.uf,
        "gerencial": registro.gerencial,
        "aguarda_ajustes": registro.aguarda_ajustes,
        "entradas": _lado(registro.entradas),
        "saidas": _lado(registro.saidas),
        "resumo": [
            {
                "codigo": f"{item.codigo:03d}",
                "rotulo": item.rotulo,
                "valor": item.valor,
                "aguarda_ajuste": item.aguarda_ajuste,
                "discriminacao": [
                    {"descricao": d, "valor": v} for d, v in item.discriminacao
                ],
            }
            for item in registro.resumo
        ],
    }


def _lado(bloco: reg.Bloco) -> dict[str, Any]:
    return {
        "lado": bloco.lado,
        "subtotais": [
            {"grupo": grupo, "valores": list(bloco.subtotal(grupo).as_tuple())}
            for grupo in bloco.grupos()
        ],
        "total": list(bloco.total.as_tuple()),
    }


def _transferencias(apuracao: Apuracao) -> list[dict[str, Any]]:
    grupos = []
    for grupo in apuracao.centralizacao:
        grupos.append({
            "uf": grupo.uf,
            "centralizadora": grupo.centralizadora,
            "homologado": grupo.homologado,
            "saldo_proprio": grupo.saldo_proprio,
            "total_recebido": grupo.total_recebido,
            "saldo_final": grupo.saldo_final,
            "instrucoes": grupo.instrucoes,
        })
    return grupos


def _beneficio(filial) -> dict[str, Any]:
    return {
        "estabelecimento": filial.estabelecimento,
        "credito_presumido": filial.credito_presumido,
        "fadefe": filial.fadefe,
        "memoria": list(filial.beneficio.memoria),
    }
