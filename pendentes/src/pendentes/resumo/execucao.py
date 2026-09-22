"""Do relatório pronto ao painel, e o que a tela mostra quando termina.

```
achar as abas `Pendentes` e `Servicos`, em um arquivo ou em dois
   ↓
derivar a unidade de cada nota pela tabela cadastrada
   ↓
montar as cinco contas do painel
   ↓
reabrir o relatório, trocar as duas abas do painel e gravar ao lado
```

### Por que o painel entra no arquivo da semana

Porque é o arquivo que é enviado. Um painel que sai em `.xlsx` separado
obriga alguém a copiar aba entre planilhas toda semana — que é exatamente o
tipo de passo manual que esta ferramenta existe para tirar do caminho.

O arquivo de entrada **não é alterado**: o relatório é relido e gravado ao
lado, com as duas abas do painel no lugar. Rodar duas vezes não empilha
painel — as abas antigas são substituídas.

### O que trava

Nota de mercadoria sem categoria reconhecida. O painel conta por categoria; a
que não tem ficaria fora da soma e ninguém veria. Ela aparece nomeada, e a
execução sai **não encerrável** — a planilha, como em mercadorias, é gravada
assim mesmo.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterable

from .. import parametros
from ..mercadorias import vocabulario
from ..planilha import PlanilhaIlegivel
from . import colunas as col
from . import escrita as desenho
from . import fontes, painel as agregacao


class SemRelatorio(fontes.SemRelatorio):
    """Mantido para quem importa o erro deste módulo."""


@dataclass
class Execucao:
    """O que uma execução do resumo produziu."""

    referencia: date | None = None
    semana: int = 0
    mercadorias: int = 0
    servicos: int = 0
    valor_total: float = 0.0
    painel: agregacao.Painel | None = None

    abas_lidas: list[str] = field(default_factory=list)
    nao_reconhecidos: tuple[str, ...] = ()
    sem_emissao: int = 0
    unidades_cadastradas: int = 0
    #: Nomes fantasia/filiais que a tabela de unidades não soube reconhecer.
    unidades_nao_reconhecidas: list[str] = field(default_factory=list)
    base: str = ""
    avisos: list[str] = field(default_factory=list)

    planilha: Path | None = None
    pasta_do_snapshot: Path | None = None

    # -- o que a tela mostra ------------------------------------------------

    @property
    def total(self) -> int:
        return self.mercadorias + self.servicos

    @property
    def encerravel(self) -> bool:
        return not self.bloqueios()

    def bloqueios(self) -> list[str]:
        if self.painel is None or not self.painel.sem_categoria:
            return []
        sem = self.painel.sem_categoria
        parceiros = ", ".join(sorted({p.parceiro for p in sem})[:3])
        return [
            f"{len(sem)} nota(s) de mercadoria sem categoria reconhecida "
            f"ficaram fora de todas as contas do painel — {parceiros}"
            + (" e outras" if len({p.parceiro for p in sem}) > 3 else "")
        ]

    def atencoes(self) -> list[str]:
        itens = list(self.avisos)
        if self.unidades_cadastradas == 0:
            itens.append(
                "a tabela de unidades está vazia: o gráfico por unidade não "
                "foi desenhado. São cinco linhas na tela de configuração.")
        elif self.unidades_nao_reconhecidas:
            mostradas = ", ".join(self.unidades_nao_reconhecidas[:3])
            itens.append(
                f"{len(self.unidades_nao_reconhecidas)} nome(s) fantasia ou "
                f"filial fora da tabela de unidades: {mostradas}")
        if self.sem_emissao:
            itens.append(
                f"{self.sem_emissao} nota(s) sem data de emissão ficaram fora "
                f"da média de dias e dos dois TOP 5")
        for nome in self.nao_reconhecidos:
            itens.append(f"não achei aba de pendências em {nome}")
        return itens

    def composicao(self) -> list[str]:
        if self.painel is None:                          # pragma: no cover
            return []
        linhas = []
        for linha in self.painel.categorias:
            media = ("—" if linha.media_dias is None
                     else f"{linha.media_dias:.1f}".replace(".", ","))
            linhas.append(
                f"{linha.categoria}: {_milhar(linha.quantidade)} nota(s), "
                f"{_reais(linha.valor)}, média de {media} dia(s)")
        return linhas

    def destaques(self) -> list[str]:
        if self.painel is None:                          # pragma: no cover
            return []
        linhas = []
        for nota in self.painel.top_dias[:3]:
            dias = nota.dias(self.painel.referencia)
            linhas.append(f"{dias} dia(s) — {nota.parceiro} "
                          f"({nota.guardiao or 'sem guardião'}), "
                          f"{_reais(nota.valor)}")
        return linhas

    def titulo(self) -> str:
        return (f"Semana {self.semana} — resumo executivo de "
                f"{_milhar(self.total)} nota(s) pendente(s), "
                f"{_reais(self.valor_total)}")

    def fichas(self) -> list[tuple[str, str]]:
        guardioes = len(self.painel.guardioes) if self.painel else 0
        return [
            ("Mercadorias", _milhar(self.mercadorias)),
            ("Serviços", _milhar(self.servicos)),
            ("Guardiões com pendência", _milhar(guardioes)),
            ("Sem categoria", _milhar(len(self.painel.sem_categoria)
                                      if self.painel else 0)),
        ]

    def listas(self) -> list[tuple[str, list[str], str]]:
        saida = []
        bloqueios = self.bloqueios()
        if bloqueios:
            saida.append(("Bloqueiam o encerramento da semana", bloqueios, "erro"))
        atencoes = self.atencoes()
        if atencoes:
            saida.append(("Degradaram ou ficaram de fora", atencoes, "atencao"))
        saida.append(("O que o painel mostra", self.composicao(), "neutro"))
        saida.append(("As mais antigas", self.destaques(), "neutro"))
        saida.append(("De onde o painel leu", self.abas_lidas, "neutro"))
        return saida


def _milhar(n: int) -> str:
    return f"{n:,}".replace(",", ".")


def _reais(valor: float) -> str:
    inteiro = f"{valor:,.2f}"
    return "R$ " + inteiro.replace(",", "·").replace(".", ",").replace("·", ".")


def data_de_referencia(dados: dict, agora: datetime) -> date:
    """A data contra a qual o tempo de pendência é contado.

    A mesma `data_de_referencia` que decide o número da semana. Um relatório
    gerado na terça sobre a posição de segunda tem que contar os dias a partir
    de segunda, senão o painel envelhece as notas em um dia.
    """
    referencia = (dados.get("semana") or {}).get("data_de_referencia")
    if referencia:
        from ..valores import data_br

        convertida = data_br(referencia)
        if isinstance(convertida, datetime):
            return convertida.date()
        if isinstance(convertida, date):
            return convertida
    return agora.date()


def _derivador_de_unidade(dados: dict, coletar: list[str]):
    """A função que transforma nome fantasia (ou filial) em unidade.

    Devolve `""` quando a tabela não reconhece — e anota o texto original, que
    é o que a tela mostra. Sem tabela cadastrada nada é reconhecido, e nada é
    inventado: é a regra nº 4.
    """
    unidades = parametros.unidades(dados)

    def unidade_de(valor: Any) -> str:
        achado = vocabulario.unidade_de(valor, unidades)
        if achado.reconhecido and achado.valor != vocabulario.SEM_UNIDADE:
            return achado.valor
        if achado.valor and achado.valor != vocabulario.SEM_UNIDADE:
            if achado.valor not in coletar:
                coletar.append(achado.valor)
        return ""

    return unidade_de


def gerar(arquivos: Iterable[Path | str], saida: Path | str, *,
          dados: dict | None = None, agora: datetime | None = None) -> Execucao:
    """Monta o painel sobre o relatório da semana e grava a planilha ao lado."""
    agora = agora or datetime.now()
    dados = dados if dados is not None else parametros.carregar()
    ajustes = parametros.resumo(dados)
    _, semana = parametros.semana_de(dados, agora.date())
    referencia = data_de_referencia(dados, agora)

    nao_reconhecidas: list[str] = []
    leitura = fontes.ler_relatorios(
        arquivos, _derivador_de_unidade(dados, nao_reconhecidas))

    quadro = agregacao.montar(
        leitura.pendencias, referencia=referencia,
        unidades=parametros.unidades(dados),
        linhas_do_top=ajustes["linhas_do_top"],
        guardioes_no_grafico=ajustes["guardioes_no_grafico"],
        fora_do_ranking=ajustes["guardioes_fora_do_ranking"],
    )

    execucao = Execucao(
        referencia=referencia, semana=semana,
        mercadorias=leitura.mercadorias, servicos=leitura.servicos,
        valor_total=quadro.total.valor if quadro.total else 0.0,
        painel=quadro, abas_lidas=list(leitura.abas),
        nao_reconhecidos=leitura.nao_reconhecidos,
        sem_emissao=leitura.sem_emissao,
        unidades_cadastradas=len(quadro.unidades),
        unidades_nao_reconhecidas=nao_reconhecidas,
    )

    execucao.planilha = _gravar(
        arquivos, Path(saida), quadro, semana,
        destacar_acima_de=ajustes["destacar_acima_de_dias"],
        avisos=execucao.avisos)
    return execucao


# -- a gravação -------------------------------------------------------------

def nome_sugerido(semana: int) -> str:
    """O nome do arquivo quando não há relatório para levar o painel junto."""
    return f"ResumoExecutivo{semana}.xlsx"


def _base(arquivos: Iterable[Path | str]) -> Path | None:
    """Qual arquivo leva o painel: o que tem mais abas de pendências.

    Com o relatório inteiro numa planilha só — que é o caso normal — é ela.
    Com as duas frentes em arquivos separados, é o que tem mercadorias, porque
    é o que a maioria abre primeiro. Empate nenhum é resolvido por acaso: a
    ordem em que os arquivos foram arrastados decide.
    """
    from ..planilha import ler

    melhor, pontos = None, 0
    for caminho in arquivos:
        caminho = Path(caminho)
        if caminho.suffix.lower() != ".xlsx":
            continue
        try:
            arquivo = ler(caminho, limite_de_linhas=fontes.LINHAS_PARA_ESPIAR)
        except PlanilhaIlegivel:                         # pragma: no cover
            continue
        quantas = sum(
            1 for ancoras in (fontes.ANCORAS_DE_MERCADORIAS,
                              fontes.ANCORAS_DE_SERVICOS)
            if fontes._achar_aba(arquivo, ancoras) is not None)
        if quantas > pontos:
            melhor, pontos = caminho, quantas
    return melhor


def _gravar(arquivos: Iterable[Path | str], saida: Path,
            quadro: agregacao.Painel, semana: int, *,
            destacar_acima_de: int, avisos: list[str]) -> Path:
    """Reabre o relatório, troca as duas abas do painel e grava ao lado."""
    import openpyxl

    arquivos = [Path(a) for a in arquivos]
    base = _base(arquivos)
    saida.mkdir(parents=True, exist_ok=True)

    if base is None:
        livro = openpyxl.Workbook()
        livro.remove(livro.active)
        destino = saida / nome_sugerido(semana)
        avisos.append(
            "o relatório da semana não veio em .xlsx, então o painel saiu "
            "num arquivo só dele — copie a aba para a planilha da semana")
    else:
        livro = openpyxl.load_workbook(str(base))
        destino = saida / base.name
        if destino.resolve() == base.resolve():
            destino = saida / f"{base.stem} com resumo{base.suffix}"
        for nome in (col.ABA_DO_PAINEL, col.ABA_AUXILIAR):
            if nome in livro.sheetnames:
                del livro[nome]

    aba = desenho.escrever_painel(livro, quadro,
                                  destacar_acima_de=destacar_acima_de)
    auxiliar = desenho.escrever_auxiliar(livro, quadro)
    desenho.desenhar(aba, auxiliar, quadro)
    livro.save(str(destino))
    return destino
