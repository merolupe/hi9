"""A base de conhecimento: o que o histórico já respondeu, e com que lastro.

Ela **propõe** classificação. Não classifica. A diferença é a regra nº 4 do
`CLAUDE.md` levada a sério: uma sugestão que entra na planilha já preenchida
vira, na prática, classificação por adivinhação — alguém confirma sem olhar.

Por isso tudo aqui tem três camadas, e nenhuma delas se esconde:

| Camada | O que é | O que pode fazer |
|---|---|---|
| **proposta** | o valor que a lista curada oferece | aparecer |
| **evidência** | quantas notas, quantas semanas, com que concordância | sustentar ou desmentir a proposta |
| **confiança** | o que sai do cruzamento das duas | decidir se aquilo pode preencher |

Nada preenche sozinho enquanto a proposta e a evidência não disserem a mesma
coisa, com lastro suficiente. O resto é sugestão visível.
"""
from __future__ import annotations

__all__ = ["base", "importacao", "simulacao"]
