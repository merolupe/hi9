"""As matrizes viram documento e linha de conferência.

Entre a planilha e a regra há uma camada só, como em serviços. A diferença é
que aqui o documento **carrega as 27 colunas do XML inteiras**, na ordem em
que elas vão para a planilha: as abas auxiliares recebem a linha crua, e o que
o relatório trouxe é o que a evidência precisa mostrar.

Por isso o `Documento` guarda uma lista de 27 valores e não 27 campos com
nome. Campos nomeados obrigariam a montar a linha de volta coluna a coluna
toda vez que uma aba fosse escrita — e é exatamente aí que a ordem se perde.
O acesso por nome existe (`de` e `definir`), e é por ele que as regras leem.

### As duas chaves do mesmo documento

`[FATO]` A `Chave Acesso` é comparada de **dois jeitos distintos**, e isso é
deliberado:

| Para quê | Como | Por quê |
|---|---|---|
| confronto XML × Conferência de Entradas | `chave_bruta` — o texto como veio | é o que o VBA faz (`CStr` dos dois lados), e mudar muda célula |
| o livro de classificação | `chave` — só os 44 dígitos | o livro é nosso, e lá não há macro com que divergir |

Normalizar também o confronto é o **defeito 11** do porte: a correção está
pronta (`chaves.chave_de_acesso`) e espera medição, porque o número de
confrontos que passariam a casar é, ele próprio, um achado a levar ao time
fiscal — cada um deles é uma nota hoje cobrada como pendente sem ser.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Sequence

from ..cabecalho import Mapa
from ..chaves import chave_de_acesso
from ..texto import texto_de
from . import colunas as col

#: Em que posição da lista de valores está cada coluna do XML.
POSICAO: dict[str, int] = {nome: i for i, nome in enumerate(col.NOMES_DO_XML)}


@dataclass
class Documento:
    """Uma NF-e do relatório de importação de XML, a caminho da planilha.

    Três blocos, montados em três momentos do pipeline, exatamente como as
    três larguras de aba que o VBA produz:

    * `valores` — as 27 colunas do XML, sempre presentes;
    * `conferencia` — as 6 do lookup do CE, vazias até a etapa de conferência;
    * `categorizacao` — as 5 da classificação, vazias até a herança.
    """

    posicao: int
    valores: list[Any]
    conferencia: list[Any] = field(default_factory=lambda: ["" for _ in range(6)])
    categorizacao: list[Any] = field(default_factory=lambda: ["" for _ in range(5)])
    #: O pedido de compra do CE, trazido para a nona coluna da `Pendentes`.
    #: Número quando a nota tem conferência física; o rótulo de "não se
    #: aplica" quando não tem. Ver `colunas.P_PEDIDO_VINCULADO`.
    pedido_vinculado: Any = ""
    #: Quais colunas de classificação foram **propostas** pela base de
    #: conhecimento, e com que grau. Rótulo da coluna → grau. Existe para que
    #: a célula proposta saia marcada na planilha: quem lê precisa saber o que
    #: é decisão de gente e o que é sugestão da ferramenta.
    propostas: dict[str, str] = field(default_factory=dict)
    #: Preenchido quando a limpeza descarta a linha (regras A1 e A3).
    motivo_do_descarte: str = ""
    #: A chave foi encontrada na Conferência de Entradas?
    #:
    #: No VBA esta pergunta não existe como campo: ela é lida indiretamente,
    #: pelo literal `"não"` que as três colunas recebem quando a nota não está
    #: no CE. A regra B1 depende disso para não disparar — e depender de um
    #: literal é frágil. Aqui a resposta é guardada, e a condição de B1 pode
    #: dizer o que quer dizer.
    no_ce: bool = False

    # -- acesso por nome ---------------------------------------------------

    def de(self, nome: str) -> Any:
        """O valor daquela coluna do XML."""
        return self.valores[POSICAO[nome]]

    def definir(self, nome: str, valor: Any) -> None:
        self.valores[POSICAO[nome]] = valor

    def texto(self, nome: str) -> str:
        """O valor como o VBA o veria: `CStr` da célula, sem normalizar."""
        return texto_de(self.de(nome))

    # -- as duas chaves ----------------------------------------------------

    @property
    def chave_bruta(self) -> str:
        """A chave como veio, para o confronto com a Conferência de Entradas."""
        return texto_de(self.de(col.X_CHAVE))

    @property
    def chave(self) -> str:
        """Os 44 dígitos, para o livro de classificação."""
        return chave_de_acesso(self.de(col.X_CHAVE))

    # -- as linhas de cada aba --------------------------------------------

    def linha_auxiliar(self) -> list[Any]:
        """27 colunas — `CTe`, `Manifestados` e `Entradas 3os`."""
        return list(self.valores)

    def linha_descartada(self) -> list[Any]:
        """28 colunas — as 27 mais o motivo pelo qual a linha saiu."""
        return [*self.valores, self.motivo_do_descarte]

    def linha_lancada(self) -> list[Any]:
        """33 colunas — as 27 com as 6 de conferência no lugar certo."""
        corte = POSICAO[col.X_CHAVE] + 1
        return [*self.valores[:corte], *self.conferencia, *self.valores[corte:]]

    def linha_pendente(self) -> list[Any]:
        """39 colunas — as 5 de categorização, as 33, e o pedido na nona.

        A inserção é pelo **nome** da coluna vizinha, como o layout faz em
        `colunas.com_conferencia`: as duas descrições do mesmo arranjo não
        podem depender de um índice escrito duas vezes.
        """
        corpo: list[Any] = []
        for coluna, valor in zip(col.XML, self.valores):
            corpo.append(valor)
            if coluna.rotulo == col.X_EMISSAO:
                corpo.append(self.pedido_vinculado)
            elif coluna.rotulo == col.X_CHAVE:
                corpo.extend(self.conferencia)
        return [*self.categorizacao, *corpo]

    def linha_fis_fat(self) -> list[Any]:
        """36 colunas — as 38 sem `Gestor de apoio` e sem `Categoria`.

        As duas saem pelo **nome**, e não por índice: é o equivalente honesto
        do que o VBA faz ao localizá-las por cabeçalho e apagá-las da maior
        posição para a menor, para não invalidar os índices no caminho.
        """
        fora = {col.POSICAO_DA_CATEGORIZACAO[nome]
                for nome in col.FORA_DA_FIS_FAT}
        categorizacao = [v for i, v in enumerate(self.categorizacao)
                         if i not in fora]
        return [*categorizacao, *self.linha_lancada()]


def ler_documentos(linhas: Sequence[Sequence[Any]], mapa: Mapa) -> list[Documento]:
    """As linhas do XML viram documentos, na ordem em que estão no relatório.

    Linha com `Nro Nota` vazio **não vira documento** — é a condição literal
    do VBA na etapa 10, e ela é o que impede o rodapé do relatório (total,
    linha em branco, assinatura) de virar uma nota pendente.
    """
    documentos = []
    for linha in linhas:
        if not texto_de(mapa.valor(linha, col.X_NRO_NOTA)).strip():
            continue
        documentos.append(Documento(
            posicao=len(documentos),
            valores=[mapa.valor(linha, nome) for nome in col.NOMES_DO_XML],
        ))
    return documentos


@dataclass(frozen=True)
class LinhaDeConferencia:
    """Uma linha da Conferência de Entradas, com as 7 colunas que interessam."""

    chave: str
    conferencia_fisica: Any
    conf_fiscal: Any
    motivo_incongruencia: Any
    data_da_conferencia: Any
    numero_do_pedido: Any
    #: O HTML cru do farol. A tradução é do módulo `conferencia`, porque a
    #: tabela de códigos é parâmetro e chega de fora.
    pedido_confirmado: Any


def ler_conferencia(linhas: Sequence[Sequence[Any]],
                    mapa: Mapa) -> list[LinhaDeConferencia]:
    """As linhas do CE viram registros — **sem** índice e sem descarte ainda.

    Quem indexa é `conferencia.indexar`, e é lá que mora a regra "primeira
    ocorrência vence". Separá-las é o que permite contar as duplicadas em vez
    de perdê-las no caminho, que é o que acontece hoje.
    """
    registros = []
    for linha in linhas:
        chave = texto_de(mapa.valor(linha, col.E_CHAVE))
        if not chave.strip():
            continue
        registros.append(LinhaDeConferencia(
            chave=chave,
            conferencia_fisica=mapa.valor(linha, col.E_CONFERENCIA_FISICA),
            conf_fiscal=mapa.valor(linha, col.E_CONF_FISCAL),
            motivo_incongruencia=mapa.valor(linha, col.E_MOTIVO_INCONGRUENCIA),
            data_da_conferencia=mapa.valor(linha, col.E_DATA_DA_CONFERENCIA),
            numero_do_pedido=mapa.valor(linha, col.E_NRO_DO_PEDIDO),
            pedido_confirmado=mapa.valor(linha, col.E_PEDIDO_CONFIRMADO),
        ))
    return registros
