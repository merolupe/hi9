"""O nome de cada coluna lida e a ordem exata das colunas de cada aba.

Duas coisas moram aqui, e nenhuma delas é regra de negócio.

**Os nomes de coluna das fontes** são constantes porque são a chave com que o
motor consulta o `Mapa` montado por `cabecalho.mapear`. O nome *aceito* é
parâmetro — está na carga de fábrica, com sinônimos, e uma exportação que
renomeie `Vlr. Nota` resolve-se cadastrando o sinônimo na tela. O que está
aqui é só o nome canônico, para o código não escrever a mesma string em cinco
lugares.

**A ordem das colunas de saída** é literal e não se mexe. A planilha vai por
e-mail para dezenas de pessoas que sabem onde cada coluna está, e várias
mantêm PROCX e tabela dinâmica por cima. `Lancadas` tem 12 colunas,
`Pendentes` 36, `Canceladas` 16 e `Sem Correspondencia ASIS` 7 + N.

Duas advertências que o porte registrou e que esta ordem preserva:

* **`Canceladas` não é a `Pendentes` mais duas colunas.** É um layout próprio,
  sem os campos de herança, sem tributos, sem `Codigo Verificador` e sem o
  bloco de Conferência, e com a ordem interna diferente — `Valor` vem antes de
  `Cidade`, o que na `Pendentes` não acontece.
* **`Lancadas` coluna 8 traz `"Nao"` em 100% das linhas**, por construção: as
  canceladas são segregadas antes da cascata e nunca chegam ali. É coluna sem
  informação, preservada porque removê-la mudaria 12 colunas para 11 — que é
  invariante da prova e possível alvo de fórmula de terceiro.
"""
from __future__ import annotations

from ..escrita import Coluna

# -- ASIS (notas emitidas, padrão Portal Nacional) --------------------------

A_NUMERO = "Numero NFe"
A_EMISSAO = "Data Emissao NFe"
A_DATA_CANCELAMENTO = "Data Cancelamento"
A_MOTIVO_CANCELAMENTO = "Motivo Cancelamento"
A_LEI116 = "Codigo Item Lei 116"
A_DESCRICAO_SERVICO = "Descricao do Servico Municipal"
A_MUNICIPIO = "Municipio Prestacao"
A_PRESTADOR = "Prestador"
A_CNPJ_PRESTADOR = "CNPJ/CPF Prestador"
A_VALOR = "Valor NFe"
A_DISCRIMINACAO = "Discriminacao"
A_CNPJ_TOMADOR = "CNPJ/CPF Tomador"
A_RPS = "Numero RPS"
A_CODIGO_VERIFICADOR = "Codigo Verificador"

#: Os cinco pares alíquota/valor, na ordem em que vão para as colunas 18 a 27.
A_TRIBUTOS = (
    "Aliquota ISS", "Valor ISS",
    "Aliquota PIS", "Valor PIS",
    "Aliquota COFINS", "Valor COFINS",
    "Aliquota CSLL", "Valor CSLL",
    "Aliquota INSS", "Valor INSS",
)

# -- Portal de Compras (Sankhya) -------------------------------------------

P_USUARIO_INCLUSAO = "Nome (Usuario Inclusao)"
P_NUMERO_UNICO = "Nro. Unico"
P_DESCRICAO_TOP = "Descricao (Tipo de Operacao)"
P_NUMERO_NOTA = "Nro. Nota"
P_CODIGO_PARCEIRO = "Parceiro"
P_NOME_PARCEIRO = "Nome Parceiro (Parceiro)"
P_VALOR = "Vlr. Nota"
P_USUARIO_RC = "Usuario inclusao RC"
P_EMPRESA = "Empresa"
P_NOME_EMPRESA = "Nome Fantasia (Empresa)"
P_TOP = "Tipo Operacao"
P_NATUREZA = "Descricao (Natureza)"
P_CENTRO_DE_RESULTADO = "Descricao (Centro de Resultado)"
P_CNPJ_PARCEIRO = "CNPJ / CPF Parceiro"
P_CNPJ_EMPRESA = "CNPJ Empresa"
P_DATA_NEGOCIACAO = "Dt. Neg."

# -- Conferência de Serviços ------------------------------------------------

C_NUMERO_UNICO = "Nro. Unico Servico"
C_ULTIMO_ANEXO = "Dt. Hra. Ult. Anexo"
C_VALOR = "Vlr. total"
C_PARCEIRO = "Parceiro"
C_EMPRESA = "Empresa"
C_STATUS = "Status lancamento"
C_PEDIDO_CONFIRMADO = "Pedido Confirmado?"
C_MOTIVO = "Motivo incongruencia"

# -- semana anterior --------------------------------------------------------

S_NUMERO_NOTA = "Nro Nota"
S_CODIGO_PARCEIRO = "Cod Parceiro"

#: As duas colunas que formam a identidade de um registro entre semanas.
S_CHAVE = (S_NUMERO_NOTA, S_CODIGO_PARCEIRO)

# -- as âncoras de cabeçalho de cada fonte ---------------------------------

ANCORA_ASIS = A_NUMERO
ANCORA_PORTAL = P_NUMERO_UNICO
ANCORA_CONFERENCIA = C_NUMERO_UNICO
ANCORA_ANTERIOR = S_NUMERO_NOTA


# -- as quatro abas ---------------------------------------------------------

