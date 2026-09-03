# Apurabot — versões

A versão aparece em três lugares: no cabeçalho da CLI, no rodapé da janela
("Procedência") e na aba `RESUMO` da planilha. Serve para responder uma
pergunta prática: **o número que estou olhando saiu de qual versão da regra?**

A numeração é por **entrega**, não por commit. Cada linha abaixo é um conjunto
de mudanças que o time fiscal viu funcionar.

| Versão | Data | O que entrou |
|---|---|---|
| 0.1.1 | 20/08/2026 | Mapeamento do Livro Fiscal, arquitetura e plano de execução |
| 0.1.2 | 21/08/2026 | Ingestão, equalização de carga e classificação da operação |
| 0.1.3 | 21/08/2026 | Motor de estorno por regime |
| 0.1.4 | 21/08/2026 | MS corrigido pela apuração individualizada de Corumbá |
| 0.1.5 | 21/08/2026 | Julho fecha sem pendência; o Termo de Acordo responde o benefício de Rio Brilhante |
| 0.1.6 | 21/08/2026 | O extrato com TOP passa a ser o formato padrão de entrada |
| 0.1.7 | 24/08/2026 | Benefício fiscal de Rio Brilhante pelo Termo de Acordo n. 1.190/2018 |
| 0.1.8 | 25/08/2026 | Motor de MS conferido contra a GIA retificadora de 07/2026 |
| 0.1.9 | 26/08/2026 | Centralização e transferência de saldo |
| 0.1.10 | 27/08/2026 | Aba REGISTRO, aba APURAÇÃO EFETIVA e a transferência como instrução |
| 0.1.11 | 28/08/2026 | A interface passa a ser o navegador, servido pela própria máquina |
| 0.1.12 | 28/08/2026 | A conferência agrega por produto, como a tabela dinâmica manual |
| 0.1.13 | 01/09/2026 | Saldo com o sinal do caixa; entrega sem passo de instalação |
| 0.1.14 | 01/09/2026 | Pendência de atividade na planilha; o resumo diz o período do livro |
| 0.1.15 | 01/09/2026 | Cadastros que a rodada de agosto pediu: devolução de venda, complemento de ICMS e as sete filiais |
| 0.1.16 | 01/09/2026 | Saldo credor de abertura: a conta gráfica atravessa a virada do mês |
| 0.1.17 | 02/09/2026 | Ajustes declarados pelo próprio arquivo; painel do ano |
| 0.1.18 | 02/09/2026 | Centralização de SP homologada, DIFAL na conta gráfica e CFOP 2923 comercial |
| 0.1.19 | 03/09/2026 | A rodada de agosto: conferência por carga efetiva, percentual da regra, totais em fórmula, frete de custo em MS |
| 0.1.20 | 03/09/2026 | Decisão nº 17 respondida: almoxarifado e venda conjunta são despesa; julho não é retificado |
| 0.1.21 | 03/09/2026 | A conferência enxuta: uma coluna de percentual, sem CHECK, categoria com nome legível |
| 0.1.22 | 03/09/2026 | A centralização passa a lançar as duas pontas: quem transfere zera o próprio Registro |
| **0.1.23** | **03/09/2026** | **O saldo mostrado passa a ser o final, o mesmo do Registro, em todo lugar** |

## 0.1.19 — o que mudou, em detalhe

**A conferência agrupa sempre pela carga efetiva equalizada.** Antes MS agrupava
pela alíquota e SP pela carga, e a mesma coluna trazia duas grandezas. A
alíquota continua sendo a chave do cálculo em MS — ela aparece no `% da regra`.

**Duas colunas de percentual, no lugar de uma.** `% da regra` é o nominal do
regime, redondo: `(carga − 4%) ÷ carga` em SP, `1 − 4 ÷ alíquota` em MS.
`% efetivo` é `ICMS a estornar ÷ crédito`, que em SP sai quebrado porque o
estorno incide sobre o valor contábil.

**Os totais deixaram de ser valor colado.** Subtotais, linhas de CFOP e TOTAL
saem como `SUM` das linhas que os compõem. `ICMS a apropriar`, `% efetivo` e
`CHECK` são fórmula em toda linha. O mesmo nas abas `REGISTRO` (linhas 004, 008
e 010 do resumo, e os totais de entradas e saídas) e `APURAÇÃO POR FILIAL`.

**O fechamento por classificação ganhou a carga efetiva**, ponderada pelo valor
contábil de cada classificação.

**Em MS, frete de custo é produção.** Compra de insumos e transferência/remessa/
retorno com "(Custo)" na descrição vão para industrial; frete de venda é
comercial. A regra do frete de transferência vale **de 08/2026 em diante**,
porque a GIA de 07/2026 o classificou como comercial — ver decisão pendente
nº 17.

**ÁCIDO FOSFÓRICO RAFINADO passou a matéria-prima.** Entra com base reduzida a
4%, então a correção não muda valor de competência nenhuma.

