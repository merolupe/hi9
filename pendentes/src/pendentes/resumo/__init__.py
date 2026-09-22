"""O painel semanal das duas frentes, sobre o relatório já classificado.

O Resumo Executivo **saiu do porte** em 15/09/2026 e volta aqui como outra
coisa. O do VBA era montado no meio da geração de mercadorias, com duas
categorias, e abortava a execução inteira quando falhava (defeito 1). Este é
uma etapa separada, roda depois da classificação estar pronta e enxerga as
**três** categorias — Indiretos, Diretos e Serviços — porque olha as duas
frentes de uma vez.

A ordem não é preferência: o painel conta notas **por categoria**, e categoria
é coisa que a ferramenta propõe e a pessoa confirma. Rodar o resumo antes da
remodelagem manual seria publicar um número que ainda vai mudar.
"""
from __future__ import annotations

__all__ = ["execucao", "escrita", "fontes", "painel"]
