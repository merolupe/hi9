"""O que sai do relatório de serviços, e por quê — nomeado, nunca calado.

Duas coisas tiram uma nota da `Pendentes` depois da cascata, e as duas vêm de
fora do confronto:

### 1. A nota cancelada na prefeitura que a nossa base não sabe

`[FATO]` Regra do time fiscal, 22/09/2026. Acontece de a NFS-e ser cancelada
na prefeitura e o evento de cancelamento **nunca chegar** à base de serviços.
Do lado de cá a nota continua emitida, nunca é lançada, e volta toda semana
como pendência de alguém — um trabalho recorrente para redescobrir a mesma
conclusão.

Quando isso é descoberto, quem remodela a planilha escreve `cancelada` em
`Guardiao`, `Gestor de apoio` e no `Retorno`. **São os três**: um campo
sozinho é digitação, os três juntos são uma afirmação.

O que este módulo faz com isso é o que o time pediu: a nota sai da
`Pendentes` e vai para uma aba própria, com o motivo. E como a marca vive no
**livro de classificação** — que é onde a classificação da semana passada já
mora —, ela sobrevive à planilha: perder o arquivo não faz a nota voltar.

### 2. A exceção cadastrada

Parceiro e valor que o time decidiu não cobrar. Não é regra de negócio
derivável de nada: é decisão, e por isso é **cadastro**, não código —
`excecoes_servicos` na base viva, com parceiro, valor e o motivo que vai
para a planilha. Nasce vazia, e vazia não exclui nada.

### Por que as duas saem para a mesma aba

Porque a pergunta que elas respondem é a mesma: *por que esta nota não está
na cobrança desta semana?* Uma aba com a coluna `Motivo` responde as duas, e
é a mesma decisão da aba `Descartados` de mercadorias — esconder, e não
apagar, para que o volume excluído seja mensurável.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Sequence

from ..estado import Classificacao
from ..texto import aparar, chave_de_texto
from ..valores import numero_br

#: O que a planilha escreve na coluna `Motivo` de cada caso.
MOTIVO_CANCELADA = "cancelada na prefeitura (marcada na semana anterior)"

#: Quantas casas decimais separam dois valores. Dinheiro se compara em
#: centavos: `50` e `50.0` e `"50,00"` são a mesma nota de cinquenta reais.
CASAS = 2


@dataclass(frozen=True)
class Excecao:
    """Um parceiro e um valor que o time decidiu não cobrar."""

    codigo_do_parceiro: str
    valor: float
    nome: str = ""
    motivo: str = ""

    def casa(self, codigo: Any, valor: Any) -> bool:
        if chave_de_texto(codigo) != chave_de_texto(self.codigo_do_parceiro):
            return False
        return round(numero_br(valor), CASAS) == round(self.valor, CASAS)

    def como_motivo(self) -> str:
        if self.motivo:
            return self.motivo
        nome = self.nome or self.codigo_do_parceiro
        return (f"exceção cadastrada: {nome} com nota de "
                f"{self.valor:.2f}".replace(".", ","))


def excecoes_de(declaradas: Iterable[dict]) -> tuple[Excecao, ...]:
    """As exceções vindas do parâmetro. Linha sem parceiro ou sem valor sai."""
    saida = []
    for linha in declaradas or ():
        codigo = aparar(linha.get("codigo_parceiro") or linha.get("parceiro"))
        bruto = linha.get("valor")
        if not codigo or bruto in (None, ""):
            continue
        saida.append(Excecao(
            codigo_do_parceiro=codigo,
            valor=numero_br(bruto),
            nome=aparar(linha.get("nome")),
            motivo=aparar(linha.get("motivo")),
        ))
    return tuple(saida)


def cancelada_na_prefeitura(classificacao: Classificacao, marca: str) -> bool:
    """Os **três** campos dizem `cancelada`?

    Exigir os três não é rigor decorativo: `Guardiao` sozinho com `cancelada`
    é a pessoa começando a escrever, e tirar a nota do relatório por causa
    disso seria decidir no lugar dela. O retorno considerado é o da semana
    mais recente que o livro guardou, que é o que a planilha devolveu.
    """
    alvo = chave_de_texto(marca)
    if not alvo:
        return False
    return all(chave_de_texto(valor) == alvo
               for valor in (classificacao.guardiao,
                             classificacao.gestor_de_apoio,
                             classificacao.ultimo_retorno))


def motivo_da_exclusao(classificacao: Classificacao, *, marca: str,
                       codigo_do_parceiro: Any, valor: Any,
                       excecoes: Sequence[Excecao] = ()) -> str:
    """O motivo pelo qual esta nota não entra na `Pendentes`, ou `""`.

    O cancelamento vem primeiro: ele é a afirmação de que a nota **não
    existe mais**, e uma nota que não existe não precisa casar com exceção
    nenhuma para ficar de fora.
    """
    if cancelada_na_prefeitura(classificacao, marca):
        return MOTIVO_CANCELADA
    for excecao in excecoes:
        if excecao.casa(codigo_do_parceiro, valor):
            return excecao.como_motivo()
    return ""
