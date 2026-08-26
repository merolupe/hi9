# Apurabot — Matriz de regras de ICMS

> **Status: rascunho a homologar pela Gerência Fiscal/Tributária.**
>
> Este documento descreve **a regra**, não uma competência. Cada linha daqui vira
> um parâmetro em `apurabot/parametros/` e um teste automático em
> `apurabot/tests/`. Os números que comprovam cada regra contra uma apuração real
> estão em [05 — Achados de Julho/2026](05-achados-julho-2026.md); aqui ficam só
> o conceito e o desenho do motor.

---

## 1. Regimes por UF

| UF | Estabelecimentos | Regime | Regra em uma linha |
|---|---|---|---|
| **SP** | Matriz, Guará, Registro | Equilíbrio fiscal | Mantém crédito até a carga de saída (4%); estorna o excedente. Saldos centralizados em **Guará**. |
| **MS** | Corumbá, Rio Brilhante | Estorno proporcional | Estorno da parcela não tributada, pela alíquota da operação. Rio Brilhante tem ainda benefício fiscal por Termo de Acordo. |
| **MT** | Barra do Garças | Diferimento | Saídas diferidas → **estorna 100%** do crédito de entrada. |
| **PR** | Londrina | Diferimento | Saídas diferidas → **mantém 100%** do crédito de entrada. |

> A assimetria MT × PR não é erro de transcrição: está explícita em *Pontos de
> Atenção*, item 4 — "Créditos PR mantêm 100% s/ saídas diferidas; créditos MT
> estornam 100% s/ saídas diferidas".

---

## 2. Categorias da operação

A categoria da entrada é o que decide se o crédito estorna. Ela vem, nesta ordem:
cadastro de produto → prefixo do código do produto → CFOP. O que não casar com
nenhuma regra recebe `SEM REGRA` e bloqueia o encerramento da competência.

### 2.1. Matéria-prima × produto químico

Esta é a distinção que mais move valor, e ela **não é sobre o que o produto é
quimicamente**. Um produto químico também é matéria-prima; o que separa os dois
é o **enquadramento fiscal**:

| Categoria | Definição | Tratamento em SP |
|---|---|---|
| `materia_prima` | Matéria-prima **enquadrada** no artigo de equalização da carga a 4% (benefício de fertilizante) | **Não estorna** |
| `produto_quimico` | Matéria-prima que **não se enquadra** nesse artigo | **Estorna** o excedente sobre 4% |

Uma matéria-prima deixa de se enquadrar por dois motivos:

1. **O produto está fora do escopo do artigo** de fertilizante.
2. **O fornecedor não tem registro no MAPA** para vender aquele produto como
   enquadrado — tipicamente quando é indústria química, e não fabricante de
   fertilizante.

> ### O enquadramento é do par produto + fornecedor
>
> O segundo motivo tem uma consequência de desenho: **o mesmo produto pode ser
> matéria-prima de um fornecedor e produto químico de outro**, e um mesmo
> fornecedor pode vender itens dos dois tipos. Classificar só pelo código do
> produto, ou só pelo fornecedor, não expressa a regra.
>
> Por isso o cadastro em `parametros/produtos.yaml` aceita a chave por produto e,
> quando o enquadramento depender de quem vendeu, por **produto + fornecedor**.
>
> O fato que decide — o enquadramento e o registro no MAPA — **não está no Livro
> Fiscal**. É informação cadastral que o time fiscal detém, e é por isso que ela
> vive num parâmetro e não numa heurística.

### 2.2. Demais categorias

| Categoria | O que é | Como o motor a reconhece |
|---|---|---|
| `embalagem` | Big bags, sacos, lapelas, lacres | Prefixo `2…` do código do produto, ou cadastro |
| `revenda` | Mercadoria adquirida para revenda | Cadastro, ou CFOP de compra para comercialização |
| `frete_compra` · `frete_venda` · `frete_transferencia` | Serviço de transporte, pela **finalidade** | Descrição do CT-e; o CFOP só decide quando a descrição não resolve |
| `ciap` | Bem do ativo imobilizado | Prefixo `6…`, ou CFOP de lançamento de crédito de ativo |
| `complemento_icms` | Complemento de imposto | Cadastro — lançamento sem valor contábil |
| `complemento_preco` | Complemento de preço | Cadastro — acompanha a situação da nota complementada |
| `quebra` | Baixa por perda, roubo ou deterioração | CFOP de baixa de estoque |
| `insumo_energetico` | Insumo de queima | Cadastro |
| `industrializacao_terceiros` | Serviço de industrialização | Cadastro |

