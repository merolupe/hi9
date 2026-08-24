# Apurabot — Decisões pendentes com a Gerência Fiscal/Tributária

> Perguntas que **precisam de resposta do time fiscal** antes (ou durante) a
> construção do motor. Cada uma está com o número real de Julho/2026 ao lado,
> para que a resposta seja objetiva.
> Nenhuma delas bloqueia o início do desenvolvimento — todas têm um
> comportamento-padrão assumido, que fica registrado aqui.

---

## 1. 🔴 Rio Brilhante — o alcance do benefício

**Termo de Acordo n. 1.190/2018**, firmado em 19/09/2018, publicado no DOE 9.755.
Base legal: LC estadual 93/2001 e Lei 4.049/2011.

### O que o Termo diz

**Cláusula terceira**, em vigor até 31/12/2032:

| Inciso | Benefício | Alcance escrito |
|---|---|---|
| **I** | **67%** do saldo devedor do ICMS | *"aplicável **exclusivamente** às operações realizadas com os produtos resultantes de sua própria industrialização neste Estado"* |
| **II** | adicional de **13%**, totalizando **80%** | *"aplicável **exclusivamente** nas operações interestaduais"* |

O benefício é *"deduzido do saldo devedor que tenha resultado como efetiva e
regularmente devido"*. Incisos III a VI tratam de diferimentos.

**Cláusula quarta**, com prazo até 31/12/2022 pela cláusula oitava: crédito
outorgado de **50%** do saldo devedor nas saídas interestaduais com mercadorias
**adquiridas em outras UFs**, e crédito presumido de 50% do imposto nas saídas
interestaduais com **itens importados**.

### 🔴 A apuração de Julho/2026 não segue esse alcance

Os percentuais da cláusula terceira foram aplicados sobre **todas** as saídas:

| Hipótese | Benefício (R$) |
|---|---|
| A) Só produção própria — leitura literal do inciso I | 228.357,72 |
| B) Cláusula terceira + quarta (50% na revenda interestadual) | 245.107,61 |
| C) **Cláusula terceira sobre todas as saídas** | 277.369,17 |
| C) idem, com o crédito mantido que a apuração manual usava | **284.294,40** |
| **Lançado na apuração de Julho** | **283.766,56** |

**A hipótese C fecha em 0,19%.** As outras não chegam perto.

### Isso indica prorrogação da cláusula quarta?

**Não.** Se a quarta estivesse em vigor, a revenda interestadual (CFOP 6102,
R$ 47.298,29 de débito em Julho) receberia **50%**, e o total ficaria em torno de
R$ 245 mil. O que se observa são os percentuais da **terceira** — 67% e 80% —
aplicados a uma base maior que a que a terceira descreve.

Duas possibilidades, e nenhuma delas se resolve com os documentos em mãos:

1. **Existe aditivo ao Termo** que amplia o alcance da cláusula terceira ou
   prorroga a quarta com outra redação. O arquivo recebido é o instrumento
   original de 2018 — não há aditivo entre as sete páginas.
2. **A base foi ampliada na prática**, sem amparo no instrumento.

### O que os dados dizem sobre "produção própria"

Os produtos vendidos com CFOP de revenda são **disjuntos** dos vendidos como
produção própria — nenhum aparece nos dois grupos:

| Vendidos como revenda (5102/6102) |
|---|
| UREIA 46-00-00 (Bag 1.000 Kg · Prill · GR SC 50 Kg · Bag 500 Kg) |
| Sulfato de Zinco 35% Imp. SC 25 Kg |
| HINOFIX 5 L |
| Nitrato de Cálcio Imp. Sc 25 Kg |

Ureia comprada e revendida, importados revendidos. Pelo cadastro, o CFOP separa
bem: essas saídas não são de produtos que Rio Brilhante industrializa.

### Como está no motor

O alcance é **parâmetro**, com os dois critérios implementados:

