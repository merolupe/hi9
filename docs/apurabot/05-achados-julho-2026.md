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
> Onde existe apuração individualizada por estabelecimento, é ela que vale.

## 7. Riscos que a análise reduziu ou confirmou

| Risco do escopo v1.0 | Situação em 25/08/2026 |
|---|---|
| Volume elevado / desempenho | **Descartado.** 6,5 mil linhas. |
| Equalização de carga exige julgamento humano | **Resolvido.** 99,87% por algoritmo, e as 3 divergências são intervenção manual, não erro. |
| Classificação exige julgamento humano | **Muito reduzido.** Julho fecha com zero pendências, e o extrato novo traz o TOP, que nomeia a operação. |
| Regra tributária não mapeada | **Reduzido.** Tratado com `SEM REGRA` bloqueando o fechamento; nada pendente em Julho. |
| Automação de MS prematura | **Resolvido.** Corumbá e Rio Brilhante reproduzem exato, e o benefício de RB confere com a GIA retificadora ao centavo. |
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
crédito mantido. Ver `04-matriz-de-regras-icms.md`, item 4.2.

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

Daí sai o achado da **centralização em MS** — Rio Brilhante recebe saldo devedor
de outro estabelecimento do estado. Ver decisão pendente nº 7.

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

### 9.5. O estorno de créditos por ajuste

R$ 3.865,30 de estorno de crédito da atividade industrial que **não nasce de
documento no Livro Fiscal** — é a linha 003 do Registro de Apuração. Entra no
motor como lançamento explícito, declarado na aba `AJUSTES` do arquivo que a
ferramenta gera.

Sem ele o motor para em R$ 258.409,05 de benefício, contra os R$ 261.431,90
declarados. A diferença de R$ 3.022,85 está medida em teste.

---

## 10. Conferência do estorno por estabelecimento

| Estabelecimento | UF | Estorno calculado | Referência | Diferença |
|---|---|---|---|---|
| Registro | SP | 50.481,97 | 50.481,97 | **0,00** |
| Guará | SP | 426.771,68 | 426.771,68 | **0,00** |
| Matriz | SP | 0,00 | 0,00 | **0,00** |
| Barra do Garças | MT | 50.309,07 | 50.309,07 | **0,00** |
| Londrina | PR | 0,00 | 0,00 | **0,00** |
| Corumbá | MS | 19.961,553359 | 19.961,553359 | **0,00** |
| Rio Brilhante | MS | 331.236,11 | 331.236,11 | **0,00** |

O crédito bruto bate nas sete e os débitos batem com a aba `Dinamica`. Corumbá é
conferido contra a **apuração individualizada (Empresa 9)**, não contra a
consolidada — que trazia R$ 26.503,24 de crédito mantido porque somava a ele o
crédito indevido de transferência.

Rio Brilhante era a exceção enquanto o motor chaveava na carga efetiva; passou a
fechar quando a chave virou a alíquota, e a referência aqui é a linha 003 do
Registro de Apuração.

## 11. Volume da competência

| Verificação | Resultado |
|---|---|
| Linhas lidas do Livro Fiscal | 6.555 |
| Linhas relevantes para ICMS | **2.345** — igual à aba `ICMS` da planilha manual |
| Carga efetiva × classificação manual | **2.342 de 2.345 (99,87%)** |
| Totais por estabelecimento × entrada/saída × carga | idênticos à aba `Dinamica` |
| Pendências | **0** |
| Alertas (não bloqueiam) | 30 |

As 3 divergências de carga são as notas da ICL Aditivos, reclassificadas à mão.
O teste **exige** que a diferença seja essa e de R$ 9.019,01 — qualquer outra o
quebra.

## 12. Os 0,941176% não existem

O escopo funcional v1.0 previa, para MS, crédito mantido de **0,941176%** nas
entradas a 4% e manutenção do mesmo percentual em fertilizante interno. O número
foi procurado em três lugares e não está em nenhum:

1. **Apuração consolidada** — varredura célula a célula nas sete abas. Só aparece
   o fator que geraria o número (`4/17 = 0,235294`), nunca o percentual aplicado.
2. **Apuração individualizada de Corumbá** — a mecânica é outra: estorno da
   parcela não tributada sobre o ICMS.
3. **Termo de Acordo n. 1.190/2018** — as sete páginas não mencionam o percentual
   nem nada equivalente.

O parâmetro não existe em `regimes.yaml`, e não fica como "não aplicado": não há
regra a aplicar. Fica o registro para que ninguém o reintroduza a partir do
escopo v1.0.

## 13. O Registro de Apuração de Rio Brilhante reproduz ao centavo

O ERP emitiu o Registro de Apuração de RIO BRILHANTE em 07/08/2026. As duas
folhas de entradas e saídas são soma pura do Livro Fiscal, e o motor as
reproduz **nas cinco colunas e nos três grupos de procedência**, sem usar
nenhum parâmetro tributário:

