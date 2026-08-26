"""Camada 9 — centralização e transferência de saldo.

Onde a UF admite apuração centralizada, cada estabelecimento apura o seu saldo
e o transfere para a centralizadora, que consolida e apura o resultado do grupo.
A transferência é documentada por NF-e, e é essa NF-e que esta camada cobra.

O que a camada garante:

    saldo individual = valor transferido + saldo residual
    recebido pela centralizadora = soma do transferido pelos demais

Quem centraliza, quem é centralizado e o que se transfere estão em
`parametros/filiais.yaml`, nunca aqui.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..parametros import Parametros

# O que o estabelecimento centralizado passa para a centralizadora.
SALDO_INTEGRAL = "saldo_integral"        # devedor e credor
SALDO_DEVEDOR = "saldo_devedor"          # só quando deve
SALDO_CREDOR = "saldo_credor"            # só quando tem crédito


class CentralizacaoDesconhecida(Exception):
    """A regra de centralização não existe ou não é reconhecida."""


@dataclass
class DocumentoDeTransferencia:
    """A NF-e que documenta a transferência de saldo."""

    numero: str
    emitente: str
    cfop: int | None
    valor: float


@dataclass
class Transferencia:
    """O que um estabelecimento centralizado passa para a centralizadora."""

    origem: str
    destino: str
    saldo_individual: float = 0.0
    valor_transferido: float = 0.0
    documentos: list[DocumentoDeTransferencia] = field(default_factory=list)

    @property
    def saldo_residual(self) -> float:
        return self.saldo_individual - self.valor_transferido

    @property
    def valor_documentado(self) -> float:
        return sum(d.valor for d in self.documentos)

    @property
    def confere(self) -> bool:
        """Identidade da camada: nada se perde na transferência."""
        soma = self.valor_transferido + self.saldo_residual
        return abs(soma - self.saldo_individual) < 0.005

    @property
    def pendencias(self) -> list[str]:
        """O que trava o encerramento da competência."""
        motivos: list[str] = []
        if not self.valor_transferido:
            return motivos
        if not self.documentos:
            motivos.append(
                f"{self.origem}: transferência de {self.valor_transferido:,.2f} "
                f"para {self.destino} sem NF-e escriturada"
            )
        elif abs(self.valor_documentado - self.valor_transferido) >= 0.005:
            motivos.append(
                f"{self.origem}: NF-e de transferência soma "
                f"{self.valor_documentado:,.2f}, e o saldo a transferir é "
                f"{self.valor_transferido:,.2f} — diferença de "
                f"{self.valor_documentado - self.valor_transferido:,.2f}"
            )
        return motivos


@dataclass
class ResultadoCentralizacao:
    uf: str
    centralizadora: str
    regra: str = ""
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
    def pendencias(self) -> list[str]:
        return [m for t in self.transferencias for m in t.pendencias]

    @property
    def memoria(self) -> list[str]:
        linhas = [
            f"Centralização de {self.uf} em {self.centralizadora}",
            f"Regra de transferência: {self.regra}"
            + ("" if self.homologado else "  (NÃO HOMOLOGADA)"),
            f"Saldo próprio da centralizadora: {self.saldo_proprio:,.2f}",
        ]
        for t in self.transferencias:
            linhas.append(
                f"{t.origem}: saldo {t.saldo_individual:,.2f} → transfere "
                f"{t.valor_transferido:,.2f}, residual {t.saldo_residual:,.2f}"
                + (
                    f", NF-e {', '.join(d.numero for d in t.documentos)}"
                    if t.documentos
                    else ", SEM NF-e"
                )
            )
        linhas.append(f"Recebido pela centralizadora: {self.total_recebido:,.2f}")
        linhas.append(f"Saldo final do grupo: {self.saldo_final:,.2f}")
        return linhas


def regras(params: Parametros) -> dict[str, dict[str, Any]]:
    return params.filiais.get("regras_de_centralizacao") or {}


def calcular(
    saldos: dict[str, float],
    livro,
    params: Parametros,
) -> list[ResultadoCentralizacao]:
    """Consolida os saldos por grupo de centralização.

    `saldos` é {estabelecimento: saldo individual}, e `livro` serve para achar a
    NF-e que documenta cada transferência.
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
            homologado=bool(regra.get("homologado", False)),
            saldo_proprio=saldos.get(centralizadora, 0.0),
        )
        cfops = set(regra.get("cfop_transferencia") or [])
        for nome in _centralizados(cadastro, uf):
            saldo = saldos.get(nome)
            if saldo is None:
                continue
            t = Transferencia(origem=nome, destino=centralizadora, saldo_individual=saldo)
            t.valor_transferido = _transferivel(saldo, transfere)
            t.documentos = _documentos(livro, nome, cfops)
            resultado.transferencias.append(t)
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


def _documentos(livro, emitente: str, cfops: set[int]) -> list[DocumentoDeTransferencia]:
    """NF-e de transferência de saldo emitidas pelo estabelecimento."""
    if livro is None or not cfops:
        return []
    achados = []
    for linha in livro:
        dados = linha.dados
        if " ".join(str(dados.get("estabelecimento") or "").split()) != emitente:
            continue
        if linha.cfop_int not in cfops:
            continue
        achados.append(
            DocumentoDeTransferencia(
                numero=str(dados.get("numero_nota") or dados.get("nota") or "?"),
                emitente=emitente,
                cfop=linha.cfop_int,
                valor=dados.get("valor_contabil") or 0.0,
            )
        )
    return achados
