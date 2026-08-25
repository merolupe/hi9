# Apurabot — Decisões pendentes com a Gerência Fiscal/Tributária

> Perguntas que **precisam de resposta do time fiscal** antes (ou durante) a
> construção do motor. Cada uma está com o número real de Julho/2026 ao lado,
> para que a resposta seja objetiva.
> Nenhuma delas bloqueia o início do desenvolvimento — todas têm um
> comportamento-padrão assumido, que fica registrado aqui.

---

## 1. ✅ Rio Brilhante — o alcance do benefício *(respondida)*

**Termo de Acordo n. 1.190/2018**, firmado em 19/09/2018, publicado no DOE 9.755.
Base legal: LC estadual 93/2001 e Lei 4.049/2011.

**Resolvida em 25/08/2026 por documento oficial, não por dedução.** O benefício
alcança a **atividade industrial**, exatamente como a leitura literal do inciso I
da cláusula terceira indicava.

### A prova

Três documentos da competência 07/2026, entregues em 25/08/2026:

1. **Registro de Apuração do ICMS**, linha 012 — a dedução tem nome:
   *"BENEFÍCIOS FISCAIS - Termo de acordo n. 1190/2018 - **Industrialização
   própria** - Incentivo TA/CDI"*.
2. **GIA - Benefício Fiscal** (protocolo 36160E2) — base de saídas incentivadas
   de **R$ 412.274,17**, que é exatamente CFOP 5101 + 5118 + 6101 do mês.
3. **GIA - Apuração Final** — quatro colunas de atividade, com o benefício
   inteiro na coluna Industrial.

### O que estava errado do nosso lado

A hipótese `todas_as_saidas` vinha de um ajuste que batia a 0,19% — e essa
proximidade era coincidência. A apuração estava certa desde o começo; o modelo é
que estava errado. Fica o registro: **número que fecha não é mecanismo provado.**

### Como ficou no motor

```yaml
alcance:
  criterio: atividade_industrial
  rateio_do_credito: participacao_do_debito
```

O regime está `homologado: true`. O rateio pela participação do débito, que era
premissa assumida, também se confirmou: a GIA reparte o crédito da parcela
incentivada em R$ 10.769,23 intra e R$ 67.213,25 inter, o que é exatamente a
participação de CFOP 5101+5118 (13,810%) e 6101 (86,190%) no débito industrial.

### A cláusula quarta continua expirada

Se ela estivesse prorrogada, haveria 50% em algum lugar da GIA. Não há: só 67% e
80%, e só sobre produção própria. A revenda de R$ 93.717,23 não recebe crédito
presumido nenhum.

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
estorno em vez de R$ 19.961,55 — R$ 1,04 de diferença.

**Atualização de 25/08/2026.** A parcela deixou de ser tabela e virou fórmula
(`1 − carga_de_referencia / alíquota`), então o arredondamento passou a ser um
parâmetro só: `casas_decimais_da_parcela: 4`. Pôr `null` usa a fração exata.

Vale registrar um resíduo achado ao implementar. Na aba ESTORNO de Rio Brilhante,
o ácido fosfórico (CFOP 2101, 7%) estorna **R$ 3.865,55** — o arredondado. A
linha 003 do Registro de Apuração traz, **além** dos R$ 331.236,11, um *"Estorno
de créditos para ajuste de apuração do ICMS"* de **R$ 3.865,30**, que é o mesmo
9.019,01 × (1 − 4/7) calculado com a **fração exata**. Vinte e cinco centavos de
diferença entre os dois. Pode ser item distinto; pode ser a mesma linha lançada
duas vezes, uma arredondada e outra exata. Não foi decidido — o motor reproduz o
declarado, e o ajuste entra como parâmetro explícito, não embutido.

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

## 17. ✅ FADEFE / Pró-Desenvolve — respondida

A cláusula terceira, parágrafo primeiro, do Termo condiciona a fruição a uma
contribuição mensal ao **Fundo de Apoio ao Desenvolvimento Econômico e de
Equilíbrio Fiscal do Estado (FADEFE)**, *"no percentual, prazo e nas condições
definidas em lei, sobre o benefício fiscal/financeiro efetivamente utilizado"*.

**Respondida em 25/08/2026:**

- **Percentual: 2%** sobre o benefício fruído.
- **Adicional Pró-Desenvolve / FADEFE Equilíbrio Fiscal: 0%** — existe como
  campo próprio na GIA e hoje está zerado.
- **É guia avulsa**, calculada na própria GIA. **Não entra na conta gráfica** da
  apuração de ICMS.

Em Julho/2026: benefício fruído R$ 261.431,90 → contribuição de **R$ 5.228,64**,
conferida contra a GIA - Benefício Fiscal e o Relatório FAI.

