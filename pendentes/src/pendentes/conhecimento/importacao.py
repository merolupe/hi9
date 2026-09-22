"""Os dois arquivos de fora viram a base — com o que eles têm de desacordo.

A base nasce de dois artefatos, e eles **não dizem a mesma coisa**:

| Arquivo | O que é | O que ele resolve |
|---|---|---|
| `parceiros.csv` | a lista **curada**: um guardião e uma categoria por parceiro | trocou nome de pessoa por nome de área, e é o que se quer propor |
| `regras_classificacao.json` | o histórico **medido**: quantas notas, quantas semanas, com que concordância, e as alternativas | é o lastro — ou a falta dele |

`[FATO]` Medido nos dois arquivos de 17/09/2026: em 221 dos 696 parceiros o
guardião proposto **não aparece nenhuma vez** no histórico daquele parceiro. O
caso típico: num parceiro com 159 notas o histórico registra o primeiro nome
de uma pessoa em 72 delas, e a lista curada propõe a área a que ela pertence.
Não é erro de nenhum dos dois: é uma pessoa sendo substituída pela área.

Por isso a importação **não escolhe** entre as duas fontes. Ela guarda a
proposta de um lado, a evidência do outro, e deixa o cruzamento visível. Quem
decide o que preencher é o grau de confiança, calculado na hora da consulta.

### O que a importação recusa a fazer

* **não mescla com a base anterior.** Duas fotografias de épocas diferentes
  somariam evidência das mesmas notas contadas duas vezes;
* **não preenche a lista de guardiões** que valida a semana. Os guardiões
  observados ficam registrados e vão para a tela, mas quem cadastra é gente:
  encher a lista daqui faria a semana seguinte bloquear em cima de nome que
  ninguém conferiu;
* **não normaliza o vocabulário de operação.** `[FATO]` As regras dizem
  `Compra Uso e Consumo` e o relatório da semana 38 diz `Compra Uso Consumo`.
  São dois textos diferentes para a mesma coisa, e casá-los por semelhança
  seria adivinhação. A importação conta o desacordo e mostra.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

from ..texto import aparar, chave_de_texto
from .base import (FIRME, SEM_PROPOSTA, SUGESTAO, Conhecimento, Evidencia,
                   _codigo, _confianca, gravar)

#: As colunas que identificam a lista curada de parceiros.
COLUNAS_DO_CSV = ("Código parceiro", "Parceiro", "Guardião sugerido",
                  "Categoria sugerida")
#: A coluna de unidade, cujo próprio rótulo diz o que o vazio significa.
COLUNA_DA_UNIDADE = "Unidade (vazio = geral)"
COLUNA_DO_GESTOR = "Gestor atual"

#: As duas categorias que o relatório de mercadorias conhece. Proposta fora
#: delas não vira proposta — vira aviso.
CATEGORIAS = ("Diretos", "Indiretos")


class ArquivoNaoReconhecido(Exception):
    """O arquivo não é nem a lista de parceiros nem as regras medidas."""


@dataclass
class Importacao:
    """O que entrou na base, e o que a importação teve a dizer sobre isso."""

    conhecimento: Conhecimento
    parceiros: int = 0
    com_unidade: int = 0
    operacoes: int = 0
    gestores: int = 0
    #: Por campo (`guardiao`, `categoria`): quantas propostas em cada grau.
    graus: dict[str, dict[str, int]] = field(default_factory=dict)
    avisos: list[str] = field(default_factory=list)
    caminho: Path | None = None

    def firmes(self, campo: str) -> int:
        return (self.graus.get(campo) or {}).get(FIRME, 0)

    def titulo(self) -> str:
        return (f"Base de conhecimento — {self.parceiros} parceiro(s), "
                f"{self.firmes('categoria')} categoria(s) e "
                f"{self.firmes('guardiao')} guardião(ões) com evidência firme")

    def fichas(self) -> list[tuple[str, str]]:
        return [
            ("Parceiros", str(self.parceiros)),
            ("Com unidade própria", str(self.com_unidade)),
            ("Operações por CFOP", str(self.operacoes)),
            ("Guardiões observados",
             str(len(self.conhecimento.guardioes_observados))),
        ]

    def listas(self) -> list[tuple[str, list[str], str]]:
        saida: list[tuple[str, list[str], str]] = []
        if self.avisos:
            saida.append(("O que a importação não pôde afirmar", self.avisos,
                          "atencao"))
        for campo in ("categoria", "guardiao"):
            graus = self.graus.get(campo) or {}
            saida.append((
                f"Propostas de {campo}",
                [f"{quantas} — {grau}" for grau, quantas in sorted(
                    graus.items(), key=lambda t: -t[1])],
                "neutro"))
        saida.append(("Guardiões que o histórico mostrou",
                      self.conhecimento.guardioes_observados, "neutro"))
        return saida


# -- reconhecer cada arquivo pelo conteúdo ---------------------------------

def _ler_csv(caminho: Path) -> list[dict[str, str]] | None:
    """A lista curada, se for ela. `utf-8-sig` porque o Excel põe BOM."""
    try:
        texto = caminho.read_text(encoding="utf-8-sig")
    except (UnicodeDecodeError, OSError):
        return None
    leitor = csv.DictReader(io.StringIO(texto), delimiter=";")
    if not leitor.fieldnames:
        return None
    presentes = {aparar(nome) for nome in leitor.fieldnames}
    if not set(COLUNAS_DO_CSV) <= presentes:
        return None
    return [dict(linha) for linha in leitor]


def _ler_json(caminho: Path) -> dict[str, Any] | None:
    """As regras medidas, se for elas."""
    try:
        bruto = json.loads(caminho.read_text(encoding="utf-8"))
    except (ValueError, UnicodeDecodeError, OSError):
        return None
    if not isinstance(bruto, dict) or "regras" not in bruto:
        return None
    return bruto


def _impressao(caminho: Path, registros: int) -> dict[str, Any]:
    conteudo = caminho.read_bytes()
    return {"nome": caminho.name, "bytes": len(conteudo), "registros": registros,
            "sha256": hashlib.sha256(conteudo).hexdigest()}


# -- as regras medidas, indexadas ------------------------------------------

def _alternativas(bruto: str) -> dict[str, int]:
    """`"Joana M.: 72 | Balança: 28"` vira `{...}`."""
    saida: dict[str, int] = {}
    for parte in str(bruto or "").split("|"):
        if ":" not in parte:
            continue
        valor, quantas = parte.rsplit(":", 1)
        if quantas.strip().isdigit():
            saida[aparar(valor)] = int(quantas.strip())
    return saida


def _evidencia(regra: dict[str, Any]) -> Evidencia:
    return Evidencia(
        valor=aparar(regra.get("valor")),
        notas=int(regra.get("total") or 0),
        apoio=int(regra.get("apoio") or 0),
        semanas=int(regra.get("semanas") or 0),
        alternativas=_alternativas(regra.get("alternativas")),
    )


def cfop_normalizado(valor: Any) -> str:
    """`"5405, 5102"` e `5102` viram a chave que as regras usam.

    `[FATO]` As regras escrevem conjunto de CFOP como `5102+5405`, em ordem
    crescente, e exigem correspondência exata do conjunto — nota com dois CFOP
    não casa com a regra de um deles. A coluna do relatório traz ora um número,
    ora um texto com vírgulas. Os dois chegam aqui e saem iguais.
    """
    codigos = sorted(set(re.findall(r"\d{4}", str(valor or ""))))
    return "+".join(codigos)


# -- a montagem ------------------------------------------------------------

def _indexar_regras(bruto: dict[str, Any]) -> dict[tuple, dict[str, Any]]:
    indice: dict[tuple, dict[str, Any]] = {}
    for regra in bruto.get("regras") or ():
        tipo = str(regra.get("tipo") or "")
        if tipo in ("parceiro", "parceiro_unidade"):
            chave = (tipo, _codigo(regra.get("codigo_parceiro")),
                     chave_de_texto(regra.get("unidade")),
                     str(regra.get("campo") or ""))
        elif tipo == "operacao":
            chave = (tipo, cfop_normalizado(regra.get("cfop")),
                     _codigo(regra.get("codigo_parceiro")),
                     chave_de_texto(regra.get("categoria")))
        elif tipo == "guardiao_gestor_atual":
            chave = (tipo, chave_de_texto(regra.get("guardiao_condicao")))
        else:                                            # pragma: no cover
            continue
        indice.setdefault(chave, regra)
    return indice


def _campo(proposto: str, evidencia: Evidencia) -> dict[str, Any]:
    return {"proposto": proposto, "evidencia": evidencia.como_dicionario()}


def importar(caminhos: Iterable[Path | str], *, responsavel: str | None = None,
             raiz: Path | None = None, agora: datetime | None = None,
             gravar_em_disco: bool = True) -> Importacao:
    """Lê os dois arquivos, monta a base e grava. Devolve o que entrou."""
    agora = agora or datetime.now()
    curada: list[dict[str, str]] = []
    medidas: dict[str, Any] = {}
    fontes: list[dict[str, Any]] = []
    nao_reconhecidos: list[str] = []

    for caminho in caminhos:
        caminho = Path(caminho)
        linhas = _ler_csv(caminho)
        if linhas is not None:
            curada, _ = linhas, fontes.append(_impressao(caminho, len(linhas)))
            continue
        bruto = _ler_json(caminho)
        if bruto is not None:
            medidas = bruto
            fontes.append(_impressao(caminho, len(bruto.get("regras") or ())))
            continue
        nao_reconhecidos.append(caminho.name)

    if not curada and not medidas:
        raise ArquivoNaoReconhecido(
            "Nenhum dos arquivos é a lista de parceiros (`.csv` com as colunas "
            f"{', '.join(COLUNAS_DO_CSV)}) nem as regras medidas (`.json` com "
            "a chave `regras`)."
        )

    indice = _indexar_regras(medidas)
    conhecimento = Conhecimento(
        dominio="mercadorias",
        versao_da_fonte=str(medidas.get("versao") or ""),
        ultimo_relatorio_classificado=int(
            medidas.get("ultimo_relatorio_classificado") or 0),
        importado_em=agora.strftime("%Y-%m-%d %H:%M:%S"),
        importado_por=(responsavel or os.environ.get("USERNAME")
                       or os.environ.get("USER") or "?"),
        fontes=fontes,
    )
    relato = Importacao(conhecimento)
    relato.avisos = [f"não reconheci {nome}; ele não entrou na base"
                     for nome in nao_reconhecidos]
    if not curada:
        relato.avisos.append(
            "a lista curada de parceiros não veio: a base guarda só o "
            "histórico medido, e ele sozinho não propõe guardião")
    if not medidas:
        relato.avisos.append(
            "as regras medidas não vieram: sem evidência, nenhuma proposta "
            "chega a firme — tudo fica como sugestão")

    _montar_parceiros(relato, curada, indice)
    _montar_operacoes(relato, indice)
    _montar_gestores(relato, indice, curada)

    if gravar_em_disco:
        relato.caminho = gravar(conhecimento, raiz=raiz)
    return relato


def _montar_parceiros(relato: Importacao, curada: list[dict[str, str]],
                      indice: dict[tuple, dict[str, Any]]) -> None:
    conhecimento = relato.conhecimento
    fora_da_categoria: list[str] = []
    guardioes: list[str] = []
    graus = {campo: {} for campo in ("guardiao", "categoria")}

    for linha in curada:
        codigo = _codigo(linha.get("Código parceiro"))
        if not codigo:
            continue
        unidade = aparar(linha.get(COLUNA_DA_UNIDADE))
        tipo = "parceiro_unidade" if unidade else "parceiro"
        destino = conhecimento.parceiros.setdefault(
            codigo, {"nome": aparar(linha.get("Parceiro"))})
        if unidade:
            destino = destino.setdefault("unidades", {}).setdefault(
                chave_de_texto(unidade), {"rotulo": unidade})
            relato.com_unidade += 1

        for campo, coluna in (("guardiao", "Guardião sugerido"),
                              ("categoria", "Categoria sugerida")):
            proposto = aparar(linha.get(coluna))
            if campo == "categoria" and proposto and proposto not in CATEGORIAS:
                fora_da_categoria.append(f"{codigo}: {proposto}")
                proposto = ""
            if campo == "guardiao" and proposto and proposto not in guardioes:
                guardioes.append(proposto)
            evidencia = _evidencia(indice.get(
                (tipo, codigo, chave_de_texto(unidade), campo)) or {})
            destino[campo] = _campo(proposto, evidencia)
            grau, _lastro = _confianca(proposto, evidencia)
            graus[campo][grau] = graus[campo].get(grau, 0) + 1

    # O que o histórico conhece e a lista curada não citou entra sem proposta:
    # a evidência fica consultável, e "não sei" continua sendo a resposta.
    for chave, regra in indice.items():
        if chave[0] != "parceiro" or chave[1] in conhecimento.parceiros:
            continue
        conhecimento.parceiros.setdefault(chave[1], {"nome": ""})[chave[3]] = (
            _campo("", _evidencia(regra)))
        graus.setdefault(chave[3], {})
        graus[chave[3]][SEM_PROPOSTA] = graus[chave[3]].get(SEM_PROPOSTA, 0) + 1

    conhecimento.guardioes_observados = sorted(guardioes)
    relato.parceiros = len(conhecimento.parceiros)
    relato.graus = graus
    if fora_da_categoria:
        mostradas = ", ".join(fora_da_categoria[:3])
        relato.avisos.append(
            f"{len(fora_da_categoria)} parceiro(s) com categoria fora de "
            f"{' e '.join(CATEGORIAS)} — não viraram proposta: {mostradas}")


def _montar_operacoes(relato: Importacao,
                      indice: dict[tuple, dict[str, Any]]) -> None:
    """O `Tipo de Operação` por CFOP, nos quatro níveis da fonte.

    `[FATO]` A precedência é a da prioridade 6: CFOP + parceiro + categoria,
    depois CFOP + parceiro, depois CFOP + categoria, depois CFOP sozinho. Como
    a chave já carrega os três pedaços, a consulta percorre os quatro níveis na
    ordem e para no primeiro que responde.
    """
    operacoes = relato.conhecimento.operacoes
    for chave, regra in indice.items():
        if chave[0] != "operacao":
            continue
        _, cfop, codigo, categoria = chave
        if not cfop:
            continue
        evidencia = _evidencia(regra)
        # Aqui a proposta **é** a evidência: não há lista curada de operação,
        # e por isso só o que se repete sem divergência chega a ser oferecido.
        operacoes.setdefault(cfop, {})[f"{codigo}|{categoria}"] = _campo(
            evidencia.valor if evidencia.repetida_sem_divergencia else "",
            evidencia)
        relato.operacoes += 1


def _montar_gestores(relato: Importacao, indice: dict[tuple, dict[str, Any]],
                     curada: list[dict[str, str]]) -> None:
    """O gestor vigente de cada guardião, e o desacordo com a lista curada."""
    conhecimento = relato.conhecimento
    for chave, regra in indice.items():
        if chave[0] != "guardiao_gestor_atual":
            continue
        evidencia = _evidencia(regra)
        conhecimento.gestor_do_guardiao[chave[1]] = {
            "rotulo": aparar(regra.get("guardiao_condicao")),
            **_campo(evidencia.valor, evidencia),
        }
        relato.gestores += 1

    desacordo: list[str] = []
    for linha in curada:
        guardiao = aparar(linha.get("Guardião sugerido"))
        gestor = aparar(linha.get(COLUNA_DO_GESTOR))
        if not guardiao or not gestor:
            continue
        proposta = conhecimento.gestor_de(guardiao)
        if proposta and chave_de_texto(proposta.valor) != chave_de_texto(gestor):
            marca = f"{guardiao}: a lista diz {gestor}, o histórico {proposta.valor}"
            if marca not in desacordo:
                desacordo.append(marca)
    if desacordo:
        relato.avisos.append(
            f"{len(desacordo)} guardião(ões) com gestor diferente entre a "
            f"lista e o histórico: {'; '.join(desacordo[:3])}")
