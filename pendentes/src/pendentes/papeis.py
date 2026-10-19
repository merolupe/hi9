"""Qual arquivo é qual — pelas âncoras do próprio cabeçalho.

Hoje o reconhecimento é por convenção de nome e por ordem de clique:

* mercadorias exige que os arquivos se chamem `XML30.xls`, `CE30.xls` e
  `XMLAnterior.xls`, na pasta da semana 30 — renomear errado o arquivo da
  semana anterior é uma das armadilhas conhecidas da rotina;
* serviços exige que a pessoa escolha os quatro diálogos **na ordem certa**,
  sem nenhuma conferência de que o arquivo escolhido é o daquele diálogo.

Aqui os arquivos são arrastados juntos, em qualquer ordem, e cada um recebe o
papel cujo **conjunto de âncoras** ele satisfaz inteiro. Três âncoras, e não
uma: `Chave Acesso` está no XML e na Conferência de Entradas, `Nro Nota` está
no XML e na planilha da semana anterior. É o conjunto que separa.

**Nada é decidido por semelhança** — regra nº 4. Papel duplicado ou papel
obrigatório ausente aborta antes de ler qualquer dado, nomeando o arquivo e o
papel. Papel opcional ausente degrada com aviso contado, que é o que o módulo
de serviços já faz hoje na mensagem final.

### Por que existe âncora ausente

A planilha da semana anterior de mercadorias **contém todas as 27 colunas do
XML** — ela é o XML acrescido das colunas de conferência e de classificação.
Nenhuma âncora positiva separa os dois, porque o conjunto de colunas de um
está contido no do outro. Então o papel do XML declara, além das âncoras que
exige, uma âncora que ele **não pode ter**: `Guardião`, coluna que só existe
na saída. É a única forma honesta de separar — e é um detalhe que o desenho
original do porte não tinha previsto.

### A aba que a própria ferramenta escreveu

A saída de uma semana volta na seguinte como "planilha da semana anterior" — e
algumas abas dela são **cópia de relatório de origem**. A `Sem Correspondencia
ASIS` de serviços devolve as colunas do Portal de Compras tal como vieram; a
`CTe`, a `Manifestados` e a `Descartados` de mercadorias são o XML cru. Pelas
âncoras, essas abas *são* o relatório de origem, e o arquivo da semana passada
era reconhecido como Portal de Compras (ou como XML) ao lado do verdadeiro.

Por isso quem chama declara as `abas_da_saida`: o nome das abas que a própria
ferramenta escreve. Uma aba com esse nome nunca carrega papel de relatório de
origem — só o papel que a pede pelo nome (`aba`), que é o da semana anterior.
O nome da aba é layout de saída, que mora no código ao lado da ordem das
colunas; não depende de a base viva ter recebido a carga de fábrica nova.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Sequence

from . import cabecalho as cab
from .planilha import Aba, Arquivo, ler
from .texto import chave_de_texto

#: Quantas linhas de cada aba são lidas só para descobrir o papel do arquivo.
LINHAS_PARA_ESPIAR = 20


class PapelDuplicado(Exception):
    """Dois arquivos foram reconhecidos como o mesmo relatório."""


class PapelAusente(Exception):
    """Nenhum arquivo enviado é o relatório obrigatório."""


class PapelAmbiguo(Exception):
    """Um arquivo satisfaz mais de um papel — não dá para escolher por ele."""


@dataclass(frozen=True)
class Papel:
    """Um relatório esperado e como reconhecê-lo."""

    id: str
    rotulo: str
    ancoras: tuple[str, ...]
    obrigatorio: bool = True
    #: Quando preenchido, só uma aba com este nome pode carregar o papel.
    aba: str = ""
    #: Colunas que, se presentes, **desqualificam** o arquivo para este papel.
    ancoras_ausentes: tuple[str, ...] = ()

    def descricao(self) -> str:
        colunas = ", ".join(f"'{a}'" for a in self.ancoras)
        if self.aba:
            return f"{self.rotulo} (aba '{self.aba}', colunas {colunas})"
        return f"{self.rotulo} (colunas {colunas})"


@dataclass(frozen=True)
class Reconhecido:
    """Um arquivo com o papel que ele recebeu, e onde está o cabeçalho dele."""

    papel: Papel
    arquivo: Arquivo
    aba: Aba
    linha_do_cabecalho: int

    @property
    def cabecalho(self) -> list:
        return self.aba.linha(self.linha_do_cabecalho)

    @property
    def dados(self) -> list[list]:
        return self.aba.linhas[self.linha_do_cabecalho + 1:]


@dataclass(frozen=True)
class Reconhecimento:
    """O que os arquivos arrastados viraram."""

    por_papel: dict[str, Reconhecido] = field(default_factory=dict)
    ausentes: tuple[Papel, ...] = ()
    nao_reconhecidos: tuple[str, ...] = ()

    def tem(self, papel_id: str) -> bool:
        return papel_id in self.por_papel

    def __getitem__(self, papel_id: str) -> Reconhecido:
        return self.por_papel[papel_id]

    def obter(self, papel_id: str) -> Reconhecido | None:
        return self.por_papel.get(papel_id)

    @property
    def avisos(self) -> list[str]:
        """O que a tela precisa dizer, contado, em vez de degradar calada."""
        recado = []
        for papel in self.ausentes:
            recado.append(
                f"Não veio {papel.rotulo} — o que depende dele não rodou."
            )
        for nome in self.nao_reconhecidos:
            recado.append(f"Não reconheci {nome}; ele não entrou.")
        return recado


def _casa(arquivo: Arquivo, papel: Papel,
          abas_da_saida: frozenset[str] = frozenset()) -> tuple[Aba, int] | None:
    """A aba e a linha de cabeçalho em que este arquivo satisfaz o papel."""
    alvo_da_aba = chave_de_texto(papel.aba) if papel.aba else ""
    for aba in arquivo.abas:
        if alvo_da_aba and chave_de_texto(aba.nome) != alvo_da_aba:
            continue
        # Aba escrita pela própria ferramenta não é relatório de origem.
        if not alvo_da_aba and chave_de_texto(aba.nome) in abas_da_saida:
            continue
        linha = cab.localizar(aba.linhas, papel.ancoras,
                              linhas_de_busca=LINHAS_PARA_ESPIAR)
        if linha < 0:
            continue
        # Basta **uma** das âncoras proibidas estar presente para o arquivo
        # deixar de servir a este papel.
        cabecalho = aba.linha(linha)
        if any(cab.achar(cabecalho, proibida) >= 0
               for proibida in papel.ancoras_ausentes):
            continue
        return aba, linha
    return None


def _chaves_das_abas(abas_da_saida: Iterable[str]) -> frozenset[str]:
    return frozenset(chave_de_texto(nome) for nome in abas_da_saida
                     if chave_de_texto(nome))


def casamentos(arquivo: Arquivo, papeis: Iterable[Papel],
               abas_da_saida: Iterable[str] = ()) -> list[Papel]:
    """Todos os papéis que este arquivo satisfaz — zero, um ou (erro) vários."""
    saida = _chaves_das_abas(abas_da_saida)
    return [papel for papel in papeis if _casa(arquivo, papel, saida) is not None]


def reconhecer(arquivos: Sequence[Arquivo], papeis: Iterable[Papel],
               abas_da_saida: Iterable[str] = ()) -> Reconhecimento:
    """Distribui os arquivos entre os papéis, ou aborta dizendo por quê."""
    papeis = list(papeis)
    saida = _chaves_das_abas(abas_da_saida)
    achados: dict[str, list[tuple[Arquivo, Aba, int]]] = {p.id: [] for p in papeis}
    papeis_do_arquivo: dict[str, list[Papel]] = {}

    for arquivo in arquivos:
        papeis_do_arquivo[arquivo.nome] = []
        for papel in papeis:
            casou = _casa(arquivo, papel, saida)
            if casou is None:
                continue
            achados[papel.id].append((arquivo, casou[0], casou[1]))
            papeis_do_arquivo[arquivo.nome].append(papel)

    ambiguos = {nome: encontrados
                for nome, encontrados in papeis_do_arquivo.items()
                if len(encontrados) > 1}
    if ambiguos:
        nome, encontrados = next(iter(ambiguos.items()))
        rotulos = " e ".join(p.rotulo for p in encontrados)
        raise PapelAmbiguo(
            f"{nome} serve tanto para {rotulos}. Não escolho por você: "
            f"envie o arquivo certo de cada um."
        )

    duplicados = {p: encontrados for p, encontrados in achados.items()
                  if len(encontrados) > 1}
    if duplicados:
        papel_id, encontrados = next(iter(duplicados.items()))
        papel = next(p for p in papeis if p.id == papel_id)
        nomes = " e ".join(f"{a.nome}" for a, _, _ in encontrados)
        raise PapelDuplicado(
            f"{nomes} foram reconhecidos como {papel.rotulo}. "
            f"Envie um de cada."
        )

    faltando = [p for p in papeis if p.obrigatorio and not achados[p.id]]
    if faltando:
        raise PapelAusente(
            "Não veio nenhum arquivo com as colunas de:\n\n  "
            + "\n  ".join(p.descricao() for p in faltando)
        )

    por_papel = {
        papel.id: Reconhecido(papel, *achados[papel.id][0])
        for papel in papeis if achados[papel.id]
    }
    ausentes = tuple(p for p in papeis if not p.obrigatorio and not achados[p.id])
    nao_reconhecidos = tuple(
        nome for nome, encontrados in papeis_do_arquivo.items() if not encontrados
    )
    return Reconhecimento(por_papel, ausentes, nao_reconhecidos)


def ler_inteiro(reconhecido: Reconhecido) -> Reconhecido:
    """Relê o arquivo inteiro, mantendo o papel que ele já recebeu.

    O reconhecimento espia só as primeiras linhas de cada aba — o suficiente
    para o cabeçalho e nada além. Quem vai **usar** o relatório precisa das
    outras sete mil linhas, e é esta função que as traz, sem repetir a
    distribuição de papéis nem arriscar que um arquivo mude de papel entre uma
    leitura e outra: o papel e o nome da aba vêm decididos de antes.
    """
    arquivo = ler(reconhecido.arquivo.caminho)
    aba = arquivo.aba(reconhecido.aba.nome) or arquivo.primeira
    linha = cab.localizar(aba.linhas, reconhecido.papel.ancoras,
                          linhas_de_busca=LINHAS_PARA_ESPIAR)
    if linha < 0:
        linha = reconhecido.linha_do_cabecalho
    return Reconhecido(reconhecido.papel, arquivo, aba, linha)


def ler_e_reconhecer(caminhos: Iterable[Path | str], papeis: Iterable[Papel],
                     abas_da_saida: Iterable[str] = ()
                     ) -> tuple[Reconhecimento, list[Arquivo]]:
    """Espia o cabeçalho de cada arquivo e distribui os papéis.

    Lê só as primeiras linhas de cada aba: descobrir o papel não exige
    carregar um relatório de sete mil linhas. Quem for usar o arquivo o lê
    inteiro depois, já sabendo o que ele é.
    """
    arquivos = [ler(caminho, limite_de_linhas=LINHAS_PARA_ESPIAR)
                for caminho in caminhos]
    return reconhecer(arquivos, papeis, abas_da_saida), arquivos


def _e_saida(arquivo: Arquivo, abas_da_saida: Iterable[str]) -> bool:
    saida = _chaves_das_abas(abas_da_saida)
    return any(chave_de_texto(aba.nome) in saida for aba in arquivo.abas)


def conferir(caminhos: Sequence[Path | str], papeis: Iterable[Papel],
             abas_da_saida: Iterable[str] = ()) -> dict:
    """O que cada arquivo é, **sem abortar** — para a tela mostrar antes de rodar.

    `reconhecer` aborta no primeiro problema, e é o certo na hora de rodar.
    Na hora de anexar, a pessoa precisa ver o quadro inteiro: o que já veio,
    o que falta e qual arquivo não serviu, para anexar o resto aos poucos.
    Devolve texto puro, na ordem dos papéis e na ordem dos arquivos:

    * `documentos` — `id`, `rotulo` e `obrigatorio` de cada papel;
    * `arquivos` — para cada caminho recebido, o `papel` que ele recebeu (ou
      vazio), o `problema` quando não recebeu nenhum, e se esse problema
      `bloqueia` a execução. Arquivo ilegível ou que serve a dois papéis
      bloqueia; arquivo que não é nenhum dos relatórios só fica de fora, com
      aviso — é o que `gerar` já faz com ele.

    Dois arquivos no mesmo papel não é problema de um arquivo, é do par: quem
    mostra a lista enxerga o papel repetido e pede para tirar um.
    """
    papeis = list(papeis)
    arquivos = []
    for caminho in caminhos:
        nome = Path(caminho).name
        try:
            arquivo = ler(caminho, limite_de_linhas=LINHAS_PARA_ESPIAR)
        except Exception as erro:                      # noqa: BLE001
            arquivos.append({"papel": "", "bloqueia": True,
                             "problema": f"não consegui abrir {nome}: {erro}"})
            continue
        casados = casamentos(arquivo, papeis, abas_da_saida)
        if len(casados) == 1:
            arquivos.append({"papel": casados[0].id, "bloqueia": False,
                             "problema": ""})
        elif casados:
            rotulos = " e ".join(p.rotulo for p in casados)
            arquivos.append({"papel": "", "bloqueia": True, "problema": (
                f"serve tanto para {rotulos}; não escolho por você")})
        elif _e_saida(arquivo, abas_da_saida):
            # A planilha que a ferramenta gerou, sem a aba que a semana
            # seguinte lê — alguém a apagou ou a renomeou antes de guardar.
            pedidas = sorted({p.aba for p in papeis if p.aba})
            arquivos.append({"papel": "", "bloqueia": False, "problema": (
                "é uma planilha gerada pela ferramenta, mas sem a aba "
                + " / ".join(f"'{a}'" for a in pedidas)
                + " — é dela que a semana anterior é lida")})
        else:
            arquivos.append({"papel": "", "bloqueia": False, "problema": (
                "não tem o cabeçalho de nenhum dos relatórios esperados")})
    return {
        "documentos": [{"id": p.id, "rotulo": p.rotulo,
                        "obrigatorio": p.obrigatorio} for p in papeis],
        "arquivos": arquivos,
    }


def papeis_de(declarados: Iterable[dict], dominio: str = "") -> tuple[Papel, ...]:
    """Os papéis vindos do parâmetro, filtrados por domínio quando pedido."""
    saida = []
    for linha in declarados:
        if dominio and str(linha.get("dominio", "")) != dominio:
            continue
        saida.append(Papel(
            id=str(linha.get("id", "")).strip(),
            rotulo=str(linha.get("rotulo", "")).strip(),
            ancoras=tuple(str(a).strip() for a in (linha.get("ancoras") or [])),
            obrigatorio=bool(linha.get("obrigatorio", True)),
            aba=str(linha.get("aba", "") or "").strip(),
            ancoras_ausentes=tuple(
                str(a).strip() for a in (linha.get("ancoras_ausentes") or [])
            ),
        ))
    return tuple(p for p in saida if p.id and p.ancoras)