> **O CFOP não vence a natureza do produto.** O CFOP de compra diz *para que* a
> mercadoria foi adquirida; a regra de estorno pergunta *o que ela é*. Uma
> embalagem comprada com CFOP de compra para industrialização continua sendo
> embalagem e continua estornando. Por isso o cadastro e o prefixo são avaliados
> antes do CFOP.

### 2.3. A coluna TOP

O extrato traz a **TOP** (Tipo de Operação), que nomeia a operação como ela foi
lançada no Sankhya. Ela é lida, viaja na base tratada e serve para conferência,
mas **não classifica**: onde a TOP e a categoria do produto divergem, vale a
categoria.

A divergência não é contradição. Uma entrada lançada como "Compra de MP" pode ser
`produto_quimico` porque, no sentido do item 2.1, aquela matéria-prima não se
enquadra. Uma importação lançada como compra pode ser `revenda` porque a
finalidade da importação era revender. A TOP descreve o lançamento; a categoria
descreve o enquadramento.

---

## 3. SP — equilíbrio fiscal (carga de saída 4%)

```
estorno         = valor contábil × (carga efetiva da entrada − carga de saída)
crédito mantido = ICMS destacado − estorno
carga de saída  = 4%
```

A base do estorno é o **valor contábil**, não a base de ICMS.

| Categoria da entrada | Dentro do estado | Fora do estado |
|---|---|---|
| **Matéria-prima / produto acabado** | Não estorna | Não estorna |
| **Produto químico** | Estorna o excedente sobre 4% | Estorna o excedente sobre 4% |
| **Embalagens** | Estorna o excedente sobre 4% | Estorna o excedente sobre 4% |
| **Frete sobre compras** | Estorna o excedente sobre 4% | Estorna o excedente sobre 4% |
| **Frete sobre vendas** | Sem crédito (diferido/isento) | Estorna o excedente sobre 4% |
| **Frete sobre transferência / remessa / retorno** | Mesma regra do frete de compra | Mesma regra do frete de compra |
| **Revenda** | Não estorna | Não estorna |
| **Retorno de industrialização** | Não estorna | Não estorna |
| **CIAP** | Mantém 100% conforme saídas tributadas | idem |

Pela fórmula: carga 7% estorna 3 pontos; 12% estorna 8; 17% estorna 13; 18%
estorna 14.

---

## 4. MS — estorno proporcional, atividade e benefício de Rio Brilhante

### 4.1. O estorno é fórmula, e a chave é a alíquota

Em MS o estorno incide sobre o **valor do ICMS**, e não sobre o valor contábil. O
crédito é limitado à **carga de referência de 4%**, e o que passa dela se estorna:

```
parcela estornada = 1 − carga de referência / alíquota
estorno           = ICMS × parcela estornada
```

| Alíquota | Parcela estornada | Crédito que resta | Confere |
|---|---|---|---|
| 4% | 0,0000 | 100% | já está em 4% |
| 7% | 0,4286 | 57,14% | 7% × 0,5714 = **4,00%** |
| 12% | 0,6667 | 33,33% | 12% × 0,3333 = **4,00%** |
| 17% | 0,7647 | 23,53% | 17% × 0,2353 = **4,00%** |
| 18% | 0,7778 | 22,22% | 18% × 0,2222 = **4,00%** |
| 19% | 0,7895 | 21,05% | 19% × 0,2105 = **4,00%** |

> ### A chave é a ALÍQUOTA, não a carga efetiva
>
> Numa entrada com **base reduzida** as duas leituras se separam. A carga efetiva
> do documento já vem em 4% — porque a redução da base é justamente o que a leva
> até lá —, mas a operação continua sendo de alíquota cheia, e é sobre ela que a
> parcela se calcula.
>
> Lendo a carga, a conclusão seria "entrada já beneficiada, estorna tudo".
> Lendo a alíquota, estorna a parcela e **mantém o crédito equivalente a 4%**.
> É a segunda que a legislação e a apuração fazem.
>
> A carga efetiva serve para **conferir** o documento. Quem comanda a proporção
> do estorno é a alíquota.

O arredondamento da parcela é parâmetro (`casas_decimais_da_parcela`): quatro
casas reproduzem o percentual tabelado, `null` usa a fração exata.

> **Por que SP é diferente:** em SP o estorno é `valor contábil × (carga − 4%)`.
> Onde base e valor contábil coincidem os dois caminhos quase se encontram, mas
> não são o mesmo cálculo — a diferença aparece assim que a base é reduzida.