```yaml
alcance:
  criterio: todas_as_saidas       # ou: cfop_de_producao_propria
```

**O padrão é `todas_as_saidas`** — reproduzir o que a apuração faz, sem impor
leitura nova. O regime está `homologado: false`, e um teste mede quanto custa a
decisão: **R$ 49.011,45** de diferença entre as duas leituras na competência de
Julho.

### Perguntas

1. Existe **aditivo ou prorrogação** ao Termo de Acordo n. 1.190/2018 que amplie
   o alcance da cláusula terceira ou estenda a quarta?
2. Se não existir, o benefício deve passar a alcançar só a produção própria?
3. Como o crédito mantido é rateado entre operações beneficiadas e não
   beneficiadas? O Termo não diz. Assumida a **participação do débito**.

## 2. ✅ MS — base do estorno proporcional *(respondida)*

**Respondido em 21/08/2026**, com a apuração individualizada de Corumbá
(Empresa 9) em mãos. Eram duas coisas erradas, não uma.

**a) A fórmula.** MS não usa a mecânica de SP. O estorno incide sobre o **valor
do ICMS**, aplicando a parcela não tributada da operação:

| CFOP | Carga | ICMS | Parcela não tributada | Estorno |
|---|---|---|---|---|
| 2102 | 7% | 5.880,00 | 42,86% | 2.520,168 |
| 2352 | 12% | 18.092,40 | 66,67% | 12.062,20308 |
| 2353 | 12% | 8.068,37 | 66,67% | 5.379,182279 |
| | | | **Total** | **19.961,553359** |

Bate na sexta casa com a Empresa 9 e com os R$ 19.961,55 da consolidada. A
fórmula de SP dava R$ 19.960,51 — e era daí que vinha o resíduo de R$ 1,04 que
eu não explicava.

**b) O crédito de transferência é indevido.** A linha de **CFOP 2152**
(R$ 14.424,02, contraparte exata do CFOP 6152 de Guará) está marcada como
*"Crédito Indevido"* na Empresa 9: sem estorno e sem apropriação.

O crédito a apropriar de Corumbá é **R$ 12.079,216641**, não os R$ 26.503,24 da
apuração consolidada — que somava o crédito indevido ao mantido
(12.079,22 + 14.424,02 = 26.503,24).

**Implementado:** regime `ms_estorno_proporcional` com
`formula_estorno: proporcional_parcela_nao_tributada`, e o crédito indevido em
parcela própria, de forma que a identidade auditada passa a ser
`mantido + estorno + indevido = bruto`.

**Ainda em aberto:** o CFOP 2152 gera crédito indevido **sempre**, ou foi
específico desta transferência? A regra está com `homologado: false`.

## 3. ✅ Os 0,941176% — encerrada, não existem *(respondida)*

Procurados em três lugares, não encontrados em nenhum:

1. **Apuração consolidada de Julho/2026** — varredura célula a célula nas 7 abas.
   Só aparece o fator que geraria o número (`4/17 = 0,235294`, em
   `Pontos de Atenção!F72`), nunca o percentual aplicado.
2. **Apuração individualizada de Corumbá (Empresa 9)** — a mecânica é outra:
   estorno da parcela não tributada sobre o ICMS.
3. **Termo de Acordo n. 1.190/2018** — as sete páginas não mencionam o percentual
   nem nada equivalente.

**Decisão de 21/08/2026: esquecer.** O parâmetro saiu de `regimes.yaml` — não
fica como "não aplicado", porque não há regra a aplicar. O número vinha do escopo
funcional v1.0, e a origem não se sustentou em nenhuma das três fontes.

## 4. ✅ Carga efetiva — régua de valores nominais *(respondida)*

**Respondido em 21/08/2026, em duas rodadas.**

**Os 20,5%** não devem constar na base. Apareceram em 30 CT-e de frete sobre
compra de insumos de Guará (CFOP 1353 e 1352) e foram aceitos na apuração manual.

