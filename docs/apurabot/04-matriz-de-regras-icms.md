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

**Um sinal prático:** entrada com base de cálculo reduzida que resulta em carga
efetiva de 4% é o próprio benefício de fertilizante já aplicado na origem — o
que aponta para `materia_prima`. Foi assim que o ÁCIDO FOSFÓRICO RAFINADO se
mostrou mal classificado (ver decisão pendente nº 8). O sinal não decide
sozinho, mas vale como conferência: produto químico de verdade entra acima de
4%, e é lá que a categoria muda o valor do estorno.

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

### 2.3. A TOP

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

### 3.1. Por que SP e MS não se comparam em percentual

As duas UFs partem da mesma carga de referência de 4%, e por isso é tentador
ler uma pela outra. São mecânicas diferentes:

| | SP | MS |
|---|---|---|
| Base do estorno | valor contábil | ICMS destacado |
| Chave da regra | carga efetiva da entrada | **alíquota** da operação |
| Resultado | pontos percentuais de carga | fração do crédito |

**"Parcela não tributada" é vocabulário de MS e só faz sentido lá**, onde a
regra devolve literalmente uma fração do crédito: `1 − 4/alíquota`.

Em SP não existe fração de regra. Se dividirmos o estorno pelo crédito para
efeito de conferência, o resultado **varia dentro de uma mesma carga** — porque
a carga do documento foi equalizada para a régua nominal, e o estorno usa a
nominal enquanto o crédito é o do documento. Uma entrada equalizada em 7% cuja
carga real é 6,77% estorna 3 pontos sobre o contábil, o que dá 44,3% do
crédito, e não os 42,9% que `1 − 4/7` sugeriria.

Por isso a aba `APURAÇÃO EFETIVA` traz **duas colunas de percentual**, e não uma:

| Coluna | O que é | SP | MS |
|---|---|---|---|
| **% da regra** | o nominal, antes de encontrar o documento | `(carga − 4%) ÷ carga` | `1 − 4 ÷ alíquota` |
| **% efetivo** | o que saiu: `ICMS a estornar ÷ crédito` | quebrado | igual ao nominal |

Em MS as duas coincidem, porque a regra devolve literalmente uma fração do
crédito. Em SP não: o estorno incide sobre o contábil e o crédito veio da base
de ICMS, que é menor, então o efetivo passa do nominal na razão contábil ÷ base.
Uma entrada equalizada em 12% com contábil 862.582,30 e base 814.253,03 estorna
69.006,58, que são 70,62% do crédito e não os 66,67% da regra.

**O agrupamento é sempre pela carga efetiva equalizada**, nos dois regimes. É a
grandeza que o documento traz depois da equalização e é por ela que a
conferência manual olha. A alíquota continua sendo a chave do cálculo em MS —
ela aparece no `% da regra`, não no agrupamento.

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
> O estorno é a parcela da alíquota, e o que resta é o crédito equivalente a 4%.
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
| Industrial | CFOP de venda de produção do estabelecimento (5101, 6101, 5118, 6118, 5109, 6109, 5111, 6111, 5122, 6122) | CFOP de compra para industrialização (1101, 2101, 3101, …), transferência para industrialização (1151, 2151, 3151) e frete de custo |
| Comercial | CFOP de venda de mercadoria de terceiros, remessa e retorno (5102, 6102, 5905, 6905, 5934, 6934, …) | CFOP de compra para comercialização (1102, 2102, 3102, …), transferência para comercialização (1152, 2152, 3152) e frete de venda |
| Prestacional/Outras | Bonificação, doação, brinde e outras saídas (5910, 6910, 5949, 6949) | CIAP (1604, 2604) |

#### O frete: custo é produção, despesa é comercial

O critério que separa os fretes em MS é **custo × despesa**, e não o CFOP:

| Descrição do CT-e | Natureza | Atividade |
|---|---|---|
| Fretes sobre Compra de Insumos (Custo) | custo | industrial |
| Fretes sobre Transf/ Remessa/ Retorno (Custo) | custo | industrial |
| Fretes sobre Vendas | despesa | comercial |

A própria descrição do Sankhya marca o custo com "(Custo)" no fim, e é isso que
`parametros/regimes.yaml` lê, no bloco `atividades.ms.por_descricao`.

