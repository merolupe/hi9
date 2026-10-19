# Slide Monitoramento das Entradas Pendentes

Fonte: planilha de pendentes (quantidade e valor por categoria — Indiretos,
Diretos, Serviços) mais os pontos de atenção e positivos escritos pelo time.

## Cartões da faixa superior

| Cartão | Valor | Legenda |
|---|---|---|
| `PENDENTES · Snn` | total de notas | `A ind · B dir · C serv` |
| `VALOR PENDENTE` | total em R$ | `média de R$ x mil por nota` |
| `NOTAS vs S(n−1)` | variação % | `de 151 para 105` |
| `VALOR vs S(n−1)` | variação % | `de R$ 883,2 mil para R$ 1,45 mi` |

Os dois cartões de variação seguem o sentido do indicador: **menos pendência
é bom**, então queda vai de verde com `▼` e alta de vermelho com `▲`. Vale
para os dois — notas e valor caminham separados e já aconteceu de um subir e
o outro cair na mesma semana.

A média por nota é `valor_total / quantidade_total`.

## Gráficos

Dois, lado a lado, cada um com sua barra de seção navy:

| | Esquerda | Direita |
|---|---|---|
| Título | `Notas pendentes por semana (quantidade)` | `Valor financeiro pendente por semana (R$)` |
| Geometria | 0,50 · 2,38 · 6,05 × 2,42 | 6,78 · 2,38 · 6,05 × ~1,95 |
| Tipo | linha com marcadores | área **empilhada** |
| Eixo | máx. ~100, passo 20 | máx. ~7.000.000, passo 1.000.000, formato `R$ #,##0` |

Três séries nos dois: Indiretos `1F3864`, Diretos `B39DDB`, Serviços `8FAFC7`.

A área empilhada foi escolhida porque com três categorias a área sobreposta
ficava ilegível — o empilhamento mostra o total da semana e a composição ao
mesmo tempo. O pico de R$ 6,7 mi da S36 (Diretos) é o que define o teto do
eixo; não encolha por causa dele.

O gráfico de quantidade carrega também os trimestres (`1ºQ`, `2ºQ`) como
categorias iniciais, com valores fracionários — são médias semanais do
trimestre, não totais. Mostre com uma casa decimal e arredondamento comercial
(`56,25` → `56,3`, não `56,2`).

## Tabela auxiliar

Abaixo do gráfico da esquerda: linhas Indiretos, Diretos, Serviços e TOTAL;
colunas iguais às do gráfico de quantidade.

| Elemento | Geometria |
|---|---|
| Rótulo de linha | `x` 0,50 · largura 1,55 — `DCE6F5`, navy negrito |
| Células | de `x` 2,05 até 6,55, divididas pelo número de colunas |
| Altura da linha | 0,31, começando em `y` 4,92 |
| Linha TOTAL | fundo `DCE6F5`, navy negrito |

Corpo 11,5pt cabe em coluna de 0,64"; com mais semanas caia para 10,5pt — já
aconteceu de `104,8` quebrar em duas linhas. Linhas alternam branco e `F5F8FD`.

## Faixas de atenção e positivos

Coluna direita, abaixo do gráfico de valor:

| Elemento | Geometria |
|---|---|
| Barra `Pontos de atenção e riscos da semana` | 6,78 · 4,45 · 6,05 × 0,28 — navy |
| Caixa | 6,78 · 4,72 · 6,05 × 0,69 |
| Barra `Pontos positivos da semana` | 6,78 · 5,66 · 6,05 × 0,28 — verde `018965` |
| Caixa | 6,78 · 5,94 · 6,05 × 0,54 |

O texto vem da planilha, em bullets de 9,5pt. Quebre um parágrafo longo da
origem em dois bullets em vez de deixar uma linha corrida — mas preserve as
palavras do time, que são deles.

Sem texto novo, deixe as caixas vazias para preenchimento: o time escreve na
hora da reunião.

## Conferência da origem

A planilha já veio com total que não batia com a soma das categorias (S36:
total 60 contra 133 somados). Some as categorias, use o que fecha e avise a
divergência — nunca escolha em silêncio.
