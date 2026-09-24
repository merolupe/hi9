"""A camada de correção humana, que a reimportação não apaga.

### Por que separada da base

A base importada é uma **fotografia**: ela é substituída inteira a cada
importação, porque somar duas fotografias de épocas diferentes produziria uma
terceira que nunca existiu, com evidência de execuções que contaram as mesmas
notas. Isso está em `base.gravar`, e continua valendo.

Uma correção feita à mão na tela não pode viver dentro da fotografia — a
próxima importação a levaria embora, junto com a explicação de por que ela
existia. Então ela mora ao lado, em `<domínio>-ajustes.json`, e é **aplicada
por cima** da fotografia na hora de carregar. É o mesmo desenho que o resto do
repositório usa entre carga de fábrica e base viva, com uma diferença: aqui o
que vem de fábrica é a importação, e quem manda é a pessoa.

### Por que o ajuste vence tudo

Um ajuste é a evidência mais forte que a base pode ter. O histórico diz o que
foi feito; a pessoa que corrigiu diz o que era certo — inclusive quando o
histórico inteiro estava errado, que é justamente o caso em que alguém abre a
tela. Por isso o grau `ajustado` preenche onde `firme` preenche, e também onde
só `sugestao` preencheria.

### O que ele guarda além do valor

Quem gravou e quando (regra nº 3: na tela de configuração, a trilha é o
carimbo) e, quando a pessoa escrever, uma observação. O que **não** se guarda
é evidência: ajuste não tem contagem de notas, e inventar uma faria a tela
mentir sobre de onde vem a confiança.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from ..texto import aparar, chave_de_texto

#: Os campos de parceiro que a tela deixa corrigir.
CAMPOS_DO_PARCEIRO = ("guardiao", "categoria")

#: A chave que o ajuste ocupa dentro do dicionário da base, ao lado de
#: `proposto` e `evidencia`. Quem consulta lê esta antes daquela.
CHAVE = "ajustado"


@dataclass(frozen=True)
class Ajuste:
    """Uma correção, com a trilha de quem a fez."""

    valor: str = ""
    por: str = ""
    em: str = ""
    observacao: str = ""

    def __bool__(self) -> bool:
        return bool(self.valor)

    def como_dicionario(self) -> dict[str, Any]:
        bruto = {"valor": self.valor, "por": self.por, "em": self.em}
        if self.observacao:
            bruto["observacao"] = self.observacao
        return bruto

    @staticmethod
    def de(bruto: Any) -> "Ajuste":
        if not isinstance(bruto, dict):
            return Ajuste()
        return Ajuste(
            valor=aparar(bruto.get("valor")),
            por=str(bruto.get("por") or ""),
            em=str(bruto.get("em") or ""),
            observacao=str(bruto.get("observacao") or ""),
        )


@dataclass
class Ajustes:
    """Tudo o que foi corrigido à mão, por escopo.

    As três chaves espelham os três dicionários da base. `parceiros` aceita o
    nível da unidade, como a base: a chave de dentro é o `Nome Fantasia`
    normalizado, e o rótulo original fica ao lado para a tela poder mostrá-lo.
    """

    dominio: str = "mercadorias"
    parceiros: dict[str, dict[str, Any]] = field(default_factory=dict)
    gestores: dict[str, dict[str, Any]] = field(default_factory=dict)
    operacoes: dict[str, dict[str, Any]] = field(default_factory=dict)

    def __len__(self) -> int:
        return self.quantos

    @property
    def quantos(self) -> int:
        """Quantas correções existem, contando por campo e não por linha."""
        total = 0
        for entrada in self.parceiros.values():
            total += sum(1 for campo in CAMPOS_DO_PARCEIRO
                         if Ajuste.de(entrada.get(campo)))
            for unidade in (entrada.get("unidades") or {}).values():
                total += sum(1 for campo in CAMPOS_DO_PARCEIRO
                             if Ajuste.de(unidade.get(campo)))
        total += sum(1 for v in self.gestores.values() if Ajuste.de(v))
        total += sum(1 for niveis in self.operacoes.values()
                     for v in niveis.values() if Ajuste.de(v))
        return total

    @property
    def vazia(self) -> bool:
        return not (self.parceiros or self.gestores or self.operacoes)

    # -- escrita, uma correção por vez -------------------------------------

    def do_parceiro(self, codigo: str, campo: str, fantasia: str = "") -> Ajuste:
        entrada = self.parceiros.get(str(codigo)) or {}
        if fantasia:
            entrada = ((entrada.get("unidades") or {})
                       .get(chave_de_texto(fantasia)) or {})
        return Ajuste.de(entrada.get(campo))

    def ajustar_parceiro(self, codigo: str, campo: str, ajuste: Ajuste, *,
                         nome: str = "", fantasia: str = "") -> None:
        """Grava — ou apaga, quando o ajuste vem vazio."""
        if campo not in CAMPOS_DO_PARCEIRO:
            raise ValueError(f"campo de parceiro desconhecido: {campo!r}")
        entrada = self.parceiros.setdefault(str(codigo), {})
        if nome:
            entrada["nome"] = nome
        alvo = entrada
        if fantasia:
            unidades = entrada.setdefault("unidades", {})
            alvo = unidades.setdefault(chave_de_texto(fantasia),
                                       {"rotulo": aparar(fantasia)})
        _por(alvo, campo, ajuste)
        self._podar()

    def ajustar_gestor(self, guardiao: str, ajuste: Ajuste) -> None:
        chave = chave_de_texto(guardiao)
        if not chave:
            return
        if ajuste:
            self.gestores[chave] = {
                **ajuste.como_dicionario(), "rotulo": aparar(guardiao)}
        else:
            self.gestores.pop(chave, None)

    def ajustar_operacao(self, cfop: str, nivel: str, ajuste: Ajuste) -> None:
        cfop = aparar(cfop)
        if not cfop:
            return
        niveis = self.operacoes.setdefault(cfop, {})
        if ajuste:
            niveis[nivel] = ajuste.como_dicionario()
        else:
            niveis.pop(nivel, None)
        if not niveis:
            self.operacoes.pop(cfop, None)

    def _podar(self) -> None:
        """Tira do arquivo o parceiro que ficou sem uma correção sequer."""
        for codigo in list(self.parceiros):
            entrada = self.parceiros[codigo]
            unidades = entrada.get("unidades") or {}
            for chave in list(unidades):
                if not any(Ajuste.de(unidades[chave].get(campo))
                           for campo in CAMPOS_DO_PARCEIRO):
                    unidades.pop(chave)
            if not unidades:
                entrada.pop("unidades", None)
            if not (entrada.get("unidades")
                    or any(Ajuste.de(entrada.get(campo))
                           for campo in CAMPOS_DO_PARCEIRO)):
                self.parceiros.pop(codigo)

    def como_dicionario(self) -> dict[str, Any]:
        return {"dominio": self.dominio, "parceiros": self.parceiros,
                "gestores": self.gestores, "operacoes": self.operacoes}


def _por(alvo: dict, campo: str, ajuste: Ajuste) -> None:
    if ajuste:
        alvo[campo] = ajuste.como_dicionario()
    else:
        alvo.pop(campo, None)


def agora() -> str:
    """O carimbo, no formato que o resto do aplicativo usa."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def caminho_dos_ajustes(dominio: str = "mercadorias",
                        raiz: Path | None = None) -> Path:
    """Ao lado da base, e fora do git pelo mesmo motivo que ela."""
    from .base import caminho_da_base

    base = caminho_da_base(dominio, raiz)
    return base.with_name(f"{dominio}-ajustes.json")


