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
(`56,25` → `56,3`, não `56,2`); o `br()` do toolkit já arredonda assim.

O gráfico de valor **não tem os trimestres**: começa na semana 35. São duas
listas de categorias diferentes no mesmo slide, e misturar as duas deixa o
empilhado deslocado em duas posições.

## Tabela auxiliar

Abaixo do gráfico da esquerda: linhas Indiretos, Diretos, Serviços e TOTAL;
colunas iguais às do gráfico de quantidade.

| Elemento | Geometria |
|---|---|
| Rótulo de linha | `x` 0,50 · largura 1,55 — `DCE6F5`, navy negrito |
| Células | de `x` 2,05 até 6,55, divididas pelo número de colunas |
| Altura da linha | 0,31, começando em `y` 4,92 |
| Linha TOTAL | fundo `DCE6F5`, navy negrito |

A fonte acompanha a largura da coluna: 12pt coube em 0,75", 8pt em 0,45" (dez
colunas). Com mais semanas, encolha antes de renderizar — já aconteceu de
`104,8` quebrar em duas linhas. Linhas alternam branco e `F5F8FD`.

O teto do eixo da quantidade olha a **maior série** (`103` em Serviços na S42
estourou o máximo de 100); o do valor olha a **soma da semana**, porque a área
é empilhada — o pico de R$ 6,73 mi da S36 é a soma das três, não o Diretos
sozinho.

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

## Quando o slide não está no deck

Já aconteceu de o time tirar o slide por uma semana e pedir de volta depois.
O deck que chega não tem o slide **nem o histórico**, então procure o último
deck que ainda o tinha e transplante a parte inteira: `slides/slideN.xml`, os
dois `chartN.xml` com seus `_rels` e as duas planilhas embutidas, mais o
`Override` no `[Content_Types].xml`, o `Relationship` em
`ppt/_rels/presentation.xml.rels` e o `<p:sldId>` no fim do `sldIdLst`.

As imagens do cabeçalho e do rodapé costumam já existir no deck de destino com
**outro número** (`image3.png` de um é `image2.png` do outro) — confira pelo
md5 e aponte os rels para as que já estão lá, em vez de duplicar arquivo.
