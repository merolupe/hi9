# Apurabot — Decisões pendentes

> Perguntas tributárias que o motor ainda não tem resposta. Cada uma traz o
> **comportamento-padrão assumido** enquanto a resposta não vem — nenhuma bloqueia
> o desenvolvimento, e todas são parâmetro, não código.
>
> A regra já decidida está em
> [04 — Matriz de regras de ICMS](04-matriz-de-regras-icms.md).

---

## 1. 🟢 PR — mantém 100% e acumula o saldo credor

*Pontos de Atenção* dizia "Créditos PR mantêm 100% s/ saídas diferidas", e a aba
ESTORNO mostrava Londrina com crédito de frete marcado como mantido — mas sem
saída tributada não havia contra o que confrontar.

**Respondida em 02/09/2026 pela Gerência Fiscal/Tributária: mantém 100%, e o
saldo credor se acumula.** É o que `regimes.yaml` já fazia; o que faltava era a
confirmação de que o crédito não se perde por falta de débito.

Deixou de ser irrelevante: Londrina saiu de R$ 13.882,40 em 07/2026 para
R$ 38.384,29 em 08/2026, e o saldo transportado de agosto é a soma dos dois —
R$ 52.266,69.

## 2. 🟢 Itens fora do processo produtivo para o DIFAL

O DIFAL usa o ICMS **do XML** nas compras de itens que não integram o processo
produtivo.

**Pergunta:** qual é o critério de "não integra o processo produtivo" — CFOP
(1556/2556 uso e consumo), grupo do produto (prefixo do código), ou lista
mantida à parte?

**Padrão assumido:** CFOP de uso e consumo + ativo, parametrizado em
`classificacao.yaml` e ajustável sem alterar código.

## 3. 🟢 Layout dos arquivos de XML e Base de Bens

O Livro Fiscal já está mapeado (ver `03-dicionario-livro-fiscal.md`).
**Faltam exemplos reais** dos outros dois arquivos de entrada. Sem eles, DIFAL e
CIAP ficam no desenho, não na construção.

**Pedido:** enviar um `.xlsx` de exemplo de cada — XML das entradas e Base de Bens.

## 4. 🟢 Aprovação de ajustes manuais

O escopo exige que só ajustes com status **Aprovado** alimentem a apuração, com
responsável e aprovador.

**Pergunta:** quem aprova, e a mesma pessoa pode lançar e aprovar? A ferramenta
deve apenas registrar, ou bloquear o fechamento quando lançador = aprovador?

**Padrão assumido:** registra os dois nomes, permite que sejam a mesma pessoa e
sinaliza no painel de auditoria — sem bloquear.

## 5. 🟢 A tolerância da equalização está frouxa

A tolerância é de **2,5 pontos** e o maior vão entre degraus da régua é de 5
pontos (7→12 e 12→17), ou seja, exatamente o dobro. Na prática, qualquer carga
entre ~1,5% e ~27,5% encaixa em algum degrau e nada é sinalizado.

**Pergunta:** apertar a tolerância para 1,5 ponto? Isso passaria a sinalizar
cargas a mais de 1,5 ponto de qualquer degrau, sem bloquear o fechamento.

**Padrão assumido:** manter 2,5 — apertar sem combinar geraria pendências novas
no primeiro fechamento.

## 6. 🟢 Corumbá — a segregação existe para o benefício, não para a GIA

A segregação por atividade é homologada contra a GIA de Rio Brilhante. Corumbá
usa o mesmo mapa porque a UF é a mesma, mas não havia GIA de Corumbá para
conferir.

**Respondida em 02/09/2026: as duas GIAs estão dispensadas.** A segregação é
feita apenas para dimensionar o benefício fiscal, e o benefício é só de Rio
Brilhante — cujo mapa está conferido ao centavo contra a GIA retificadora de
25/08/2026.

Em Corumbá a segregação continua saindo, porque o mapa é da UF e a ferramenta
não classifica por estabelecimento. Ela é informativa: não dimensiona benefício
nenhum e não alimenta declaração nenhuma.

## 7. 🟡 MS — o que acontece quando o centralizado tem saldo credor?

Corumbá transfere o **saldo devedor** para Rio Brilhante, por lançamento de
ajuste no Registro de Apuração — é o que o motor faz hoje, e o valor fecha com
a linha 002 da centralizadora.

O que não está evidenciado é o caminho inverso: nenhuma competência observada
teve Corumbá com saldo credor.

**Perguntas:** o crédito também vai para Rio Brilhante, ou fica em Corumbá e é
transportado para o período seguinte? Existe ato formal de centralização em MS
que discipline isso?

**Padrão assumido:** só o saldo devedor se transfere; o crédito fica no
estabelecimento (`transfere: saldo_devedor` em `filiais.yaml`).

