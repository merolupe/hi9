"""A janela do Apurabot: interface no navegador, servida pela própria máquina.

Ver `servidor.py` para o motivo de a interface ser o navegador, e não um
programa novo instalado.
"""
from .servidor import abrir

__all__ = ["abrir"]
