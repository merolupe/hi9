# Padrão visual dos três slides

Slide 13,333" × 7,5" (16:9). Fonte **Lato** em tudo que é conteúdo; o rodapé
institucional usa Assistant e não se mexe.

## Paleta

| Uso | Hex |
|---|---|
| Navy — títulos, barras de seção, valores | `1F3864` |
| Borda de card e de célula | `BFCDE4` |
| Pílula neutra | `DCE6F5` |
| Linha alternada da tabela | `F5F8FD` |
| Texto corrente | `333F50` |
| Rótulo discreto | `7B8AA3` |
| Positivo — valor | `1E7B34` |
| Positivo — pílula / barra de seção | `E3F3E7` / `018965` |
| Negativo — valor | `B02B3A` |
| Negativo — pílula | `FBE7E4` |
| Atenção intermediária | `9C5A0C` sobre `FCE9D4` |

Nas três frentes dos gráficos a cor identifica a categoria e é a mesma nos
três slides: **roxo `B39DDB`**, **azul `8FAFC7`**, **azul escuro `1F3864`**.

## Positivo e negativo

O padrão do deck é pílula + seta: `▼` para queda, `▲` para alta, e a cor diz
se aquilo é bom ou ruim **no contexto do indicador**, não pela direção. Notas
pendentes caindo é verde com `▼`; valor pendente subindo é vermelho com `▲`.

Zero pendência é verde, qualquer pendência é vermelha — vale tanto no cartão
quanto na coluna da frente.

## Cartões de indicador (faixa superior)

Os três slides usam a mesma faixa de quatro cartões, nas mesmas coordenadas:

| Elemento | Geometria (polegadas) |
|---|---|
| Caixa do cartão | `x` = 0,50 / 3,62 / 6,75 / 9,87 · `y` 0,92 · 2,97 × 1,06 |
| Rótulo (topo) | `x`+0,10 · `y` 0,99 · 2,77 × 0,22 — 10,6pt negrito navy, centrado |
| Pílula do valor | `x`+0,14 · `y` 1,22 · 2,69 × 0,46 — roundRect adj 42000, 19pt negrito |
| Legenda (base) | `x`+0,10 · `y` 1,70 · 2,77 × 0,22 — 10pt `7B8AA3`, centrado |

Valor longo pede corpo menor na pílula (15pt para `R$ 883,2 mil`, 14pt para
`de R$ 1,93 mi para R$ 883,2 mil`); o resto fica em 19pt.

## Barras de seção

Retângulo de largura cheia da coluna, 0,27"–0,30" de altura, texto 12,5pt
branco negrito. Navy `1F3864` para conteúdo neutro, verde `018965` para
"Pontos positivos". Abaixo, caixa branca com borda `BFCDE4` e texto 9,5pt.

## Escrita

Sem rótulo miúdo nem explicação extra: a apresentação tem quem apresente.
Número grande, rótulo curto acima, contexto de uma linha abaixo. Evite
repetir na legenda o que a tabela ao lado já diz.
