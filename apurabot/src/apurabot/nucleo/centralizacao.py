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

Os saldos chegam aqui na convenção de caixa da apuração: **positivo é credor,
negativo é devedor.** Por isso "transferir o saldo devedor" é transferir um
valor negativo.

O mecanismo diz como a transferência entra na conta gráfica:

    nfe                   a transferência só existe pela NF-e emitida pelo
                          estabelecimento centralizado
    ajuste_de_apuracao    a transferência é lançamento no Registro de Apuração —
                          linha 002 quando a centralizadora recebe saldo devedor,
                          linha 006 quando recebe saldo credor

**Lançamento de ajuste e NF-e não são alternativas.** Onde a UF exige a nota,
ela continua sendo emitida — só que **depois** do fim do mês, porque é o
resultado da apuração que a origina, e ela não retroage. Quem fecha a
competência é o lançamento; a nota formaliza e vai escriturada no mês seguinte.
Por isso `emite_nfe` é campo próprio, e não o contrário de `mecanismo`.

**O crédito transferido tem teto: o saldo devedor da centralizadora.** Ele
existe para compensar, e o que passa disso fica onde está — a competência
observada mostra a centralizadora recebendo exatamente o crédito de que
precisava para zerar, e nem um centavo além. O saldo devedor não tem teto: a
centralizadora assume a dívida do grupo para recolher de uma vez só.

Quem centraliza, quem é centralizado, o que se transfere, com qual teto e por
qual mecanismo estão em `parametros/filiais.yaml`, nunca aqui.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..formato import reais
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
    emite_nfe: bool = False
    cfop_sugerido: list[int] = field(default_factory=list)
    #: Crédito que não coube no saldo devedor da centralizadora e ficou aqui.
    retido_pelo_teto: float = 0.0

    @property
    def saldo_residual(self) -> float:
        """O que fica no estabelecimento — o retido pelo teto está aqui."""
        return self.saldo_individual - self.valor_transferido

    @property
    def confere(self) -> bool:
        """Identidade da camada: nada se perde na transferência."""
        soma = self.valor_transferido + self.saldo_residual
        return abs(soma - self.saldo_individual) < 0.005

    @property
    def instrucao(self) -> str:
        """O que o time fiscal precisa fazer depois de fechar a competência."""
        if not self.valor_transferido:
            if self.retido_pelo_teto:
                return (
                    f"{self.origem}: saldo credor de "
                    f"{reais(self.saldo_individual)} — nada a transferir, porque "
                    f"{self.destino} não fechou com saldo devedor a compensar"
                )
            return (
                f"{self.origem}: saldo {reais(self.saldo_individual)} — "
                "nada a transferir nesta competência"
            )
        sentido = "devedor" if self.valor_transferido < 0 else "credor"
        partes = [
            f"{self.origem} → {self.destino}: transferir saldo {sentido} de "
            f"{reais(abs(self.valor_transferido))} por "
            + MECANISMOS.get(self.mecanismo, self.mecanismo)
        ]
        if self.emite_nfe:
            cfop = (
                f", CFOP {' ou '.join(str(c) for c in self.cfop_sugerido)}"
                if self.cfop_sugerido else ""
            )
            partes.append(
                f"e emitir a NF-e de transferência de saldo{cfop} — ela nasce do "
                "resultado da apuração, então sai depois do fechamento e vai "
                "escriturada na competência seguinte"
            )
        if self.retido_pelo_teto:
            partes.append(
                f"o crédito de {reais(self.retido_pelo_teto)} que passou do "
                f"saldo devedor de {self.destino} fica onde está"
            )
        return "; ".join(partes)


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
        """Positivo = crédito do grupo a transportar; negativo = a recolher."""
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
            f"Saldo próprio da centralizadora: {reais(self.saldo_proprio)}",
        ]
        for t in self.transferencias:
            teto = (
                f"  (teto: {reais(t.retido_pelo_teto)} de crédito não coube no "
                "saldo devedor da centralizadora)" if t.retido_pelo_teto else ""
            )
            linhas.append(
                f"{t.origem}: saldo {reais(t.saldo_individual)} → transfere "
                f"{reais(t.valor_transferido)}, residual {reais(t.saldo_residual)}"
                + teto
            )
        linhas.append(f"Recebido pela centralizadora: {reais(self.total_recebido)}")
        linhas.append(f"Saldo final do grupo: {reais(self.saldo_final)}")
        return linhas


def regras(params: Parametros) -> dict[str, dict[str, Any]]:
    return params.filiais.get("regras_de_centralizacao") or {}


def debito_recebido_por(
    resultados: list[ResultadoCentralizacao], estabelecimento: str
) -> float:
    """Débito que um estabelecimento assume por ser centralizador.

    É a linha 002 do Registro de Apuração da centralizadora — "recebimento de
    saldo devedor do estabelecimento centralizador" — quando o mecanismo da UF
    é o ajuste de apuração.

    Devolve um valor **positivo**, porque no livro o débito é positivo: aqui a
    convenção de caixa da apuração é trocada pela da conta gráfica.

    O caminho inverso — o centralizado com saldo credor — não está modelado.
    Ele seria crédito da centralizadora, linha 006, e nenhuma competência
    observada o produziu. Ver decisão pendente nº 7.
    """
    return sum(
        -t.valor_transferido
        for r in resultados
        if r.centralizadora == estabelecimento
        and r.mecanismo == AJUSTE_DE_APURACAO
        for t in r.transferencias
        if t.valor_transferido < 0
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
        emite_nfe = bool(regra.get("emite_nfe", mecanismo == NFE))
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

        # O crédito transferido para de compensar quando a dívida da
        # centralizadora acaba. O teto é consumido na ordem do cadastro — com
        # dois centralizados credores e dívida para um só, é o primeiro que
        # transfere. Nenhuma competência observada chegou aí; quando chegar, a
        # ordem tem que ser decidida em vez de herdada do arquivo.
        teto = max(-resultado.saldo_proprio, 0.0)

        for nome in _centralizados(cadastro, uf):
            saldo = saldos.get(nome)
            if saldo is None:
                continue
            valor = _transferivel(saldo, transfere)
            retido = 0.0
            if valor > 0:                       # crédito: respeita o teto
                cabe = min(valor, teto)
                retido, valor = valor - cabe, cabe
                teto -= cabe
            resultado.transferencias.append(
                Transferencia(
                    origem=nome,
                    destino=centralizadora,
                    saldo_individual=saldo,
                    valor_transferido=valor,
                    mecanismo=mecanismo,
                    emite_nfe=emite_nfe,
                    cfop_sugerido=cfops,
                    retido_pelo_teto=retido,
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
    """Na convenção de caixa, devedor é negativo e credor é positivo."""
    if transfere == SALDO_INTEGRAL:
        return saldo
    if transfere == SALDO_DEVEDOR:
        return saldo if saldo < 0 else 0.0
    return saldo if saldo > 0 else 0.0