### 4.2. Crédito indevido de transferência

O crédito de **CFOP 2152** (transferência interestadual recebida) **não é
apropriado**. Não é estorno: é crédito que não podia ter sido tomado, e por isso
fica em parcela própria na apuração. A identidade que a auditoria valida passa a
ser:

```
crédito mantido + estorno + crédito indevido = crédito bruto
```

### 4.3. Segregação por atividade

A GIA de MS não aceita uma apuração só por estabelecimento: exige o resultado
separado em **Industrial, Comercial, Importados e Prestacional/Outras**.

Isso não é formalidade de declaração. **É a segregação que dimensiona o
benefício**, porque o crédito presumido incide exclusivamente sobre o saldo
devedor da atividade industrial. Sem ela não existe "crédito da parcela
incentivada" e o benefício não tem como ser calculado.

A atividade sai do **CFOP**, com uma exceção: o CFOP do serviço de transporte diz
quem contratou o frete, não o que o frete carrega — e é o que ele carrega que
decide. Por isso a **descrição vence o CFOP** quando casa.

| Atividade | Débito | Crédito |
|---|---|---|
| Industrial | CFOP de venda de produção do estabelecimento (5101, 6101, 5118, 6118, 5109, 6109, 5111, 6111, 5122, 6122) | CFOP de compra para industrialização (1101, 2101, 3101, …), transferência para industrialização (1151, 2151, 3151) e frete de insumo |
| Comercial | CFOP de venda de mercadoria de terceiros, remessa e retorno (5102, 6102, 5905, 6905, 5934, 6934, …) | CFOP de compra para comercialização (1102, 2102, 3102, …), transferência para comercialização (1152, 2152, 3152), fretes de venda e transferência |
| Prestacional/Outras | Bonificação, doação, brinde e outras saídas (5910, 6910, 5949, 6949) | CIAP (1604, 2604) |

O corte **intra/inter** vem do primeiro dígito do CFOP: 5 é interno, 6 é
interestadual, 7 é exterior.

> **Atividade indefinida bloqueia o encerramento.** CFOP que não casa com nenhuma
> atividade recebe `SEM REGRA`, como manda a regra 4 do projeto.

### 4.4. Demais regras de MS

| Item | Regra |
|---|---|
| Entrada com alíquota acima de 4% | Crédito mantido limitado à carga de referência |
| DIFAL em MS | Informa na apuração e recolhe em **guia avulsa** — não entra em conta gráfica |
| Centralização | Rio Brilhante **recebe** saldo devedor de estabelecimento centralizador; a regra de MS ainda não está modelada |

### 4.5. Benefício fiscal de Rio Brilhante — Termo de Acordo n. 1.190/2018

Firmado em 19/09/2018 entre o Estado de MS e a Hinove, publicado no DOE 9.755.
Base legal: LC estadual 93/2001 e Lei 4.049/2011.

**Cláusula terceira — em vigor até 31/12/2032:**

| Inciso | Benefício | Alcance |
|---|---|---|
| **I** | **67%** do saldo devedor do ICMS | **Exclusivamente** operações com produtos resultantes de **própria industrialização neste Estado** |
| **II** | adicional de **13%**, totalizando **80%** | **Exclusivamente** operações **interestaduais** |
| III | Diferimento na importação de máquinas e equipamentos do processo industrial | — |
| IV | Diferimento do DIFAL em transferências e aquisições interestaduais de máquinas | — |
| V | Diferimento na importação das matérias-primas da cláusula primeira, IV | — |
| VI | Regime especial de apuração mensal do DIFAL sobre ativo, uso e consumo e material de construção | — |

**Parágrafo terceiro:** *"As matérias-primas não envolvidas no processo fabril
não poderão gozar dos incentivos previstos neste instrumento."*

**Cláusula quarta — expirou em 31/12/2022.** Dava 50% do saldo devedor nas saídas
interestaduais com mercadorias adquiridas em outras UFs, e 50% do imposto nas
saídas interestaduais com itens importados. Revenda, portanto, está fora da base.

#### O alcance é a atividade industrial

O inciso I restringe às operações com produtos de própria industrialização, e é
assim que o benefício é declarado: a dedução no Registro de Apuração se chama
*"Industrialização própria - Incentivo TA/CDI"*, e a base de saídas incentivadas
da GIA - Benefício Fiscal é a dos CFOP de produção própria.

#### A cadeia de cálculo

