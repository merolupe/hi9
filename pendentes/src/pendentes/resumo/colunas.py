"""Onde cada coisa fica nas duas abas do painel.

O painel da semana 38 foi desenhado à mão, numa planilha, e é ele que manda
aqui: as posições abaixo são as **medidas** daquele arquivo, não uma
interpretação dele. Onde este porte se afasta, o comentário diz por quê.

### Por que existe uma aba auxiliar

Gráfico de Excel não desenha lista de Python: ele aponta para um intervalo de
células. `_AuxResumo` é esse intervalo — e é por isso que ela existe no
arquivo de origem também. Fica **oculta**, como as auxiliares de mercadorias:
esconder não é apagar, e quem quiser conferir o número do gráfico clica com o
botão direito e reexibe.
"""
from __future__ import annotations

#: As duas abas que o painel cria. A segunda nasce oculta.
ABA_DO_PAINEL = "Resumo Executivo"
ABA_AUXILIAR = "_AuxResumo"

#: As três categorias do painel, na ordem em que ele as mostra.
#: `[FATO]` É a ordem do arquivo da semana 38: Diretos, Indiretos, Serviços.
#: Não é alfabética nem por tamanho — é a que está lá, e mudá-la mudaria a
#: leitura de quem já conhece o painel.
DIRETOS = "Diretos"
INDIRETOS = "Indiretos"
SERVICOS = "Serviços"
CATEGORIAS = (DIRETOS, INDIRETOS, SERVICOS)

#: A ordem em que as três aparecem **nos gráficos** e na aba auxiliar.
#: `[FATO]` É outra: lá as colunas são Indiretos, Diretos, Serviços. As duas
#: ordens são do arquivo de origem, e as duas ficam como estão — a cor de cada
#: categoria na barra empilhada vem daqui.
CATEGORIAS_DO_GRAFICO = (INDIRETOS, DIRETOS, SERVICOS)

#: A categoria das notas que vêm do relatório de serviços. Serviço não é
#: classificado entre direto e indireto: a frente inteira **é** a categoria.
CATEGORIA_DE_SERVICOS = SERVICOS

# -- os títulos, como estão no arquivo de origem ---------------------------

TITULO = "Resumo executivo"
TITULO_DA_PIZZA = ("Proporção de notas pendentes por categoria "
                   "(Indiretos, Diretos e Serviços)")
TITULO_DAS_UNIDADES = "Valor de pendências por Unidade (Total)"
TITULO_DOS_GUARDIOES = "Quantidade de pendências por Guardião (Total)"
TITULO_DO_TOP_DIAS = "Notas de maior tempo pendente"
TITULO_DO_TOP_VALOR = "Notas de maior valor pendente"
ROTULO_DA_REFERENCIA = "Data de referência:"
ROTULO_DO_DESTAQUE = "Destacar acima de (dias):"

#: O cabeçalho da tabela por categoria.
TABELA_DE_CATEGORIAS = ("Categoria", "Quantidade", "Valor", "Média dias pendente")
TOTAL = "Total"

#: O cabeçalho dos dois TOP N. `Tempo até` recebe a data de referência.
TABELA_DO_TOP = ("Categoria", "Guardião", "Gestor", "Parceiro", "Valor (R$)",
                 "Emissão", "Tempo até {referencia}")

#: Os formatos de número do painel, medidos no arquivo de origem.
FORMATO_DE_VALOR = '"R$"\\ #,##0.00'
FORMATO_DE_MEDIA = "#,##0.0"
FORMATO_DE_DIAS = "0"
FORMATO_DE_DATA = "DD/MM/YYYY"

# -- a grade do painel ------------------------------------------------------
# Coluna e linha de cada bloco, na notação do openpyxl (1 = A, 1 = primeira).
# As colunas A, F e O são as calhas estreitas do desenho original.

COLUNA_DA_ESQUERDA = 2          # B — a coluna do título e da tabela
COLUNA_DA_DIREITA = 7           # G — a coluna dos dois TOP N
COLUNA_DOS_AJUSTES = 19         # S — os dois rótulos do canto direito
LINHA_DO_TITULO = 2
LINHA_DA_PIZZA = 3              # o título; o gráfico entra na linha seguinte
LINHA_DA_TABELA = 12            # o cabeçalho; os dados vêm depois
LINHA_DOS_GRAFICOS_DE_BAIXO = 18
LINHA_DO_TOP_DIAS = 2           # o título; cabeçalho em +1, dados em +2
LINHA_DO_TOP_VALOR = 10

#: As larguras de coluna do arquivo de origem, por letra. As três calhas
#: (A, F, O) são estreitas de propósito: é o que separa os blocos sem borda.
LARGURAS = {
    "A": 2.8, "B": 18.8, "C": 11.8, "D": 15.8, "E": 17.8, "F": 2.8,
    "G": 9.1, "H": 19.8, "I": 11.8, "J": 34.8, "K": 13.8, "L": 11.8,
    "M": 14.8, "N": 8.8, "O": 2.8, "S": 22.8, "T": 12.8,
}

# -- as colunas da aba auxiliar --------------------------------------------
# Cada bloco ocupa um intervalo fixo, porque é para ele que o gráfico aponta.

BLOCO_DAS_CATEGORIAS = 1        # A:C — categoria, quantidade, valor
BLOCO_DA_CONTAGEM_POR_UNIDADE = 4   # D:G — unidade × as três categorias
BLOCO_DO_VALOR_POR_UNIDADE = 8      # H:K — unidade × as três categorias
BLOCO_DOS_GUARDIOES = 12        # L:O — guardião × as três categorias
BLOCO_DO_GRAFICO_DE_GUARDIOES = 30  # AD:AG — só os que entram no gráfico
CABECALHO_DA_UNIDADE = "Unidade"
CABECALHO_DO_GUARDIAO = "Guardião"
CABECALHO_DA_QUANTIDADE = "Quantidade"
CABECALHO_DO_VALOR = "Valor"
