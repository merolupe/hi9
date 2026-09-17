"""O nome de cada coluna lida e a ordem exata das colunas de cada aba.

Como em serviços, duas coisas moram aqui e nenhuma delas é regra de negócio:
o **nome canônico** com que o motor consulta o `Mapa` (o nome *aceito* é
parâmetro, com sinônimos, na carga de fábrica) e a **ordem de saída**, que é
literal e não se mexe — a planilha vai por e-mail para dezenas de pessoas que
sabem onde cada coluna está, e várias mantêm PROCX por cima.

### As larguras, e por que elas são diferentes

| Aba | Colunas | De onde vem a largura |
|---|---|---|
| `Pendentes` | **38** | 5 de categorização + 27 do XML + 6 de conferência |
| `PENDENTES FIS-FAT` | **36** | as 38 menos `Gestor de apoio` e `Categoria` |
| `CTe`, `Manifestados`, `Entradas 3os` | **27** | o cabeçalho copiado na etapa 11 |
| `Lançados` | **33** | o cabeçalho copiado na etapa 15: já com as 6, ainda sem as 5 |
| `Descartados` | **28** | as 27 do XML mais o motivo — **a única aba nova** |

`[FATO]` A diferença entre 27 e 33 é acidente do momento em que cada aba
recebe a cópia da linha 1, e não decisão. Igualar todas em 38 seria trivial e
**não se faz**: são invariantes da prova de regressão, e alguém pode ter
fórmula apontando para a coluna 27 de `Entradas 3os`. É a pendência nº 8, para
depois da divergência zero.

### Os formatos, e por que eles são declarados antes da escrita

O VBA formata `Chave Acesso`, `Cnpj Parceiro`, `Código`, `Nro Nota` e `Nome
Parceiro (Parceiro)` como Texto **antes** de gravar — sem isso o Excel
converte 44 dígitos em `3,52604E+43` e o PROCX para de casar. E formata as
seis colunas de conferência uma a uma logo depois de inseri-las, porque
`Insert Shift:=xlToRight` as faria herdar o Texto da vizinha `Chave Acesso` e
a data viraria string. Aqui não há `Insert`, mas a doutrina fica: a coluna
declara o formato, e a aba só então recebe a primeira linha.

`Dias Emissão Doc` é declarada `data_ou_contagem`: recebe o formato de data,
como o VBA faz, e o valor vai **como veio**, também como o VBA faz — ele
escreve essa coluna sem conversão. Se a coluna for contagem de dias, o valor 30
aparece como uma data de janeiro de 1900. Defeito visível, preservado de
propósito enquanto a pendência nº 2 não for respondida; converter o número
numa data de verdade trocaria esse defeito por outro, e mudaria a célula.
"""
from __future__ import annotations

from typing import Sequence

from ..escrita import Coluna

# -- XML (Sankhya, relatório de importação) ---------------------------------

X_NRO_NOTA = "Nro Nota"
X_COD_PARCEIRO = "Cód. Parceiro"
X_NOME_PARCEIRO = "Nome Parceiro (Parceiro)"
X_EMISSAO = "Dh. Emissão"
X_CFOP = "CFOP's XML"
X_VALOR = "Valor da Nota"
X_NOME_FANTASIA = "Nome Fantasia"
X_CHAVE = "Chave Acesso"
X_VENCIMENTO = "Dt. Vencimento"
X_SITUACAO_DA_MANIFESTACAO = "Situação da manifestação"
X_SITUACAO_NFE = "Situação NF-e"
X_TIPO_NFE = "Tipo NF-e"
X_ULTIMO_EVENTO = "Último Evento DF-e"
X_NATUREZA = "Descrição Nat. Operação"
X_ENTRADA_SAIDA = "Entrada/Saida NF-e"
X_TOMADOR_CTE = "Tomador CT-e"
X_DIAS_EMISSAO = "Dias Emissão Doc"
X_IMPORTACAO = "Dh. Importação"
X_STATUS = "Status"
X_USUARIO = "Nome (Usuário)"
X_PAPEL_NO_CTE = "Papel no CT-e"
X_CODIGO_DA_EMPRESA = "Código da Empresa"
X_CNPJ_PARCEIRO = "Cnpj Parceiro"
X_CODIGO = "Código"
X_POSSUI_XML = "Possui o XML"
X_IMPORTADO_DFE = "Importado pelo DF-e"
X_SERIE = "Série Doc"

