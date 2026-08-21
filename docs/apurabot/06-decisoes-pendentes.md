# Apurabot — Decisões pendentes com a Gerência Fiscal/Tributária

> Perguntas que **precisam de resposta do time fiscal** antes (ou durante) a
> construção do motor. Cada uma está com o número real de Julho/2026 ao lado,
> para que a resposta seja objetiva.
> Nenhuma delas bloqueia o início do desenvolvimento — todas têm um
> comportamento-padrão assumido, que fica registrado aqui.

---

## 1. 🔴 Rio Brilhante — critério do crédito presumido *(respondida pelo Termo, com ressalva)*

**Termo de Acordo n. 1.190/2018**, firmado em 19/09/2018 entre o Estado de MS e a
Hinove, publicado no DOE 9.755. Base: LC estadual 93/2001 e Lei 4.049/2011.

### Cláusula terceira — o benefício em vigor, até 31/12/2032

> **I** — benefício fiscal equivalente a **67%** do saldo devedor do ICMS,
> aplicável **exclusivamente às operações realizadas com os produtos resultantes
> de sua própria industrialização neste Estado**, que será deduzido do saldo
> devedor que tenha resultado como efetiva e regularmente devido;
>
> **II** — adicional de **13%** ao previsto no inciso anterior, aplicável
> **exclusivamente nas operações interestaduais**, resultando num percentual de
> **80%**.

E o **parágrafo terceiro**: *"As matérias-primas não envolvidas no processo
fabril não poderão gozar dos incentivos previstos neste instrumento."*

Os incisos III a VI tratam de diferimento (importação de máquinas, DIFAL de
ativo, importação de matéria-prima) e do regime especial de apuração mensal do
DIFAL sobre ativo, uso e consumo e material de construção.

### Cláusula quarta — expirou em 31/12/2022

Concedia **50%** do saldo devedor nas saídas interestaduais com **mercadorias
adquiridas em outras UFs**, e **50%** do imposto nas saídas interestaduais com
**itens importados**. A cláusula oitava é explícita: vale *"a partir da data de
sua assinatura e até 31 de dezembro de 2022 em relação ao disposto na cláusula
quarta"*.

**Em Julho/2026, portanto, revenda de mercadoria de terceiros não tem benefício.**

### 🔴 O que isso levanta sobre Julho/2026

A regra é clara — o benefício alcança **só a produção própria**. Mas a apuração
de Julho parece tê-lo aplicado sobre **todas** as saídas:

| Base do benefício | Cálculo (R$) | vs. lançado |
|---|---|---|
| Só produção própria — CFOP 5101, 6101, 5118. **O que o Termo diz** | 228.357,72 | **−55.408,84** |
| Todas as saídas | 277.369,17 | −6.397,39 |
| **Lançado na apuração de Julho** | **283.766,56** | — |

Débito de saída de Rio Brilhante, separado como manda a cláusula:

| | Produção própria | Demais |
|---|---|---|
| **Intra** | 56.934,28 (5101, 5118) | 44.420,07 (5102, 5905, 5910) |
| **Inter** | 355.339,89 (6101) | 49.297,17 (6102, 6934) |

**Pergunta:** o benefício de Julho foi mesmo calculado sobre todas as saídas? Se
foi, há cerca de **R$ 55 mil** apropriados sobre operações que a cláusula terceira
não alcança — revenda de terceiros (5102/6102) e remessas (5905/6934) — e cuja
cobertura pela cláusula quarta acabou em 2022.

**O cálculo não foi implementado**, justamente porque a resposta muda o resultado
em R$ 55 mil. O regime `ms_beneficio_rio_brilhante` segue `homologado: false`.

**Ainda em aberto:**
- Como o crédito é rateado entre operações beneficiadas e não beneficiadas?
- A contribuição ao **FADEFE** (parágrafo primeiro) é condição de fruição — qual
  o percentual, e entra na apuração como dedução?

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

## 5. 🟡 Qual totalizador é o oficial

A aba **APURAÇÃO** e o totalizador da aba **ESTORNO** trazem números diferentes
para a mesma competência (ex.: saldo final 286.697,73 × 4.593.359,70; a aba
ESTORNO não computa o débito de saída dos estabelecimentos paulistas).

**Pergunta:** confirmar que a aba **APURAÇÃO** é o resultado oficial de Julho/2026,
para servir de referência do teste de regressão.

