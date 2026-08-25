# Apurabot — Matriz de regras de ICMS

> Fonte: aba **Pontos de Atenção** e aba **ESTORNO** da apuração de Julho/2026,
> cruzadas com o item 5 do escopo funcional v1.0.
> **Status: rascunho a homologar pela Gerência Fiscal/Tributária.**
> Cada linha desta matriz vira um parâmetro em `apurabot/parametros/` e um teste
> automático em `apurabot/tests/unidade/`.

---

## 1. Regimes por UF

| UF | Estabelecimentos | Regime | Regra em uma linha |
|---|---|---|---|
| **SP** | Matriz, Guará, Registro | Equilíbrio fiscal | Mantém crédito até a carga de saída (4%); estorna o excedente. Saldos centralizados em **Guará**. |
| **MS** | Corumbá, Rio Brilhante | Estorno proporcional + crédito presumido | Estorno conforme alíquota de entrada vigente (apuração individualizada). Rio Brilhante tem benefício fiscal por Termo de Acordo. |
| **MT** | Barra do Garças | Diferimento | Saídas diferidas → **estorna 100%** do crédito de entrada. |
| **PR** | Londrina | Diferimento | Saídas diferidas → **mantém 100%** do crédito de entrada. |

> A assimetria MT × PR não é erro de transcrição: está explícita em *Pontos de
> Atenção*, item 4 — "Créditos PR mantêm 100% s/ saídas diferidas; créditos MT
> estornam 100% s/ saídas diferidas".

## 2. SP — equilíbrio fiscal (carga de saída 4%)

**Fórmula confirmada contra a apuração de Julho/2026:**

```
estorno        = valor_contábil × (carga_efetiva_entrada − carga_saída_referência)
crédito_mantido = ICMS_destacado − estorno
carga_saída_referência = 4%
```

A base do estorno é o **valor contábil**, não a base de ICMS. Verificado linha a
linha na aba ESTORNO (ex.: Registro, carga 7% → 448.750,00 × 3% = 13.462,50;
Guará, carga 20,5% → 21.665,88 × 16,5% = 3.574,87).

| Categoria da entrada | Dentro do estado | Fora do estado |
|---|---|---|
| **Matéria-prima / produto acabado** | Não estorna | Não estorna |
| **Embalagens** | Estorna o excedente sobre 4% | Estorna o excedente sobre 4% |
| **Produtos químicos** | Estorna o excedente sobre 4% | Estorna o excedente sobre 4% |
| **Frete sobre compras** | Estorna o excedente sobre 4% | Estorna o excedente sobre 4% |
| **Frete sobre vendas** | Sem crédito (diferido/isento) | Estorna o excedente sobre 4% |
| **Frete sobre transferência / remessa / retorno** | Mesma regra do frete de compra | Mesma regra do frete de compra |
| **Revenda** (ex.: enxofre) | Não estorna | Não estorna |
| **Retorno de industrialização** | Não estorna | Não estorna |
| **CIAP** | Mantém 100% conforme saídas tributadas | idem |

Exemplos numéricos da própria regra: carga 12% estorna 8%; carga 7% estorna 3%;
carga 17% estorna 13%; carga 18% estorna 14%; carga 20,5% estorna 16,5%.

## 3. MS — estorno proporcional, atividade e benefício de Rio Brilhante

### 3.1. O estorno é fórmula, e a chave é a alíquota

Em MS o estorno incide sobre o **valor do ICMS**, e não sobre o valor contábil.
O benefício limita o crédito à **carga de referência de 4%**, e o que passa dela
se estorna:

