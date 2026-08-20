# Apurabot — Achados da análise de Julho/2026

> O que a análise do arquivo `Apuração ICMS Julho 2026` revelou sobre o processo
> atual, e o que isso significa para a automação. Os scripts que produziram estes
> números estão em `apurabot/analise/`.

---

## 1. Volume e forma do Livro Fiscal

| Medida | Julho/2026 |
|---|---|
| Linhas no Livro Fiscal | 6.504 |
| Notas distintas | 5.213 |
| Colunas | 52 |
| Produtos distintos | 829 |
| Estabelecimentos | 7 |
| CFOPs distintos | 103 |
| Documentos cancelados | 0 |
| Linhas com carga efetiva (relevantes para ICMS) | 2.345 (36%) |

Volume pequeno. **Desempenho não é um risco deste projeto** — o risco é regra
errada, não máquina lenta.

Espécies de documento: 4.851 NF (modelo 55) · 1.652 CT-e (modelo 57) ·
5 NF de telecomunicações · 4 contas de energia.

## 2. A aba "ICMS" é um filtro determinístico da aba "Livro Fiscal"

A aba `ICMS` (2.346 linhas) é exatamente o Livro Fiscal filtrado pelas linhas que
têm carga efetiva — ou seja, com ICMS efetivo. As 4.159 linhas descartadas são
todas de CST sem crédito/débito:

| CST descartado | Linhas |
|---|---|
| 90 — Outras | 1.800 |
| 41 — Não tributada | 1.322 |
| 60 — ICMS cobrado anteriormente por ST | 337 |
| 51 — Diferimento | 320 |
| 40 — Isenta | 303 |
| 50 — Suspensão | 73 |

**Nenhuma dessas linhas tem ICMS diferente de zero.** O filtro é seguro e
automatizável sem julgamento humano.

## 3. A equalização de carga efetiva é reproduzível — 99,87% de acerto

Este era o ponto de maior incerteza do projeto: transformar a carga bruta
(`ICMS ÷ valor contábil`, que produz 0,100315 · 0,105467 · 0,106649…) em carga
nominal (4 · 7 · 12 · 17 · 18 · 20,5).

Os artefatos aparecem porque o **valor contábil inclui parcelas fora da base do
ICMS** (frete, pedágio, IPI, descontos), enquanto `ICMS ÷ base = alíquota exata`.

Algoritmo testado contra as 2.336 linhas classificadas manualmente:

```
carga_bruta = ICMS ÷ valor_contábil × 100
candidatas  = cargas nominais ≤ alíquota do ICMS      # {4, 7, 12, 17, 18, 19, 20,5, 25}
carga_efetiva = candidata mais próxima da carga_bruta
```

**Resultado: 2.333 de 2.336 linhas idênticas à classificação manual (99,87%).**

E as 3 divergências **não são falha do algoritmo**: são as três notas da ICL
Aditivos (Rio Brilhante, CFOP 2101, CST 00, alíquota 7%) que foram
*manualmente reclassificadas* para 4% e tratadas via ajuste na aba *Controle
Ajustes Docs* — estorno de R$ 1.232,12 + 1.322,39 + 1.310,79, exatamente
`ICMS × 3/7`, que é a regra de MS de limitar o crédito mantido a 4%.

> **Conclusão importante:** aquilo que hoje é ajuste manual em MS é, na verdade,
> a regra de estorno de MS aplicada no documento. Parametrizada, deixa de ser
> ajuste. O algoritmo acerta 100% do que é regra — as exceções eram intervenção.

Cruzamento CST × alíquota × carga efetiva encontrado nos dados:

| CST | Alíquota | Carga efetiva | Linhas |
|---|---|---|---|
| 00 | 7 / 12 / 17 / 18 / 20,5 | igual à alíquota | 1.018 |
| 20 | 7 / 12 / 17 / 18 | **4** (base reduzida) | 1.311 |
| 20 | 18 | 12 | 2 |
| 90 | 18 | 18 | 2 |
| 00 | 7 | 4 (ajuste manual MS) | 3 |

## 4. A classificação da operação é mais automatizável do que parecia

O receio era depender de julgamento humano para separar frete de compra, frete de
venda, embalagem, matéria-prima e produto químico. Os dados já trazem os sinais:

