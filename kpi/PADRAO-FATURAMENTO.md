# Padrão do slide Faturamento x Meta

Registro do formato aprovado pelo time, para o gerador reproduzir toda semana.
A referência é a versão da **S41/2026**, revisada por Luan Lupe.

## Cabeçalho

| Elemento | Texto |
|---|---|
| Título | `Faturamento x Meta – Acumulado/Semanal-<ano>` |
| Subtítulo | `Faturamento bruto em milhões` |
| Faixa do gráfico | `Evolução acumulada  ·  Realizado x Meta` |

A unidade **saiu do título da faixa** e virou uma pílula no canto esquerdo dela:
retângulo arredondado em `0,74" × 0,99"`, `0,56" × 0,27"`, fundo `DCE6F5`,
texto `R$ mil` em Lato 10pt negrito `1F3864`.

## Anotações dentro do gráfico

Duas caixas de texto, Lato 11,9pt negrito, à direita da área de plotagem:

1. **Valores da semana** — duas linhas, uma por linha:
   - `Orçado Sem.: <valor>` em verde `018965`
   - `Realizado Sem.: <valor>` em vermelho `C00000`
2. **Diferença** — `Diferença S<nn>  ·  ▼ R$ <x> mi  (<y>%)` em vermelho `C00000`.

As duas ficam empilhadas, sem sobreposição, acima da curva do realizado.
Na S41 a caixa da diferença ficou estreita demais (1,3") e encavalou na de cima;
o gerador usa 2,6" de largura e posiciona logo abaixo.

## Tabela

- Coluna de rótulos: `x = 0,50"`, largura `1,40"`.
- Colunas de dados dividem o restante até `x = 12,83"` em partes iguais.
- **Todo texto centralizado**, inclusive os rótulos de linha e o `Semanas`.
- Tamanhos: cabeçalho 9pt, rótulos de linha 8,2pt, valores 7,2pt.
  O gerador reduz os valores se a coluna ficar estreita demais.

### Cores por linha

| Linha | Fundo | Texto |
|---|---|---|
| `Semanas` (cabeçalho) | `1F3864` | `FFFFFF` negrito |
| Rótulos de linha | `DCE6F5` | `1F3864` negrito |
| Orçado Acumulado | `FFFFFF` | `333F50` |
| Realizado Acumulado | `F5F8FD` | `333F50` |
| Orçado Semanal | `FFFFFF` | `333F50` |
| Realizado Semanal — abaixo da meta | `B3121F` | `FFFFFF` negrito |
| Realizado Semanal — a partir de 95% da meta | `FFD100` | `1F1F1F` negrito |

O vermelho e o amarelo são **sólidos**, como na planilha de origem — não é mais
o rosa claro com texto vermelho que o slide usava até a S40.

### Colunas de fechamento de trimestre

`1ºQ`, `2ºQ`, `3ºQ`… entram como colunas normais nas linhas acumuladas.
Nas duas linhas semanais não há valor: a célula recebe `–`, fundo `DCE6F5`,
texto `7B8AA3`. As colunas `1ºQ` e `2ºQ` ficam cobertas pelo rótulo da linha,
que se estende por elas.

## Cartões da direita

Calculados a partir dos quatro números da semana — o gerador não recebe
percentual pronto:

| Cartão | Fórmula |
|---|---|
| Atingimento acumulado | `realizado_acum / orçado_acum` |
| Déficit acumulado | `1 − atingimento`, valor `orçado_acum − realizado_acum` |
| Atingimento semanal | `realizado_sem / orçado_sem` |
| Déficit semanal | `1 − atingimento`, valor `orçado_sem − realizado_sem` |
| Meta 3ºQ | `realizado_acum / meta_3q` — congela no fechamento do trimestre |
| Meta anual | `realizado_acum / meta_anual` |

Valores em `R$ <n> mi` (a tabela está em R$ mil, então divide por 1.000).
Acima de 1.000 mi usa `R$ <n,nn> Bi` para não quebrar linha no cartão.

## Destaque tracejado

Retângulo sem preenchimento, borda `C00000` tracejada, 0,64" × ~0,5",
centrado na última categoria do gráfico e cobrindo os dois últimos pontos.
O gerador calcula a posição a partir do número de colunas e da escala do eixo.

## Eixo do gráfico

Máximo fixo em `1.200.000` com unidade de `200.000` enquanto a meta acumulada
couber. O gerador sobe o máximo se a meta passar do topo.
