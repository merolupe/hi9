"""O motor de mercadorias: o cruzamento do XML com a Conferência de Entradas.

A pergunta que este módulo responde é *quais NF-e emitidas contra a Hinove
ainda não têm conferência fiscal* — e, para cada uma, de quem é a
responsabilidade e há quantos dias ela está parada.

Aqui existe chave natural: a **chave de acesso**, 44 dígitos. Por isso não há
cascata de procedimentos como em serviços; há um lookup só. O trabalho está em
outro lugar — em decidir **o que entra no relatório**, e é uma sequência de
regras cuja ordem é a regra:

```
limpeza        A1 (XML de terceiro)  →  A3 (NF-e de transporte)  →  A2 (parceiro)
   ↓           o que A1 e A3 tiram vai para a aba `Descartados`, com o motivo
roteamento     4 condições, a primeira verdadeira consome a linha
   ↓           CTe · Manifestados · Entradas 3os — e o que sobra é pendência
conferência    o lookup do CE: 6 colunas, farol de três estados
   ↓           `Conf fiscal = Sim` sai para `Lançados`
classificação  a herança vem do livro  →  B1 (Fiscal)  →  B2 (split FIS-FAT)
```

**A ordem carrega correção de defeito antigo, e o VBA documenta cada uma:**
A1 antes de A3 (fantasia vazia sai antes de o tipo ser consultado); a limpeza
antes do roteamento (senão um XML de terceiro com `Entrada` sobreviveria em
`Entradas 3os`); B1 depois da herança (senão o valor herdado a sobrescreveria)
e antes de B2 (senão os registros já teriam sido movidos e o split não os
pegaria). Cada uma dessas ordens tem teste com nome próprio.

| Módulo | O que resolve |
|---|---|
| `colunas` | as 27 do XML, as 7 do CE e a ordem exata das 38 / 36 / 33 / 27 / 28 |
| `fontes` | as matrizes viram documento e linha de conferência |
| `limpeza` | A1, A2, A3 — e a aba `Descartados`, que é a única aba nova do porte |
| `roteamento` | as 4 condições parametrizadas e a segregação de `Lançados` |
| `conferencia` | o lookup do CE, as 6 colunas e os três estados do farol |
| `classificacao` | a herança pelo livro, B1 e B2 |
| `vocabulario` | unidade, categoria e guardião: o que a ferramenta não reconhece |
| `execucao` | o pipeline de ponta a ponta e o que a tela mostra |

**Sem Resumo Executivo.** Ele saiu do porte por decisão do Compliance
Tributário de 15/09/2026 e vira outra coisa — um resumo das duas frentes, com
três categorias. Por isso não há `resumo.py` nem `graficos.py` aqui, e não há
`_AuxResumo` na planilha. O que sobrou do painel é a derivação de unidade e de
categoria, que continua em `vocabulario`: ela não é ornamento, é o que permite
dizer que a ferramenta **não** reconheceu alguma coisa — e bloquear a semana.
"""