**O painel do ano foi para o fim da página**, e um respiro entre os blocos da
`APURAÇÃO EFETIVA`.

## 0.1.20 — a decisão nº 17, respondida

**"Fretes sobre Compras (Almoxarifado)" e "Fretes sobre Transf/ Retorno - Venda
conjunta" são despesa, e portanto comerciais.** As duas já caíam em comercial
pela atividade do CFOP, então **nenhum número mudou** — o que mudou é que agora
elas estão no parâmetro como regra explícita. Vêm antes das regras de custo na
lista, porque a ordem é a de avaliação.

**Julho não é retificado.** A vigência da regra do frete de transferência fica
em 2026-08-01. O que julho declarou permanece.

## 0.1.21 — a conferência enxuta

**Uma coluna de percentual, não duas.** Ficou `% do crédito estornado` =
`ICMS a estornar ÷ Vlr. ICMS`. A `% da regra` saiu: ela ficava vazia nas linhas
de CFOP que misturam cargas — em Guará, 6 dos 17 CFOPs —, e meia coluna
preenchida confunde mais do que informa. O nominal da regra continua em
`04-matriz-de-regras-icms.md`, item 3.1.

**A coluna CHECK saiu.** A identidade que ela mostrava — `a estornar +
a apropriar = crédito` — é garantida por teste no motor, em todas as linhas de
todos os estabelecimentos. Não precisa de uma célula que alguém confira. Linha
que não fechar sai inteira em vermelho.

**A carga efetiva do complemento de ICMS aparece.** No bloco `CRÉDITOS` a carga
de cada classificação é a média ponderada pelo valor contábil; o complemento
não tem contábil, só base e imposto, e a célula saía vazia. Agora a ponderação
cai para o ICMS quando não há contábil — o complemento mostra os 4% que sempre
teve.

**A operação vem com nome de gente.** `frete_transferencia` na conferência é
"Frete de Transferência"; `materia_prima` é "Matéria-Prima". A `BASE TRATADA`
continua com o nome interno de propósito — é por ele que a ferramenta relê o
próprio arquivo.

## 0.1.22 — a centralização lança as duas pontas

**Quem transfere também lança.** A centralizadora recebia o saldo na linha 002,
mas o centralizado não se desfazia dele: fechava com a linha 013 devendo o
mesmo valor que ela já tinha assumido. Quem lesse os dois Registros via o grupo
pagando duas vezes.

Agora o centralizado lança na linha oposta, com a redação do ERP:

```
Corumbá   006  45.695,15  Transferência de saldo devedor para
                          estabelecimento centralizador       →  013 = 0,00
Rio Brilh 002  45.695,15  Recebimento de saldo devedor —
                          estabelecimento centralizador       →  013 = 460.870,70
```

O saldo do grupo não mudou; o que mudou é que ele aparece uma vez só. Em SP,
Registro passa a fechar em 013 = 0,00 e Guará recebe os 209.981,15 na 002.

A referência é o Registro de 07/2026 de Corumbá, emitido pelo ERP: linha 006 =
99.412,10, com essa mesma redação, e 013 = 0,00.

**Os dois sentidos.** O lançamento é simétrico: o centralizado que transfere
saldo credor debita na 002, e a centralizadora o credita na 006 — que é o que o
Registro de 06/2026 de Guará mostra, com 455.859,54 recebidos.

**As linhas 011 a 014 saem arredondadas ao centavo.** O documento fiscal não
tem casa abaixo dela, e quem transferia o saldo inteiro fechava em 4,6e-10 em
vez de zero.

## 0.1.23 — um saldo só, o do Registro

O mesmo estabelecimento tinha **dois saldos diferentes** no mesmo arquivo:

```
tabela APURAÇÃO POR FILIAL   Guará  1.980.927,86
Registro de Guará, linha 014        1.770.946,71
```

O primeiro era o saldo individual, antes de receber a centralização; o segundo,
o final. O bloco "Saldo credor" prometia ser a linha 014, mostrava o individual
— e mandava cadastrá-lo em `saldos.yaml`. Cadastrar o número errado abriria
setembro com R$ 209.981,15 de crédito que não existe.

**Agora `filial.saldo` é o final**, o mesmo que o Registro daquele
estabelecimento fecha. Registro-SP e Corumbá aparecem em 0,00, como nos
documentos deles; Rio Brilhante em −460.870,70; Guará em 1.770.946,71.

O saldo antes de centralizar continua acessível como `saldo_individual` e
aparece no bloco de Centralização, onde faz sentido: "Saldo próprio da
centralizadora", "HINOVE (REGISTRO): saldo −209.981,15 → transfere".

**O TOTAL "a recolher" passou a somar as filiais.** Saía 0,00 porque calculava
`max(−saldo do grupo, 0)`, e o grupo é credor. O caixa de agosto é R$ 460.870,70.