**A régua estava larga demais.** 19% e 25% não ocorrem nas operações da Hinove e
saíram das homologadas.

| | Cargas |
|---|---|
| **Homologadas** | 4 · 7 · 12 · 17 · 18 |
| **Toleradas** — advertência, sem bloquear | 19 · 20,5 · 25 |

A equalização continua reconhecendo as toleradas, para que a regressão de
Julho/2026 reproduza o resultado. Todo documento que cair numa delas recebe o
alerta `CARGA NÃO HOMOLOGADA`, apontando para revisão do lançamento na origem.

## 5. ✅ Qual apuração é a oficial *(respondida)*

**Decisão de 21/08/2026: vale a apuração individualizada por estabelecimento.**

A apuração consolidada de Julho/2026 foi montada toda no molde do equilíbrio
fiscal de SP, e por isso não reflete a mecânica das outras UFs. Onde as duas
divergem, a individualizada é a correta — foi assim que a divergência de Corumbá
apareceu (item 2).

**Consequência para o motor:** a conferência é feita contra a apuração
individualizada quando ela existe. A consolidada continua útil como referência
de totais, mas não é a fonte da verdade.

## 6. ✅ Saldo credor do período anterior *(respondida)*

**Decisão de 21/08/2026:** informado uma primeira vez e, a partir daí, puxado do
que ficou apurado na competência anterior.

Ou seja: no primeiro fechamento pela ferramenta o saldo entra digitado; nos
seguintes ele vem do encerramento do mês anterior, sem redigitação. Sobrescrever
manualmente continua possível, mas passa a ser exceção registrada, não rotina.

**A implementar** junto com o encerramento de competência (Entrega 6) — é ele
que grava o saldo que a competência seguinte vai ler.

**Segue em aberto:** MICROBIO (R$ 110.078,22) e HINOVE FERTILIZANTES ESPECIAIS
(R$ 172,02) entram no escopo do Apurabot ou continuam controle à parte?

## 7. 🟡 PR — mantém 100% ou não credita?

*Pontos de Atenção* diz "Créditos PR mantêm 100% s/ saídas diferidas", e a aba
ESTORNO mostra Londrina com crédito de frete de R$ 13.882,40 a 12% marcado como
mantido — mas o totalizador da mesma aba zera o crédito mantido de Londrina, e no
resultado final PR aparece só com o saldo credor anterior (R$ 327.121,97).

**Pergunta:** o crédito de PR é mantido e acumulado como saldo credor, ou é
estornado?

**Padrão assumido:** mantido e acumulado (conforme *Pontos de Atenção*).

## 8. 🟢 Itens fora do processo produtivo para o DIFAL

O DIFAL usa o ICMS **do XML** nas compras de itens que não integram o processo
produtivo.

**Pergunta:** qual é o critério de "não integra o processo produtivo" — CFOP
(1556/2556 uso e consumo), grupo do produto (prefixo do código), ou lista
mantida à parte?

**Padrão assumido:** CFOP de uso e consumo + ativo, parametrizado em
`classificacao.yaml` e ajustável sem alterar código.

## 9. 🟢 Layout dos arquivos de XML e Base de Bens

O Livro Fiscal já está mapeado (52 colunas, ver `03-dicionario-livro-fiscal.md`).
**Faltam exemplos reais** dos outros dois arquivos de entrada. Sem eles, DIFAL e
CIAP ficam no desenho, não na construção.

**Pedido:** enviar um `.xlsx` de exemplo de cada — XML das entradas e Base de Bens.

## 10. 🟢 Aprovação de ajustes manuais

O escopo exige que só ajustes com status **Aprovado** alimentem a apuração, com
responsável e aprovador.

**Pergunta:** quem aprova, e a mesma pessoa pode lançar e aprovar? A ferramenta
deve apenas registrar, ou bloquear o fechamento quando lançador = aprovador?

**Padrão assumido:** registra os dois nomes, permite que sejam a mesma pessoa e
sinaliza no painel de auditoria — sem bloquear.