| | Valores contábeis | Base de cálculo | Imposto | Isentas/N.Trib. | Outras |
|---|---|---|---|---|---|
| Entradas — do Estado | 5.302.366,31 | 0,00 | 2.146,57 | 2.456.680,40 | 2.845.685,91 |
| Entradas — de outros Estados | 5.667.570,01 | 1.479.555,26 | 153.929,91 | 3.880.746,19 | 351.013,04 |
| Entradas — do Exterior | 13.510.547,87 | 1.846.038,67 | 313.826,57 | 5.999.625,90 | 5.664.883,30 |
| **Entradas — total** | **24.480.484,19** | **3.325.593,93** | **469.903,05** | **12.337.052,49** | **8.861.582,25** |
| Saídas — para o Estado | 7.289.225,52 | 596.202,18 | 101.354,35 | 4.008.653,75 | 2.684.369,59 |
| Saídas — para outros Estados | 12.970.887,39 | 3.371.976,03 | 404.637,06 | 9.227.165,58 | 371.745,78 |
| **Saídas — total** | **20.260.112,91** | **3.968.178,21** | **505.991,41** | **13.235.819,33** | **3.056.115,37** |

O resumo da folha 3 também fecha, com os ajustes declarados:

| Linha | Documento | Motor | Origem do valor no motor |
|---|---|---|---|
| 001 por Saídas com Débito | 505.991,41 | 505.991,41 | Livro Fiscal |
| 002 Outros Débitos | 99.412,10 | 99.412,10 | **calculado** — saldo devedor de Corumbá |
| 003 Estornos de Créditos | 335.101,41 | 335.101,41 | 331.236,11 da regra + 3.865,30 de ajuste |
| 004 Sub Total | 940.504,92 | 940.504,92 | |
| 005 por Entradas com Crédito | 469.903,05 | 469.903,05 | Livro Fiscal |
| 006 + 007 | 79.178,39 | 79.178,39 | ajuste declarado |
| 008 Sub Total | 549.081,44 | 549.081,44 | |
| 011 SALDO DEVEDOR | 391.423,48 | 391.423,48 | |

Dois pontos merecem registro.

**A linha 002 não é ajuste declarado.** O valor é o saldo devedor apurado de
Corumbá, que a camada de centralização calcula e leva ao registro do
centralizador. Os dois lados fecham sem que nenhum deles tenha sido informado.

**A linha 012 diverge, e o motor é que está certo.** O documento traz
283.766,56 de dedução e 107.656,92 a recolher; o motor calcula 261.431,90 e
129.991,58. A diferença de 22.334,66 é exatamente a inversão entre Industrial e
Comercial que a GIA retificadora de 25/08/2026 corrigiu — o Registro emitido em
07/08 é anterior à retificação. Sobre a GIA retificadora, o benefício bate ao
centavo.


---

## 14. O registro de julho de Guará fecha em R$ 2,99

A folha 3 do Registro de Apuração de 07/2026 da Filial Guará decompõe o que
faltava. Contra o que o motor apura sobre o Livro:

| Linha | Motor | Documento | Diferença |
|---|---|---|---|
| 001 por Saídas com Débito | 1.633.053,78 | 1.633.053,78 | — |
| 002 Outros Débitos | 303.470,87 | 308.585,58 | 5.114,71 |
| 003 Estornos de Créditos | 426.771,68 | 426.771,68 | — |
| 005 por Entradas com Crédito | 4.167.368,77 | 4.167.368,77 | — |
| 006 Outros Créditos | 0,00 | 414.424,02 | 414.424,02 |
| 009 Saldo Credor Anterior | 0,00 | 1.782,53 | 1.782,53 |
| **014 a Transportar** | **1.804.072,44** | **2.215.164,28** | **411.091,84** |

As três linhas que o Livro sustenta — 001, 003 e 005 — batem ao centavo. Todo o
resto é lançamento que não nasce de documento, discriminado no próprio registro:

| O quê | Valor | Linha |
|---|---|---|
| Recebimento de crédito de estabelecimento de produtor ou cooperativas | +400.000,00 | 006 |
| Estorno de débitos | +14.424,02 | 006 |
| Saldo credor do período anterior | +1.782,53 | 009 |
| Baixa de estoque — Artigo 73 | −5.111,72 | 002 |
| Centralização recebida, diferença | −2,99 | 002 |
| **Total** | **411.091,84** | |

Cadastrada a abertura e declarados os três ajustes, o registro fecha em
**R$ 2,99** — resíduo na linha 002, entre os R$ 299.563,94 que o documento
declara ter recebido por centralização e os R$ 299.560,95 que o motor apura
como saldo devedor de Registro e Matriz.

Duas observações que o time fiscal pode querer olhar:

**Os R$ 14.424,02 da linha 006 são o crédito indevido de Corumbá** — o CFOP
2152 que é contraparte do 6152 de Guará (ver item 10). O motor já o separa do
estorno em Corumbá; o documento mostra Guará recuperando-o do outro lado.

