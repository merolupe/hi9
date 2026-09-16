"""Central de Ferramentas Fiscais — a janela única do time Fiscal/Tributário.

Uma tela com as ferramentas do setor: escolhe-se uma, ela pede o arquivo de
que precisa e devolve o resultado. Sem instalar nada, sem sair da máquina.

O que cada ferramenta declara para aparecer aqui está em `ferramentas.py`.
"""
from ._dependencias import preparar as _preparar

_preparar()

__version__ = "0.1.0"