#: As 27 colunas do XML, na ordem em que o VBA as escreve — as 16 que ele
#: chama de principais seguidas das 11 complementares. A distinção existe só
#: na declaração: `ConcatArrays` une as duas listas antes de validar, e **as
#: 27 são igualmente obrigatórias**.
XML: tuple[Coluna, ...] = (
    Coluna(X_NRO_NOTA, "texto"),
    Coluna(X_COD_PARCEIRO),
    Coluna(X_NOME_PARCEIRO, "texto"),
    Coluna(X_EMISSAO, "data"),
    Coluna(X_CFOP),
    Coluna(X_VALOR, "valor"),
    Coluna(X_NOME_FANTASIA),
    Coluna(X_CHAVE, "texto"),
    Coluna(X_VENCIMENTO, "data"),
    Coluna(X_SITUACAO_DA_MANIFESTACAO),
    Coluna(X_SITUACAO_NFE),
    Coluna(X_TIPO_NFE),
    Coluna(X_ULTIMO_EVENTO),
    Coluna(X_NATUREZA),
    Coluna(X_ENTRADA_SAIDA),
    Coluna(X_TOMADOR_CTE),
    Coluna(X_DIAS_EMISSAO, "data_ou_contagem"),
    Coluna(X_IMPORTACAO, "data"),
    Coluna(X_STATUS),
    Coluna(X_USUARIO),
    Coluna(X_PAPEL_NO_CTE),
    Coluna(X_CODIGO_DA_EMPRESA),
    Coluna(X_CNPJ_PARCEIRO, "texto"),
    Coluna(X_CODIGO, "texto"),
    Coluna(X_POSSUI_XML),
    Coluna(X_IMPORTADO_DFE),
    Coluna(X_SERIE),
)

#: Os nomes das 27, na ordem — é a ordem dos valores de cada `Documento`.
NOMES_DO_XML: tuple[str, ...] = tuple(c.rotulo for c in XML)

# -- Conferência de Entradas ------------------------------------------------

E_CHAVE = "Chave Acesso"
E_CONFERENCIA_FISICA = "Conferência Física"
E_CONF_FISCAL = "Conf. Fiscal"
E_MOTIVO_INCONGRUENCIA = "Motivo Incongruência"
E_DATA_DA_CONFERENCIA = "Dh. Conferência Física"
E_NRO_DO_PEDIDO = "Nro. do Pedido"
E_PEDIDO_CONFIRMADO = "Pedido confirmado?"

#: As 7 colunas do CE, todas obrigatórias.
NOMES_DO_CE: tuple[str, ...] = (
    E_CHAVE, E_CONFERENCIA_FISICA, E_CONF_FISCAL, E_MOTIVO_INCONGRUENCIA,
    E_DATA_DA_CONFERENCIA, E_NRO_DO_PEDIDO, E_PEDIDO_CONFIRMADO,
)

# -- o bloco de conferência, na saída ---------------------------------------

P_CONF_FISICA = "Conf fisica"
P_DATA_CONF_FISICA = "Dt. Conf. Física"
P_CONF_FISCAL = "Conf fiscal"
P_INCONGRUENCIA = "Incongruência"
P_NRO_DO_PEDIDO = "Nro. do Pedido"
P_PEDIDO_CONFIRMADO = "Pedido confirmado?"

#: As 6 colunas de conferência, sempre imediatamente após `Chave Acesso`. A
#: data acompanha a conferência física — é o par lógico —, e as duas de pedido
#: vêm depois de `Incongruência`.
CONFERENCIA: tuple[Coluna, ...] = (
    Coluna(P_CONF_FISICA, "texto"),
    Coluna(P_DATA_CONF_FISICA, "data"),
    Coluna(P_CONF_FISCAL, "texto"),
    Coluna(P_INCONGRUENCIA, "texto"),
    Coluna(P_NRO_DO_PEDIDO, "texto"),
    Coluna(P_PEDIDO_CONFIRMADO, "texto"),
)

# -- o bloco de categorização, na saída -------------------------------------

C_TIPO_DE_OPERACAO = "Tipo de Operação"
C_GUARDIAO = "Guardião"
C_GESTOR = "Gestor de apoio"
C_CATEGORIA = "Categoria"

#: O prefixo da quinta coluna. O nome inteiro carrega o número da semana, e é
#: por isso que ela é procurada por prefixo em toda leitura.
C_PREFIXO_DO_RETORNO = "Retorno semana"

