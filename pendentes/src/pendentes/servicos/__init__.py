"""O motor de serviços: o confronto do ASIS com os lançamentos do Sankhya.

A pergunta que este módulo responde é *quais notas de serviço emitidas contra
a Hinove ainda não foram lançadas* — e, para cada uma, qual pedido de compra e
qual requisitante estão por trás dela.

Não existe chave natural entre as duas fontes. O ASIS (Portal Nacional) não
traz código de parceiro do ERP, e não há chave de acesso nem dígito
verificador em comum. Por isso o confronto é uma **cascata de quatro
procedimentos**, da chave mais forte para a mais fraca, com **consumo**: cada
lançamento casa com no máximo uma nota, e cada nota com no máximo um
lançamento.

| # | Chave | Força |
|---|---|---|
| 1 | número da nota + CNPJ do prestador | forte |
| 2 | número da **RPS** + CNPJ, contra número da nota do Sankhya | forte |
| 3 | CNPJ + valor | fraca |
| 4 | número da nota + valor, **sem CNPJ** | fraca — sai marcada para revisão |

**O laço externo é o passo, nunca a nota.** Cada procedimento varre todas as
notas antes de o seguinte começar. Inverter os dois laços é a armadilha nº 1
do porte: uma chave fraca consumiria um lançamento que pertence a um match de
chave forte, e o resultado passaria a depender da ordem das linhas no
relatório. O módulo `confronto` é quem garante isso, e há teste que falha se
alguém inverter.

| Módulo | O que resolve |
|---|---|
| `colunas` | o nome de cada coluna lida e a ordem exata das quatro abas |
| `fontes` | as matrizes viram nota, lançamento e anexo |
| `chaves` | as três chaves do confronto e o índice que consome |
| `confronto` | a segregação das canceladas e a cascata **por passos** |
| `enriquecimento` | cadastro de parceiro, de-para de filial, pedido mais recente |
| `vinculo` | a nota × o pedido da Conferência de Serviços |
| `inversa` | `Sem Correspondencia ASIS` — o que o ASIS deixou de capturar |
| `execucao` | o pipeline de ponta a ponta e o que a tela mostra |
"""