**A linha 009 de julho não é a linha 014 de junho.** Junho fecha em R$ 0,00 e
julho abre com R$ 1.782,53. A descontinuidade está entre dois documentos do
ERP, não na ferramenta.

## 15. Junho de Guará fecha em zero — e mostra como SP centraliza

O mesmo documento de 06/2026 fecha as duas colunas no mesmo número:

```
004 Sub Total (débito) ....  3.383.492,59
008 Sub Total (crédito) ...  3.383.492,59
011 SALDO DEVEDOR .........          0,00
014 SALDO CREDOR ..........          0,00
```

Não é coincidência. Guará apurou saldo devedor e recebeu, na linha 006, **exatamente**
os R$ 455.859,54 de que precisava para zerar — nem um centavo a mais. É a
regra do teto: o crédito transferido pelos estabelecimentos centralizados para
a centralizadora **para no saldo devedor dela**. O excedente fica onde está.

Dois pontos que o documento estabelece e que a ferramenta ainda não reflete:

**A transferência de SP é lançamento de apuração, não NF-e.** As duas pontas
aparecem discriminadas com a mesma redação que MS usa: "recebimento de saldo
credor — estabelecimento centralizador" na linha 006, e "recebimento de saldo
devedor — estabelecimento centralizador" na linha 002. `filiais.yaml` foi
corrigido: SP passou a `mecanismo: ajuste_de_apuracao` com `emite_nfe: true`,
homologado em 02/09/2026.

**Os dois sentidos são recebidos pela centralizadora.** Em junho Guará recebeu
crédito (455.859,54) e débito (1.022,71) no mesmo mês, de estabelecimentos
diferentes.

Ver decisão pendente nº 11.

## 16. Os seis registros de julho fecham a virada do mês (02/09/2026)

Com os Registros de Apuração de 07/2026 de Matriz, Registro, Rio Brilhante,
Corumbá, Londrina e Guará em mãos, a abertura de agosto deixa de ser estimativa
e passa a ser leitura de documento. A linha 014 de cada um:

| Estabelecimento | cód | 009 (abre julho) | 014 (abre agosto) |
|---|---|---|---|
| HINOVE (MATRIZ) | 1 | 0,00 | 0,00 |
| HINOVE (RIO BRILHANTE) | 2 | 0,00 | 0,00 |
| HINOVE (REGISTRO) | 4 | 0,00 | 0,00 |
| HINOVE (LONDRINA) | 7 | 327.121,97 | **341.004,37** |
| HINOVE (CORUMBÁ- MS) | 9 | 0,00 | 0,00 |
| HINOVE (FILIAL GUARÁ) | 11 | 1.782,53 | **2.215.164,28** |

Barra do Garças (8) não tem registro emitido no período.

**Londrina é a conta gráfica inteira num documento só.** PR difere a saída, então
o mês não tem débito e a linha 014 é a soma da abertura com o crédito das
entradas: 327.121,97 + 13.882,40 = 341.004,37. O motor reproduz as três linhas,
e é o teste mais direto que existe da virada do mês
(`test_londrina_fecha_julho_na_linha_014_do_documento`).

Correção do que estava cadastrado: `saldos.yaml` trazia R$ 13.882,40 como
abertura de agosto em Londrina. Esse é o crédito das entradas do próprio julho
— a linha 005 —, não a linha 014. A abertura correta é **R$ 341.004,37**.

**A centralização de SP fecha entre as três pontas.** O que Guará declara ter
recebido na linha 002 é a soma exata do que os dois centralizados declaram ter
transferido na linha 006:

```
Registro (4) ....  299.453,69
Matriz (1) ......      110,25
                   ----------
Guará (11) 002 ..  299.563,94   ✔ igual ao documento de Guará
```

Os R$ 2,99 do item 14 estão, portanto, entre o motor e o ERP — não entre dois
documentos do ERP. O ERP transferiu R$ 299.453,69 de Registro e deixou lá
R$ 24,27 de saldo devedor; o motor apura o saldo devedor de Registro inteiro. É
resíduo de composição da linha 002 de Registro, cujo detalhe (DIFAL 12.337,04 +
baixa de estoque 40,85) o motor só conhece pela parte do DIFAL.

**As demais linhas dos cinco documentos batem com a regressão que já existia.**
Crédito da linha 005 e estorno da linha 003, contra `test_regressao_apuracao`:

| Estabelecimento | 005 | 003 | confere |
|---|---|---|---|
| REGISTRO | 286.030,83 | 50.481,97 | ✔ |
| GUARÁ | 4.167.368,77 | 426.771,68 | ✔ |
| LONDRINA | 13.882,40 | 0,00 | ✔ |
| CORUMBÁ | 46.464,79 | 19.961,55 | ✔ |
| RIO BRILHANTE | 469.903,05 | 335.101,40 | ✔ |

Rio Brilhante confirma também o crédito outorgado retificado do art. 68 —
**R$ 68.473,36** na linha 006 — e a centralização de MS: Corumbá transfere
R$ 99.412,10 de saldo devedor na linha 006 e Rio Brilhante o recebe na 002.