---

## 11. ✅ Complemento de ICMS — é regra *(respondida)*

**Decisão de 21/08/2026: é regra, não acaso.** O complemento acompanha a
situação da nota complementada, mesma lógica do complemento de preço (item 13).

Os 4% aplicados às 6 linhas de Julho/2026 (R$ 17.490,73 de ICMS) são a carga das
notas que elas complementam. Se um complemento vier de nota com outra carga, é a
carga dela que vale — e a referência está na coluna `Observação` do extrato.

O parâmetro passou a `homologado: true` e essas linhas deixaram de gerar alerta.
Os alertas de Julho caíram de 36 para 30, que são as 30 linhas de carga 20,5%.

## 12. ✅ NBPT BLUE 20% — produto químico *(respondida)*

**Respondido em 21/08/2026:** segue o que a apuração fez. Conferido nos três
lugares onde o produto entrou em Julho/2026:

| Filial | CFOP | Carga | ICMS | Tratamento na apuração |
|---|---|---|---|---|
| Corumbá | 2102 | 7% | 5.880,00 | estorno de 2.520,17 pelos 42,86% — Empresa 9, aba ENTRADAS |
| Guará | 2102 | 12% | 10.080,00 | dentro do grupo de 12% que estornou 8% |
| Rio Brilhante | 2102 | 7% | 14.700,00 | mantido — carga fora das beneficiadas |

Nos dois primeiros a apuração tratou como **crédito comum sujeito a estorno**, e
não como revenda com crédito integral. Confirma `produto_quimico`, que é como já
estava no cadastro. A marca `homologado: false` saiu.

## 13. ✅ Complemento de preço — acompanha a nota complementada *(respondida)*

**Respondido em 21/08/2026:** o complemento de preço acompanha a situação da nota
que ele complementa. Saída de matéria-prima, por exemplo, vai a 4%.

Na prática o documento já resolve sozinho: em Julho as 22 linhas saíram com
alíquota de 7% sobre base reduzida (ex.: contábil 2.343,26 · base 1.338,94 · ICMS
93,73), o que dá **carga efetiva de 4%** — exatamente a carga de uma saída de
matéria-prima. A equalização já chegava nesse número; faltava a categoria, e o
produto ficava em `SEM REGRA`.

A ligação com a nota original está na **observação** do documento
(*"COMPLEMENTO DE PREÇO REFERENTE A NF 57081"*), e é por ela que a memória de
cálculo aponta para a nota complementada.

**Com isso, Julho/2026 fecha sem nenhuma pendência.**

## 14. 🟢 A tolerância da equalização está frouxa

A régua homologada é `{4, 7, 12, 17, 18, 19, 20,5, 25}` e a tolerância é de
**2,5 pontos**. O maior vão entre degraus é de 5 pontos (7→12 e 12→17), ou seja,
exatamente o dobro da tolerância. Na prática, **qualquer carga entre ~1,5% e
~27,5% encaixa em algum degrau** e nada é sinalizado.

Em Julho isso não escondeu nada — a maior distância observada foi de 1,97 ponto,
e as 30 linhas de 20,5% já são sinalizadas pela via da carga tolerada. Mas a
rede está larga.

**Pergunta:** apertar a tolerância para 1,5 ponto? Isso passaria a sinalizar
cargas a mais de 1,5 ponto de qualquer degrau, sem bloquear o fechamento.

**Padrão assumido:** manter 2,5 até haver decisão — apertar sem combinar geraria
pendências novas no primeiro fechamento.


## 15. ✅ Arredondamento da parcela não tributada *(respondida)*

**Decisão de 21/08/2026: tanto faz.** Mantidos os percentuais **arredondados em
4 casas** (`0,4286` e `0,6667`), que são os que a apuração individualizada de
Corumbá usa e os que reproduzem Julho/2026 exatamente.