def carregar(dominio: str = "mercadorias",
             raiz: Path | None = None) -> Ajustes:
    caminho = caminho_dos_ajustes(dominio, raiz)
    if not caminho.is_file():
        return Ajustes(dominio=dominio)
    bruto = json.loads(caminho.read_text(encoding="utf-8"))
    return Ajustes(
        dominio=str(bruto.get("dominio") or dominio),
        parceiros=dict(bruto.get("parceiros") or {}),
        gestores=dict(bruto.get("gestores") or {}),
        operacoes=dict(bruto.get("operacoes") or {}),
    )


def gravar(ajustes: Ajustes, raiz: Path | None = None) -> Path:
    """Grava a camada inteira — ela é pequena, e é a única fonte dela mesma."""
    caminho = caminho_dos_ajustes(ajustes.dominio, raiz)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(
        json.dumps(ajustes.como_dicionario(), ensure_ascii=False, indent=1),
        encoding="utf-8")
    return caminho


def aplicar(conhecimento, ajustes: Ajustes):
    """Põe as correções por cima da fotografia, em memória.

    A fotografia no disco **não** é tocada: quem pergunta à base recebe a
    correção, e quem reimportar continua substituindo só a fotografia. Parceiro
    que só existe no ajuste é criado aqui — é o caso de quem corrigiu antes de
    a importação alcançar aquele fornecedor.
    """
    if ajustes.vazia:
        return conhecimento

    for codigo, entrada in ajustes.parceiros.items():
        parceiro = conhecimento.parceiros.setdefault(str(codigo), {})
        if entrada.get("nome") and not parceiro.get("nome"):
            parceiro["nome"] = entrada["nome"]
        for campo in CAMPOS_DO_PARCEIRO:
            ajuste = Ajuste.de(entrada.get(campo))
            if ajuste:
                parceiro[campo] = {**(parceiro.get(campo) or {}),
                                   CHAVE: ajuste.como_dicionario()}
        for chave, bruto in (entrada.get("unidades") or {}).items():
            unidades = parceiro.setdefault("unidades", {})
            unidade = unidades.setdefault(
                chave, {"rotulo": bruto.get("rotulo") or ""})
            for campo in CAMPOS_DO_PARCEIRO:
                ajuste = Ajuste.de(bruto.get(campo))
                if ajuste:
                    unidade[campo] = {**(unidade.get(campo) or {}),
                                      CHAVE: ajuste.como_dicionario()}

    for chave, bruto in ajustes.gestores.items():
        ajuste = Ajuste.de(bruto)
        if ajuste:
            conhecimento.gestor_do_guardiao[chave] = {
                **(conhecimento.gestor_do_guardiao.get(chave) or {}),
                CHAVE: ajuste.como_dicionario()}

    for cfop, niveis in ajustes.operacoes.items():
        alvo = conhecimento.operacoes.setdefault(cfop, {})
        for nivel, bruto in niveis.items():
            ajuste = Ajuste.de(bruto)
            if ajuste:
                alvo[nivel] = {**(alvo.get(nivel) or {}),
                               CHAVE: ajuste.como_dicionario()}
    return conhecimento