> **A regra do frete de transferência vale de 08/2026 em diante.** A GIA de
> 07/2026 de Rio Brilhante o classificou como comercial, e é contra ela que a
> regressão de julho fecha. Por isso a regra carrega `vigencia_inicio` — regra 3
> do repositório. Ver decisão pendente nº 17, com o efeito de retificar julho.

Duas descrições ficaram **de fora de propósito** — "Fretes sobre Compras
(Almoxarifado)" e "Fretes sobre Transf/ Retorno - Venda conjunta" —, porque o
critério não as resolve. Elas seguem a atividade do CFOP até o time fiscal
decidir. Também na decisão pendente nº 17.

O corte **intra/inter** vem do primeiro dígito do CFOP: 5 é interno, 6 é
interestadual, 7 é exterior.

> **Atividade indefinida bloqueia o encerramento.** CFOP que não casa com nenhuma
> atividade recebe `SEM REGRA`, como manda a regra 4 do projeto.

### 4.4. Devolução de venda segue a venda que desfaz

A devolução entra pela atividade da operação que ela cancela, porque é isso que
ela é: o desfazimento de uma venda já apurada.

| CFOP | | Atividade |
|---|---|---|
| 1201 / 2201 / 3201 | Devolução de venda de produção do estabelecimento | Industrial |
| 1202 / 2202 / 3202 | Devolução de venda de mercadoria de terceiros | Comercial |

### 4.5. Demais regras de MS

| Item | Regra |
|---|---|
| Entrada com alíquota acima de 4% | Crédito mantido limitado à carga de referência |
| DIFAL em MS | Informa na apuração e recolhe em **guia avulsa** — não entra em conta gráfica |
| Centralização | Rio Brilhante **recebe** saldo devedor de estabelecimento centralizador; a regra de MS ainda não está modelada |

### 4.6. Benefício fiscal de Rio Brilhante — Termo de Acordo n. 1.190/2018

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

### 5.1. O sinal do saldo é o do caixa

```
saldo = saldo credor anterior + crédito mantido + crédito presumido − débito
```

**Positivo é credor: crédito que se transporta para o mês seguinte.**
**Negativo é devedor: sai do caixa.**

A conta gráfica trata o débito como positivo, e a ferramenta poderia ter
seguido essa direção. Não segue, porque quem fecha a competência não lê a conta
gráfica — lê o efeito financeiro, e ali um número negativo significa dinheiro
saindo. `a recolher` repete o mesmo valor em positivo, porque é ele que vai
para a guia.

**O Registro de Apuração é a exceção, e é deliberada.** Lá as linhas 011
(saldo devedor), 013 (imposto a recolher) e 014 (saldo credor a transportar)
têm linhas próprias, todas positivas, como o livro manda. O espelho reproduz o
documento, não a leitura gerencial.

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
| **Saldo credor do período anterior** | Informado na primeira competência; nas seguintes vem do encerramento anterior | — |

Sobrescrever o saldo credor à mão continua possível, mas é exceção registrada, não
rotina.

### 5.2. Os ajustes: quatro linhas, e o sentido vem da linha

As linhas **002, 003, 006 e 007** do Registro não nascem de documento. São
decisões da apuração, e só podem chegar declaradas — enquanto não chegam, o
registro as mostra zeradas e marcadas.

O valor é **sempre positivo**. Quem dá o sentido é a linha escolhida, como no
próprio Registro, onde nenhuma linha aceita número negativo:

| Linha | Efeito na conta |
|---|---|
| **002** Outros Débitos | aumenta o que se deve |
| **003** Estornos de Créditos | aumenta o que se deve |
| **006** Outros Créditos | diminui o que se deve |
| **007** Estornos de Débitos | diminui o que se deve |

Reduzir um estorno que a regra calculou não é lançar negativo na 003: é lançar
positivo na 006. Admitir as duas formas daria dois jeitos de escrever a mesma
coisa, e a conferência ficaria mais difícil sem ganhar nada.