A alternativa seriam as frações exatas `3/7` e `2/3`, que dariam R$ 19.960,51 de
estorno em vez de R$ 19.961,55 — R$ 1,04 de diferença. Os valores em uso estão
explícitos em `parametros/regimes.yaml`, então trocar depois é editar duas linhas.

## 16. 🟡 Coluna TOP — extração definida, classificação a validar

**Respondido em 21/08/2026: a extração com TOP passa a ser o padrão mensal.**

O extrato `Movimento Livros Fiscais` já é lido pelo motor, e um teste prova que
ele produz **apuração idêntica** à extração antiga — mesmo crédito bruto, mesmo
estorno, mesmo crédito mantido, nas sete filiais. Ele traz ainda a `Observação`
(que liga o complemento de preço à nota complementada), as colunas de DIFAL e os
51 documentos cancelados que a extração antiga filtrava.

### 🟡 O que falta decidir: usar o TOP para classificar

O TOP nomeia a operação **como ela foi lançada**. Onde ele concorda com a
heurística atual, trocar é ganho puro de confiabilidade. Mas há **três casos em
que ele discorda**, e cada um é uma decisão tributária:

| TOP | Descrição | Hoje classificado como | Linhas | ICMS (R$) |
|---|---|---|---|---|
| **2103** | Compra de MP | 210 como `materia_prima`, **4 como `produto_quimico`** | 214 | 368.978,94 |
| **2124** | Compra com Moeda Importação- mãe | 47 como `materia_prima`, **1 como `revenda`** (Enxofre) | 48 | 3.129.066,39 |
| **2130** | Compra em Moeda | 6 como `materia_prima`, **50 como `produto_quimico`** | 56 | 198.836,35 |

Em SP, matéria-prima **não** estorna e produto químico **estorna** — então a
escolha muda valor. O Enxofre é o caso mais claro: o TOP diz "compra
importação", mas a apuração o trata como **revenda**, e é isso que a aba ESTORNO
confirma com R$ 474.416,28 de estorno zero.

**Proposta de desenho:** o TOP entra como sinal primário, e o **cadastro de
produtos continua sobrepondo** — assim o TOP resolve os 95% e o cadastro guarda
as exceções que o fiscal decidiu. A ordem ficaria:

```
1. lançamentos sem contábil (CIAP, complemento de ICMS)
2. cadastro de produtos          ← exceção decidida pelo fiscal, vence tudo
3. TOP                            ← a operação como foi lançada
4. exceções por CFOP (quebra, devolução, retorno)
5. finalidade do frete (descrição do CT-e)
6. prefixo do código do produto
7. SEM REGRA
```

**Pergunta:** o TOP `2103 Compra de MP` deve mandar sobre o cadastro no caso do
ácido fosfórico — isto é, ele é matéria-prima porque foi lançado assim, ou é
produto químico e o lançamento é que deveria mudar?

**Enquanto não há resposta, a classificação por TOP não foi implementada.** A
coluna é lida, viaja na base tratada e está disponível para conferência.

## 17. 🟡 FADEFE — condição de fruição do benefício de RB

A cláusula terceira, parágrafo primeiro, do Termo de Acordo condiciona a fruição
do benefício a uma contribuição mensal ao **Fundo de Apoio ao Desenvolvimento
Econômico e de Equilíbrio Fiscal do Estado (FADEFE)**, *"no percentual, prazo e
nas condições definidas em lei, sobre o benefício fiscal/financeiro efetivamente
utilizado"*.

O Termo não fixa o percentual — remete à lei. Em Julho/2026 o benefício apurado
foi de R$ 228.357,72, então a contribuição sai desse valor.

**Perguntas:** qual o percentual em vigor? A contribuição entra na apuração de
ICMS como dedução, ou é obrigação apartada, fora da conta gráfica?

**Padrão assumido:** não calculada. O parâmetro `fadefe.percentual` está `null`
em `regimes.yaml`, e o benefício é apurado sem ela.
