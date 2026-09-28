"""O que o Portal de Compras sabe e o ASIS não: parceiro, filial e pedido.

O ASIS traz o nome do prestador e o CNPJ; não traz o código do parceiro no
ERP, não sabe para qual filial a nota foi emitida e não conhece pedido de
compra. Os três saem do **próprio** relatório do Portal de Compras, montados
num passe único sobre ele.

| Mapa | De | Para | Regra |
|---|---|---|---|
| parceiros | CNPJ do parceiro | código e nome no Sankhya | qualquer TOP; a primeira ocorrência vence |
| filiais | CNPJ da empresa | nome fantasia | idem |
| códigos de filial | CNPJ da empresa | código da empresa | idem |
| pedidos | CNPJ do parceiro | o pedido de maior `Nro. Unico` | só descrição de TOP começando em `PC` |

### O de-para de filiais é dinâmico, e isso tem preço

**Não existe mapa estático de filiais.** O de-para é construído do movimento
do período — e é exatamente por isso que a filial **sem movimento naquela
semana** desaparece do mapa e a nota dela recebe `CNPJ nao mapeado: …` dentro
da célula. É o caso que o time já conhece.

Aqui a regra é a mesma, com duas diferenças: a base viva pode cadastrar um
**complemento estático** (que só é consultado quando o mapa dinâmico não
responde, porque o dinâmico é o que está atual), e o CNPJ que nenhum dos dois
resolve **bloqueia o encerramento da semana** em vez de virar texto dentro da
planilha.

### O "pedido mais recente" pode ser de outra filial

O índice é por CNPJ do parceiro e só por ele: sem filtro de empresa, sem
filtro de período, vencendo o maior `Nro. Unico`. O pedido exibido pode
pertencer a outra filial e a outro mês, e as colunas `Ultimo Comprador`,
`Ultimo Requisitante`, `Ultima Natureza` e `Ultimo CR` vêm dele.

A regra fica **como está** — mudá-la muda quatro colunas que o time lê toda
semana. O que muda é que os casos de pedido de filial diferente passam a ser
**contados** na tela. É esse número que vai fundamentar a resposta à
pendência nº 5.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Sequence

from ..chaves import (
    CNPJ_ZERADO, SEM_CADASTRO, cnpj as so_cnpj, cnpj_utilizavel,
)
from ..texto import aparar, texto_de
from .fontes import Registro

#: O que vai para `Cod Parceiro` quando o CNPJ do prestador não está no
#: cadastro do Sankhya. Mora no núcleo (`chaves.SEM_CADASTRO`) porque é o
#: mesmo literal que mercadorias grava na regra A2; fica reexportado aqui para
#: quem lê este módulo saber de onde vem.

#: O que vai para `Pedido de compra mais recente` quando não há pedido.
SEM_PEDIDO = "Nao encontrado"

#: O prefixo da célula de filial quando o CNPJ do tomador não foi resolvido.
#: O CNPJ fica visível ali **e** entra na lista bloqueante da tela.
FILIAL_NAO_MAPEADA = "CNPJ nao mapeado: "


def cnpj_formatado(digitos: str) -> str:
    """`12345678000190` vira `12.345.678/0001-90`; CPF, `123.456.789-01`.

    O que não tem 14 nem 11 dígitos sai como veio: pontuar um número que não
    é CNPJ nem CPF seria inventar uma forma que ele não tem.
    """
    if len(digitos) == 14 and digitos.isdigit():
        return (f"{digitos[:2]}.{digitos[2:5]}.{digitos[5:8]}/"
                f"{digitos[8:12]}-{digitos[12:]}")
    if len(digitos) == 11 and digitos.isdigit():
        return f"{digitos[:3]}.{digitos[3:6]}.{digitos[6:9]}-{digitos[9:]}"
    return digitos


def nome_com_cnpj(prestador: object, cnpj: str) -> object:
    """O nome do prestador seguido do CNPJ — `OFICINA (CNPJ 12.345.678/0001-90)`.

    Sem CNPJ, o nome como veio; sem nome, o CNPJ sozinho.
    """
    if not cnpj:
        return prestador
    tipo = "CPF" if len(cnpj) == 11 else "CNPJ"
    rotulo = f"{tipo} {cnpj_formatado(cnpj)}"
    nome = aparar(prestador)
    return f"{nome} ({rotulo})" if nome else rotulo


@dataclass(frozen=True)
class Pedido:
    """O pedido de compra mais recente de um parceiro, e o que vem dele."""

    numero_unico: float
    comprador: object = ""
    requisitante: object = ""
    natureza: object = ""
    centro_de_resultado: object = ""
    #: O código da empresa do pedido. Não vai para a planilha — serve só para
    #: contar quantas notas receberam pedido de filial diferente da sua.
    empresa: str = ""


@dataclass(frozen=True)
class Parceiro:
    """O parceiro como o Sankhya o cadastra."""

    codigo: str
    nome: object


@dataclass
class Cadastro:
    """Tudo que o Portal de Compras sabe, indexado para consulta."""

    parceiros: dict[str, Parceiro] = field(default_factory=dict)
    filiais: dict[str, object] = field(default_factory=dict)
    codigos_de_filial: dict[str, str] = field(default_factory=dict)
    pedidos: dict[str, Pedido] = field(default_factory=dict)
    lancamentos_por_cnpj: dict[str, int] = field(default_factory=dict)
    #: Lançamentos de serviço descartados por CNPJ vazio ou zerado. Hoje somem
    #: sem contagem e sem aviso; aqui viram número na tela.
    descartados_por_cnpj: int = 0
    #: Os CNPJ que a semana não conhecia e o histórico do Portal de Compras
    #: respondeu — parceiro e pedido. Só para contar na tela.
    parceiros_do_historico: set[str] = field(default_factory=set)
    pedidos_do_historico: set[str] = field(default_factory=set)

    def veio_do_historico(self, cnpj: str) -> bool:
        return cnpj in self.parceiros_do_historico

    # -- as consultas que a montagem da planilha faz ------------------------

    def parceiro_de(self, cnpj: str) -> Parceiro | None:
        return self.parceiros.get(cnpj)

    def codigo_do_parceiro(self, cnpj: str) -> str:
        parceiro = self.parceiros.get(cnpj)
        return parceiro.codigo if parceiro else SEM_CADASTRO

    def nome_do_parceiro(self, cnpj: str, prestador: object = "") -> object:
        """O nome do Sankhya; sem cadastro, o nome do ASIS **com o CNPJ**.

        Quem recebe a linha `Sem cadastro` precisa do CNPJ para cadastrar o
        parceiro, e a aba não tem coluna de CNPJ. Ele vai na célula do nome,
        e não numa coluna nova: a largura das abas é invariante (ver
        `colunas.py`). Não mexe na identidade entre semanas, que é número da
        nota e `Cod Parceiro`.
        """
        parceiro = self.parceiros.get(cnpj)
        if parceiro:
            return parceiro.nome
        return nome_com_cnpj(prestador, cnpj)

    def filial_de(self, cnpj: str) -> object:
        """O nome fantasia da filial, ou o aviso com o CNPJ dentro da célula."""
        if cnpj in self.filiais:
            return self.filiais[cnpj]
        return FILIAL_NAO_MAPEADA + cnpj

    def filial_mapeada(self, cnpj: str) -> bool:
        return cnpj in self.filiais

    def codigo_da_filial(self, cnpj: str) -> str:
        return self.codigos_de_filial.get(cnpj, "")

    def pedido_de(self, cnpj: str) -> Pedido | None:
        return self.pedidos.get(cnpj)

    def quantos_lancamentos(self, cnpj: str) -> int:
        return self.lancamentos_por_cnpj.get(cnpj, 0)


def _complementar_filiais(cadastro: Cadastro, complemento: Iterable[dict]) -> None:
    """O de-para estático preenche o que o movimento da semana não trouxe.

    Nunca o contrário: o mapa dinâmico é o que está atual, e um cadastro
    esquecido na base não pode sobrepor o que o export acabou de dizer.
    """
    for linha in complemento or ():
        cnpj = so_cnpj(linha.get("cnpj"))
        if not cnpj:
            continue
        nome = texto_de(linha.get("nome") or "")
        codigo = aparar(linha.get("codigo") or "")
        if nome and cnpj not in cadastro.filiais:
            cadastro.filiais[cnpj] = nome
        if codigo and cnpj not in cadastro.codigos_de_filial:
            cadastro.codigos_de_filial[cnpj] = codigo


def _complementar_com_o_historico(cadastro: Cadastro, historico) -> None:
    """O que a semana não respondeu, o histórico do Portal de Compras responde.

    Parceiro e filial: só onde a semana não conhece — o que o export acabou de
    dizer é o que está atual. Pedido: vence o de maior `Nro. Único` entre os
    dois, que é a regra da semana aplicada a um relatório mais longo.
    """
    for cnpj, guardado in historico.parceiros.items():
        if cnpj not in cadastro.parceiros and guardado.get("codigo"):
            cadastro.parceiros[cnpj] = Parceiro(str(guardado["codigo"]),
                                                guardado.get("nome", ""))
            cadastro.parceiros_do_historico.add(cnpj)
    for cnpj, guardado in historico.pedidos.items():
        numero_unico = float(guardado.get("numero_unico") or 0)
        atual = cadastro.pedidos.get(cnpj)
        if atual is None or numero_unico > atual.numero_unico:
            cadastro.pedidos[cnpj] = Pedido(
                numero_unico=numero_unico,
                comprador=guardado.get("comprador", ""),
                requisitante=guardado.get("requisitante", ""),
                natureza=guardado.get("natureza", ""),
                centro_de_resultado=guardado.get("centro_de_resultado", ""),
                empresa=str(guardado.get("empresa", "")),
            )
            cadastro.pedidos_do_historico.add(cnpj)
    for cnpj, guardada in historico.filiais.items():
        if guardada.get("nome") and cnpj not in cadastro.filiais:
            cadastro.filiais[cnpj] = guardada["nome"]
        if guardada.get("codigo") and cnpj not in cadastro.codigos_de_filial:
            cadastro.codigos_de_filial[cnpj] = str(guardada["codigo"])


def cadastrar(registros: Sequence[Registro], *, tops: Sequence[str],
              prefixo_de_pedido: str, cnpj_descartado: str = CNPJ_ZERADO,
              complemento_de_filiais: Iterable[dict] = (),
              historico=None) -> Cadastro:
    """Monta os quatro mapas num passe único sobre o Portal de Compras.

    Um passe só, e não quatro: o relatório tem centenas de colunas e milhares
    de linhas, e é o mesmo laço que o VBA faz.

    `historico` (ver `historico.py`) complementa parceiro, pedido e filial com
    o que as semanas anteriores ensinaram. Vem antes do complemento estático
    de filiais, porque é movimento real e mais recente que um cadastro manual.
    """
    cadastro = Cadastro()
    for registro in registros:
        cnpj_da_empresa = registro.cnpj_da_empresa
        if cnpj_da_empresa and cnpj_da_empresa not in cadastro.filiais:
            cadastro.filiais[cnpj_da_empresa] = registro.nome_da_empresa
            cadastro.codigos_de_filial.setdefault(cnpj_da_empresa, registro.empresa)

        cnpj = registro.cnpj_do_parceiro
        if not cnpj_utilizavel(cnpj, cnpj_descartado):
            if registro.top in tops:
                cadastro.descartados_por_cnpj += 1
            continue

        if cnpj not in cadastro.parceiros:
            cadastro.parceiros[cnpj] = Parceiro(registro.codigo_do_parceiro,
                                                registro.nome_do_parceiro)

        if registro.e_pedido(prefixo_de_pedido):
            atual = cadastro.pedidos.get(cnpj)
            if atual is None or registro.numero_unico > atual.numero_unico:
                cadastro.pedidos[cnpj] = Pedido(
                    numero_unico=registro.numero_unico,
                    comprador=registro.usuario_de_inclusao,
                    requisitante=registro.usuario_do_rc,
                    natureza=registro.natureza,
                    centro_de_resultado=registro.centro_de_resultado,
                    empresa=registro.empresa,
                )

        if registro.top in tops:
            cadastro.lancamentos_por_cnpj[cnpj] = (
                cadastro.lancamentos_por_cnpj.get(cnpj, 0) + 1)

    if historico:
        _complementar_com_o_historico(cadastro, historico)
    _complementar_filiais(cadastro, complemento_de_filiais)
    return cadastro


def lancamentos_de(registros: Sequence[Registro], tops: Sequence[str],
                   cnpj_descartado: str = CNPJ_ZERADO) -> list[Registro]:
    """Os lançamentos de serviço, na ordem do relatório.

    São eles, e só eles, que entram nos três índices do confronto e que a aba
    inversa percorre no fim.
    """
    return [r for r in registros if r.e_lancamento(tops, cnpj_descartado)]
