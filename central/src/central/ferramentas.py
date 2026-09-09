"""O catálogo: o que a central mostra na tela e o que cada ferramenta declara.

Este arquivo é o **contrato de ferramenta** do repositório. Para uma automação
do setor aparecer na janela, ela precisa dizer três coisas:

1. **quem é** — nome, uma linha de resumo e o estado em que está;
2. **o que pede** — que arquivo, quais extensões, um ou vários (`Entrada`);
3. **o que devolve** — números para a tela e, quando houver, uma planilha
   para baixar (`Resultado`).

Só isso. A ferramenta não sabe que existe navegador, não monta HTML e não
conhece as outras — quem costura é a central. Foi assim que o DiXML entrou
sem nenhuma linha de interface própria, e é assim que os próximos entram.

**Ferramenta ainda não importada também é declarada aqui**, com estado
`A_IMPORTAR`. Aparece na tela apagada, com o nome e o que faz. O time enxerga
o que ainda falta, em vez de descobrir que falta quando precisar.
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

# -- estados ---------------------------------------------------------------

#: Roda dentro da própria janela da central.
DISPONIVEL = "disponivel"
#: Tem tela própria; a central abre a janela dela. Caso do Apurabot.
JANELA_PROPRIA = "janela"
#: Já existe e é usada pelo time, mas ainda não veio para o repositório.
A_IMPORTAR = "a_importar"


# -- o que a ferramenta pede -----------------------------------------------

@dataclass(frozen=True)
class Entrada:
    """O arquivo que a ferramenta pede, e como pedi-lo na tela."""

    rotulo: str
    apoio: str
    extensoes: tuple[str, ...]
    varios: bool = False


# -- o que a ferramenta devolve --------------------------------------------

@dataclass(frozen=True)
class Ficha:
    """Um número do resumo, em destaque."""

    rotulo: str
    valor: str


@dataclass(frozen=True)
class Lista:
    """O que precisa ser visto item a item — o que ficou de fora, o que falhou.

    `tom` é `"neutro"`, `"atencao"` ou `"erro"`; muda só a cor.
    """

    titulo: str
    itens: list[str]
    tom: str = "neutro"


@dataclass(frozen=True)
class Resultado:
    """O que a central mostra quando a ferramenta termina."""

    titulo: str
    fichas: list[Ficha] = field(default_factory=list)
    listas: list[Lista] = field(default_factory=list)
    planilha: Path | None = None


# -- o que se configura na ferramenta --------------------------------------

@dataclass(frozen=True)
class Campo:
    """Uma coluna da tela de configuração."""

    chave: str
    rotulo: str
    largura: int = 14
    ajuda: str = ""
    tipo: str = "texto"                 # texto | numero | booleano


@dataclass(frozen=True)
class Secao:
    """Uma tabela editável na tela de configuração.

    `fixa` marca a seção que tem uma linha só e não aceita acrescentar nem
    remover — é o caso dos parâmetros gerais de um motor.
    """

    id: str
    titulo: str
    explicacao: str
    campos: tuple[Campo, ...]
    fixa: bool = False


@dataclass(frozen=True)
class Configuracao:
    """O que a ferramenta guarda entre uma execução e outra.

    A **terceira parte do contrato**, ao lado de "o que pede" e "o que devolve".
    O Fiscalbot foi a primeira ferramenta com estado próprio: as regras
    tributárias dele são cadastradas aqui, não em planilha nem em arquivo no
    git. `ler` devolve o que está gravado; `gravar` confere e grava, e
    responde `(gravou, problemas)` — com erro não grava, com aviso grava e
    conta o que vai acontecer.
    """

    resumo: str
    secoes: Callable[[], list[Secao]]
    ler: Callable[[], dict[str, list[dict]]]
    gravar: Callable[[dict, str], tuple[bool, list[dict]]]


@dataclass(frozen=True)
class Ferramenta:
    """Uma automação do setor, do jeito que a central precisa conhecê-la."""

    id: str
    nome: str
    resumo: str
    icone: str
    estado: str
    entrada: Entrada | None = None
    verbo: str = "Processando…"
    detalhe: str = ""
    executar: Callable[[list[Path], Path], Resultado] | None = None
    configuracao: Configuracao | None = None


# -- DiXML -----------------------------------------------------------------

def _milhar(n: int) -> str:
    """1234 vira "1.234" — separador de milhar brasileiro, sem depender de locale."""
    return f"{n:,}".replace(",", ".")


def _rodar_dixml(arquivos: list[Path], saida: Path) -> Resultado:
    """Lê os `.zip`, grava a planilha e devolve o resumo para a tela."""
    from dixml.extracao import escrever, extrair, nome_sugerido

    lido = extrair(arquivos)
    planilha = escrever(lido, saida / nome_sugerido())

    listas = []
    if lido.nao_reconhecidos:
        listas.append(Lista(
            "Não entraram na planilha — eventos, cartas de correção, inutilizações",
            lido.nao_reconhecidos, "neutro",
        ))
    if lido.com_erro:
        listas.append(Lista("XML que não deu para ler", lido.com_erro, "erro"))
    if lido.pacotes_com_erro:
        listas.append(Lista("Pacotes ilegíveis", lido.pacotes_com_erro, "erro"))

    return Resultado(
        titulo=f"{_milhar(lido.xmls_lidos)} XML lidos de "
               f"{len(lido.pacotes)} pacote(s)",
        fichas=[
            Ficha("Notas (NF-e)", _milhar(lido.notas)),
            Ficha("Linhas de item", _milhar(len(lido.nfe))),
            Ficha("Conhecimentos (CT-e)", _milhar(lido.conhecimentos)),
            Ficha("Não reconhecidos", _milhar(len(lido.nao_reconhecidos))),
        ],
        listas=listas,
        planilha=planilha,
    )


# -- Fiscalbot -------------------------------------------------------------

def _rodar_fiscalbot(arquivos: list[Path], saida: Path) -> Resultado:
    """Audita o Livro Fiscal e devolve o resumo para a tela."""
    from fiscalbot.execucao import auditar, escrever, nome_sugerido

    resultado = auditar(arquivos[0])
    planilha = escrever(resultado, saida / nome_sugerido(resultado.arquivo))

    listas = [Lista(
        "Ocorrências por dimensão",
        [f"{rotulo}: {_milhar(quantos)}"
         for rotulo, quantos in resultado.por_dimensao() if quantos],
        "atencao",
    )] if any(q for _, q in resultado.por_dimensao()) else []

    manuais = resultado.manuais_por_operacao()
    if manuais:
        listas.append(Lista(
            "Ficaram para validação manual, por operação",
            [f"{operacao}: {quantos}" for operacao, quantos in manuais],
            "neutro",
        ))

    faltando = resultado.colunas_nao_encontradas
    if faltando:
        listas.append(Lista(
            "Colunas opcionais que o relatório não trouxe — as camadas que "
            "dependem delas não rodaram",
            list(faltando), "atencao",
        ))

    return Resultado(
        titulo=f"{_milhar(len(resultado))} registros auditados contra "
               f"{resultado.regras_ativas} regras ativas",
        fichas=[
            Ficha("Conformes", _milhar(resultado.conformes)),
            Ficha("Advertências", _milhar(resultado.advertencias)),
            Ficha("Validação manual", _milhar(resultado.validacao_manual)),
        ],
        listas=listas,
        planilha=planilha,
    )


def _configuracao_do_fiscalbot() -> Configuracao:
    """A tela de regras do Fiscalbot.

    O Fiscalbot é lido tarde, dentro das funções, para a Central abrir mesmo
    que uma ferramenta esteja quebrada — o menu não pode cair junto.
    """
    def secoes() -> list[Secao]:
        from fiscalbot.configuracao import secoes as declaradas

        return [
            Secao(
                id=s["id"], titulo=s["titulo"], explicacao=s["explicacao"],
                fixa=s["fixa"],
                campos=tuple(
                    Campo(c["chave"], c["rotulo"], c["largura"], c["ajuda"], c["tipo"])
                    for c in s["campos"]
                ),
            )
            for s in declaradas()
        ]

    def ler() -> dict:
        from fiscalbot.configuracao import ler as ler_base

        return ler_base()

    def gravar(dados: dict, responsavel: str) -> tuple[bool, list[dict]]:
        from fiscalbot.configuracao import gravar as gravar_base

        return gravar_base(dados, responsavel)

    return Configuracao(
        resumo="Regras de enquadramento, parâmetros do motor, matriz de "
               "alíquotas e as listas de parceiros.",
        secoes=secoes, ler=ler, gravar=gravar,
    )


# -- o catálogo ------------------------------------------------------------

FERRAMENTAS: list[Ferramenta] = [
    Ferramenta(
        id="apurabot",
        nome="Apurabot",
        resumo="Apuração mensal de ICMS a partir do Livro Fiscal.",
        icone="📘",
        estado=JANELA_PROPRIA,
        detalhe="Abre em janela própria: a apuração tem tela de conferência, "
                "registro por estabelecimento e a série do ano.",
    ),
    Ferramenta(
        id="dixml",
        nome="DiXML",
        resumo="Lote de XML de nota em planilha, para conferir qualquer campo.",
        icone="🧾",
        estado=DISPONIVEL,
        entrada=Entrada(
            rotulo="Arraste aqui os pacotes de XML",
            apoio="um ou mais arquivos <code>.zip</code> — pode haver .zip "
                  "dentro de .zip, a leitura desce sozinha",
            extensoes=(".zip",),
            varios=True,
        ),
        verbo="Lendo os XMLs…",
        detalhe="NF-e vira uma linha por item; CT-e vira uma linha por documento.",
        executar=_rodar_dixml,
    ),
    Ferramenta(
        id="fiscalbot",
        nome="Fiscalbot",
        resumo="Confere o lançamento de cada nota e valida o Livro Fiscal.",
        icone="✅",
        estado=DISPONIVEL,
        entrada=Entrada(
            rotulo="Arraste aqui o Movimento Livros Fiscais",
            apoio="o relatório extraído do Sankhya — <code>.xls</code> ou "
                  "<code>.xlsx</code>",
            extensoes=(".xls", ".xlsx", ".xlsm"),
            varios=False,
        ),
        verbo="Auditando o Livro Fiscal…",
        detalhe="É quem entrega o Livro Fiscal que o Apurabot consome.",
        executar=_rodar_fiscalbot,
        configuracao=_configuracao_do_fiscalbot(),
    ),
    Ferramenta(
        id="gerarpendentes",
        nome="GerarPendentes",
        resumo="Planilha de notas de mercadoria pendentes de entrada.",
        icone="📦",
        estado=A_IMPORTAR,
    ),
    Ferramenta(
        id="gerarservpend",
        nome="GerarServPend",
        resumo="Planilha de notas de serviço pendentes de entrada.",
        icone="🧰",
        estado=A_IMPORTAR,
    ),
    Ferramenta(
        id="faturabot",
        nome="Faturabot",
        resumo="Conferências da expedição: desvios de balança, saídas e diretos.",
        icone="⚖️",
        estado=A_IMPORTAR,
        detalhe="Em desenvolvimento.",
    ),
]


def achar(identificador: str) -> Ferramenta | None:
    for ferramenta in FERRAMENTAS:
        if ferramenta.id == identificador:
            return ferramenta
    return None


def catalogo() -> list[dict]:
    """O catálogo como a página o consome."""
    return [
        {
            "id": f.id,
            "nome": f.nome,
            "resumo": f.resumo,
            "icone": f.icone,
            "estado": f.estado,
            "verbo": f.verbo,
            "detalhe": f.detalhe,
            "tem_configuracao": f.configuracao is not None,
            "resumo_da_configuracao":
                f.configuracao.resumo if f.configuracao else "",
            "entrada": None if f.entrada is None else {
                "rotulo": f.entrada.rotulo,
                "apoio": f.entrada.apoio,
                "extensoes": list(f.entrada.extensoes),
                "varios": f.entrada.varios,
            },
        }
        for f in FERRAMENTAS
    ]
