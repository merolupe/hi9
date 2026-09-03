"""Apurabot — apuração mensal de ICMS da Hinove Agrociência S.A."""

# As bibliotecas de terceiros viajam junto, em `vendor/`, para que a ferramenta
# rode sem instalação em máquina sem privilégio de administrador. Isto precisa
# acontecer antes de qualquer import delas — por isso está no topo do pacote.
from ._dependencias import preparar as _preparar

_preparar()

__version__ = "0.1.23"