**O ajuste entra na conta, não na escrituração.** Crédito bruto, estorno e
débito continuam sendo o que o Livro sustenta; o ajuste soma por cima, no saldo
e no registro ao mesmo tempo. Se mudasse só o registro, a tela e o livro
contariam histórias diferentes do mesmo mês.

**Onde ele é informado depende de ter documento ou não.** O que pertence a uma
nota vai na linha dela, e aí o estabelecimento e a atividade saem da linha —
ninguém os digita e ninguém os erra. O que não pertence a nota nenhuma é
declarado à parte, com o estabelecimento escrito; onde a UF segrega por
atividade, a atividade também, porque é ela que dimensiona o benefício.

**`ANOTAR` marca sem lançar.** Um ICMS reconhecido como indevido mas tratado
fora da competência — por anuência, por exemplo — não pode alterar a apuração
nem desaparecer dela. Fica registrado, com valor e motivo, sob o total do que
está marcado e não lançado.

**Ajuste pela metade bloqueia.** Valor sem linha, linha sem motivo, lançamento
sem aprovador: nada disso é aceito nem descartado em silêncio. Descartar
perderia uma decisão que alguém tomou; completar é o que a regra 4 proíbe.

### 5.3. A conta gráfica não começa no dia 1º

O Livro Fiscal traz os documentos de uma competência e nada mais. A conta
gráfica, não: o crédito que sobrou no fim de um mês abre o mês seguinte. São as
duas pontas da mesma conta, e no Registro de Apuração elas têm linha própria:

| Linha | O que é | De onde vem |
|---|---|---|
| **009** — Saldo Credor do Período Anterior | A abertura do mês | Declarada, porque não está no Livro |
| **014** — Saldo Credor a Transportar p/ o Período Seguinte | O fechamento do mês | Calculada: `010 − 004` |

**A 014 de um mês é a 009 do mês seguinte.** É a única grandeza da apuração que
atravessa a virada, e é o que torna o encadeamento das competências verificável:
quem fecha agosto confere a abertura contra o fechamento de julho, sem refazer
conta nenhuma.

A abertura é declarada em `parametros/saldos.yaml`, por competência e por
**código** da empresa. Uma competência presente no arquivo é declaração
completa: estabelecimento que não aparece abriu o mês sem saldo credor.
Competência ausente é outra coisa — aí ninguém declarou nada, a apuração roda
com todo mundo zerado e o registro **marca a linha 009**, porque preencher por
conta própria é o que a regra 4 do repositório proíbe.

Duas consequências da ordem em que a abertura entra:

* **não mexe na escrituração.** Crédito bruto, estorno e débito são do mês, e a
  abertura não os toca. Se ela vazasse para lá, a conferência linha a linha
  deixaria de fechar;
* **entra antes da centralização.** O estabelecimento leva para o grupo o saldo
  que efetivamente tem, abertura incluída.

O benefício fiscal continua dimensionado sobre o saldo devedor da atividade
industrial, sem a abertura. O que a abertura faz é limitar quanto dele se
deduz, pela própria aritmética do livro: a linha 012 não pode passar da 011.
Se a abertura devesse reduzir a base do benefício, e não só a dedução, a regra
seria outra — ver decisão pendente nº 14.

---

## 6. Centralização e transferência de saldo

Onde a UF admite apuração centralizada, cada estabelecimento apura o seu saldo e
o transfere para a **centralizadora**, que consolida e apura o resultado do
grupo.

A transferência é **consequência da apuração, não insumo dela**. O documento que
a formaliza só pode ser emitido depois que a competência fechou, e vai
escriturado na competência seguinte — não existe, nem pode existir, dentro do
livro que está sendo apurado. Por isso a ferramenta não cobra esse documento na
competência: ela **emite a instrução** do que precisa ser transferido.

Quem centraliza, quem é centralizado, o que se transfere e por qual mecanismo
estão em `parametros/filiais.yaml`.

### 6.1. O que se transfere, e até quanto

| Regra | O centralizado passa adiante |
|---|---|
| `saldo_integral` | o saldo, devedor ou credor |
| `saldo_devedor` | só quando deve; o crédito fica no estabelecimento |
| `saldo_credor` | só quando tem crédito; o débito fica no estabelecimento |

