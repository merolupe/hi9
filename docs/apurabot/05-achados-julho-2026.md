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

| Risco do escopo v1.0 | Situação em 21/08/2026 |
|---|---|
| Volume elevado / desempenho | **Descartado.** 6,5 mil linhas. |
| Equalização de carga exige julgamento humano | **Resolvido.** 99,87% por algoritmo, e as 3 divergências são intervenção manual, não erro. |
| Classificação exige julgamento humano | **Muito reduzido.** Julho fecha com zero pendências, e o extrato novo traz o TOP, que nomeia a operação. |
| Regra tributária não mapeada | **Reduzido.** Tratado com `SEM REGRA` bloqueando o fechamento; nada pendente em Julho. |
| Automação de MS prematura | **Parcialmente resolvido.** Corumbá reproduz exato; o benefício de RB aguarda decisão. |
| Mudança de layout do Sankhya | **Mitigado na prática.** O motor lê dois layouts e valida o cabeçalho, procurando-o nas 10 primeiras linhas. |

## 8. O que a implementação corrigiu na própria análise

Dois números desta análise estavam errados e só apareceram ao escrever o motor:

**O denominador do 99,87%.** O script de análise pulava em silêncio 6 linhas de
`COMPLEMENTO DE ICMS` (R$ 17.490,73) que chegam com valor contábil zero. Com o
denominador completo o índice inicial era 99,62%; tratadas por parâmetro, voltou
a 99,87% — desta vez sobre as 2.345 linhas.

**A ordem da classificação.** O CFOP de compra vencia a categoria do produto, e
embalagem comprada com CFOP 1101 virava matéria-prima. O CFOP diz *para que* a
mercadoria foi comprada; a regra de estorno pergunta *o que ela é*. Invertido, a
conferência do Enxofre de revenda passou a bater exato com a aba ESTORNO
(R$ 474.416,28).

E um terceiro, na apuração consolidada e não na minha análise: **Corumbá não
usava a mecânica de SP**, e o crédito indevido de transferência estava somado ao
crédito mantido. Ver `06-decisoes-pendentes.md`, item 2.

## 9. Rio Brilhante — o que os documentos oficiais mostraram (25/08/2026)

Quatro documentos da competência fecharam o que a planilha manual não explicava:
o **Registro de Apuração do ICMS**, a **GIA - Benefício Fiscal**, a **GIA -
Apuração Final** (protocolo 36160E2, retificadora) e o **Relatório FAI**.

### 9.1. O bloco-resumo da planilha trocava Industrial por Comercial

A aba `ESTORNO` classifica **linha a linha** numa coluna de atividade. Somando
por esse rótulo dá crédito industrial de R$ 327.834,95 e comercial de
R$ 134.672,19. O **bloco-resumo** da mesma aba trocava os dois — e era o resumo
que alimentava o cálculo do benefício.

Os R$ 7,8 milhões de ureia e ácido bórico importados, cujo CFOP 3101 se chama
literalmente *"Compra p/ industrialização"*, caíam na conta comercial. A GIA
retificadora corrigiu.

### 9.2. A chave do estorno é a alíquota

Com a chave na carga efetiva, as importações a 17% com base reduzida a 4%
estornavam 100%. Pela alíquota estornam 76,47%. A diferença é R$ 73.843,39 de
crédito mantido — e é o que faz o estorno total de RB cair exatamente nos
**R$ 331.236,11** que a linha 003 do Registro declara.

### 9.3. Os "valores prestacionais" da GIA não são documentos

A coluna `Prestacional/Outras`, que não se achava no Livro Fiscal, são as linhas
de **ajuste** da apuração:

| Lado | Composição | Total |
|---|---|---|
| Crédito | ajuste art. 68 RICMS/MS (46.138,68) + estorno de débitos (33.039,71) | 79.178,39 |
| Débito | saldo devedor do centralizador (99.412,10) + estorno de créditos (3.865,30) | 103.277,40 |

Daí sai o achado da centralização em MS (decisão nº 20) e o dos créditos de
ajuste (nº 21).

### 9.4. Novos alvos de regressão

A regressão de Rio Brilhante deixou de se ancorar na planilha manual e passou a
se ancorar no documento oficial:

| Campo | Valor (R$) |
|---|---|
| Crédito industrial | 327.834,95 |
| Estorno industrial | 245.987,17 |
| Crédito da parcela incentivada | 77.982,48 |
| Base do incentivo | 334.291,69 |
| Benefício (67% intra + 80% inter) | **261.431,90** |
| FADEFE 2% — guia avulsa | 5.228,64 |

### 9.5. O que ainda não fecha

- **R$ 5.249,34** de complemento de ICMS que está no Livro e não está nos
  créditos da GIA (decisão nº 18).
- **R$ 3.865,30** de estorno de créditos que não nasce de documento e hoje entra
  como parâmetro (decisões nº 15 e 21).
- A **EFD/SPED** de 07/2026 aparentemente não foi retificada junto com a GIA
  (decisão nº 22).

