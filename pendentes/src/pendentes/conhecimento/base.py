"""Onde a base mora, o que ela guarda e como se pergunta a ela.

### Por que `.json` e não `.yaml`

O resto do aplicativo guarda parâmetro em YAML, porque quem edita é gente. A
base de conhecimento tem milhares de entradas, é escrita por importação e é
lida a cada execução — e o YAML puro-Python (sem `CLoader`, que é extensão
compilada e não entra, regra nº 6) leva segundos onde o `json` da biblioteca
padrão leva milissegundos. Quem precisa ler a base lê o relatório da
importação, que é feito para gente.

### Por que fora do git

Código de parceiro, nome de fornecedor, nome de área e primeiro nome de
gestor. É dado da empresa inteiro — regra nº 1. A base vive em
`dados/pendentes/conhecimento/`, ao lado do livro de classificação, e nasce
**vazia**: numa máquina nova nada é proposto até alguém importar.

### A precedência das consultas

`[FATO]` É a da fonte (prioridade 4): **parceiro + unidade** antes de
**parceiro**. Uma regra geral não pode encobrir um conflito que existe no
nível específico — se para aquele parceiro naquela unidade o histórico briga
consigo mesmo, a resposta é o conflito, e não a média de todas as unidades.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ..texto import chave_de_texto

#: Os três graus de confiança. Só o primeiro pode preencher célula.
FIRME = "firme"
SUGESTAO = "sugestao"
SEM_PROPOSTA = "sem proposta"

#: O que o cruzamento entre proposta e evidência encontrou. Vai para a tela e
#: para o relatório da importação — é o que explica por que algo é só
#: sugestão.
LASTRO_CONFIRMA = "o histórico confirma"
LASTRO_CURTO = "evidência curta"
LASTRO_DIVERGE = "o histórico diverge"
LASTRO_AUSENTE = "sem lastro no histórico"

#: O que a fonte chama de "repetida sem divergência", em números: três notas
#: distintas, em duas semanas, com 100% do mesmo rótulo. É o limiar que separa
#: preencher de sugerir, e está aqui, em um lugar só.
NOTAS_PARA_FIRMAR = 3
SEMANAS_PARA_FIRMAR = 2


@dataclass(frozen=True)
class Evidencia:
    """Quanto o histórico sustenta um valor."""

    valor: str = ""
    notas: int = 0
    apoio: int = 0
    semanas: int = 0
    alternativas: dict[str, int] = field(default_factory=dict)

    @property
    def taxa(self) -> float:
        return self.apoio / self.notas if self.notas else 0.0

    @property
    def repetida_sem_divergencia(self) -> bool:
        return (self.notas >= NOTAS_PARA_FIRMAR
                and self.semanas >= SEMANAS_PARA_FIRMAR
                and self.apoio == self.notas)

    def como_dicionario(self) -> dict[str, Any]:
        return {"valor": self.valor, "notas": self.notas, "apoio": self.apoio,
                "semanas": self.semanas, "alternativas": self.alternativas}

    @staticmethod
    def de(bruto: dict[str, Any] | None) -> "Evidencia":
        bruto = bruto or {}
        return Evidencia(
            valor=str(bruto.get("valor") or ""),
            notas=int(bruto.get("notas") or 0),
            apoio=int(bruto.get("apoio") or 0),
            semanas=int(bruto.get("semanas") or 0),
            alternativas={str(k): int(v)
                          for k, v in (bruto.get("alternativas") or {}).items()},
        )


@dataclass(frozen=True)
class Proposta:
    """O que a base responde sobre um campo de uma nota.

    `confianca` é o que decide o que fazer com ela, e `lastro` é o que explica
    a confiança para quem lê a tela. Proposta sem valor é resposta legítima:
    "não sei" é melhor do que um palpite.
    """

    campo: str
    valor: str = ""
    confianca: str = SEM_PROPOSTA
    lastro: str = LASTRO_AUSENTE
    nivel: str = ""
    evidencia: Evidencia = field(default_factory=Evidencia)

    def __bool__(self) -> bool:
        return bool(self.valor)

    @property
    def pode_preencher(self) -> bool:
        return self.confianca == FIRME and bool(self.valor)


#: As palavras que ligam e não classificam. `Compra Uso e Consumo` e
#: `Compra Uso Consumo` são o mesmo tipo de operação escrito por duas pessoas
#: diferentes, e tratá-los como valores distintos faz a ferramenta discordar
#: de si mesma.
#:
#: `[FATO]` A lista é fechada e curta de propósito. Ela remove conectivo, não
#: aproxima palavras: `Compra MP` e `Compra Embalagem` continuam diferentes,
#: porque o que os separa é substantivo. Normalizar é tirar ruído conhecido —
#: casar por semelhança seria adivinhação, e é outra coisa.
PALAVRAS_DE_LIGACAO = ("E", "DE", "DA", "DO", "DAS", "DOS", "EM", "COM",
                       "PARA", "POR", "A", "O", "AS", "OS")


def chave_de_operacao(valor: Any) -> str:
    """O `Tipo de Operação` sem o que nele é só ligação."""
    palavras = [p for p in chave_de_texto(valor).split()
                if p not in PALAVRAS_DE_LIGACAO]
    return " ".join(palavras)


def _confianca(valor: str, evidencia: Evidencia) -> tuple[str, str]:
    """O cruzamento entre o que se propõe e o que o histórico mostra.

    Preencher exige as duas coisas dizendo o mesmo, com lastro. Qualquer outra
    combinação é sugestão — inclusive a proposta que o histórico **nunca viu**,
    que é o caso mais comum quando a lista curada troca o nome de uma pessoa
    pela área a que ela pertence.
    """
    if not valor:
        return SEM_PROPOSTA, LASTRO_AUSENTE
    if not evidencia.notas:
        return SUGESTAO, LASTRO_AUSENTE
    mesmo = chave_de_texto(valor) == chave_de_texto(evidencia.valor)
    if mesmo and evidencia.repetida_sem_divergencia:
        return FIRME, LASTRO_CONFIRMA
    if mesmo:
        return SUGESTAO, LASTRO_CURTO
    if chave_de_texto(valor) in {chave_de_texto(a) for a in evidencia.alternativas}:
        return SUGESTAO, LASTRO_DIVERGE
    return SUGESTAO, LASTRO_AUSENTE


@dataclass
class Conhecimento:
    """A base inteira, como ela fica no disco."""

    dominio: str = "mercadorias"
    versao_da_fonte: str = ""
    ultimo_relatorio_classificado: int = 0
    importado_em: str = ""
    importado_por: str = ""
    fontes: list[dict[str, Any]] = field(default_factory=list)
    #: `codigo do parceiro` → {nome, guardiao, categoria, unidades: {...}}
    parceiros: dict[str, dict[str, Any]] = field(default_factory=dict)
    #: `CFOP normalizado` → os quatro níveis daquele CFOP, cada um com a
    #: proposta de `Tipo de Operação` e a evidência que a sustenta.
    operacoes: dict[str, dict[str, Any]] = field(default_factory=dict)
    #: `guardião normalizado` → o gestor vigente dele
    gestor_do_guardiao: dict[str, dict[str, Any]] = field(default_factory=dict)
    #: Os guardiões que o histórico mostrou. **Não** é a lista de validação:
    #: essa é cadastrada na tela, e enchê-la daqui faria a semana seguinte
    #: bloquear em cima de nome que ninguém conferiu.
    guardioes_observados: list[str] = field(default_factory=list)

    def __len__(self) -> int:
        return len(self.parceiros)

    @property
    def vazia(self) -> bool:
        """Sem parceiro **e** sem operação não há o que propor.

        As duas metades são independentes: uma base só de operação continua
        servindo para `Tipo de Operação`, e contar só parceiros a daria por
        inútil.
        """
        return not self.parceiros and not self.operacoes

    # -- a consulta --------------------------------------------------------

    def propor(self, codigo: Any, campo: str, fantasia: Any = "") -> Proposta:
        """O que a base tem a dizer sobre um campo daquela nota.

        `campo` é `guardiao` ou `categoria`. A unidade vem do `Nome Fantasia`
        da própria nota, como no relatório — e é comparada normalizada, porque
        `HINOVE  (REGISTRO)`, com dois espaços, é a mesma coisa que
        `Hinove (Registro)`.
        """
        parceiro = self.parceiros.get(_codigo(codigo))
        if not parceiro:
            return Proposta(campo)

        unidade = (parceiro.get("unidades") or {}).get(chave_de_texto(fantasia))
        for origem, nivel in ((unidade, "parceiro + unidade"),
                              (parceiro, "parceiro")):
            if not origem:
                continue
            bruto = (origem.get(campo) or {})
            valor = str(bruto.get("proposto") or "")
            if not valor:
                continue
            evidencia = Evidencia.de(bruto.get("evidencia"))
            confianca, lastro = _confianca(valor, evidencia)
            return Proposta(campo, valor, confianca, lastro, nivel, evidencia)
        return Proposta(campo)

    def gestor_de(self, guardiao: Any) -> Proposta:
        """O gestor vigente daquele guardião.

        `[FATO]` Gestor não se mede por repetição: a regra da fonte é *o
        gestor com mais notas na última observação daquele guardião*, e só o
        empate impede escolher. Então o que firma aqui é a **ausência de
        empate**, e não três notas em duas semanas.
        """
        bruto = self.gestor_do_guardiao.get(chave_de_texto(guardiao))
        if not bruto:
            return Proposta("gestor")
        valor = str(bruto.get("proposto") or "")
        if not valor:
            return Proposta("gestor")
        evidencia = Evidencia.de(bruto.get("evidencia"))
        empatado = any(
            quantas >= evidencia.apoio
            and chave_de_texto(outro) != chave_de_texto(valor)
            for outro, quantas in evidencia.alternativas.items())
        confianca = SUGESTAO if empatado else FIRME
        lastro = LASTRO_DIVERGE if empatado else LASTRO_CONFIRMA
        return Proposta("gestor", valor, confianca, lastro, "guardião", evidencia)

    def propor_operacao(self, cfop: str, codigo: Any = "",
                        categoria: Any = "") -> Proposta:
        """O `Tipo de Operação` daquele CFOP, no nível mais específico que houver.

        `[FATO]` A ordem é a da prioridade 6 da fonte: CFOP + parceiro +
        categoria, depois CFOP + parceiro, depois CFOP + categoria, depois
        CFOP sozinho. `cfop` já vem normalizado — conjunto de CFOP casa por
        correspondência exata do conjunto, não de um dos códigos.
        """
        niveis = self.operacoes.get(cfop or "")
        if not niveis:
            return Proposta("operacao")
        parceiro, classe = _codigo(codigo), chave_de_texto(categoria)
        for chave in (f"{parceiro}|{classe}", f"{parceiro}|", f"|{classe}", "|"):
            bruto = niveis.get(chave)
            if not bruto:
                continue
            evidencia = Evidencia.de(bruto.get("evidencia"))
            valor = str(bruto.get("proposto") or "")
            confianca, lastro = _confianca(valor, evidencia)
            return Proposta("operacao", valor, confianca, lastro,
                            _nivel_do_cfop(chave), evidencia)
        return Proposta("operacao")

    def nome_do_parceiro(self, codigo: Any) -> str:
        return str((self.parceiros.get(_codigo(codigo)) or {}).get("nome") or "")

    # -- disco -------------------------------------------------------------

    def como_dicionario(self) -> dict[str, Any]:
        return {
            "dominio": self.dominio,
            "versao_da_fonte": self.versao_da_fonte,
            "ultimo_relatorio_classificado": self.ultimo_relatorio_classificado,
            "importado_em": self.importado_em,
            "importado_por": self.importado_por,
            "fontes": self.fontes,
            "guardioes_observados": self.guardioes_observados,
            "gestor_do_guardiao": self.gestor_do_guardiao,
            "operacoes": self.operacoes,
            "parceiros": self.parceiros,
        }


def _nivel_do_cfop(chave: str) -> str:
    """O nome do nível sai da **chave encontrada**, não da ordem da busca.

    Com categoria vazia, a primeira tentativa (`parceiro|`) é idêntica à
    segunda — e chamá-la de "CFOP + parceiro + categoria" descreveria uma
    especificidade que a regra não tem.
    """
    parceiro, _, categoria = chave.partition("|")
    partes = ["CFOP"]
    if parceiro:
        partes.append("parceiro")
    if categoria:
        partes.append("categoria")
    return " + ".join(partes)


def _codigo(valor: Any) -> str:
    """O código do parceiro como texto, sem o `.0` que o Excel enfia nele."""
    if isinstance(valor, float) and valor.is_integer():
        return str(int(valor))
    texto = str(valor or "").strip()
    if texto.endswith(".0") and texto[:-2].isdigit():
        return texto[:-2]
    return texto


def _raiz() -> Path:
    for pasta in Path(__file__).resolve().parents:
        if (pasta / "vendor" / "openpyxl").is_dir():
            return pasta
    return Path(__file__).resolve().parents[4]   # pragma: no cover


def caminho_da_base(dominio: str = "mercadorias",
                    raiz: Path | None = None) -> Path:
    """`dados/pendentes/conhecimento/<domínio>.json` — fora do git."""
    base = Path(raiz) if raiz else _raiz() / "dados"
    return base / "pendentes" / "conhecimento" / f"{dominio}.json"


def carregar(dominio: str = "mercadorias",
             raiz: Path | None = None) -> Conhecimento:
    """A base do disco. Sem base, uma vazia — que não propõe nada."""
    caminho = caminho_da_base(dominio, raiz)
    if not caminho.is_file():
        return Conhecimento(dominio=dominio)
    bruto = json.loads(caminho.read_text(encoding="utf-8"))
    return Conhecimento(
        dominio=str(bruto.get("dominio") or dominio),
        versao_da_fonte=str(bruto.get("versao_da_fonte") or ""),
        ultimo_relatorio_classificado=int(
            bruto.get("ultimo_relatorio_classificado") or 0),
        importado_em=str(bruto.get("importado_em") or ""),
        importado_por=str(bruto.get("importado_por") or ""),
        fontes=list(bruto.get("fontes") or []),
        parceiros=dict(bruto.get("parceiros") or {}),
        gestor_do_guardiao=dict(bruto.get("gestor_do_guardiao") or {}),
        operacoes=dict(bruto.get("operacoes") or {}),
        guardioes_observados=list(bruto.get("guardioes_observados") or []),
    )


def gravar(conhecimento: Conhecimento, raiz: Path | None = None) -> Path:
    """Grava a base inteira. Importação substitui — ela não mescla.

    Mesclar duas fotografias de épocas diferentes produziria uma terceira que
    nunca existiu, com evidência somada de execuções que contaram as mesmas
    notas. A importação é a fotografia, e a anterior fica no histórico de quem
    guardou o arquivo de origem.
    """
    caminho = caminho_da_base(conhecimento.dominio, raiz)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(
        json.dumps(conhecimento.como_dicionario(), ensure_ascii=False, indent=1),
        encoding="utf-8")
    return caminho