#: Os cinco nomes do bloco de categorização, na ordem em que eles ocupam as
#: cinco primeiras posições. O quinto muda de nome toda semana — por isso ele
#: entra aqui pelo prefixo, e é pelo prefixo que ele é procurado em toda
#: leitura.
NOMES_DA_CATEGORIZACAO: tuple[str, ...] = (
    C_TIPO_DE_OPERACAO, C_GUARDIAO, C_GESTOR, C_CATEGORIA, C_PREFIXO_DO_RETORNO,
)

#: Em que posição do bloco está cada um. Existe para que nenhuma regra precise
#: escrever "a coluna 2" — o VBA escreve, e é assim que a herança dele
#: embaralha os campos quando alguém insere uma coluna.
POSICAO_DA_CATEGORIZACAO: dict[str, int] = {
    nome: i for i, nome in enumerate(NOMES_DA_CATEGORIZACAO)
}

#: As colunas que a `PENDENTES FIS-FAT` **não** tem. O retorno permanece nela,
#: e o comentário do VBA diz por quê: "é mantido para histórico".
FORA_DA_FIS_FAT: tuple[str, ...] = (C_GESTOR, C_CATEGORIA)

#: A coluna que a aba nova acrescenta, e a razão de ela existir.
D_MOTIVO = "Motivo do descarte"


def rotulo_do_retorno(semana: int) -> str:
    """`Retorno semana 30` quando a semana corrente é a 31.

    O número é o da semana **anterior**, e não o da corrente: a leitura
    pretendida é "retorno recebido referente à cobrança da semana passada".
    É a armadilha nº 11 do porte, e ela vive neste `- 1`.
    """
    return f"{C_PREFIXO_DO_RETORNO} {max(semana - 1, 0)}"


def categorizacao(semana: int) -> tuple[Coluna, ...]:
    """As 5 colunas de classificação, sempre nas posições 1 a 5."""
    return (
        Coluna(C_TIPO_DE_OPERACAO),
        Coluna(C_GUARDIAO),
        Coluna(C_GESTOR),
        Coluna(C_CATEGORIA),
        Coluna(rotulo_do_retorno(semana)),
    )


def com_conferencia(colunas: Sequence[Coluna] = XML) -> tuple[Coluna, ...]:
    """As 27 do XML com as 6 de conferência logo depois de `Chave Acesso`."""
    saida: list[Coluna] = []
    for coluna in colunas:
        saida.append(coluna)
        if coluna.rotulo == X_CHAVE:
            saida.extend(CONFERENCIA)
    return tuple(saida)


#: `Lançados` — 33 colunas: as 27 mais as 6 de conferência, sem as 5 de
#: categorização, porque a aba nasce na etapa 15 e elas só chegam na 16.
LANCADOS: tuple[Coluna, ...] = com_conferencia()

#: `CTe`, `Manifestados` e `Entradas 3os` — 27 colunas, o XML cru.
AUXILIARES: tuple[Coluna, ...] = XML

#: `Descartados` — as 27 mais o motivo. Hoje estas linhas somem sem rastro.
DESCARTADOS: tuple[Coluna, ...] = XML + (Coluna(D_MOTIVO),)


def pendentes(semana: int) -> tuple[Coluna, ...]:
    """`Pendentes` — 38 colunas, na ordem exata da seção A7 do documento."""
    return categorizacao(semana) + com_conferencia()


def fis_fat(semana: int) -> tuple[Coluna, ...]:
    """`PENDENTES FIS-FAT` — as 38 menos `Gestor de apoio` e `Categoria`."""
    return tuple(c for c in pendentes(semana) if c.rotulo not in FORA_DA_FIS_FAT)


def indice(colunas: Sequence[Coluna], rotulo: str) -> int:
    """Em que posição está aquela coluna. `-1` quando ela não está no layout."""
    for i, coluna in enumerate(colunas):
        if coluna.rotulo == rotulo:
            return i
    return -1


#: Os nomes das abas, na ordem em que elas aparecem no arquivo, e se cada uma
#: nasce visível. A ordem é a do VBA, sem `Resumo Executivo` e sem
#: `_AuxResumo` — os dois saíram do porte com o painel. `Descartados` é nova e
#: entra por último, oculta como as outras auxiliares.
ABAS: tuple[tuple[str, bool], ...] = (
    ("Pendentes", True),
    ("CTe", False),
    ("Manifestados", False),
    ("Entradas 3os", False),
    ("Lançados", False),
    ("PENDENTES FIS-FAT", True),
    ("Descartados", False),
)

#: As três abas de destino do roteamento, na ordem em que o VBA as cria.
ABAS_DO_ROTEAMENTO: tuple[str, ...] = ("CTe", "Manifestados", "Entradas 3os")