## 8. 🟡 Enquadramento: é do produto ou do fornecedor?

Matéria-prima não enquadrada é `produto_quimico`, e o não enquadramento vem do
produto **ou** do fornecedor (ver `04-matriz-de-regras-icms.md`, item 2.1). Para
cada item hoje cadastrado como produto químico, falta saber **qual dos dois
motivos** se aplica.

A diferença é prática: se o motivo é o produto, a categoria vale sempre; se é o
fornecedor, o mesmo produto comprado de um fabricante de fertilizante enquadrado
é `materia_prima`. Já se observa o mesmo fornecedor vendendo item enquadrado e
item não enquadrado, então não dá para decidir pelo fornecedor sozinho.

**Pergunta:** para cada produto químico do cadastro, o não enquadramento é do
produto ou do fornecedor?

**Padrão assumido:** cadastro por produto. O cadastro já aceita a chave por
produto + fornecedor, então mudar é editar o parâmetro.

## 9. 🟢 CFOP 2152 — o crédito é sempre indevido

A transferência interestadual para comercialização chega em Corumbá com ICMS
destacado, e a saída correspondente de Guará sai com débito. Depois da ADC 49 a
transferência entre estabelecimentos do mesmo titular não gera imposto, então o
crédito da entrada é indevido.

**Respondida em 02/09/2026: é sempre indevido** — e a operação **não deveria
acontecer**. O destaque será parametrizado na origem para deixar de sair.

O motor já tratava assim, separando o crédito indevido do estorno por regra:
R$ 14.424,02 em 07/2026 e R$ 2.560,56 em 08/2026. A queda é consistente com a
correção estar em andamento.

## 10. 🟢 MICROBIO e HINOVE FERTILIZANTES ESPECIAIS

Os dois carregam saldo credor próprio.

**Pergunta:** entram no escopo do Apurabot ou continuam controle à parte?

**Padrão assumido:** fora do escopo — não estão em `filiais.yaml`.

## 11. 🟢 SP — lançamento fecha o mês, a NF-e vem depois

**Respondida em 02/09/2026**, sobre o Registro de Apuração de 06/2026 da Filial
Guará, que mostra os dois sentidos chegando à centralizadora como lançamento:

| Linha | Valor | Redação no documento |
|---|---|---|
| 006 Outros Créditos | 455.859,54 | recebimento de saldo credor — estabelecimento centralizador |
| 002 Outros Débitos | 1.022,71 | recebimento de saldo devedor — estabelecimento centralizador |

**O mecanismo é o lançamento de ajuste, e a NF-e continua sendo emitida.** Não
são alternativas: a nota nasce do resultado da apuração e não retroage, então
sai depois do fechamento e vai escriturada na competência seguinte. Quem fecha
a competência é o lançamento. Por isso `emite_nfe` é campo próprio em
`filiais.yaml`, e não o contrário de `mecanismo`.

**O crédito transferido tem teto: o saldo devedor da centralizadora.** O
documento evidencia — a linha 006 trouxe exatamente o saldo devedor de Guará, e
o mês fechou com as linhas 011 e 014 em zero. O que passa do teto fica onde
está. O saldo devedor não tem teto: a centralizadora assume a dívida do grupo
para recolher de uma vez só.

**Fica em aberto uma ponta:** com dois centralizados credores e dívida para um
só, o teto se esgota na ordem do cadastro — hoje é o primeiro do arquivo que
transfere. Nenhuma competência observada chegou aí. Quando chegar, a ordem tem
que ser decidida em vez de herdada.

## 12. 🟡 Local de expedição — qual relatório e como cruzar?

Produção e revenda não se distinguem só pelo produto e pelo CFOP: quando a
mercadoria **sai de armazém geral industrializador**, e não da fábrica de MS, a
operação é revenda — não houve produção na fábrica.

Essa informação não está no Livro Fiscal. Vem de relatório à parte, cruzado com
o movimento, e hoje o motor não a consome: ele decide a atividade por descrição
e CFOP (ver `04-matriz-de-regras-icms.md`, item 4.3).

**Perguntas:** qual é o relatório, qual a sua chave de cruzamento com o Livro
(nota, item, pedido?) e ele cobre todas as saídas ou só as expedidas por
terceiro?

**Padrão assumido:** nenhum — o cruzamento não está implementado. Enquanto não
estiver, uma saída de armazém geral industrializador é classificada pela
descrição e pelo CFOP, e pode ficar como produção quando é revenda.

## 13. 🟢 CFOP 2923 — resolvida: é sempre comercial

O CFOP 1923/2923 é a entrada de mercadoria recebida do vendedor remetente em
venda à ordem. Na prática da empresa, ele documenta **transmissão de
propriedade de mercadoria depositada em armazém**, em referência a notas de
transferência entre unidades.

