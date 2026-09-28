"""O histórico do Portal de Compras: o cadastro que não cabe numa semana.

O confronto de serviços descobre quem é o parceiro, de qual filial é a nota e
qual o pedido de compra mais recente **dentro do próprio relatório do Portal
de Compras da semana** (`enriquecimento.cadastrar`). É um problema crônico:
há parceiro que manda nota sobre pedido de muitos meses atrás, e parceiro que
simplesmente não teve movimento no período exportado. Os dois saem da semana
como `Sem cadastro` e `Nao encontrado`, embora o Sankhya os conheça.

Exportar o Portal de Compras do ano inteiro toda semana resolveria, a um custo
que ninguém paga. Este módulo guarda o que cada exportação ensinou e devolve
na seguinte:

| O que guarda | Por CNPJ de | Regra quando dois relatórios discordam |
|---|---|---|
| parceiro — código e nome no Sankhya | parceiro | vence o de **maior `Nro. Único`**, que é o mais recente |
| pedido de compra mais recente | parceiro | vence o de maior `Nro. Único` — a mesma regra da semana |
| filial — nome fantasia e código | empresa | vence o de maior `Nro. Único` |

### O que ele **não** faz

Não entra no confronto. Os lançamentos (TOP 2020/2111), os quatro
procedimentos e a aba `Sem Correspondencia ASIS` continuam medindo **a semana**
— misturar lançamento de março no confronto de setembro mudaria as contagens
que a prova de divergência zero compara com a macro, e a aba inversa passaria
a listar o ano inteiro. O histórico só responde as três perguntas de cadastro,
e só quando a semana não respondeu (ou, para o pedido, respondeu com um mais
antigo).

### Onde mora, e como cresce

`dados/pendentes/conhecimento/portal_de_compras.json`, fora do git — é código
e nome de fornecedor, regra nº 1. Nasce vazio. Cresce de dois jeitos:

* **toda execução do GerarServPend** absorve o Portal de Compras da semana;
* a entrada **Base de conhecimento** aceita um Portal de Compras de período
  longo (reconhecido pelo cabeçalho, como tudo) e o absorve sem rodar
  confronto nenhum — é assim que se faz a carga inicial.

Absorver é **somar**, não substituir: um relatório curto não apaga o que um
longo ensinou. E é idempotente — absorver o mesmo arquivo duas vezes não muda
nada na segunda.

`.json`, e não `.yaml`, pelo motivo da base de mercadorias: são milhares de
entradas lidas a cada execução, e o YAML puro-Python é lento demais para isso.
"""
from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterable, Sequence

from ..chaves import CNPJ_ZERADO, cnpj_utilizavel
from ..texto import texto_de
from .fontes import Registro

#: Quantas fontes absorvidas o arquivo lembra. As mais antigas saem da lista,
#: não do histórico: o que elas ensinaram continua lá.
FONTES_LEMBRADAS = 60


@dataclass
class Historico:
    """O que as exportações do Portal de Compras já ensinaram, por CNPJ."""

    parceiros: dict[str, dict[str, Any]] = field(default_factory=dict)
    pedidos: dict[str, dict[str, Any]] = field(default_factory=dict)
    filiais: dict[str, dict[str, Any]] = field(default_factory=dict)
    fontes: list[dict[str, Any]] = field(default_factory=list)
    atualizado_em: str = ""
    atualizado_por: str = ""

    def __bool__(self) -> bool:
        return bool(self.parceiros or self.pedidos or self.filiais)


@dataclass
class Absorcao:
    """O que uma absorção acrescentou — é o que a tela conta."""

    registros: int = 0
    parceiros_novos: int = 0
    parceiros_atualizados: int = 0
    pedidos_novos: int = 0
    pedidos_mais_recentes: int = 0
    filiais_novas: int = 0
    primeira_data: str = ""
    ultima_data: str = ""

    @property
    def mudou(self) -> bool:
        return bool(self.parceiros_novos or self.parceiros_atualizados
                    or self.pedidos_novos or self.pedidos_mais_recentes
                    or self.filiais_novas)


# -- onde mora -------------------------------------------------------------

def caminho(raiz: Path | None = None) -> Path:
    # A mesma raiz do livro de classificação, e pela mesma função: quem muda
    # onde o livro mora (a Central nos testes, por exemplo) muda as duas.
    from .. import estado

    base = Path(raiz) if raiz else estado._raiz() / "dados"
    return base / "pendentes" / "conhecimento" / "portal_de_compras.json"