**O crédito tem teto: o saldo devedor da centralizadora.** A transferência
existe para compensar, e o que passa disso fica onde está. O saldo devedor não
tem teto — a centralizadora assume a dívida do grupo para recolher de uma vez
só.

O teto é do grupo, não de cada estabelecimento: com dois centralizados credores
e uma dívida só, o segundo transfere o que sobrou do primeiro. A ordem, hoje, é
a do cadastro — e é decisão pendente enquanto nenhuma competência a exercitar.

### 6.2. Identidades que a ferramenta valida

```
saldo individual = valor transferido + saldo residual
recebido pela centralizadora = soma do transferido pelos demais
saldo final do grupo = saldo próprio da centralizadora + total recebido
```

**Sinal:** os saldos circulam na convenção de caixa — positivo é credor,
negativo é devedor. Ver item 5.1. Transferir "o saldo devedor" é, portanto,
transferir um valor negativo.

### 6.3. Como a transferência se formaliza

| Mecanismo | Como se documenta | Onde aparece |
|---|---|---|
| `nfe` | NF-e de transferência de saldo emitida pelo centralizado | escrituração da competência seguinte |
| `ajuste_de_apuracao` | lançamento no Registro de Apuração, sem documento próprio | linha 002 da centralizadora, no mesmo período |

A diferença é substantiva. Onde a transferência tem NF-e, ela entra na conta
gráfica da centralizadora **pela escrituração da nota** — e por isso não é
ajuste. Onde é lançamento, ela **é** o ajuste: a ferramenta calcula o valor a
partir do saldo apurado do centralizado e o leva à linha 002 da centralizadora.

### 6.4. SP

São Paulo centraliza em **Guará**; Matriz e Registro são centralizados.

**A transferência chega como lançamento de apuração**, nos dois sentidos e com
a mesma redação que MS usa — "recebimento de saldo credor / devedor —
estabelecimento centralizador", nas linhas 006 e 002 do Registro da
centralizadora.

**A NF-e continua sendo emitida, e não é alternativa ao lançamento.** Ela nasce
do resultado da apuração e não retroage: sai depois do fechamento e vai
escriturada na competência seguinte. Quem fecha o mês é o lançamento; a nota
formaliza.

**O crédito transferido para no saldo devedor da centralizadora** — ver 6.1.

### 6.5. MS

Mato Grosso do Sul centraliza em **Rio Brilhante**; Corumbá é centralizado. O
centralizado transfere o **saldo devedor**, e o mecanismo é o ajuste de
apuração: o valor aparece no Registro da centralizadora como *"Recebimento de
saldo devedor - estabelecimento centralizador"*, na linha 002.

O que segue em aberto é o caso do saldo credor no centralizado — não há
competência observada em que isso tenha ocorrido. Ver decisão pendente nº 7.

### 6.6. Controles da NF-e de transferência

Valem para o mecanismo `nfe`, e são conferência **da competência seguinte**:
a nota emitida sobre a apuração de um mês é escriturada no mês posterior, e é
lá que ela se confere contra o plano de transferência que aquela apuração
emitiu.

| Situação | Tratamento | Situação no motor |
|---|---|---|
| NF-e de valor diferente do saldo transferido | Revisão, com a diferença evidenciada | ⬜ a implementar |
| NF-e cancelada | Bloqueio | ⬜ a implementar |
| CFOP incompatível | Revisão | ⬜ a implementar |
| Emissão fora da competência | Revisão | ⬜ a implementar |
| Duplicidade | Bloqueio | ⬜ a implementar |
| Resíduo sem justificativa | Revisão | ⬜ a implementar |

## 7. Carga efetiva

### 7.1. Régua de valores nominais

A equalização encaixa a carga bruta de cada documento num valor nominal da régua.

| | Cargas |
|---|---|
| **Homologadas** | 4 · 7 · 12 · 17 · 18 |
| **Toleradas** — advertência, sem bloquear | 19 · 20,5 · 25 |

As toleradas continuam reconhecidas para que uma competência antiga siga
reproduzível, mas todo documento que cair numa delas recebe o alerta
`CARGA NÃO HOMOLOGADA`, apontando para revisão do lançamento na origem.

### 7.2. Tabelas de carga (adubos e fertilizantes)

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
