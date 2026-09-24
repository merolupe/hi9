"""O catálogo: o que a central mostra na tela e o que cada ferramenta declara.

Este arquivo é o **contrato de ferramenta** do repositório. Para uma automação
do setor aparecer na janela, ela precisa dizer três coisas:

1. **quem é** — nome, uma linha de resumo e o estado em que está;
2. **o que pede** — que arquivo, quais extensões, um ou vários (`Entrada`);
3. **o que devolve** — números para a tela e, quando houver, uma planilha
   para baixar (`Resultado`).

Quem pede mais de um relatório pode declarar também **como conferir** o que
chegou (`conferir`, que devolve uma `Conferencia`): a tela passa a mostrar a
lista dos relatórios esperados, marca cada um conforme o arquivo chega — de
uma vez ou aos poucos — e só acende o botão de gerar quando nada falta.

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


# -- o que cada arquivo anexado é ------------------------------------------

@dataclass(frozen=True)
class Anexo:
    """Um arquivo já enviado. `indice` é a posição dele entre os recebidos."""

    indice: int
    nome: str
    problema: str = ""
    bloqueia: bool = False


@dataclass(frozen=True)
class Documento:
    """Um relatório que a ferramenta espera, e os arquivos que o preencheram."""

    id: str
    rotulo: str
    obrigatorio: bool
    anexos: list[Anexo] = field(default_factory=list)

    @property
    def estado(self) -> str:
        """`ok`, `falta` (obrigatório sem arquivo), `opcional` ou `repetido`."""
        if len(self.anexos) > 1:
            return "repetido"
        if self.anexos:
            return "ok"
        return "falta" if self.obrigatorio else "opcional"


@dataclass(frozen=True)
class Conferencia:
    """O quadro da tela de anexar: o que já veio, o que falta, o que sobrou.

    É o **quarto** item do contrato, e é opcional. A ferramenta que pede mais
    de um relatório e reconhece cada um pelo cabeçalho declara `conferir`; a
    Central mostra então a lista dos relatórios esperados, marca cada um
    conforme os arquivos chegam — aos poucos, em quantas levas a pessoa quiser
    — e só libera o botão de gerar quando nada impede.
    """

    documentos: list[Documento] = field(default_factory=list)
    soltos: list[Anexo] = field(default_factory=list)

    @property
    def pendencias(self) -> list[str]:
        """O que impede de gerar, em frase. Lista vazia: pode gerar."""
        recado = []
        for doc in self.documentos:
            if doc.estado == "falta":
                recado.append(f"Falta o {doc.rotulo}.")
            elif doc.estado == "repetido":
                nomes = " e ".join(a.nome for a in doc.anexos)
                recado.append(f"{nomes} são, os dois, o {doc.rotulo}. "
                              f"Tire um.")
        for solto in self.soltos:
            if solto.bloqueia:
                recado.append(f"{solto.nome}: {solto.problema}.")
        return recado

    @property
    def pronta(self) -> bool:
        return not self.pendencias


def _conferencia(respondido: dict, nomes: list[str]) -> Conferencia:
    """O texto puro da ferramenta vira o quadro da Central."""
    documentos = [Documento(d["id"], d["rotulo"], bool(d["obrigatorio"]))
                  for d in respondido.get("documentos") or []]
    por_id = {d.id: d for d in documentos}
    soltos = []
    for indice, (nome, achado) in enumerate(
            zip(nomes, respondido.get("arquivos") or [])):
        anexo = Anexo(indice, nome, str(achado.get("problema") or ""),
                      bool(achado.get("bloqueia")))
        destino = por_id.get(achado.get("papel") or "")
        if destino is None:
            soltos.append(anexo)
        else:
            destino.anexos.append(anexo)
    return Conferencia(documentos, soltos)


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
    #: Quando declarado, os arquivos são anexados aos poucos e conferidos um a
    #: um; o botão de gerar só acende quando a `Conferencia` está pronta.
    conferir: Callable[[list[Path]], Conferencia] | None = None


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


# -- GerarServPend ---------------------------------------------------------

def _rodar_gerarpendentes(arquivos: list[Path], saida: Path) -> Resultado:
    """Cruza o XML com a Conferência de Entradas e resume para a tela.

    Mesmo desenho do GerarServPend: a ferramenta devolve o painel em texto
    puro e quem traduz para `Ficha` e `Lista` é este arquivo. A importação é
    tardia, dentro da função, para a Central abrir mesmo que uma ferramenta
    esteja quebrada.
    """
    from pendentes.mercadorias.execucao import gerar

    execucao = gerar(arquivos, saida)

    return Resultado(
        titulo=execucao.titulo(),
        fichas=[Ficha(rotulo, valor) for rotulo, valor in execucao.fichas()],
        listas=[Lista(titulo, itens, tom)
                for titulo, itens, tom in execucao.listas()],
        planilha=execucao.planilha,
    )


def _conferir_gerarpendentes(arquivos: list[Path]) -> Conferencia:
    from pendentes.mercadorias.execucao import conferir

    return _conferencia(conferir(arquivos), [a.name for a in arquivos])


def _conferir_gerarservpend(arquivos: list[Path]) -> Conferencia:
    from pendentes.servicos.execucao import conferir

    return _conferencia(conferir(arquivos), [a.name for a in arquivos])


def _rodar_gerarservpend(arquivos: list[Path], saida: Path) -> Resultado:
    """Confronta o ASIS com os lançamentos do Sankhya e resume para a tela.

    A ferramenta devolve o painel em texto puro — ela não conhece `Ficha` nem
    `Lista`, que são da central. Quem traduz é este arquivo, como já faz com o
    DiXML e com o Fiscalbot.
    """
    from pendentes.servicos.execucao import gerar

    execucao = gerar(arquivos, saida)

    return Resultado(
        titulo=execucao.titulo(),
        fichas=[Ficha(rotulo, valor) for rotulo, valor in execucao.fichas()],
        listas=[Lista(titulo, itens, tom)
                for titulo, itens, tom in execucao.listas()],
        planilha=execucao.planilha,
    )


def _rodar_resumo(arquivos: list[Path], saida: Path) -> Resultado:
    """Monta o painel semanal sobre o relatório já classificado.

    A terceira rotina das notas pendentes, e a única que recebe a **saída** das
    outras duas em vez de um export do Sankhya. Mesmo desenho: a ferramenta
    devolve o painel em texto e quem traduz para `Ficha` e `Lista` é aqui.
    """
    from pendentes.resumo.execucao import gerar

    execucao = gerar(arquivos, saida)

    return Resultado(
        titulo=execucao.titulo(),
        fichas=[Ficha(rotulo, valor) for rotulo, valor in execucao.fichas()],
        listas=[Lista(titulo, itens, tom)
                for titulo, itens, tom in execucao.listas()],
        planilha=execucao.planilha,
    )


def _rodar_conhecimento(arquivos: list[Path], saida: Path) -> Resultado:
    """Importa a base de pré-categorização, ou a mede contra um relatório.

    Duas coisas numa entrada só, decididas pelo **conteúdo** do que foi
    arrastado: planilha já classificada é gabarito e a base é medida contra
    ela; `.csv` e `.json` são fonte e a base é refeita. É o mesmo princípio do
    reconhecimento de papel — nada é decidido pelo nome do arquivo.
    """
    from pendentes.conhecimento import base as conhecido
    from pendentes.conhecimento.importacao import importar
    from pendentes.conhecimento.simulacao import simular

    planilhas = [a for a in arquivos
                 if a.suffix.lower() in (".xls", ".xlsx", ".xlsm")]
    if planilhas and len(planilhas) == len(arquivos):
        execucao = simular(planilhas, conhecido.carregar())
    else:
        execucao = importar([a for a in arquivos if a not in planilhas])

    return Resultado(
        titulo=execucao.titulo(),
        fichas=[Ficha(rotulo, valor) for rotulo, valor in execucao.fichas()],
        listas=[Lista(titulo, itens, tom)
                for titulo, itens, tom in execucao.listas()],
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


def _configuracao_do_conhecimento() -> Configuracao:
    """A tela da base de conhecimento: consultar, filtrar e corrigir.

    O que a pessoa grava aqui **não** entra na fotografia importada: vai para a
    camada de ajustes, que sobrevive à próxima importação e vence o que ela
    propuser. Lido tarde, como o Fiscalbot, para a Central abrir mesmo que uma
    ferramenta esteja quebrada.
    """
    def secoes() -> list[Secao]:
        from pendentes.conhecimento.configuracao import secoes as declaradas

        return [
            Secao(
                id=s["id"], titulo=s["titulo"], explicacao=s["explicacao"],
                fixa=s["fixa"],
                campos=tuple(
                    Campo(c["chave"], c["rotulo"], c["largura"], c["ajuda"],
                          c["tipo"])
                    for c in s["campos"]
                ),
            )
            for s in declaradas()
        ]

    def ler() -> dict:
        from pendentes.conhecimento.configuracao import ler as ler_base

        return ler_base()

    def gravar(dados: dict, responsavel: str) -> tuple[bool, list[dict]]:
        from pendentes.conhecimento.configuracao import gravar as gravar_base

        return gravar_base(dados, responsavel)

    return Configuracao(
        resumo="Guardião e categoria por parceiro, gestor vigente de cada área "
               "e Tipo de Operação por CFOP. Corrigir aqui vence o que a "
               "importação propôs, e a correção sobrevive à próxima.",
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
        resumo="Notas de mercadoria emitidas contra a Hinove que ainda não têm "
               "entrada.",
        icone="📦",
        estado=DISPONIVEL,
        entrada=Entrada(
            rotulo="Arraste os relatórios da semana",
            apoio="o relatório de importação de <code>XML</code> e a "
                  "<code>Conferência de Entradas</code> são obrigatórios; a "
                  "planilha da semana passada, com as classificações "
                  "preenchidas, entra se houver. De uma vez ou aos poucos, em "
                  "qualquer ordem: cada arquivo é reconhecido pelo próprio "
                  "cabeçalho, e a lista abaixo mostra o que já veio e o que "
                  "falta.",
            extensoes=(".xls", ".xlsx", ".xlsm"),
            varios=True,
        ),
        verbo="Cruzando o XML com a Conferência de Entradas…",
        detalhe="A classificação por guardião é herdada do livro da "
                "ferramenta, não do arquivo — renomear ou perder a planilha "
                "da semana passada não apaga mais o histórico. O que a "
                "limpeza descarta passa a aparecer na aba Descartados, com o "
                "motivo.",
        executar=_rodar_gerarpendentes,
        conferir=_conferir_gerarpendentes,
    ),
    Ferramenta(
        id="gerarservpend",
        nome="GerarServPend",
        resumo="Notas de serviço emitidas contra a Hinove que ainda não foram "
               "lançadas.",
        icone="🧰",
        estado=DISPONIVEL,
        entrada=Entrada(
            rotulo="Arraste os relatórios da semana",
            apoio="o <code>ASIS</code> (notas emitidas) e o <code>Portal de "
                  "Compras</code> são obrigatórios; a <code>Conferência de "
                  "Serviços</code> e a planilha da semana passada entram se "
                  "houver. De uma vez ou aos poucos, em qualquer ordem: cada "
                  "arquivo é reconhecido pelo próprio cabeçalho, e a lista "
                  "abaixo mostra o que já veio e o que falta.",
            extensoes=(".xls", ".xlsx", ".xlsm"),
            varios=True,
        ),
        verbo="Confrontando o ASIS com os lançamentos do Sankhya…",
        detalhe="Quatro procedimentos de confronto, do mais forte para o mais "
                "fraco. O que casou só por nota e valor sai marcado para "
                "revisão, e a classificação vem do livro da ferramenta — "
                "perder a planilha da semana passada não apaga mais o "
                "histórico.",
        executar=_rodar_gerarservpend,
        conferir=_conferir_gerarservpend,
    ),
    Ferramenta(
        id="resumoexecutivo",
        nome="Resumo Executivo",
        resumo="O painel da semana sobre as duas frentes, já classificadas.",
        icone="📊",
        estado=DISPONIVEL,
        entrada=Entrada(
            rotulo="Arraste a planilha da semana",
            apoio="a planilha que o <code>GerarPendentes</code> e o "
                  "<code>GerarServPend</code> geraram, <b>depois</b> de "
                  "classificada. As abas <code>Pendentes</code> e "
                  "<code>Servicos</code> podem vir num arquivo só ou em dois.",
            extensoes=(".xlsx",),
            varios=True,
        ),
        verbo="Montando o painel da semana…",
        detalhe="O painel entra na própria planilha, na primeira aba, e o "
                "arquivo de entrada não é alterado. Roda por último: as "
                "contas são por categoria, e categoria é o que a pessoa "
                "confirma depois da geração.",
        executar=_rodar_resumo,
    ),
    Ferramenta(
        id="conhecimento",
        nome="Base de conhecimento",
        resumo="O que o histórico já respondeu sobre cada parceiro — para "
               "propor classificação, nunca para decidir por ela.",
        icone="🧠",
        estado=DISPONIVEL,
        entrada=Entrada(
            rotulo="Arraste a base, ou uma planilha já classificada",
            apoio="a lista de parceiros (<code>.csv</code>) e as regras "
                  "medidas (<code>.json</code>) refazem a base; uma planilha "
                  "de semana já classificada, sozinha, <b>mede</b> a base "
                  "contra ela e não altera nada.",
            extensoes=(".csv", ".json", ".xls", ".xlsx", ".xlsm"),
            varios=True,
        ),
        verbo="Lendo o que o histórico já respondeu…",
        detalhe="A base propõe; quem classifica é gente. Só o que a lista "
                "curada e o histórico afirmam juntos, com três notas em duas "
                "semanas, chega a poder preencher célula — o resto aparece "
                "como sugestão, com a evidência ao lado. A tela de "
                "configuração mostra a base inteira e deixa corrigir: a "
                "correção vence a importação e sobrevive a ela.",
        executar=_rodar_conhecimento,
        configuracao=_configuracao_do_conhecimento(),
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
            "confere": f.conferir is not None,
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
