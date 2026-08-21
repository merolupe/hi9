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

## 3. MS — estorno proporcional e benefício de Rio Brilhante

### 3.1. A mecânica de MS não é a de SP

Confirmado contra a **apuração individualizada de Corumbá (Empresa 9)**, aba
`ENTRADAS`. Em MS o estorno incide sobre o **valor do ICMS**, e não sobre o valor
contábil:

```
estorno = ICMS × parcela não tributada da operação
```

A parcela não tributada é a coluna *REDUÇÃO ATUAL* da tabela de operação
interestadual, e o que sobra leva a carga exatamente a 4%:

| Carga da entrada | Parcela não tributada | Crédito que resta | Confere |
|---|---|---|---|
| 12% | 66,67% | 33,33% | 12% × 0,3333 = **4,00%** |
| 7% | 42,86% | 57,14% | 7% × 0,5714 = **4,00%** |
| 4% | — | 100% | já está em 4% |

Reproduz Julho/2026 na sexta casa decimal: R$ 19.961,553359 de estorno e
R$ 12.079,216641 de crédito a apropriar.

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

### 3.3. Demais regras de MS

| Item | Regra | Situação |
|---|---|---|
| Entrada interestadual > 4% | Crédito mantido limitado a 4% | Escopo v1.0, item 5.3 |
| Entrada a 4% | Crédito mantido de **0,941176%** | Escopo v1.0, item 5.3 |
| Fertilizante interno MS | Manutenção de **0,941176%** | Escopo v1.0, item 5.4 |
| **B.F. Rio Brilhante — saída intraestadual** | Crédito presumido de **67% sobre o saldo devedor** | Produção própria de RB |
| **B.F. Rio Brilhante — saída interestadual** | Crédito presumido de **80% sobre o saldo devedor** | Produção própria de RB |
| DIFAL em MS | Informa na apuração e recolhe em **guia avulsa** | Não entra em conta gráfica |

O benefício de RB movimenta ainda um **controle de crédito outorgado**
(código de ajuste `MS090004` — apropriação de crédito outorgado para abatimento
de débitos), com saldo anterior, créditos recebidos por transferência, créditos
utilizados no período e saldo a transportar.

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