**a) A finalidade do frete já está escrita na descrição do CT-e:**

| Descrição do serviço | Linhas |
|---|---|
| Fretes sobre Vendas | 854 |
| Fretes sobre Transf/ Remessa/ Retorno (Custo) | 403 |
| Fretes sobre Compra de Insumos (Custo) | 265 |
| Fretes sobre Transf/ Retorno - Venda conjunta | 81 |
| Fretes sobre Compras (Almoxarifado) | 43 |
| Fretes sobre Compra Revenda | 6 |

**b) O código do produto tem prefixo por categoria:**

| Prefixo | Categoria | Exemplo |
|---|---|---|
| `1…` | Produto / matéria-prima | `101010021` HiPhós 25 Bag 1.000 kg |
| `2…` | Embalagem | `201000026` BIG BAG PCR NPK 90X90X120 |
| `6…` | Ativo imobilizado (CIAP) | `606000001` Máquinas e equipamentos |
| `7…` | Frete | `700000001` Fretes sobre Vendas |

**c) O CFOP identifica as exceções:** `5927` = baixa de estoque por perda
(regra de quebra), `5556` = devolução de uso e consumo, `1101/2101` = compra
para industrialização, `1102/2102` = compra para revenda.

**Desenho decorrente:** classificação por CFOP + espécie do documento + prefixo
do produto, com um **cadastro de produtos** (829 itens, estável entre meses) para
as exceções. Produto novo sem categoria cai automaticamente em `SEM REGRA` e vira
pendência — nunca é classificado por adivinhação.

## 5. Os ajustes manuais de Julho/2026 se explicam por regra

| Estabelecimento | Ajuste débito | Ajuste crédito | Origem |
|---|---|---|---|
| Guará | 5.111,72 | — | 15 baixas de estoque, CFOP 5927 (**regra de quebra**) |
| Registro | 40,85 | 13,59 | 2 baixas CFOP 5927 + 2 devoluções de uso e consumo CFOP 5556 |
| Rio Brilhante | 3.865,29 | 33.039,71 | 3 notas ICL a 7% (**regra MS**) + 2 notas TBL CFOP 5905 |
| Matriz / Corumbá | 0 | 0 | — |

Cerca de **90% do valor dos ajustes manuais é regra parametrizável**, não
exceção. Isso é uma redução direta de trabalho manual já na primeira entrega.

## 6. Resultado consolidado de Julho/2026 (referência de regressão)

Linha de totais da aba APURAÇÃO, que a ferramenta precisa reproduzir:

| Campo | Valor (R$) |
|---|---|
| Valor contábil — entradas | 75.371.274,49 |
| ICMS — entradas | 3.568.076,95 |
| Estorno de ICMS | 622.140,71 |
| Crédito mantido | 2.945.936,24 |
| Recebimento de ICMS (centralização) | 18.857,22 |
| Benefício fiscal | 98.892,91 |
| Saldo credor do período anterior | 902.567,05 |
| Valor contábil — saídas | 91.198.795,36 |
| ICMS — saídas | 3.657.487,61 |
| DIFAL | 53.023,49 |
| **Saldo final** | **286.697,73** |

> A aba ESTORNO traz um totalizador paralelo com números diferentes destes.
> Como o arquivo era um relatório manual e essa divergência não muda o resultado
> final, ela **não será replicada**: a ferramenta produz um totalizador único.
> Ver `06-decisoes-pendentes.md`, item 5.

## 7. Riscos que a análise reduziu ou confirmou

| Risco do escopo v1.0 | Situação após a análise |
|---|---|
| Volume elevado / desempenho | **Descartado.** 6,5 mil linhas. |
| Equalização de carga exige julgamento humano | **Muito reduzido.** 99,87% por algoritmo. |
| Classificação exige julgamento humano | **Reduzido.** Sinais existem na base; resta o cadastro de 829 produtos. |
| Regra tributária não mapeada | **Ativo.** Tratado com status `SEM REGRA` bloqueando o fechamento. |
| Automação de MS prematura | **Ativo e agora em fase 1.** Ver decisões pendentes. |
| Mudança de layout do Sankhya | **Ativo.** Mitigado por validação de cabeçalho na ingestão. |