```
parcela estornada = 1 − 4 / alíquota
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

Fonte: aba `ESTORNO` da apuração de Rio Brilhante, tabelas *OPERAÇÃO
INTRAESTADUAL* e *OPERAÇÃO INTERESTADUAL*, coluna *REDUÇÃO ATUAL*.

> ### ⚠️ A chave é a ALÍQUOTA, não a carga efetiva
>
> Esse é o ponto que separou o motor da apuração real por mais tempo, e vale
> R$ 73.843,39 numa competência só.
>
> As importações de ureia e ácido bórico de Julho/2026 (CFOP 3101) têm
> **alíquota de 17% com base reduzida**: valor contábil de R$ 7.845.664,57 para
> base de R$ 1.846.038,67, o que dá **carga efetiva de 4%**.
>
> Lendo a carga, a conclusão é "entrada já beneficiada, estorna tudo".
> Lendo a alíquota, estorna 76,47% e **mantém R$ 73.843,39 de crédito**.
> É a segunda que a apuração faz.
>
> A carga efetiva serve para **conferir** o documento. Quem comanda a proporção
> do estorno é a alíquota.

O arredondamento da parcela é parâmetro (`casas_decimais_da_parcela: 4`).
Reproduz Julho/2026 na sexta casa decimal em Corumbá — R$ 19.961,553359 de
estorno — e ao centavo em Rio Brilhante: **R$ 331.236,11**, o mesmo valor que a
linha 003 do Registro de Apuração declara.

> **Por que SP é diferente:** em SP o estorno é `valor contábil × (carga − 4%)`.
> Onde base e valor contábil coincidem os dois caminhos quase se encontram, mas
> não são o mesmo cálculo — a diferença aparece assim que a base é reduzida.

### 3.2. Crédito indevido de transferência

O crédito de **CFOP 2152** (transferência interestadual recebida) **não é
apropriado**. Em Julho/2026 foram R$ 14.424,02 em Corumbá, a contraparte exata
do débito de CFOP 6152 de Guará.

Não é estorno: é crédito que não podia ter sido tomado, e por isso fica em
parcela própria na apuração. A identidade que a auditoria valida passa a ser:

```
crédito mantido + estorno + crédito indevido = crédito bruto
```

> A apuração **consolidada** de Julho somava esse valor ao crédito mantido
> (26.503,24 = 12.079,22 + 14.424,02). A **individualizada** de Corumbá, não.
> Vale a individualizada.

### 3.3. Segregação por atividade

A GIA de MS não aceita uma apuração só por estabelecimento: exige o resultado
separado em **Industrial, Comercial, Importados e Prestacional/Outras**.

Isso não é formalidade de declaração. **É a segregação que dimensiona o
benefício**, porque o crédito presumido incide exclusivamente sobre o saldo
devedor da atividade industrial. Sem ela, não existe "crédito da parcela
incentivada" e o benefício não tem como ser calculado.

A atividade sai do **CFOP**, com uma exceção: o CFOP do serviço de transporte
diz quem contratou o frete, não o que o frete carrega — e é o que ele carrega
que decide. Por isso a **descrição vence o CFOP** quando casa.

| Atividade | Débito | Crédito |
|---|---|---|
| Industrial | 5101, 6101, 5118, 6118, 5109, 6109, 5111, 6111, 5122, 6122 | 1101, 2101, 3101, 1151, 2151, 3151, … + frete de insumo |
| Comercial | 5102, 6102, 5905, 6905, 5934, 6934, … | 1102, 2102, 3102, 1152, 2152, 3152, 1352, 2352, 1353, 2353, 2906, … |
| Prestacional/Outras | 5910, 6910, 5949, 6949 | 1604, 2604 (CIAP) |

Julho/2026 em Rio Brilhante, conferido contra a GIA - Apuração Final:

| Atividade | Crédito | Estorno | Débito |
|---|---|---|---|
| Industrial | 327.834,95 | 245.987,17 | **412.274,17** |
| Comercial | 134.672,19 | 85.248,94 | 93.717,23 |
| Prestacional/Outras (CIAP) | 2.146,57 | — | 0,01 |

O corte **intra/inter** vem do primeiro dígito do CFOP: 5 é interno, 6 é
interestadual, 7 é exterior. No débito industrial de Julho: R$ 56.934,28 intra
(5101 + 5118) e R$ 355.339,89 inter (6101).

> **Atividade indefinida bloqueia o encerramento.** CFOP que não casa com nenhuma
> atividade recebe `SEM REGRA`, como manda a regra 4 do projeto.

### 3.4. Demais regras de MS

| Item | Regra | Situação |
|---|---|---|
| Entrada com alíquota > 4% | Crédito mantido limitado à carga de 4% | Homologado |
| DIFAL em MS | Informa na apuração e recolhe em **guia avulsa** | Não entra em conta gráfica |
| Centralização | RB **recebe** saldo devedor de estabelecimento centralizador | Não modelada — decisão nº 20 |

### 3.5. Benefício fiscal de Rio Brilhante — Termo de Acordo n. 1.190/2018

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
saídas interestaduais com itens importados.

#### O alcance está resolvido: é a atividade industrial

A linha 012 do Registro de Apuração nomeia a dedução — *"Termo de acordo
n. 1190/2018 - **Industrialização própria** - Incentivo TA/CDI"* — e a GIA -
Benefício Fiscal traz base de saídas incentivadas de R$ 412.274,17, exatamente
os CFOP industriais do mês. A revenda de R$ 93.717,23 não recebe nada, o que
confirma que a cláusula quarta segue expirada.

#### A cadeia de cálculo

```
    crédito industrial normal ........  327.834,95
    (−) estorno industrial ...........  245.987,17
    (−) estorno de créditos (ajuste) .    3.865,30   ← linha 003 do Registro
    (=) crédito da parcela incentivada   77.982,48

    débito industrial 412.274,17 − 77.982,48 = base 334.291,69

      intra  (56.934,28  − 10.769,23) × 67% =  30.930,58
      inter  (355.339,89 − 67.213,25) × 80% = 230.501,31
                                              ──────────
                                   BENEFÍCIO  261.431,90