#: `Lancadas` — 12 colunas. A 12ª (`Obs`) é o alerta de chave duplicada, e é o
#: que o dossiê contava como inexistente: ele declarava 11.
LANCADAS: tuple[Coluna, ...] = (
    Coluna("Nro. Nota", "texto"),
    Coluna("Emissao", "data"),
    Coluna("Cod. Parceiro"),
    Coluna("Parceiro"),
    Coluna("Valor", "valor"),
    Coluna("Cidade da prestacao"),
    Coluna("Filial"),
    Coluna("Cancelada?"),
    Coluna("Codigo servico da nota"),
    Coluna("Servico (descricao do codigo do servico LC/116)"),
    Coluna("Confronto utilizado"),
    Coluna("Obs"),
)

#: `Pendentes` — 36 colunas. As 8 últimas são o vínculo com a Conferência de
#: Serviços, que o dossiê dava como desconhecido e o código já implementava.
PENDENTES: tuple[Coluna, ...] = (
    Coluna("Nro Nota", "texto"),
    Coluna("Emissao", "data"),
    Coluna("Cod Parceiro"),
    Coluna("Parceiro"),
    Coluna("Guardiao"),
    Coluna("Gestor de apoio"),
    Coluna("Retorno"),
    Coluna("Valor NFSe (Valor Bruto)", "valor"),
    Coluna("Cidade da prestacao"),
    Coluna("Filial"),
    Coluna("Pedido de compra mais recente"),
    Coluna("Ultimo Comprador"),
    Coluna("Ultimo Requisitante"),
    Coluna("Observacao da nota"),
    Coluna("Ultima Natureza"),
    Coluna("Ultimo CR"),
    Coluna("Servico (descricao do codigo do servico LC/116)"),
    Coluna("Aliq. ISS", "valor"),
    Coluna("Valor ISS", "valor"),
    Coluna("Aliq. PIS", "valor"),
    Coluna("Valor PIS", "valor"),
    Coluna("Aliq. COFINS", "valor"),
    Coluna("Valor COFINS", "valor"),
    Coluna("Aliq. CSLL", "valor"),
    Coluna("Valor CSLL", "valor"),
    Coluna("Aliq. INSS", "valor"),
    Coluna("Valor INSS", "valor"),
    Coluna("Codigo Verificador", "texto"),
    Coluna("Pedido conferencia (NU)"),
    Coluna("Dt. ult. anexo", "data"),
    Coluna("Vlr. pedido", "valor"),
    Coluna("Fator"),
    Coluna("Status lancamento"),
    Coluna("Pedido confirmado?"),
    Coluna("Motivo incongruencia"),
    Coluna("Confianca do vinculo"),
)

#: `Canceladas` — 16 colunas, layout próprio.
CANCELADAS: tuple[Coluna, ...] = (
    Coluna("Nro Nota", "texto"),
    Coluna("Emissao", "data"),
    Coluna("Cod Parceiro"),
    Coluna("Parceiro"),
    Coluna("Valor NFSe (Valor Bruto)", "valor"),
    Coluna("Cidade da prestacao"),
    Coluna("Filial"),
    Coluna("Pedido de compra mais recente"),
    Coluna("Ultimo Comprador"),
    Coluna("Ultimo Requisitante"),
    Coluna("Ultima Natureza"),
    Coluna("Ultimo CR"),
    Coluna("Servico (descricao do codigo do servico LC/116)"),
    Coluna("Observacao da nota"),
    Coluna("Data Cancelamento", "data"),
    Coluna("Motivo Cancelamento"),
)

#: O bloco de análise da aba inversa. Vem **antes** das colunas de origem, e
#: não depois: o relatório do Portal de Compras chega a 268 colunas, e no fim
#: da linha o bloco ficaria invisível.
ANALISE_DA_INVERSA: tuple[Coluna, ...] = (
    Coluna("Correspondencia no ASIS antes?"),
    Coluna("Emissao ASIS anterior mais proxima", "data"),
    Coluna("Correspondencia no ASIS depois?"),
    Coluna("Emissao ASIS posterior mais proxima", "data"),
    Coluna("Qtde notas do parceiro (Entradas)"),
    Coluna("Qtde notas do parceiro (ASIS)"),
    Coluna("Diferenca (Entradas - ASIS)"),
)

#: As colunas de origem que abrem o bloco, na ordem da `Lancadas`.
PREDEFINIDAS_DA_INVERSA = (
    P_NUMERO_NOTA, P_CODIGO_PARCEIRO, P_NOME_PARCEIRO, P_VALOR, P_EMPRESA,
)

#: O trecho que define o segundo bloco de colunas da inversa: tudo que tiver
#: `CIDADE` no nome vem logo depois das pré-definidas.
TRECHO_DE_CIDADE = "CIDADE"

#: Os nomes das abas, na ordem de criação.
#: `Fora do relatorio` — as 36 da `Pendentes` mais o motivo de ter saído.
#: A nota sai inteira, e não resumida: quem for conferir a exclusão precisa do
#: mesmo que precisaria para cobrá-la.
FORA_DO_RELATORIO: tuple[Coluna, ...] = (*PENDENTES, Coluna("Motivo"))

ABAS = ("Lancadas", "Pendentes", "Canceladas", "Sem Correspondencia ASIS",
        "Fora do relatorio")

#: A aba de exclusões, pelo nome — é por ele que a semana seguinte a encontra
#: no arquivo anterior, como `ABA_FIS_FAT_ANTERIOR` faz em mercadorias.
ABA_FORA_DO_RELATORIO = ABAS[4]
