# Slide Agendamentos de Faturamento e Recebimento

Fonte: print do "Painel Gerencial | Agendamentos de Faturamento, Recebimento
e 3ºs". Dele saem três frentes, cada uma com total agendado, processos
finalizados, fila/pendência e % de atendimento contra meta de 95%.

## Cartões da faixa superior

| Cartão | Valor | Legenda |
|---|---|---|
| `AGENDAMENTOS · Snn` | soma das três frentes | `A próprio · B receb. · C 3ºs` |
| `FINALIZADOS` | soma dos finalizados | `X% do total agendado` |
| `PENDÊNCIAS` | quantas em aberto | onde estão, ex.: `entrada em aberto em Registro` |
| `METAS ALCANÇADAS` | `n de 3` | `meta de atendimento 95%` |

Pendências zeradas vão na pílula verde; qualquer pendência vai na vermelha
`FBE7E4` com valor `B02B3A`. O resumo do painel ("1 pendência da unidade de
Registro, sem pedido") cabe na legenda do cartão — não precisa de faixa
própria, a não ser que o time peça.

## Colunas por frente

Três colunas à direita, larguras iguais, uma por frente. A ordem é sempre
Faturamento próprio · Recebimento · Faturamento em 3ºs.

| Elemento | Geometria |
|---|---|
| Barra do nome | `x` = 6,78 / 8,84 / 10,89 · `y` 2,08 · 1,94 × 0,34 — navy, 11,5pt branco |
| Corpo da coluna | mesmo `x` · `y` 2,42 · 1,94 × 4,11 — branco, borda `BFCDE4` |
| `AGENDADOS` / valor | `y` 2,62 (9,5pt `7B8AA3`) e 2,84 (24pt navy) |
| `FINALIZADOS` / valor | `y` 3,56 e 3,78 |
| `PENDENTES` / valor | `y` 4,50 e 4,72 — verde `1E7B34` se 0, vermelho `B02B3A` se > 0 |
| `ATENDIMENTO` / pílula | `y` 5,44 e `x`+0,17 · 5,70 · 1,60 × 0,58 — pílula verde, 20pt |

Os rótulos são iguais nas três frentes mesmo quando o painel usa outro nome
("Notas solicitadas" em 3ºs vira `AGENDADOS`). Essa uniformidade é o que
permite ler as três colunas de enfiada — foi uma decisão do time, mantenha.

## Gráfico de evolução

Linha com as três frentes, uma categoria por semana (`S34`, `S35`…), rótulos
de dados ligados e legenda dentro da área de plotagem.

| Série | Cor |
|---|---|
| Fat. próprio | `B39DDB` |
| Recebimento | `8FAFC7` |
| Fat. 3ºs | `1F3864` |

**O eixo já estourou aqui.** Quando 3ºs foi a 206 com o máximo em 200, a
linha saiu cortada e o rótulo sumiu. Rode `teto_do_eixo(p, graf, maior, 50)`
toda semana.

## Linha TOTAL

Abaixo do gráfico, uma célula por semana com o total agendado daquela semana,
mais um rótulo `TOTAL` à esquerda. **Alinhe com as categorias do gráfico**, não
por espaçamento constante — toda semana nova redistribui as colunas:

```python
centros = centros_das_categorias(p, slide, graf, n_semanas)
largura = 0.63                       # encolha se as colunas apertarem
for centro, celula in zip(centros, celulas):
    x = mover(x, cx_antigo, 5.20, novo_x=centro - largura / 2, w=largura)
```

O rótulo `TOTAL` precisa terminar antes da primeira célula; ajuste a largura
dele junto.

## Semana sem nada a relatar

Já aconteceu de a semana fechar sem fila nem pendência. Nesse caso o time
chegou a remover as faixas de pontos de atenção e positivos e centralizar o
bloco do gráfico. Se o deck vier assim, mantenha assim — e se houver
pendência de novo, vale perguntar se querem a faixa de volta em vez de
recriá-la por conta própria.