**Padrão assumido:** APURAÇÃO é o oficial; a ferramenta gera um totalizador único.

## 6. 🟡 Saldo credor do período anterior

Hoje entra digitado (R$ 902.567,05 no total de Julho). Também aparecem duas
empresas fora do grupo apurado — **MICROBIO** (R$ 110.078,22) e **HINOVE
FERTILIZANTES ESPECIAIS** (R$ 172,02) — carregando apenas saldo credor.

**Perguntas:** o saldo anterior deve ser (a) digitado pelo usuário, (b) puxado da
competência anterior fechada na própria ferramenta, ou (c) lido da apuração do
Sankhya? E MICROBIO e HFE entram no escopo do Apurabot ou continuam controle à parte?

**Padrão assumido:** (b) puxado da competência anterior quando existir, com
possibilidade de sobrescrever no primeiro mês; MICROBIO e HFE fora do escopo.

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

## 11. 🟡 Complemento de ICMS — de onde vem a carga

O produto `701000075` (COMPLEMENTO DE ICMS) aparece em **6 linhas** de
Julho/2026, somando **R$ 17.490,73** de ICMS — 5 entradas e 1 saída. Todas
chegam com **valor contábil zerado**, então `ICMS ÷ valor contábil` não existe
e a carga não pode ser calculada.

A apuração manual atribuiu **carga 4%** às seis. Não há regra escrita em
*Pontos de Atenção* para o caso.

**Pergunta:** os 4% são a regra, ou foram o que coube naquele mês? Se for regra,
ela vale para todo complemento ou depende da operação que está sendo
complementada?

**Padrão assumido:** carga 4%, parametrizada em `classificacao.yaml` com
`homologado: false`, gerando alerta `CARGA NÃO HOMOLOGADA` sem bloquear.

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


## 15. 🟡 Arredondamento da parcela não tributada — vale R$ 1,04

A Empresa 9 aplica os percentuais **arredondados em 4 casas** — `0,4286` e
`0,6667` — e não as frações exatas `3/7` e `2/3`:

| | Exato (3/7 e 2/3) | Arredondado (0,4286 e 0,6667) |
|---|---|---|
| Estorno de Corumbá | 19.960,51 | **19.961,55** |

Os R$ 1,04 de diferença são inteiramente arredondamento. O Apurabot usa os
valores arredondados, porque é o que reproduz a apuração de Julho/2026, e eles
estão explícitos em `parametros/regimes.yaml`.

**Pergunta:** manter o arredondado, ou passar a usar a fração exata daqui para
frente? Trocar muda o resultado de competências futuras — e faria a regressão de
Julho falhar, que é o comportamento correto para uma mudança de regra.

**Padrão assumido:** manter o arredondado.

## 16. 🟢 Coluna TOP — trocar heurística por dado

O extrato `Movimento Livros Fiscais` traz duas colunas que a extração usada na
apuração não tinha: **`Tipo Operação`** e **`Descrição (Tipo de Operação)`**.
São 75 TOPs distintos em Julho/2026, e eles nomeiam a operação como ela foi
lançada, em vez de deixá-la ser inferida de CFOP + prefixo do produto.

Confere exato com o que o motor hoje deduz por heurística:

| TOP | Descrição | Linhas | ICMS (R$) | Hoje o motor deduz de |
|---|---|---|---|---|
| 2310 | CIAP | 3 | 24.903,24 | CFOP 1604 |
| 2316 + 3216 | NF Complementar ICMS | 6 | 17.490,73 | produto 701000075 |
| 3217 | NF Complementar Preço | 22 | 2.181,70 | produto 401002106 |
| 49 · 51 · 59 | Fretes | 1.652 | 891.356,65 | espécie CT-e + descrição |
| 3297 + 8888 | Quebras (Acerto de Estoque) | 17 | — | CFOP 5927 |
| 2108 | Compra de Embalagem | 4 | 23.475,30 | prefixo `2` do produto |
| 2103 | Compra de MP | 214 | 368.978,94 | prefixo `1` do produto |
| 21200-21202 | Retorno de Industrialização | 106 | 16.464,48 | CFOP 2903/2906 |

**Proposta:** usar o TOP como sinal primário de classificação, mantendo a
heurística atual como fallback para extrações que não tenham a coluna.

**Pergunta:** a extração com TOP passa a ser o padrão mensal? Se sim, o cadastro
de produtos encolhe muito — ele deixa de ser a fonte da categoria e vira só
exceção.
