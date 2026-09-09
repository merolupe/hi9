"""A auditoria de ponta a ponta: do relatório extraído até a planilha gravada."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from . import base as bases
from . import leitura, planilha, saida
from .auditoria import ADVERTENCIA, CONFORME, VALIDACAO_MANUAL, Achado, auditar_linha
from .leitura import MapaDeColunas
from .modelo import BaseDeRegras
from .planilha import LayoutInvalido

#: Os rótulos das seis dimensões, na ordem em que aparecem no resumo.
DIMENSOES = ("CST", "Valor ICMS", "Produto", "Alíquota", "Carga Efetiva", "Outros")


@dataclass
class Auditoria:
    """O que uma execução produziu."""

    arquivo: str
    achados: list[Achado] = field(default_factory=list)
    linhas: list[list[Any]] = field(default_factory=list)
    cabecalho: int = -1
    ultima: int = -1
    mapa: MapaDeColunas | None = None
    regras_ativas: int = 0
    executada_em: str = ""

    def __len__(self) -> int:
        return len(self.achados)

    def _quantos(self, status: str) -> int:
        return sum(1 for a in self.achados if a.status == status)

    @property
    def conformes(self) -> int:
        return self._quantos(CONFORME)

    @property
    def advertencias(self) -> int:
        return self._quantos(ADVERTENCIA)

    @property
    def validacao_manual(self) -> int:
        return self._quantos(VALIDACAO_MANUAL)

    @property
    def colunas_nao_encontradas(self) -> list[str]:
        """As colunas opcionais que faltaram — cada uma desliga uma camada."""
        if self.mapa is None:
            return []
        return [campo for campo in leitura.OPCIONAIS if not self.mapa.tem(campo)]

    def por_dimensao(self) -> list[tuple[str, int]]:
        return [
            (rotulo, sum(1 for a in self.achados if a.ocorrencias.como_lista()[k]))
            for k, rotulo in enumerate(DIMENSOES)
        ]

    def manuais_por_operacao(self) -> list[tuple[str, int]]:
        contagem: dict[str, int] = {}
        for achado in self.achados:
            if achado.status != VALIDACAO_MANUAL:
                continue
            chave = achado.operacao or "(sem operacao)"
            contagem[chave] = contagem.get(chave, 0) + 1
        return sorted(contagem.items(), key=lambda item: -item[1])

    def resumo(self) -> list[str]:
        total = len(self.achados) or 1
        return [
            f"Registros auditados: {len(self.achados)}",
            f"Conformes: {self.conformes} ({self.conformes / total * 100:.1f}%)",
            f"Advertências: {self.advertencias} "
            f"({self.advertencias / total * 100:.1f}%)",
            f"Validação manual: {self.validacao_manual} "
            f"({self.validacao_manual / total * 100:.1f}%)",
            f"Regras ativas na base: {self.regras_ativas}",
        ]


def _ultima_linha(linhas: list[list[Any]], cabecalho: int, coluna_cfop: int) -> int:
    """A última linha com CFOP preenchido.

    O relatório costuma trazer rodapé ou linha em branco no fim; o CFOP é a
    coluna que nunca falta num registro de verdade.
    """
    ultima = cabecalho
    for i in range(cabecalho + 1, len(linhas)):
        linha = linhas[i]
        if coluna_cfop < len(linha) and str(linha[coluna_cfop]).strip():
            ultima = i
    return ultima


def auditar(caminho: Path, base: BaseDeRegras | None = None,
            progresso: Callable[[int], None] | None = None) -> Auditoria:
    """Lê o relatório, audita cada registro e devolve o resultado."""
    base = base if base is not None else bases.carregar()
    if not base.ativas:
        raise LayoutInvalido(
            "Nenhuma regra ativa na base do Fiscalbot. Cadastre as regras na "
            "tela de configuração antes de auditar."
        )

    caminho = Path(caminho)
    linhas = planilha.ler(caminho)
    cabecalho = leitura.localizar_cabecalho(linhas)
    if cabecalho < 0:
        raise LayoutInvalido(
            "Não encontrei a linha de cabeçalho nas 15 primeiras linhas do "
            "arquivo. Confira se é o relatório Movimento Livros Fiscais."
        )
    mapa = leitura.mapear(linhas[cabecalho], base.parametros)
    ultima = _ultima_linha(linhas, cabecalho, mapa.posicoes["CFOP"])

    achados = []
    for i in range(cabecalho + 1, ultima + 1):
        achados.append(auditar_linha(linhas[i], mapa, base))
        if progresso and len(achados) % 500 == 0:
            progresso(len(achados))

    return Auditoria(
        arquivo=caminho.name, achados=achados, linhas=linhas,
        cabecalho=cabecalho, ultima=ultima, mapa=mapa,
        regras_ativas=len(base.ativas),
        executada_em=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    )


def nome_sugerido(arquivo: str, agora: datetime | None = None) -> str:
    agora = agora or datetime.now()
    return f"Fiscalbot_{Path(arquivo).stem}_{agora:%Y-%m-%d_%H%M}.xlsx"


def escrever(auditoria: Auditoria, destino: Path) -> Path:
    if auditoria.mapa is None:
        raise ValueError("auditoria sem mapa de colunas")
    return saida.escrever(Path(destino), auditoria.linhas, auditoria.cabecalho,
                          auditoria.ultima, auditoria.mapa, auditoria.achados)