```
crédito da parcela incentivada = crédito industrial normal
                                 − estornos de crédito da atividade industrial

base do incentivo              = débito industrial
                                 − crédito da parcela incentivada

benefício = base intraestadual × 67%  +  base interestadual × 80%
```

A base é repartida entre intra e inter pela **participação de cada destino no
débito industrial** — o mesmo rateio que a GIA aplica ao crédito da parcela
incentivada.

Nem todo estorno de crédito industrial nasce de documento no Livro Fiscal: a
apuração admite estornos por ajuste, que entram como lançamento explícito.

**Travas do motor:** o benefício nunca supera o saldo devedor que o gerou;
atividade indefinida bloqueia o encerramento; e aplicar a cláusula quarta levanta
erro com a data de expiração na mensagem.

#### FADEFE / Pró-Desenvolve — guia avulsa

A cláusula terceira, parágrafo primeiro, condiciona a fruição a uma contribuição
mensal ao **Fundo de Apoio ao Desenvolvimento Econômico e de Equilíbrio Fiscal do
Estado**, sobre o benefício efetivamente utilizado. São dois percentuais
parametrizados com vigência: a contribuição ao Pró-Desenvolve / FADEFE
Desenvolvimento Econômico / FAI, e um adicional de equilíbrio fiscal.

É calculada na própria GIA e recolhida em **guia avulsa**: sai no relatório como
informação e **não entra na conta gráfica**.

#### Controle de crédito outorgado

O benefício movimenta ainda um controle de crédito outorgado (código de ajuste
`MS090004` — apropriação de crédito outorgado para abatimento de débitos), com
saldo anterior, créditos recebidos por transferência, créditos utilizados no
período e saldo a transportar.

---

## 5. Regras que valem para todas as UFs

| Situação | Tratamento | Sinal no Livro Fiscal |
|---|---|---|
| **Devolução de compra** | Estorna o crédito da compra referida | CFOP de devolução de entrada |
| **Devolução de venda** | Mantém 100% do crédito (consultas tributárias) | CFOP de devolução de venda |
| **Quebra / perda de estoque** | Estorna **100%** do crédito da entrada | **CFOP 5927** |
| **Complemento de ICMS** | Crédito apropriável | Lançamento sem valor contábil |
| **Complemento de preço** | Acompanha a situação da nota complementada | Referência na coluna Observação |
| **CIAP** | Mantém 100% conforme saídas tributadas | Produto do grupo de ativo (prefixo `6…`) |
| **DIFAL SP** | Apurado em conta gráfica | — |
| **DIFAL MS** | Informado na apuração, recolhido em guia avulsa | — |

---

## 6. Centralização de SP em Guará

```
1. saldo individual de cada estabelecimento paulista (antes da centralização)
2. classifica credor ou devedor
3. determina o valor transferível
4. indica se precisa emitir NF-e
5. registra a NF-e emitida
6. compara valor esperado × valor emitido
7. consolida os recebimentos em Guará
8. apura o resultado final da centralizadora
```

**Identidades que a ferramenta valida:**
- `saldo individual = valor transferido + saldo residual`
- `transferências recebidas em Guará = soma das NF-e emitidas pelos demais`

**Travas da NF-e de transferência:** não emitida → pendência crítica ·
cancelada → bloqueio · CFOP incompatível → revisão · valor divergente →
diferença evidenciada · emissão fora da competência → revisão · não escriturada
→ pendência · duplicidade → bloqueio · resíduo sem justificativa → revisão.

---

## 7. Tabelas de carga efetiva (adubos e fertilizantes)

Entram em `parametros/cargas.yaml` com vigência.

**Operação intraestadual**

| Origem | Alíquota geral | Redução | Carga efetiva | CST |
|---|---|---|---|---|
| SP | 18% | 77,78% | 4% | 20 |
| MG | 18% | 77,78% | 4% | 20 |
| MS | 17% | 76,47% | 4% | 20 |
| PR | 19% | 78,95% | 4% | 20 |
| MT | 17% | — | Diferimento | 51 |
| PR (diferido) | 19% | — | Diferimento | 51 |

**Operação interestadual** (adubos/fertilizantes e também ácido nítrico,
sulfúrico, fosfórico, fosfato natural bruto e enxofre)

| Alíquota geral | Redução | Carga efetiva | CST |
|---|---|---|---|
| 4% | — | 4% | 00 |
| 7% | 42,86% | 4% | 20 |
| 12% | 66,67% | 4% | 20 |
