"""Camada 3 — equalização da carga efetiva.

A carga bruta (ICMS ÷ valor contábil) traz artefatos — 0,100315 · 0,105467 —
porque o valor contábil inclui parcelas fora da base do ICMS: frete, pedágio,
IPI, descontos. A equalização traz o valor para a carga nominal.

Aderência medida contra a classificação manual de Julho/2026: 99,87%.
Ver docs/apurabot/05-achados-julho-2026.md.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from ..ingestao import LinhaLivro
from ..parametros import Parametros
from .classificacao import casa_lancamento_sem_contabil


class Situacao(str, Enum):
    """O que aconteceu com a linha na equalização."""

    EQUALIZADA = "EQUALIZADA"                       # caso normal
    CIAP = "CIAP"                                   # crédito de ativo, sem carga
    SEM_ICMS = "SEM ICMS"                           # fora da apuração de ICMS
    CANCELADA = "CANCELADA"                         # documento cancelado
    NAO_EQUALIZADA = "CARGA NÃO EQUALIZADA"         # fora da tolerância → pendência
    SEM_BASE = "SEM BASE"                           # ICMS sem valor contábil → pendência


# Alerta emitido quando a carga cai numa faixa reconhecida mas não homologada.
ALERTA_NAO_HOMOLOGADA = "CARGA NÃO HOMOLOGADA"


@dataclass(frozen=True)
class ResultadoCarga:
    situacao: Situacao
    carga: float | None = None
    carga_bruta: float | None = None
    alerta: str | None = None
    regra: str = ""

    @property
    def relevante_para_icms(self) -> bool:
        """A linha entra na apuração de ICMS?"""
        return self.situacao in (
            Situacao.EQUALIZADA, Situacao.CIAP, Situacao.NAO_EQUALIZADA, Situacao.SEM_BASE
        )

    @property
    def e_pendencia(self) -> bool:
        return self.situacao in (Situacao.NAO_EQUALIZADA, Situacao.SEM_BASE)


def equalizar(linha: LinhaLivro, params: Parametros) -> ResultadoCarga:
    """Determina a carga efetiva nominal de uma linha do Livro Fiscal."""
    classif = params.classificacao

    if classif["relevancia_icms"].get("excluir_documento_cancelado") and linha.cancelado:
        return ResultadoCarga(Situacao.CANCELADA, regra="documento cancelado")

    icms = linha.dados.get("valor_icms") or 0.0
    if not icms:
        return ResultadoCarga(Situacao.SEM_ICMS, regra="ICMS igual a zero")

    # Lançamentos sem valor contábil vêm antes de qualquer divisão: têm ICMS
    # diferente de zero com contábil zerado, então ICMS ÷ contábil não existe.
    especial = _lancamento_sem_contabil(linha, params)
    if especial is not None:
        return especial

    contabil = linha.dados.get("valor_contabil") or 0.0
    if not contabil:
        return ResultadoCarga(
            Situacao.SEM_BASE,
            regra=(
                "ICMS diferente de zero sem valor contábil, e o lançamento não "
                "casa com nenhum item de `lancamentos_sem_contabil` — carga "
                "indeterminável"
            ),
        )

    bruta = icms / contabil * 100.0
    aliquota = linha.dados.get("aliquota_icms") or 0.0

    candidatas = params.regua_completa
    if params.limite_teto_aliquota and aliquota:
        acima = [c for c in candidatas if c <= aliquota + 1e-9]
        candidatas = acima or candidatas

    escolhida = min(candidatas, key=lambda c: abs(c - bruta))
    if abs(escolhida - bruta) > params.tolerancia:
        return ResultadoCarga(
            Situacao.NAO_EQUALIZADA,
            carga_bruta=round(bruta, 6),
            regra=(
                f"carga bruta {bruta:.4f}% a mais de {params.tolerancia}% de "
                f"qualquer valor da régua {params.regua_completa}"
            ),
        )

    tolerada = params.cargas_toleradas.get(escolhida)
    return ResultadoCarga(
        situacao=Situacao.EQUALIZADA,
        carga=escolhida,
        carga_bruta=round(bruta, 6),
        alerta=ALERTA_NAO_HOMOLOGADA if tolerada else None,
        regra=(
            f"carga bruta {bruta:.4f}% equalizada para {escolhida:g}%"
            + (" (carga tolerada, não homologada)" if tolerada else "")
        ),
    )


def _lancamento_sem_contabil(
    linha: LinhaLivro, params: Parametros
) -> ResultadoCarga | None:
    """Trata os lançamentos cuja carga não sai de `ICMS ÷ valor contábil`.

    São o crédito de ativo (CIAP) e o complemento de ICMS. Ambos chegam com
    valor contábil zerado, então a carga vem do parâmetro e não da fórmula.

    Quem reconhece cada um é `casa_lancamento_sem_contabil`, para o critério
    ser um só aqui e na classificação.
    """
    itens = params.classificacao.get("lancamentos_sem_contabil") or []
    for item in itens:
        origem = casa_lancamento_sem_contabil(linha, item)
        if origem is None:
            continue

        carga = item.get("carga_efetiva")
        descricao = item.get("descricao", item.get("categoria", ""))
        pendente = "" if item.get("homologado", True) else " (regra não homologada)"

        if carga == "CIAP":
            return ResultadoCarga(
                Situacao.CIAP, regra=f"{origem} — {descricao}{pendente}"
            )
        return ResultadoCarga(
            situacao=Situacao.EQUALIZADA,
            carga=float(carga),
            alerta=None if item.get("homologado", True) else ALERTA_NAO_HOMOLOGADA,
            regra=(
                f"{origem} — {descricao}: carga {float(carga):g}% vem do "
                f"parâmetro, sem valor contábil para calcular{pendente}"
            ),
        )
    return None