def carregar(raiz: Path | None = None) -> Historico:
    """O histórico gravado. Sem arquivo, ele nasce vazio — não é erro."""
    arquivo = caminho(raiz)
    if not arquivo.is_file():
        return Historico()
    bruto = json.loads(arquivo.read_text(encoding="utf-8")) or {}
    return Historico(
        parceiros=dict(bruto.get("parceiros") or {}),
        pedidos=dict(bruto.get("pedidos") or {}),
        filiais=dict(bruto.get("filiais") or {}),
        fontes=list(bruto.get("fontes") or []),
        atualizado_em=str(bruto.get("atualizado_em") or ""),
        atualizado_por=str(bruto.get("atualizado_por") or ""),
    )


def gravar(historico: Historico, responsavel: str | None = None,
           raiz: Path | None = None) -> Path:
    arquivo = caminho(raiz)
    historico.atualizado_em = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    historico.atualizado_por = (responsavel or os.environ.get("USERNAME")
                                or os.environ.get("USER") or "?")
    arquivo.parent.mkdir(parents=True, exist_ok=True)
    arquivo.write_text(json.dumps({
        "atualizado_em": historico.atualizado_em,
        "atualizado_por": historico.atualizado_por,
        "fontes": historico.fontes[-FONTES_LEMBRADAS:],
        "parceiros": historico.parceiros,
        "pedidos": historico.pedidos,
        "filiais": historico.filiais,
    }, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")
    return arquivo


# -- absorver um relatório -------------------------------------------------

def _texto(valor: Any) -> str:
    """O que vai para o `.json`: texto, sempre. `None` vira vazio."""
    return texto_de(valor).strip()


def _data(valor: Any) -> str:
    if isinstance(valor, datetime):
        return valor.date().isoformat()
    if isinstance(valor, date):
        return valor.isoformat()
    return ""


def _mais_recente(guardado: dict[str, Any] | None, numero_unico: float) -> bool:
    return guardado is None or numero_unico > float(
        guardado.get("numero_unico") or 0)


def absorver(historico: Historico, registros: Sequence[Registro], *,
             prefixo_de_pedido: str, cnpj_descartado: str = CNPJ_ZERADO,
             fonte: dict[str, Any] | None = None) -> Absorcao:
    """Soma ao histórico o que este relatório do Portal de Compras sabe."""
    relato = Absorcao(registros=len(registros))
    datas: list[str] = []
    # O que já estava guardado antes deste relatório. Troca dentro do próprio
    # relatório não é "mais recente que o histórico" — é o relatório se
    # resolvendo, e contá-la inflaria o número da tela.
    parceiros_de_antes = set(historico.parceiros)
    pedidos_de_antes = set(historico.pedidos)
    for registro in registros:
        numero_unico = float(registro.numero_unico or 0)
        dia = _data(registro.data_de_negociacao)
        if dia:
            datas.append(dia)

        empresa = registro.cnpj_da_empresa
        if empresa:
            guardada = historico.filiais.get(empresa)
            if guardada is None:
                relato.filiais_novas += 1
            if _mais_recente(guardada, numero_unico):
                historico.filiais[empresa] = {
                    "nome": _texto(registro.nome_da_empresa),
                    "codigo": _texto(registro.empresa),
                    "numero_unico": numero_unico,
                }

        cnpj = registro.cnpj_do_parceiro
        if not cnpj_utilizavel(cnpj, cnpj_descartado):
            continue

        codigo = _texto(registro.codigo_do_parceiro)
        if codigo:
            guardado = historico.parceiros.get(cnpj)
            if _mais_recente(guardado, numero_unico):
                if guardado is None:
                    relato.parceiros_novos += 1
                elif (cnpj in parceiros_de_antes
                      and guardado.get("codigo") != codigo):
                    relato.parceiros_atualizados += 1
                historico.parceiros[cnpj] = {
                    "codigo": codigo,
                    "nome": _texto(registro.nome_do_parceiro),
                    "numero_unico": numero_unico,
                    "visto_em": dia,
                }

        if registro.e_pedido(prefixo_de_pedido):
            guardado = historico.pedidos.get(cnpj)
            if _mais_recente(guardado, numero_unico):
                if guardado is None:
                    relato.pedidos_novos += 1
                elif cnpj in pedidos_de_antes:
                    relato.pedidos_mais_recentes += 1
                historico.pedidos[cnpj] = {
                    "numero_unico": numero_unico,
                    "comprador": _texto(registro.usuario_de_inclusao),
                    "requisitante": _texto(registro.usuario_do_rc),
                    "natureza": _texto(registro.natureza),
                    "centro_de_resultado": _texto(registro.centro_de_resultado),
                    "empresa": _texto(registro.empresa),
                    "data": dia,
                }

    if datas:
        relato.primeira_data, relato.ultima_data = min(datas), max(datas)
    if fonte is not None:
        historico.fontes.append({
            **fonte, "registros": relato.registros,
            "periodo": [relato.primeira_data, relato.ultima_data],
            "absorvido_em": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        })
    return relato


def impressao(caminho_do_arquivo: Path) -> dict[str, Any]:
    """Nome, tamanho e SHA-256 do relatório absorvido."""
    conteudo = Path(caminho_do_arquivo).read_bytes()
    return {"nome": Path(caminho_do_arquivo).name, "bytes": len(conteudo),
            "sha256": hashlib.sha256(conteudo).hexdigest()}


# -- a entrada Base de conhecimento ----------------------------------------

@dataclass
class Carga:
    """O painel da carga de um Portal de Compras longo no histórico."""

    absorcoes: list[tuple[str, Absorcao]] = field(default_factory=list)
    historico: Historico = field(default_factory=Historico)
    caminho: Path | None = None

    def titulo(self) -> str:
        return (f"Histórico do Portal de Compras — "
                f"{len(self.historico.parceiros)} parceiro(s) e "
                f"{len(self.historico.pedidos)} pedido(s) guardados")

    def fichas(self) -> list[tuple[str, str]]:
        soma = lambda campo: sum(getattr(a, campo)          # noqa: E731
                                 for _, a in self.absorcoes)
        return [
            ("Linhas lidas", str(soma("registros"))),
            ("Parceiros novos", str(soma("parceiros_novos"))),
            ("Pedidos novos", str(soma("pedidos_novos"))),
            ("Pedidos mais recentes", str(soma("pedidos_mais_recentes"))),
            ("Filiais novas", str(soma("filiais_novas"))),
        ]

    def listas(self) -> list[tuple[str, list[str], str]]:
        itens = []
        for nome, absorcao in self.absorcoes:
            periodo = (f"de {absorcao.primeira_data} a {absorcao.ultima_data}"
                       if absorcao.primeira_data else "sem data de negociação")
            itens.append(f"{nome}: {absorcao.registros} linha(s), {periodo}")
        return [
            ("O que entrou", itens, "neutro"),
            ("Para que serve", [
                "a partir da próxima execução do GerarServPend, parceiro sem "
                "movimento na semana deixa de sair como 'Sem cadastro', e o "
                "pedido de compra mais recente é procurado no histórico todo",
                "o confronto continua usando só o Portal de Compras da semana",
            ], "neutro"),
        ]


def carregar_relatorios(caminhos: Iterable[Path | str], *,
                        dados: dict | None = None,
                        raiz: Path | None = None,
                        responsavel: str | None = None,
                        gravar_em_disco: bool = True) -> Carga:
    """Absorve um ou mais relatórios do Portal de Compras no histórico."""
    from .. import papeis, parametros
    from . import colunas as col
    from .execucao import DOMINIO, _ler
    from .fontes import ler_registros

    dados = dados if dados is not None else parametros.carregar()
    ajuste = parametros.confronto_de_servicos(dados)
    papel_do_portal = [p for p in parametros.papeis_de(dados, DOMINIO)
                       if p.id == "portal_de_compras"]
    historico = carregar(raiz)
    carga = Carga(historico=historico)
    for caminho_do_arquivo in caminhos:
        caminho_do_arquivo = Path(caminho_do_arquivo)
        reconhecimento, _ = papeis.ler_e_reconhecer(
            [caminho_do_arquivo], papel_do_portal, col.ABAS)
        _, linhas, mapa = _ler(reconhecimento["portal_de_compras"], dados,
                               "portal_de_compras", "Portal de Compras",
                               col.ANCORA_PORTAL)
        absorcao = absorver(
            historico, ler_registros(linhas, mapa),
            prefixo_de_pedido=ajuste["prefixo_de_pedido"],
            cnpj_descartado=ajuste["cnpj_descartado"],
            fonte={**impressao(caminho_do_arquivo), "como": "carga"})
        carga.absorcoes.append((caminho_do_arquivo.name, absorcao))
    if gravar_em_disco:
        carga.caminho = gravar(historico, responsavel, raiz=raiz)
    return carga


def e_portal_de_compras(caminho_do_arquivo: Path | str,
                        dados: dict | None = None) -> bool:
    """Se o arquivo tem o cabeçalho do Portal de Compras — e só dele."""
    from .. import papeis, parametros
    from . import colunas as col
    from .execucao import DOMINIO

    dados = dados if dados is not None else parametros.carregar()
    todos = parametros.papeis_de(dados, DOMINIO)
    try:
        arquivo = papeis.ler(caminho_do_arquivo,
                             limite_de_linhas=papeis.LINHAS_PARA_ESPIAR)
    except Exception:                                    # noqa: BLE001
        return False
    casados = papeis.casamentos(arquivo, todos, col.ABAS)
    return [p.id for p in casados] == ["portal_de_compras"]
