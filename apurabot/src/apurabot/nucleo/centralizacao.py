"""Camada 9 — centralização e transferência de saldo.

Onde a UF admite apuração centralizada, cada estabelecimento apura o seu saldo
e o transfere para a centralizadora, que consolida e apura o resultado do grupo.

**A transferência é consequência da apuração, não insumo dela.** O documento que
a formaliza — NF-e ou lançamento de ajuste — só pode ser emitido depois que a
competência fechou, e vai escriturado na competência seguinte. Por isso esta
camada não cobra documento dentro do livro que está sendo apurado: ela **emite a
instrução** do que precisa ser transferido, com valor, sentido e mecanismo.

O que a camada garante:

    saldo individual = valor transferido + saldo residual
    recebido pela centralizadora = soma do transferido pelos demais

O mecanismo muda com a UF:

    nfe                   a transferência é documentada por NF-e emitida pelo
                          estabelecimento centralizado
    ajuste_de_apuracao    a transferência é lançamento no Registro de Apuração —
                          débito na centralizadora, crédito no centralizado —
                          sem documento fiscal próprio

Quem centraliza, quem é centralizado, o que se transfere e por qual mecanismo
estão em `parametros/filiais.yaml`, nunca aqui.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..parametros import Parametros

# O que o estabelecimento centralizado passa para a centralizadora.
SALDO_INTEGRAL = "saldo_integral"        # devedor e credor
SALDO_DEVEDOR = "saldo_devedor"          # só quando deve
SALDO_CREDOR = "saldo_credor"            # só quando tem crédito

# Como a transferência se formaliza.
NFE = "nfe"
AJUSTE_DE_APURACAO = "ajuste_de_apuracao"

MECANISMOS = {
    NFE: "NF-e de transferência de saldo emitida pelo estabelecimento",
    AJUSTE_DE_APURACAO: "lançamento de ajuste no Registro de Apuração",
}


class CentralizacaoDesconhecida(Exception):
    """A regra de centralização não existe ou não é reconhecida."""


@dataclass
class Transferencia:
    """O que um estabelecimento centralizado passa para a centralizadora."""

    origem: str
    destino: str
    saldo_individual: float = 0.0
    valor_transferido: float = 0.0
    mecanismo: str = NFE
    cfop_sugerido: list[int] = field(default_factory=list)

    @property
    def saldo_residual(self) -> float:
        return self.saldo_individual - self.valor_transferido

    @property
    def confere(self) -> bool:
        """Identidade da camada: nada se perde na transferência."""
        soma = self.valor_transferido + self.saldo_residual
        return abs(soma - self.saldo_individual) < 0.005

    @property
    def instrucao(self) -> str:
        """O que o time fiscal precisa emitir depois de fechar a competência."""
        if not self.valor_transferido:
            return (
                f"{self.origem}: saldo {self.saldo_individual:,.2f} — "
                "nada a transferir nesta competência"
            )
        sentido = "devedor" if self.valor_transferido > 0 else "credor"
        como = (
            f"NF-e de transferência de saldo, CFOP "
            f"{' ou '.join(str(c) for c in self.cfop_sugerido)}"
            if self.mecanismo == NFE and self.cfop_sugerido
            else MECANISMOS.get(self.mecanismo, self.mecanismo)
        )
        return (
            f"{self.origem} → {self.destino}: transferir saldo {sentido} de "
            f"{abs(self.valor_transferido):,.2f} por {como}"
        )


@dataclass
class ResultadoCentralizacao:
    uf: str
    centralizadora: str
    regra: str = ""
    mecanismo: str = NFE
    homologado: bool = False
    saldo_proprio: float = 0.0
    transferencias: list[Transferencia] = field(default_factory=list)

    @property
    def total_recebido(self) -> float:
        return sum(t.valor_transferido for t in self.transferencias)

    @property
    def saldo_final(self) -> float:
        """Positivo = a recolher pelo grupo; negativo = saldo credor a transportar."""
        return self.saldo_proprio + self.total_recebido

    @property
    def confere(self) -> bool:
        return all(t.confere for t in self.transferencias)

    @property
    def instrucoes(self) -> list[str]:
        """As transferências a emitir depois do encerramento da competência."""
        return [t.instrucao for t in self.transferencias if t.valor_transferido]

    @property
    def memoria(self) -> list[str]:
        linhas = [
            f"Centralização de {self.uf} em {self.centralizadora}",
            f"Regra de transferência: {self.regra} por "
            + MECANISMOS.get(self.mecanismo, self.mecanismo)
            + ("" if self.homologado else "  (NÃO HOMOLOGADA)"),
            f"Saldo próprio da centralizadora: {self.saldo_proprio:,.2f}",
        ]
        for t in self.transferencias:
            linhas.append(
                f"{t.origem}: saldo {t.saldo_individual:,.2f} → transfere "
                f"{t.valor_transferido:,.2f}, residual {t.saldo_residual:,.2f}"
            )
        linhas.append(f"Recebido pela centralizadora: {self.total_recebido:,.2f}")
        linhas.append(f"Saldo final do grupo: {self.saldo_final:,.2f}")
        return linhas


def regras(params: Parametros) -> dict[str, dict[str, Any]]:
    return params.filiais.get("regras_de_centralizacao") or {}


def recebido_por(
    resultados: list[ResultadoCentralizacao], estabelecimento: str
) -> float:
    """Saldo que um estabelecimento recebe por ser centralizador.

    É a linha 002 do Registro de Apuração da centralizadora — "recebimento de
    saldo devedor do estabelecimento centralizador" — quando o mecanismo da UF
    é o ajuste de apuração.
    """
    return sum(
        r.total_recebido
        for r in resultados
        if r.centralizadora == estabelecimento
        and r.mecanismo == AJUSTE_DE_APURACAO
    )


def calcular(saldos: dict[str, float], params: Parametros) -> list[ResultadoCentralizacao]:
    """Consolida os saldos por grupo de centralização.

    `saldos` é {estabelecimento: saldo individual}, já apurado.
    """
    cadastro = {
        " ".join(str(f["nome"]).split()): f
        for f in params.filiais.get("filiais") or []
    }
    resultados: list[ResultadoCentralizacao] = []

    for nome_regra, regra in regras(params).items():
        uf = regra.get("uf", "")
        transfere = regra.get("transfere", SALDO_INTEGRAL)
        if transfere not in (SALDO_INTEGRAL, SALDO_DEVEDOR, SALDO_CREDOR):
            raise CentralizacaoDesconhecida(
                f"regra {nome_regra!r}: `transfere` {transfere!r} não é reconhecido "
                f"— os válidos são {SALDO_INTEGRAL}, {SALDO_DEVEDOR} e {SALDO_CREDOR}"
            )
        mecanismo = regra.get("mecanismo", NFE)
        if mecanismo not in MECANISMOS:
            raise CentralizacaoDesconhecida(
                f"regra {nome_regra!r}: `mecanismo` {mecanismo!r} não é reconhecido "
                f"— os válidos são {NFE} e {AJUSTE_DE_APURACAO}"
            )

        centralizadora = _papel(cadastro, uf, "centralizadora")
        if centralizadora is None:
            raise CentralizacaoDesconhecida(
                f"regra {nome_regra!r}: nenhuma filial de {uf} tem papel "
                "`centralizadora` em filiais.yaml"
            )

        resultado = ResultadoCentralizacao(
            uf=uf,
            centralizadora=centralizadora,
            regra=transfere,
            mecanismo=mecanismo,
            homologado=bool(regra.get("homologado", False)),
            saldo_proprio=saldos.get(centralizadora, 0.0),
        )
        cfops = [int(c) for c in (regra.get("cfop_transferencia") or [])]
        for nome in _centralizados(cadastro, uf):
            saldo = saldos.get(nome)
            if saldo is None:
                continue
            resultado.transferencias.append(
                Transferencia(
                    origem=nome,
                    destino=centralizadora,
                    saldo_individual=saldo,
                    valor_transferido=_transferivel(saldo, transfere),
                    mecanismo=mecanismo,
                    cfop_sugerido=cfops,
                )
            )
        resultados.append(resultado)

    return resultados


def _papel(cadastro: dict[str, Any], uf: str, papel: str) -> str | None:
    for nome, ficha in cadastro.items():
        c = ficha.get("centralizacao") or {}
        if ficha.get("uf") == uf and c.get("participa") and c.get("papel") == papel:
            return nome
    return None


def _centralizados(cadastro: dict[str, Any], uf: str) -> list[str]:
    return [
        nome
        for nome, ficha in cadastro.items()
        if ficha.get("uf") == uf
        and (ficha.get("centralizacao") or {}).get("participa")
        and (ficha.get("centralizacao") or {}).get("papel") == "centralizado"
    ]


def _transferivel(saldo: float, transfere: str) -> float:
    if transfere == SALDO_INTEGRAL:
        return saldo
    if transfere == SALDO_DEVEDOR:
        return saldo if saldo > 0 else 0.0
    return saldo if saldo < 0 else 0.0
