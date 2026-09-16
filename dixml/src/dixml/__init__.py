"""DiXML — transforma um lote de XML de nota em planilha.

Lê NF-e e CT-e de dentro de arquivos `.zip` (inclusive `.zip` dentro de `.zip`)
e entrega um `.xlsx` com uma aba por tipo de documento. Serve para conferir
qualquer informação fiscal que esteja no arquivo da nota.

Descende do script `robozinho` v2.2, que rodava com popup do tkinter e pandas.
Aqui a interface é o navegador (ver `central/`) e a planilha é escrita direto
com openpyxl — o pandas tem extensão compilada e não poderia viajar embarcado.
"""

# As bibliotecas de terceiros viajam junto, em `vendor/`. Isto precisa
# acontecer antes de qualquer import delas — por isso está no topo do pacote.
from ._dependencias import preparar as _preparar

_preparar()

__version__ = "2.2.0"
