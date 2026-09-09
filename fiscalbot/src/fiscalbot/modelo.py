"""O que é uma regra, e o que é a base de regras.

A base tem três naturezas de conteúdo, e elas não se misturam:

* **regra tributária** — as regras, os parâmetros do motor e a matriz de
  alíquotas. Acompanham legislação, não a empresa. É o que vai na carga de
  fábrica (`regras_de_fabrica.yaml`), versionada no git;
* **dado da empresa** — as listas de parceiros (Simples Nacional e cavaco),
  que trazem código e nome de fornecedor real. **Nunca** vão para o git;
* **trilha** — quem alterou a base e quando. Fica no aplicativo, e é o que
  substitui o histórico que o git daria.

Quem edita tudo isso é a tela do Fiscalbot na Central. Ninguém abre arquivo
de configuração à mão.
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any

#: Os campos que identificam a operação — todos avaliados em `AND`.
CAMPOS_DE_IDENTIFICACAO = ("es", "especie", "cfop", "cond_produto",
                           "cond_par_uf", "cond_parceiro")

#: As seis dimensões conferidas quando a regra casa.
DIMENSOES = ("esp_cst", "esp_icms", "esp_aliq", "esp_carga", "esp_outros")


@dataclass(frozen=True)
class Regra:
    """Uma regra de enquadramento.

    Os campos de condição usam a mini-linguagem descrita em `predicados.py`.
    `base_legal` e `ultima_revisao` não entram no motor: existem para o time
    fiscal saber de onde a regra veio e quando foi conferida pela última vez.
    """

    id: str
    operacao: str
    ativa: bool = True
    es: str = ""
    especie: str = ""
    cfop: tuple[str, ...] = ()
    cond_produto: str = ""
    cond_par_uf: str = ""
    cond_parceiro: str = ""
    esp_cst: str = ""
    esp_icms: str = ""
    esp_aliq: str = ""
    esp_carga: str = ""
    esp_outros: str = ""
    base_legal: str = ""
    ultima_revisao: str = ""

    @property
    def cfops_conferidos(self) -> tuple[str, ...]:
        """Os CFOP que o motor realmente compara.

        A lista para no primeiro vazio — é o que o VBA faz, porque conta os
        CFOP preenchidos e depois percorre essa **quantidade** de posições.
        `1602;;2602` confere `1602` e a posição vazia, e nunca chega ao `2602`.
        Reproduzido de propósito: a base de regras foi montada contra este
        comportamento, e mudá-lo mudaria a auditoria de meses já fechados.
        A tela avisa quando uma regra tem CFOP vazio no meio da lista.
        """
        preenchidos = sum(1 for c in self.cfop if c.strip())
        return tuple(self.cfop[:preenchidos])


@dataclass(frozen=True)
class Parametros:
    """Os parâmetros do motor, fora das regras."""

    #: Tolerância da carga efetiva, em pontos percentuais, para mais e para menos.
    tolerancia_carga: float = 0.05
    #: CST que exigem ICMS > 0; os demais exigem ICMS = 0 (Camada 0, regra A).
    cst_exigem_icms_positivo: tuple[str, ...] = ()
    #: Listas nomeadas de produto, usadas por `TABELA:` e `TABELAEXCETO:`.
    tabelas: dict[str, tuple[str, ...]] = field(default_factory=dict)
    #: Nomes aceitos para cada coluna do relatório — o layout do Sankhya varia.
    sinonimos: dict[str, tuple[str, ...]] = field(default_factory=dict)


@dataclass(frozen=True)
class Parceiro:
    """Um parceiro numa lista de exceção. Dado da empresa."""

    codigo: str
    descricao: str = ""


@dataclass
class BaseDeRegras:
    """Tudo o que o motor precisa saber antes de olhar para o relatório."""

    regras: list[Regra] = field(default_factory=list)
    parametros: Parametros = field(default_factory=Parametros)
    #: Matriz origem → destino → alíquota, para o operador `TABELAUF`.
    aliquotas: dict[str, dict[str, float]] = field(default_factory=dict)
    parceiros_simples_nacional: list[Parceiro] = field(default_factory=list)
    parceiros_cavaco: list[Parceiro] = field(default_factory=list)
    #: Trilha de alteração — substitui o histórico que o git daria.
    atualizado_em: str = ""
    atualizado_por: str = ""

    @property
    def ativas(self) -> list[Regra]:
        return [r for r in self.regras if r.ativa]

    def achar(self, identificador: str) -> Regra | None:
        for regra in self.regras:
            if regra.id == identificador:
                return regra
        return None

    def substituir(self, regra: Regra) -> None:
        """Troca a regra de mesmo `id`, ou acrescenta se ainda não existir."""
        for i, atual in enumerate(self.regras):
            if atual.id == regra.id:
                self.regras[i] = regra
                return
        self.regras.append(regra)

    def remover(self, identificador: str) -> bool:
        antes = len(self.regras)
        self.regras = [r for r in self.regras if r.id != identificador]
        return len(self.regras) != antes

    def codigos_simples_nacional(self) -> set[str]:
        return {p.codigo for p in self.parceiros_simples_nacional if p.codigo}

    def codigos_cavaco(self) -> set[str]:
        return {p.codigo for p in self.parceiros_cavaco if p.codigo}

    def aliquota_de(self, par_uf: str) -> float | None:
        # Separa antes de subir a caixa: o "x" do par é minúsculo.
        origem, _, destino = par_uf.partition("x")
        origem, destino = origem.upper(), destino.upper()
        return self.aliquotas.get(origem, {}).get(destino)


def com_campos(regra: Regra, **alteracoes: Any) -> Regra:
    """Uma cópia da regra com os campos trocados — `Regra` é imutável."""
    return replace(regra, **alteracoes)