A dúvida era se o destino da mercadoria deveria decidir a atividade, como no par
1151/1152. A segregação não é detalhe: é ela que dimensiona o benefício de Rio
Brilhante, que incide só sobre o saldo devedor industrial.

**Respondida em 02/09/2026 pela Gerência Fiscal/Tributária: é sempre
comercial**, independentemente do produto ou da nota de transferência
referenciada. Cadastrado em `regimes.yaml`, bloco `atividades.ms.por_cfop`.

É coerente com a contraparte: o 5934/6934 — remessa simbólica de mercadoria
depositada em armazém — já era comercial. Os dois lados da mesma operação ficam
na mesma atividade.

Efeito medido em 08/2026: os R$ 55.369,48 de crédito das três linhas de Rio
Brilhante saem de `SEM REGRA` para Comercial. O crédito industrial não muda, e
**o benefício fiscal fica idêntico** — R$ 442.528,58.

## 14. 🟢 Saldo credor de abertura — respondida para 07/2026

A linha 009 do Registro é o crédito que veio do mês anterior. Não está no Livro
Fiscal e por isso é declarada em `parametros/saldos.yaml`.

**Respondida em 02/09/2026, pelo Registro de Apuração de 06/2026 da Filial
Guará:** a linha 014 de junho fecha em **R$ 0,00**, e a linha 009 dele também.
Nenhum estabelecimento do grupo abriu julho com saldo credor, e o parâmetro
declara a competência com a lista vazia — que é a declaração de que todos abrem
zerados, e não a ausência de declaração.

Junho fechou em zero porque a centralização de SP transferiu para Guará
exatamente o crédito de que ele precisava. Ver
[05 — Achados](05-achados-julho-2026.md), item 15.

**Fica em aberto o destino dos R$ 107.620,97** que separam a apuração de julho
de Guará (R$ 2.107.543,31) do que o Registro de 07/2026 declara
(R$ 2.215.164,28). Não é abertura: é ajuste da competência, linha 002, 006 ou
007. Como é crédito líquido, o candidato natural é a **linha 006** — em junho
ela trouxe o recebimento de saldo credor da centralização. Confirmar depende da
folha 3 do Registro de 07/2026.

Isso não bloqueia nada: o valor entra pela aba `AJUSTES` quando for declarado, e
até lá o registro de Guará mostra `AGUARDA AJUSTE` nas linhas 002, 006 e 007.

**Segue em aberto:** quando o estabelecimento incentivado abrir o mês com saldo
credor, esse crédito entra no cálculo do benefício de MS ou fica fora dele,
abatendo só o imposto a recolher? Hoje o crédito presumido de Rio Brilhante é
dimensionado sobre o saldo devedor da atividade industrial, sem a abertura, e a
abertura só limita quanto se deduz, pela aritmética do livro — a linha 012 não
passa da 011. Nenhuma competência observada tem Rio Brilhante abrindo o mês com
saldo credor, então a hipótese não foi testada contra documento.

**Padrão assumido:** fica fora do cálculo e abate só a dedução.

## 15. 🟡 Crédito outorgado de MS — o controle não está na ferramenta

O benefício de Rio Brilhante tem um **estoque** de crédito outorgado, controlado
à parte pelo time fiscal sob o código de ajuste **MS090004** — "Apropriação de
crédito outorgado com o fim de abatimento de débitos". O controle é uma conta
corrente:

```
saldo anterior  +  recebido por transferência  −  utilizado no período
                                              =  saldo a transportar
```

Em 07/2026: 91.845,01 + 62.720,00 − 68.473,36 = **86.091,65** a transportar.

Os créditos recebidos por transferência vêm de nota de ICMS emitida pela
ADECOAGRO, dimensionada em **30% do saldo devedor da apuração centralizada de
Rio Brilhante e Corumbá**.

**Julho não serve de referência para esse percentual.** A competência usou mais
do que os 30% de propósito, para abater débito e evitar a saída de caixa —
decisão da Gerência Fiscal/Tributária, não desvio de regra. Reconciliar a base
dos 30% contra julho leva a conclusão errada.

**O que falta:**

1. **A base e a competência dos 30%.** Se o percentual incide sobre o saldo
   devedor do mês corrente ou do anterior — a nota chega depois do fechamento —
   ainda não foi confirmado.
2. **Onde o estoque mora.** Ele atravessa a competência, como o saldo credor, e
   hoje não existe na ferramenta. O lugar natural é `parametros/saldos.yaml`
   ganhar um bloco próprio, com o utilizado saindo calculado — é a linha 012 do
   Registro, limitada ao que o estoque tem.

**Padrão assumido:** nenhum. O crédito outorgado entra hoje como ajuste
declarado na aba `AJUSTES`, com o valor que o time fiscal informar. A ferramenta
não controla o estoque nem confere se o utilizado cabe nele.
