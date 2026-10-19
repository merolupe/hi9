# Slide Faturamento x Meta

O padrão visual congelado está em `kpi/PADRAO-FATURAMENTO.md` — leia de lá as
cores da tabela, a pílula "R$ mil", as anotações dentro do gráfico e a faixa
de pontos de atenção. Aqui ficam o mapa de coordenadas e as fórmulas.

## Caminho rápido: o gerador

Semana de rotina se resolve numa linha:

```bash
python3 kpi/gerar_faturamento.py \
    --base      deck_anterior.pptx \
    --historico competencias/kpi/faturamento.json \
    --saida     "REUNIAO_SEMANAL_-_S43_2026.pptx" \
    --semana 42 --capa 43 \
    --orc-acum 1.148.975,4 --real-acum 973.083,5 \
    --orc-sem     33.719,5 --real-sem    17.090,1 \
    --atencao "texto da faixa, ou vazio para limpar"
```

Ele refaz tabela, cartões, gráfico, eixo e destaque tracejado. O `--historico`
é um JSON com a série acumulada; se ele não existir (container novo), recrie
a partir da tabela do próprio deck — ela tem a série inteira.

Fechamento de trimestre entra como coluna sem valor semanal: omita
`--orc-sem` e `--real-sem`.

## Fórmulas dos cartões

Nada de percentual digitado à mão:

| Cartão | Conta |
|---|---|
| Atingimento acumulado | `realizado_acum / orçado_acum`, 2 casas |
| Déficit acumulado | `1 − atingimento`; valor `orçado_acum − realizado_acum` |
| Atingimento semanal | `realizado_sem / orçado_sem`, 2 casas |
| Déficit semanal | `1 − atingimento`; valor `orçado_sem − realizado_sem` |
| Meta do trimestre | `realizado no fechamento / meta_trimestre`, 1 casa |
| Meta anual | `realizado_acum / meta_anual`, 1 casa |

A tabela está em **R$ mil**, então o cartão divide por mil: `930.855,6` vira
`R$ 930,9 mi`. Passando de mil milhões usa `R$ 1,08 Bi`, senão o texto quebra
linha dentro do cartão.

**O atingimento do trimestre congela no fechamento.** Depois que a coluna
`3ºQ` existe, ele mede o realizado daquela coluna, não o acumulado corrente —
senão um trimestre fechado continuaria "melhorando".

## Mapa de coordenadas

Posições depois da compressão que abriu espaço para a faixa de atenção (S42).

| Conteúdo | x, y |
|---|---|
| Título / subtítulo (parágrafos 0 e 1) | 0,74 · 0,05 |
| Faixa do gráfico | 0,50 · 0,88 |
| Pílula "R$ mil" | 0,74 · 0,99 |
| Moldura do gráfico | 0,56 · 1,22 · 7,93 × 3,42 |
| `R$ x mi de R$ y` (acumulado) | 8,90 · 1,24 |
| Atingimento acumulado | 11,08 · 1,03 |
| `R$ x mi abaixo da meta` (acumulado) | 8,97 · 1,82 |
| Déficit acumulado | 11,18 · 1,59 |
| Atingimento semanal | 11,08 · 2,61 |
| `R$ x mi de R$ y` (semanal) | 8,91 · 2,86 |
| `DÉFICIT SEMANAL · Snn` | 8,90 · 3,21 |
| Déficit semanal | 11,26 · 3,22 |
| `R$ x mi abaixo da meta` (semanal) | 8,91 · 3,42 |
| Meta do trimestre | 10,09 · 3,96 |
| Meta anual | 10,13 · 4,44 |
| Orçado/Realizado Sem. (anotação) | 5,60 · 2,23 · 2,90 × 0,60 |
| Diferença (anotação) | 4,40 · 2,85 · 4,10 × 0,30 |
| Tabela — primeira linha | 0,50 · 4,80, linhas de 0,24 |
| Faixa de atenção — barra | 0,50 · 6,12 · 12,33 × 0,27 |
| Faixa de atenção — caixa | 0,50 · 6,39 · 12,33 × 0,31 |

As duas anotações são alinhadas à direita e terminam em 8,50", antes da
coluna de cartões. O destaque tracejado é a única forma do slide com
`<a:prstDash val="dash"/>` — ache por isso, não por posição.

## Tabela

Colunas: trimestres fechados mais as semanas do trimestre corrente
(`1ºQ`, `2ºQ`, `3ºQ`, `40`, `41`, `42`…). Quando um trimestre fecha, as
semanas dele somem dentro da coluna do trimestre.

Linhas: Orçado Acumulado, Realizado Acumulado, Orçado Semanal, Realizado
Semanal. Nas duas semanais a coluna de trimestre recebe `–` em `DCE6F5`
com texto `7B8AA3`.

*Realizado Semanal* é o semáforo: vermelho sólido `B3121F` com texto branco
abaixo da meta, amarelo `FFD100` com texto `1F1F1F` a partir de 95% dela.

## Eixo do gráfico

Degraus de 200.000. O gerador sobe o teto quando a meta acumulada passa dele —
confira, porque meta estourando o topo sai cortada.
