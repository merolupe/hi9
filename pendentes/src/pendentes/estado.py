"""O livro de classificação: onde o julgamento humano passa a morar.

Hoje o estado da rotina vive **dentro do `.xls` da semana anterior**. Quem
renomeia errado, perde o anexo do e-mail ou salva por cima perde o trabalho de
classificação de todo mundo — e o módulo de mercadorias chega a **abortar**
quando o arquivo da semana passada não está lá.

Aqui a planilha deixa de ser a fonte da verdade e vira **ida e volta**:

```
segunda    arrasta os relatórios da semana  →  a Central gera a planilha
           (o livro preenche as colunas de classificação)
a semana   o time edita as colunas na planilha e cobra por e-mail,
           exatamente como hoje
quarta,    arrasta a planilha editada de volta  →  a Central INGERE as
sexta      colunas no livro, carimba, e REGERA a planilha inteira
```

O livro mora em `dados/pendentes/classificacao/<domínio>.yaml`, **fora do
git** — é dado da empresa (nome de guardião, de gestor, de parceiro), regra
nº 1 —, e carimba quem gravou e quando, como a base do Fiscalbot.

### As cinco regras da ingestão

1. As colunas são lidas **por cabeçalho**, nunca por posição. O VBA lê as
   colunas 1 a 5 da aba anterior por posição fixa; basta alguém inserir uma
   coluna para a herança embaralhar os campos sem erro nenhum.
2. Onde o arquivo diverge do livro, **o arquivo vence** — é a edição humana
   mais recente — e a divergência é contada para a tela.
3. Onde o arquivo está vazio e o livro tem valor, **o livro vence**. É o que
   conserta o defeito de hoje: nota que saiu de `Pendentes` (foi lançada,
   cancelada ou roteada) perde a classificação, e se voltar, volta vazia. O
   livro guarda todo mundo, para sempre.
4. Chave que não existe no livro entra como registro novo.
5. A ingestão é **idempotente**: arrastar o mesmo arquivo duas vezes não muda
   nada na segunda.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Iterable, Sequence

import yaml

from . import cabecalho as cab
from .texto import aparar

#: Os quatro campos de classificação que o time preenche na planilha. O
#: retorno é o quinto, mas ele é por semana e mora em `retornos`.
CAMPOS = ("tipo_de_operacao", "guardiao", "gestor_de_apoio", "categoria")

#: O contexto da nota — **não** é julgamento humano, e por isso não entra em
#: `CAMPOS`: ele não conta como "alterada" na ingestão e o valor mais recente
#: vence em silêncio. Existe para a base de conhecimento poder aprender do
#: livro: sem código de parceiro, CFOP, unidade e semana, o livro sabe *o que*
#: foi decidido mas não *sobre o que*, e a evidência não se refaz.
CONTEXTO = ("semana", "codigo_do_parceiro", "cfop", "fantasia")

#: Como cada campo se chama na planilha. O primeiro é o nome canônico.
NOMES_NA_PLANILHA: dict[str, tuple[str, ...]] = {
    "tipo_de_operacao": ("Tipo de Operação", "Tipo de Operacao"),
    "guardiao": ("Guardião", "Guardiao"),
    "gestor_de_apoio": ("Gestor de apoio", "Gestor de Apoio"),
    "categoria": ("Categoria",),
}

#: O título da coluna de retorno carrega o número da semana, então ela é
#: procurada por prefixo — é a única coluna do projeto que muda de nome.
PREFIXO_DO_RETORNO = "Retorno"


@dataclass
class Classificacao:
    """O que uma pessoa decidiu sobre um documento, e quando."""

    chave: str
    tipo_de_operacao: str = ""
    guardiao: str = ""
    gestor_de_apoio: str = ""
    categoria: str = ""
    retornos: dict[int, str] = field(default_factory=dict)
    #: O CNPJ do emitente, quando a execução o conhece.
    #:
    #: Não faz parte da chave e nunca vem da planilha — a aba `Pendentes` de
    #: serviços não carrega CNPJ, e é por isso que a identidade entre semanas
    #: é `número | código do parceiro`. Guardá-lo aqui é o que permite
    #: **perceber** a colisão: dois prestadores distintos sem cadastro no
    #: Sankhya compartilham o literal `Sem cadastro` e podem produzir a mesma
    #: chave. Hoje isso acontece em silêncio; com o CNPJ gravado, a execução
    #: seguinte vê que o registro mudou de dono e conta o caso.
    cnpj: str = ""
    #: O contexto da nota, para a base aprender. Ver `CONTEXTO`.
    semana: int = 0
    codigo_do_parceiro: str = ""
    cfop: str = ""
    fantasia: str = ""
    origem: str = ""
    gravado_por: str = ""
    gravado_em: str = ""

    def vazia(self) -> bool:
        return not any(getattr(self, campo) for campo in CAMPOS) and not self.retornos

    def retorno_da_semana(self, semana: int) -> str:
        return self.retornos.get(semana, "")

    @property
    def ultimo_retorno(self) -> str:
        """O retorno da semana mais recente que o livro guardou.

        A planilha carrega **uma** coluna de retorno; o livro guarda todas. É
        esta que volta para a planilha da semana seguinte — que é o que o VBA
        fazia ao copiar a coluna de um arquivo para o outro, só que sem
        depender de o arquivo existir.
        """
        if not self.retornos:
            return ""
        return self.retornos[max(self.retornos)]


@dataclass
class Livro:
    """Todas as classificações de um domínio, indexadas pela chave."""

    dominio: str
    registros: dict[str, Classificacao] = field(default_factory=dict)
    atualizado_em: str = ""
    atualizado_por: str = ""

    def __len__(self) -> int:
        return len(self.registros)

    def obter(self, chave: str) -> Classificacao | None:
        return self.registros.get(chave)

    def de(self, chave: str) -> Classificacao:
        """A classificação daquela chave, ou uma vazia — nunca `None`."""
        return self.registros.get(chave) or Classificacao(chave)


@dataclass
class Ingestao:
    """O que a ingestão de uma planilha editada mudou no livro."""

    lidas: int = 0
    novas: int = 0
    alteradas: int = 0
    preservadas: int = 0
    inalteradas: int = 0
    retornos: int = 0
    detalhes: list[str] = field(default_factory=list)

    @property
    def mudou(self) -> bool:
        return bool(self.novas or self.alteradas or self.retornos)


# -- onde o livro mora -----------------------------------------------------

def _raiz() -> Path:
    for pasta in Path(__file__).resolve().parents:
        if (pasta / "vendor" / "openpyxl").is_dir():
            return pasta
    return Path(__file__).resolve().parents[3]         # pragma: no cover


def caminho_do_livro(dominio: str, raiz: Path | None = None) -> Path:
    base = Path(raiz) if raiz else _raiz() / "dados"
    return base / "pendentes" / "classificacao" / f"{dominio}.yaml"


def carregar(dominio: str, caminho: Path | None = None,
             raiz: Path | None = None) -> Livro:
    """O livro do domínio. Na primeira execução ele nasce vazio — não é erro."""
    caminho = Path(caminho) if caminho else caminho_do_livro(dominio, raiz)
    if not caminho.is_file():
        return Livro(dominio)
    bruto = yaml.safe_load(caminho.read_text(encoding="utf-8")) or {}
    registros = {}
    for linha in bruto.get("registros") or []:
        chave = str(linha.get("chave", "")).strip()
        if not chave:
            continue
        registros[chave] = Classificacao(
            chave=chave,
            tipo_de_operacao=str(linha.get("tipo_de_operacao", "") or ""),
            guardiao=str(linha.get("guardiao", "") or ""),
            gestor_de_apoio=str(linha.get("gestor_de_apoio", "") or ""),
            categoria=str(linha.get("categoria", "") or ""),
            retornos={int(s): str(v or "")
                      for s, v in (linha.get("retornos") or {}).items()},
            cnpj=str(linha.get("cnpj", "") or ""),
            semana=int(linha.get("semana") or 0),
            codigo_do_parceiro=str(linha.get("codigo_do_parceiro", "") or ""),
            cfop=str(linha.get("cfop", "") or ""),
            fantasia=str(linha.get("fantasia", "") or ""),
            origem=str(linha.get("origem", "") or ""),
            gravado_por=str(linha.get("gravado_por", "") or ""),
            gravado_em=str(linha.get("gravado_em", "") or ""),
        )
    return Livro(
        dominio=str(bruto.get("dominio", dominio) or dominio),
        registros=registros,
        atualizado_em=str(bruto.get("atualizado_em", "") or ""),
        atualizado_por=str(bruto.get("atualizado_por", "") or ""),
    )


def para_dicionario(livro: Livro) -> dict[str, Any]:
    return {
        "dominio": livro.dominio,
        "atualizado_em": livro.atualizado_em,
        "atualizado_por": livro.atualizado_por,
        "registros": [
            {
                "chave": r.chave,
                "tipo_de_operacao": r.tipo_de_operacao,
                "guardiao": r.guardiao,
                "gestor_de_apoio": r.gestor_de_apoio,
                "categoria": r.categoria,
                "retornos": dict(sorted(r.retornos.items())),
                "cnpj": r.cnpj,
                "semana": r.semana,
                "codigo_do_parceiro": r.codigo_do_parceiro,
                "cfop": r.cfop,
                "fantasia": r.fantasia,
                "origem": r.origem,
                "gravado_por": r.gravado_por,
                "gravado_em": r.gravado_em,
            }
            for r in sorted(livro.registros.values(), key=lambda r: r.chave)
        ],
    }


def gravar(livro: Livro, responsavel: str | None = None,
           caminho: Path | None = None, raiz: Path | None = None) -> Path:
    """Grava o livro e carimba quem alterou e quando."""
    caminho = Path(caminho) if caminho else caminho_do_livro(livro.dominio, raiz)
    livro.atualizado_em = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    livro.atualizado_por = responsavel or _quem()
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(
        yaml.safe_dump(para_dicionario(livro), allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    return caminho


def _quem(responsavel: str | None = None) -> str:
    return (responsavel or os.environ.get("USERNAME")
            or os.environ.get("USER") or "?")


# -- ler a planilha editada ------------------------------------------------

def semana_do_rotulo(rotulo: str, padrao: int | None = None) -> int | None:
    """`Retorno semana 30` devolve `30`.

    O rótulo carrega o número da **semana anterior**, e não o da corrente —
    a leitura pretendida é "retorno recebido referente à cobrança da semana
    passada". Ler o número do próprio rótulo é o que evita ter de sabê-lo.
    """
    digitos = "".join(c if c.isdigit() else " " for c in str(rotulo)).split()
    return int(digitos[-1]) if digitos else padrao


def extrair_da_planilha(
    cabecalho: Sequence[Any],
    linhas: Iterable[Sequence[Any]],
    *,
    colunas_da_chave: Sequence[str],
    montar_chave: Callable[[list[Any]], str],
    semana: int | None = None,
    sinonimos: dict[str, Sequence[str]] | None = None,
    colunas_do_contexto: dict[str, Sequence[str]] | None = None,
) -> list[Classificacao]:
    """As classificações que estão numa aba `Pendentes`, lidas por cabeçalho.

    `colunas_da_chave` são as colunas que formam a identidade do documento, e
    `montar_chave` recebe os valores dessas colunas na linha. É o que permite
    a mesma leitura servir aos dois domínios: mercadorias identifica por
    `Chave Acesso`, serviços por número da nota mais código do parceiro.

    `colunas_do_contexto` diz onde estão código do parceiro, CFOP e unidade
    naquela aba — os nomes mudam entre os domínios, e quem sabe deles é quem
    chama. Coluna que não existir na aba simplesmente não vem: o contexto é o
    que permite a base aprender, e não ter a informação é melhor do que
    abortar a ingestão da classificação por causa dela.
    """
    sinonimos = sinonimos or {}
    posicoes_da_chave = [
        cab.achar(cabecalho, nome, sinonimos.get(nome, ()))
        for nome in colunas_da_chave
    ]
    if any(p < 0 for p in posicoes_da_chave):
        faltando = [nome for nome, p in zip(colunas_da_chave, posicoes_da_chave)
                    if p < 0]
        raise cab.ColunasFaltando("da semana anterior", faltando)

    posicoes = {
        campo: cab.achar(cabecalho, nomes[0], nomes[1:] + tuple(sinonimos.get(campo, ())))
        for campo, nomes in NOMES_NA_PLANILHA.items()
    }
    coluna_do_retorno = cab.achar_por_prefixo(cabecalho, PREFIXO_DO_RETORNO)
    semana_do_retorno = (
        semana_do_rotulo(cabecalho[coluna_do_retorno], semana)
        if 0 <= coluna_do_retorno < len(cabecalho) else semana
    )

    posicoes_do_contexto = {}
    for campo, nomes in (colunas_do_contexto or {}).items():
        nomes = tuple(nomes)
        achada = cab.achar(cabecalho, nomes[0], nomes[1:])
        if achada >= 0:
            posicoes_do_contexto[campo] = achada

    def valor(linha: Sequence[Any], posicao: int) -> str:
        return aparar(linha[posicao]) if 0 <= posicao < len(linha) else ""

    extraidas = []
    for linha in linhas:
        chave = montar_chave([
            linha[p] if p < len(linha) else "" for p in posicoes_da_chave
        ])
        if not chave:
            continue
        registro = Classificacao(chave=chave)
        for campo, posicao in posicoes.items():
            setattr(registro, campo, valor(linha, posicao))
        if semana:
            registro.semana = semana
        for campo, posicao in posicoes_do_contexto.items():
            lido = valor(linha, posicao)
            if lido:
                setattr(registro, campo, lido)
        retorno = valor(linha, coluna_do_retorno)
        if retorno and semana_do_retorno is not None:
            registro.retornos[semana_do_retorno] = retorno
        extraidas.append(registro)
    return extraidas


# -- ingerir ---------------------------------------------------------------

def ingerir(livro: Livro, classificacoes: Iterable[Classificacao], *,
            origem: str = "", responsavel: str | None = None,
            agora: str | None = None) -> Ingestao:
    """Traz para o livro o que uma planilha editada trouxe de volta.

    Conta o que fez, em vez de mudar em silêncio: são esses números que a
    tela mostra depois ("312 classificações alteradas pelo retorno").
    """
    relato = Ingestao()
    carimbo = agora or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    quem = _quem(responsavel)

    for entrada in classificacoes:
        relato.lidas += 1
        atual = livro.registros.get(entrada.chave)
        if atual is None:
            novo = Classificacao(
                chave=entrada.chave,
                retornos=dict(entrada.retornos),
                origem=origem or "planilha",
                gravado_por=quem, gravado_em=carimbo,
            )
            for campo in (*CAMPOS, *CONTEXTO):
                setattr(novo, campo, getattr(entrada, campo))
            livro.registros[entrada.chave] = novo
            relato.novas += 1
            relato.retornos += len(entrada.retornos)
            continue

        # O contexto não é julgamento: o mais recente vence, sem contar nada.
        for campo in CONTEXTO:
            veio = getattr(entrada, campo)
            if veio:
                setattr(atual, campo, veio)

        mudou = False
        for campo in CAMPOS:
            veio = getattr(entrada, campo)
            tinha = getattr(atual, campo)
            if not veio:
                # Regra 3: o arquivo em branco não apaga o que o livro sabe.
                if tinha:
                    relato.preservadas += 1
                continue
            if veio != tinha:
                # Regra 2: a edição humana mais recente vence, e é contada.
                setattr(atual, campo, veio)
                relato.alteradas += 1
                relato.detalhes.append(
                    f"{entrada.chave}: {campo} de "
                    f"{tinha or '(vazio)'} para {veio}"
                )
                mudou = True

        for semana, texto in entrada.retornos.items():
            if texto and atual.retornos.get(semana) != texto:
                atual.retornos[semana] = texto
                relato.retornos += 1
                mudou = True

        if mudou:
            atual.origem = origem or atual.origem
            atual.gravado_por = quem
            atual.gravado_em = carimbo
        else:
            relato.inalteradas += 1
    return relato


def registrar_identidade(livro: Livro, chave: str, cnpj: str) -> bool:
    """Grava no registro o CNPJ de quem emitiu, e diz se o dono mudou.

    A identidade entre semanas é `número da nota | código do parceiro`, porque
    é a única que a planilha carrega. Para todo prestador **sem cadastro** no
    Sankhya a segunda metade é o mesmo literal, e dois fornecedores distintos
    com o mesmo número normalizado produzem a mesma chave — a classificação de
    um passaria a valer para o outro.

    Isto não elimina a colisão: elimina o **silêncio** dela. Quando o CNPJ
    gravado difere do CNPJ de agora, a função devolve `True`, a execução conta
    o caso e a tela mostra. Ver a decisão pendente sobre acrescentar o CNPJ à
    planilha, que é o que resolveria de vez — ao preço de mudar a largura da
    aba, que é invariante da prova.
    """
    registro = livro.registros.get(chave)
    if registro is None or not cnpj:
        return False
    if registro.cnpj and registro.cnpj != cnpj:
        registro.cnpj = cnpj
        return True
    registro.cnpj = cnpj
    return False
