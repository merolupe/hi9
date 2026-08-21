# Apurabot — Decisões pendentes com a Gerência Fiscal/Tributária

> Perguntas que **precisam de resposta do time fiscal** antes (ou durante) a
> construção do motor. Cada uma está com o número real de Julho/2026 ao lado,
> para que a resposta seja objetiva.
> Nenhuma delas bloqueia o início do desenvolvimento — todas têm um
> comportamento-padrão assumido, que fica registrado aqui.

---

## 1. 🔴 Rio Brilhante — critério do crédito presumido

> **Em espera (21/08/2026):** deixada em aberto até a chegada do Termo de Acordo.

**A estrutura da regra está confirmada nos dados.** *Pontos de Atenção* diz:
intra 67% e inter 80% de crédito sobre o saldo devedor. Reproduzindo:

| | Valor (R$) |
|---|---|
| Débito de saída INTRA (MS→MS) | 101.354,35 |
| Débito de saída INTER (MG, SP, PR) | 404.637,06 |
| Débito total | 505.991,41 ✓ confere com a apuração |
| Crédito mantido | 138.666,94 |
| Saldo devedor | 367.324,47 |
| **67% × SD intra + 80% × SD inter** | **284.294,41** |
| **B.F. lançado na apuração de Julho** | **283.766,56** |
| Diferença | 527,85 (0,19%) |

**Pergunta:** como o crédito mantido é rateado entre as saídas intra e
interestaduais? O rateio por débito e o rateio por valor contábil dão o mesmo
resultado (284.294) — para chegar nos 283.766,56 lançados, o rateio teria que
atribuir **17,10%** do crédito às operações internas, e não os 20,03% que a
participação do débito indica.

**Perguntas relacionadas:**
- A remessa para depósito fechado (CFOP 5905, R$ 33.039,71 de débito intra,
  neutralizada por ajuste de crédito de mesmo valor) entra ou sai da base do
  benefício?
- O benefício alcança **todas** as saídas ou só as de **produção própria** de RB?
  *Pontos de Atenção* diz "Saídas com Produção Própria de Rio Brilhante", mas o
  cálculo de Julho só fecha considerando todas as saídas (só produção própria
  daria R$ 213.973,78, R$ 69,8 mil abaixo do lançado).
- Confirmar contra o texto do **Termo de Acordo** — o documento não foi anexado.

**Padrão assumido enquanto não houver resposta:** 67% intra + 80% inter sobre o
saldo devedor total, com crédito rateado pela participação do débito, e o
resultado sinalizado como `A CONFERIR` no painel.

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

## 3. 🟡 Os 0,941176% do escopo não aparecem em Julho/2026

O escopo v1.0 (itens 5.3 e 5.4) determina, para entradas destinadas a MS com
alíquota de 4%, crédito mantido de **0,941176%** — e o mesmo para fertilizante
interno em MS. **Não encontrei esse percentual aplicado na apuração de Julho.**

**Pergunta:** a regra dos 0,941176% está em vigor? Se sim, em quais operações
exatamente, e por que não aparece em Julho/2026?

## 4. ✅ Carga efetiva — régua de valores nominais *(parcialmente respondida)*

O algoritmo de equalização reproduz 99,87% da classificação manual usando a régua
`{4, 7, 12, 17, 18, 19, 20,5, 25}` com a restrição "a carga nominal nunca excede a
alíquota do ICMS" (detalhes em `05-achados-julho-2026.md`).

**Respondido em 21/08/2026 — os 20,5%:** não devem constar na base. Apareceram em
30 CT-e de frete sobre compra de insumos da filial Guará (CFOP 1353 e 1352) e
foram aceitos na apuração manual de Julho/2026.

**Tratamento implementado:** 20,5% sai das cargas homologadas e entra como carga
*tolerada* em `parametros/cargas.yaml`. Na prática:

- a equalização continua reconhecendo o valor, para que a regressão de
  Julho/2026 reproduza o resultado da apuração manual;
- todo documento que cair nessa carga recebe o alerta `CARGA NÃO HOMOLOGADA`,
  apontando para revisão do lançamento na origem;
- o alerta **não bloqueia** o encerramento da competência — é sinalização, não
  impedimento.

**Ainda em aberto:** a régua homologada `{4, 7, 12, 17, 18, 19, 25}` está
completa? Alguma UF ou operação pode gerar carga nominal fora dela?

**Padrão assumido:** régua acima; carga que não encoste em nenhum valor dentro da
tolerância vira pendência `CARGA NÃO EQUALIZADA` em vez de ser arredondada.

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

## 12. 🟡 NBPT BLUE 20% — revenda ou produto químico?

O produto `132010008` (NBPT BLUE 20%) entra com **CFOP 2102**, compra para
comercialização, o que apontaria para **revenda** e crédito integral. Mas é um
aditivo inibidor de urease, o que apontaria para **produto químico** e estorno
do que excede 4%.

Em Julho são 3 linhas, R$ 30.660,00 de ICMS, a 7% e a 12% — o que dá
**R$ 12.978,00 de estorno** se for químico e **zero** se for revenda.

**Pergunta:** qual das duas?

**Padrão assumido:** produto químico, marcado como não homologado no cadastro.

## 13. 🟡 Complemento de preço — 22 linhas sem regra

O produto `401002106` (COMPLEMENTO DE PREÇO) aparece em **22 linhas de saída**
com CFOP 6102, somando **R$ 2.181,70** de ICMS. Nenhuma regra escrita cobre o
caso, então hoje ele é a **única pendência** que bloqueia o encerramento de
Julho/2026.

**Pergunta:** complemento de preço de venda segue a mesma regra da venda que ele
complementa, ou tem tratamento próprio?

**Padrão assumido:** nenhum — fica como `SEM REGRA`, que é o comportamento
correto para o que não tem regra.

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