```

O crédito da parcela incentivada é **rateado pela participação do débito**
industrial em cada destino — 13,810% intra e 86,190% inter.

O ajuste de R$ 3.865,30 **não nasce de documento no Livro Fiscal**. É a linha
003 do Registro de Apuração, e entra como parâmetro explícito. Sem ele o motor
para em R$ 258.409,05 de benefício — a distância entre o Livro e a declaração.

#### FADEFE / Pró-Desenvolve — guia avulsa

**2%** sobre o benefício fruído, mais um **adicional de equilíbrio fiscal hoje
em 0%**. Em Julho/2026: R$ 261.431,90 × 2% = **R$ 5.228,64**.

É condição de fruição (cláusula terceira, parágrafo primeiro), calculada na
própria GIA e recolhida em **guia avulsa** — sai no relatório como informação e
**não entra na conta gráfica**.

#### Controle de crédito outorgado

O benefício movimenta ainda um controle de crédito outorgado (código de ajuste
`MS090004` — apropriação de crédito outorgado para abatimento de débitos), com
saldo anterior, créditos recebidos por transferência, créditos utilizados no
período e saldo a transportar.

## 4. Regras que valem para todas as UFs

| Situação | Tratamento | Sinal no Livro Fiscal |
|---|---|---|
| **Devolução de compra** | Estorna o crédito da compra referida | CFOP de devolução de entrada |
| **Devolução de venda** | Mantém 100% do crédito (consultas tributárias) | CFOP de devolução de venda |
| **Quebra / perda de estoque** | Estorna **100%** do crédito da entrada | **CFOP 5927** |
| **CIAP** | Mantém 100% conforme saídas tributadas | Produto do grupo de ativo (prefixo `6…`) |
| **DIFAL SP** | Apurado em conta gráfica | — |
| **DIFAL MS** | Informado na apuração, recolhido em guia avulsa | — |

> A regra de quebra já é aplicada hoje: em Julho/2026 as baixas com CFOP 5927 de
> Guará e Registro somaram R$ 5.152,57 de estorno de crédito, lançadas na aba
> *Controle Ajustes Docs*. Com a regra parametrizada isso deixa de ser ajuste
> manual e passa a ser cálculo.

## 5. Centralização de SP em Guará

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

## 6. Tabelas de carga efetiva (adubos e fertilizantes)

Extraídas de *Pontos de Atenção*. Entram em `parametros/cargas.yaml` com vigência.

**Operação intraestadual**

| Origem | Alíquota geral | Redução atual | Carga efetiva | CST |
|---|---|---|---|---|
| SP | 18% | 77,78% | 4% | 20 |
| MG | 18% | 77,78% | 4% | 20 |
| MS | 17% | 76,47% | 4% | 20 |
| PR | 19% | 78,95% | 4% | 20 |
| MT | 17% | — | Diferimento | 51 |
| PR (diferido) | 19% | — | Diferimento | 51 |

**Operação interestadual** (adubos/fertilizantes e também ácido nítrico,
sulfúrico, fosfórico, fosfato natural bruto e enxofre)

| Alíquota geral | Redução atual | Carga efetiva | CST |
|---|---|---|---|
| 4% | — | 4% | 00 |
| 7% | 42,86% | 4% | 20 |
| 12% | 66,67% | 4% | 20 |