**Como ficou no motor:** os dois percentuais são parâmetro com vigência, o valor
sai numa seção própria do relatório — *"Contribuição ao Pró-Desenvolve / FADEFE
— GUIA AVULSA"* — e não toca o saldo apurado.

---

## 18. 🟡 Complemento de ICMS de RB — está no Livro e não está na GIA

O complemento de ICMS de Rio Brilhante (CFOP 2906, produto 701000075) traz
**R$ 5.249,34** de crédito no Livro Fiscal de Julho/2026, com base de
R$ 43.744,48 — ou seja, 12%.

A GIA retificadora declara créditos normais de R$ 464.653,71. O Livro tem
R$ 469.903,05. **A diferença é exatamente esse complemento.**

Duas coisas a decidir:

1. O crédito de R$ 5.249,34 é apropriável ou não? Se for, a GIA o omitiu; se não
   for, o motor precisa saber por quê.
2. A decisão nº 13 diz que o complemento **acompanha a situação da nota
   complementada**. A 12%, ele deveria estornar 0,6667 — R$ 3.499,73. Na planilha
   ele foi apropriado integralmente, sem estorno.

**Padrão assumido:** o motor mantém o complemento no crédito, classificado na
atividade comercial, e **não o estorna** (a alíquota da linha é zero, então a
fórmula não tem o que aplicar). A diferença de R$ 5.249,34 contra a GIA é
exigida por teste, com valor exato — não passa em silêncio.

---

## 19. 🟡 Corumbá — a segregação por atividade não tem documento

O mapa de atividades foi homologado contra os documentos de **Rio Brilhante**.
Corumbá usa o mesmo mapa, porque a UF é a mesma e a GIA de MS é a mesma — mas
**não há GIA de Corumbá** para conferir a segregação dela.

Em Julho/2026 o motor separa Corumbá em R$ 85.506,00 de débito industrial e
R$ 25.985,32 de comercial. Ninguém conferiu esses números contra declaração.

**Pergunta:** Corumbá também declara GIA segregada por atividade? Se sim, é
possível enviar a de Julho/2026 para fechar a homologação?

**Padrão assumido:** aplicar o mesmo mapa e marcar como não conferido.

---

## 20. 🟡 MS tem centralização, e ela não está no motor

A linha 002 do Registro de Apuração de Rio Brilhante traz **R$ 99.412,10** de
*"Recebimento de saldo devedor - estabelecimento centralizador"*.

Ou seja: **Rio Brilhante recebe saldo devedor de outro estabelecimento de MS.**
Até aqui, o projeto tinha centralização modelada apenas em SP, com Guará.

**Perguntas:** quem transfere para RB — Corumbá? A regra é a mesma de SP? Existe
ato formal de centralização em MS?

**Padrão assumido:** o valor entra como ajuste manual (linha 002), na atividade
Prestacional/Outras, sem regra de centralização automática. A Entrega 4 trata
centralização e vai precisar dessa resposta.

---

## 21. 🟡 Os créditos de ajuste de RB — origem e valor

O Registro de Apuração e a GIA retificadora divergem no lado do crédito:

| Linha | Registro (07/08) | GIA retificadora (25/08) |
|---|---|---|
| Outros créditos | 46.138,68 — *"Ajuste de créditos conforme art. 68 RICMS/MS"* | 73.722,69 — *"Transferência de crédito acumulado – Processo e-SAP 502558 – NF 244564/243285"* |

Rubrica diferente, descrição diferente, R$ 27.584,01 a mais.

Registra-se também, sem juízo de valor, que a soma dessa mudança com a saída do
complemento (nº 18) dá **R$ 22.334,67**, e que a correção da inversão de colunas
reduziu o benefício em **R$ 22.334,66** — de modo que o ICMS a recolher ficou em
R$ 107.656,90 contra os R$ 107.656,92 originais. Um centavo de diferença entre
dois movimentos de naturezas independentes.

**Perguntas:** qual o valor homologado no processo e-SAP 502558 e a partir de
quando o crédito ficou disponível? O ajuste do art. 68 foi substituído por ele ou
são coisas distintas?

**Padrão assumido:** ambos entram como ajuste manual, fora do Livro. O motor não
os calcula nem os concilia.

---

## 22. 🟡 EFD/SPED — o livro ainda tem a composição antiga

A GIA foi retificada em 25/08/2026. O **Registro de Apuração do ICMS** que consta
é o emitido em 07/08/2026, com a composição anterior. As duas declarações da
mesma competência divergem em todas as linhas de crédito e na dedução — só o
total a recolher coincide, e ainda assim por dois centavos.

**Pergunta:** a EFD ICMS/IPI de 07/2026 também foi retificada?

**Padrão assumido:** o motor reproduz a **GIA retificadora**, que é o documento
mais recente. A regressão de Julho está ancorada nela.
