"""Falta de parâmetro não é defeito da ferramenta.

Quando a apuração para porque uma filial não está cadastrada, ou porque um CFOP
não casa com nenhuma atividade, a ferramenta está funcionando exatamente como
deve: a regra 4 do repositório proíbe classificar por adivinhação, e a falta
tem que aparecer.

O que não pode é a mensagem tratar isso como bug. Quem fecha a competência
resolve sozinho, editando um `.yaml` — dizer "defeito da ferramenta" mandaria a
pessoa abrir chamado para um problema que é dela e que ela sabe resolver.
"""
from __future__ import annotations

from .nucleo.atividade import MapaDeAtividadeAusente
from .nucleo.centralizacao import CentralizacaoDesconhecida
from .nucleo.estorno import RegimeDesconhecido

#: Falhas que se resolvem cadastrando parâmetro, não corrigindo código.
FALTA_DE_PARAMETRO = (
    RegimeDesconhecido,
    CentralizacaoDesconhecida,
    MapaDeAtividadeAusente,
)

ONDE_CADASTRAR = (
    "Os parâmetros ficam em apurabot/parametros, em arquivos de texto — a "
    "mensagem acima diz qual deles e o que falta nele."
)
