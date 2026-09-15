"""As matrizes viram nota, lançamento e anexo.

Entre a planilha e a regra há uma camada só: cada linha do relatório vira um
registro com os campos já normalizados — o CNPJ sem pontuação, o número da
nota sem o prefixo de ano do Portal Nacional, o valor como número nas três
notações que chegam e a data com parse explícito.

**Isto não é conveniência: é onde as três gramáticas se encontram.** O ASIS
exporta valor como texto com ponto decimal, o Sankhya exporta como número, e
o Excel guarda data como número de série. Se a conversão ficasse espalhada
pelo motor, cada regra teria a sua — e a chave de confronto de um lado
deixaria de bater com a do outro por um detalhe de digitação.

Uma coisa que **não** se normaliza: o registro guarda a linha crua do Portal
de Compras. A aba `Sem Correspondencia ASIS` devolve as colunas de origem tal
como vieram, e é isso que permite ao time conferir o lançamento no Sankhya.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Sequence

from ..cabecalho import Mapa
from ..chaves import (
    CNPJ_ZERADO, analisar_numero_de_nfse, cnpj as so_cnpj, cnpj_utilizavel,
)
from ..texto import aparar, chave_de_texto, limpar_quebras, so_digitos, texto_de
from ..valores import chave_de_valor, data_br, data_hora, numero_br
from . import colunas as col


# -- o número da RPS --------------------------------------------------------

def numero_de_rps(valor: Any) -> str:
    """Só dígitos e sem zeros à esquerda — **sem** o corte de prefixo de ano.

    É a assimetria do procedimento 2, e ela está no VBA: o número da nota
    passa pelo corte dos quatro dígitos de ano, e o da RPS não. Um RPS que
    viesse com prefixo de ano não casaria. O defeito é conhecido, está
    documentado no registro do porte e fica como está até haver medição.
    """
    digitos = so_digitos(valor)
    while len(digitos) > 1 and digitos[0] == "0":
        digitos = digitos[1:]
    return digitos


# -- ASIS -------------------------------------------------------------------

@dataclass(frozen=True)
class NotaDeServico:
    """Uma NFS-e emitida contra a Hinove, como o ASIS a entrega."""

    posicao: int
    numero: str
    numero_bruto: Any
    cortou_prefixo_de_ano: bool
    rps: str
    emissao: Any
    data_de_cancelamento: str
    motivo_do_cancelamento: Any
    cnpj_do_prestador: str
    cnpj_do_tomador: str
    prestador: Any
    municipio: Any
    codigo_lei116: Any
    descricao_do_servico: Any
    discriminacao: str
    codigo_verificador: str
    valor: float
    tributos: tuple[float, ...] = ()

    @property
    def cancelada(self) -> bool:
        """Qualquer conteúdo em `Data Cancelamento` cancela a nota.

        É a condição literal do VBA, e ela é generosa de propósito: uma célula
        com um traço ou com a palavra "sim" também cancela. Adivinhar o
        formato da data para decidir seria pior.
        """
        return bool(self.data_de_cancelamento)

    @property
    def chave_de_valor(self) -> str:
        return f"{self.valor:.2f}"

    @property
    def emissao_e_data(self) -> bool:
        """Falso quando a data não foi interpretável e ficou como texto."""
        return not isinstance(self.emissao, str)


def ler_notas(linhas: Sequence[Sequence[Any]], mapa: Mapa) -> list[NotaDeServico]:
    """As linhas do ASIS viram notas, na ordem em que estão no relatório."""
    notas = []
    for posicao, linha in enumerate(linhas):
        bruto = mapa.valor(linha, col.A_NUMERO)
        analise = analisar_numero_de_nfse(bruto)
        notas.append(NotaDeServico(
            posicao=posicao,
            numero=analise.valor,
            numero_bruto=bruto,
            cortou_prefixo_de_ano=analise.cortou_prefixo_de_ano,
            rps=numero_de_rps(mapa.valor(linha, col.A_RPS)),
            emissao=data_br(mapa.valor(linha, col.A_EMISSAO)),
            data_de_cancelamento=aparar(
                mapa.valor(linha, col.A_DATA_CANCELAMENTO)),
            motivo_do_cancelamento=mapa.valor(linha, col.A_MOTIVO_CANCELAMENTO),
            cnpj_do_prestador=so_cnpj(mapa.valor(linha, col.A_CNPJ_PRESTADOR)),
            cnpj_do_tomador=so_cnpj(mapa.valor(linha, col.A_CNPJ_TOMADOR)),
            prestador=mapa.valor(linha, col.A_PRESTADOR),
            municipio=mapa.valor(linha, col.A_MUNICIPIO),
            codigo_lei116=mapa.valor(linha, col.A_LEI116),
            descricao_do_servico=mapa.valor(linha, col.A_DESCRICAO_SERVICO),
            discriminacao=limpar_quebras(mapa.valor(linha, col.A_DISCRIMINACAO)),
            codigo_verificador=texto_de(
                mapa.valor(linha, col.A_CODIGO_VERIFICADOR)),
            valor=numero_br(mapa.valor(linha, col.A_VALOR)),
            tributos=tuple(numero_br(mapa.valor(linha, nome))
                           for nome in col.A_TRIBUTOS),
        ))
    return notas


# -- Portal de Compras ------------------------------------------------------

@dataclass(frozen=True)
class Registro:
    """Uma linha do Portal de Compras — lançamento, pedido ou nenhum dos dois.

    O relatório traz tudo junto: os lançamentos de serviço (TOP 2020/2111),
    os pedidos de compra (descrição de TOP começando em `PC`) e todo o resto.
    Quem separa é `enriquecimento`; aqui cada linha vira registro sem julgar
    o que ela é.
    """

    posicao: int
    numero: str
    numero_bruto: Any
    cnpj_do_parceiro: str
    codigo_do_parceiro: str
    nome_do_parceiro: Any
    valor: float
    chave_de_valor: str
    empresa: str
    nome_da_empresa: Any
    cnpj_da_empresa: str
    top: str
    descricao_do_top: str
    numero_unico: float
    usuario_de_inclusao: Any
    usuario_do_rc: Any
    natureza: Any
    centro_de_resultado: Any
    data_de_negociacao: Any
    linha: list[Any] = field(default_factory=list)

    def e_lancamento(self, tops: Sequence[str],
                     cnpj_descartado: str = CNPJ_ZERADO) -> bool:
        """TOP de lançamento de serviço **e** CNPJ utilizável.

        As duas condições são do VBA, e a segunda tem consequência: um
        lançamento 2020 com CNPJ vazio ou zerado não é indexado em lugar
        nenhum — some da análise. Hoje some em silêncio; aqui passa a ser
        contado, e a contagem vai para a tela.
        """
        return (self.top in tops) and cnpj_utilizavel(
            self.cnpj_do_parceiro, cnpj_descartado)

    def e_pedido(self, prefixo: str) -> bool:
        return self.descricao_do_top.startswith(chave_de_texto(prefixo))


def ler_registros(linhas: Sequence[Sequence[Any]], mapa: Mapa) -> list[Registro]:
    """As linhas do Portal de Compras viram registros, na ordem do relatório."""
    registros = []
    for posicao, linha in enumerate(linhas):
        bruto = mapa.valor(linha, col.P_NUMERO_NOTA)
        valor = numero_br(mapa.valor(linha, col.P_VALOR))
        registros.append(Registro(
            posicao=posicao,
            numero=analisar_numero_de_nfse(bruto).valor,
            numero_bruto=bruto,
            cnpj_do_parceiro=so_cnpj(mapa.valor(linha, col.P_CNPJ_PARCEIRO)),
            codigo_do_parceiro=texto_de(mapa.valor(linha, col.P_CODIGO_PARCEIRO)),
            nome_do_parceiro=mapa.valor(linha, col.P_NOME_PARCEIRO),
            valor=valor,
            chave_de_valor=f"{valor:.2f}",
            empresa=aparar(mapa.valor(linha, col.P_EMPRESA)),
            nome_da_empresa=mapa.valor(linha, col.P_NOME_EMPRESA),
            cnpj_da_empresa=so_cnpj(mapa.valor(linha, col.P_CNPJ_EMPRESA)),
            top=aparar(mapa.valor(linha, col.P_TOP)),
            descricao_do_top=chave_de_texto(mapa.valor(linha, col.P_DESCRICAO_TOP)),
            numero_unico=numero_br(mapa.valor(linha, col.P_NUMERO_UNICO)),
            usuario_de_inclusao=mapa.valor(linha, col.P_USUARIO_INCLUSAO),
            usuario_do_rc=mapa.valor(linha, col.P_USUARIO_RC),
            natureza=mapa.valor(linha, col.P_NATUREZA),
            centro_de_resultado=mapa.valor(linha, col.P_CENTRO_DE_RESULTADO),
            data_de_negociacao=data_br(mapa.valor(linha, col.P_DATA_NEGOCIACAO)),
            linha=list(linha),
        ))
    return registros


# -- Conferência de Serviços ------------------------------------------------

@dataclass(frozen=True)
class Anexo:
    """Um pedido da Conferência de Serviços, com o último anexo que recebeu."""

    posicao: int
    numero_unico: float
    data_do_anexo: Any
    valor: float
    parceiro: str
    empresa: str
    status_do_lancamento: Any
    pedido_confirmado: Any
    motivo_da_incongruencia: str

    @property
    def chave(self) -> str:
        """`código do parceiro | código da empresa` — a âncora do vínculo."""
        return f"{self.parceiro}|{self.empresa}"


def ler_anexos(linhas: Sequence[Sequence[Any]], mapa: Mapa) -> list[Anexo]:
    """As linhas da Conferência de Serviços viram anexos."""
    anexos = []
    for posicao, linha in enumerate(linhas):
        anexos.append(Anexo(
            posicao=posicao,
            numero_unico=numero_br(mapa.valor(linha, col.C_NUMERO_UNICO)),
            data_do_anexo=data_hora(mapa.valor(linha, col.C_ULTIMO_ANEXO)),
            valor=numero_br(mapa.valor(linha, col.C_VALOR)),
            parceiro=aparar(mapa.valor(linha, col.C_PARCEIRO)),
            empresa=aparar(mapa.valor(linha, col.C_EMPRESA)),
            status_do_lancamento=mapa.valor(linha, col.C_STATUS),
            pedido_confirmado=mapa.valor(linha, col.C_PEDIDO_CONFIRMADO),
            motivo_da_incongruencia=limpar_quebras(
                mapa.valor(linha, col.C_MOTIVO)),
        ))
    return anexos


# -- o fim do relatório -----------------------------------------------------

def ate_a_ultima(linhas: Sequence[Sequence[Any]], mapa: Mapa,
                 ancora: str) -> list[list[Any]]:
    """As linhas até a última que tem a coluna-âncora preenchida.

    O relatório costuma trazer rodapé, total ou linha em branco no fim. O VBA
    resolve com `Cells(Rows.Count, coluna).End(xlUp).Row`, que é exatamente
    isto: a última linha com aquela coluna preenchida manda, e o que vem
    depois não existe. Linha vazia **no meio** continua entrando — ela é dado
    incompleto, não fim de arquivo.
    """
    indice = mapa[ancora]
    ultima = -1
    for i, linha in enumerate(linhas):
        if 0 <= indice < len(linha) and texto_de(linha[indice]).strip():
            ultima = i
    return [list(linha) for linha in linhas[:ultima + 1]]


def chave_de_valor_de(valor: Any) -> str:
    """Atalho para quem precisa da chave de valor sem montar um registro."""
    return chave_de_valor(valor)
