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
| **0.1.19** | **03/09/2026** | **A rodada de agosto: conferência por carga efetiva, percentual da regra, totais em fórmula, frete de custo em MS** |

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
