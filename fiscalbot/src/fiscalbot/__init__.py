"""Fiscalbot — auditoria do Livro Fiscal de ICMS da Hinove Agrociência S.A.

Lê o relatório *Movimento Livros Fiscais* extraído do Sankhya, identifica a
operação de cada registro pela base de regras e valida o enquadramento em seis
dimensões: CST, valor de ICMS, produto, alíquota, carga efetiva e outros.

É o fornecedor do Livro Fiscal validado que o Apurabot consome.

Descende do módulo VBA `modFiscalbot` v3.2, que rodava dentro de um `.xlsm`.
Aqui o motor é Python e as regras vivem na base do aplicativo, cadastradas pela
tela da Central — não há mais Excel no caminho, só entrada e saída de arquivo.
"""

# As bibliotecas de terceiros viajam junto, em `vendor/`. Isto precisa
# acontecer antes de qualquer import delas — por isso está no topo do pacote.
from ._dependencias import preparar as _preparar

_preparar()

__version__ = "3.2.0"
