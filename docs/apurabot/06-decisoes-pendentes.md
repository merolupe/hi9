# Apurabot — Decisões pendentes com a Gerência Fiscal/Tributária

> Perguntas que **precisam de resposta do time fiscal** antes (ou durante) a
> construção do motor. Cada uma está com o número real de Julho/2026 ao lado,
> para que a resposta seja objetiva.
> Nenhuma delas bloqueia o início do desenvolvimento — todas têm um
> comportamento-padrão assumido, que fica registrado aqui.

---

## 1. 🔴 Rio Brilhante — critério do crédito presumido

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

## 2. 🔴 MS — base do estorno proporcional

Corumbá e Rio Brilhante são rotulados igualmente como "Estorno Proporcional" na
aba ESTORNO, mas **os números seguem lógicas diferentes**:

**Corumbá** — segue a mesma fórmula de SP (estorno do que excede 4%):

| Carga | Valor contábil | ICMS | Estorno pela fórmula de SP |
|---|---|---|---|
| 4% | 360.618,45 | 14.424,02 | — |
| 7% | 84.000,00 | 5.880,00 | 2.520,00 |
| 12% | 218.006,40 | 26.160,77 | 17.440,51 |
| | | **46.464,79** | **19.960,51** |

Estorno lançado: **19.961,55** — diferença de R$ 1,04.

**Rio Brilhante** — estorna praticamente 100% do crédito das entradas com carga 4%:

| Carga | ICMS | Tratamento aparente |
|---|---|---|
| 4% | 331.307,32 | estornado quase integralmente |
| 7% | 24.044,44 | mantido |
| 12% | 112.404,72 | mantido |
| CIAP | 2.146,57 | mantido |
| | **469.903,05** | estorno lançado **331.236,11** · mantido **138.666,94** |

`331.307,32 − 331.236,11 = 71,21`, exatamente o mesmo valor que falta no
crédito mantido. Ou seja, houve um deslocamento manual de R$ 71,21 entre estorno
e crédito mantido.

**Pergunta:** confirmar que a regra de MS é (a) estorno integral do crédito das
entradas beneficiadas a 4% no estabelecimento que tem o benefício (RB), e
(b) estorno do excedente sobre 4% no estabelecimento sem benefício (Corumbá) —
e o que originou os resíduos de R$ 1,04 e R$ 71,21.

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
