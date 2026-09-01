# Apurabot — Decisões pendentes

> Perguntas tributárias que o motor ainda não tem resposta. Cada uma traz o
> **comportamento-padrão assumido** enquanto a resposta não vem — nenhuma bloqueia
> o desenvolvimento, e todas são parâmetro, não código.
>
> A regra já decidida está em
> [04 — Matriz de regras de ICMS](04-matriz-de-regras-icms.md).

---

## 1. 🟡 PR — mantém 100% ou não credita?

*Pontos de Atenção* diz "Créditos PR mantêm 100% s/ saídas diferidas", e a aba
ESTORNO mostra Londrina com crédito de frete marcado como mantido — mas o
totalizador da mesma aba zera o crédito mantido de Londrina, e no resultado final
PR aparece só com o saldo credor anterior.

**Pergunta:** o crédito de PR é mantido e acumulado como saldo credor, ou é
estornado?

**Padrão assumido:** mantido e acumulado, conforme *Pontos de Atenção*.

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

## 6. 🟡 Corumbá — a segregação por atividade não tem documento

O mapa de atividades de MS foi conferido contra os documentos de **Rio
Brilhante**. Corumbá usa o mesmo mapa, porque a UF é a mesma e a GIA de MS é a
mesma — mas não há GIA de Corumbá que confirme a segregação dela.

**Pergunta:** Corumbá também declara GIA segregada por atividade? Se sim, é
possível enviar uma para fechar a conferência?

**Padrão assumido:** aplicar o mesmo mapa e marcar como não conferido.

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

## 9. 🟡 CFOP 2152 — o crédito é sempre indevido?

O crédito de transferência interestadual recebida (CFOP 2152) não é apropriado
nem estornado: fica em parcela própria (ver `04-matriz-de-regras-icms.md`,
item 4.2).

**Pergunta:** isso vale para toda transferência interestadual recebida, ou foi
específico de uma operação?

**Padrão assumido:** vale sempre, com a regra marcada `homologado: false` em
`regimes.yaml`.

## 10. 🟢 MICROBIO e HINOVE FERTILIZANTES ESPECIAIS

Os dois carregam saldo credor próprio.

**Pergunta:** entram no escopo do Apurabot ou continuam controle à parte?

**Padrão assumido:** fora do escopo — não estão em `filiais.yaml`.

## 11. 🟡 SP — o que o centralizado transfere para Guará?

A centralização está calculada, mas a regra de transferência vem do escopo
funcional v1.0 e não foi confirmada.

**Perguntas:**

1. O estabelecimento centralizado transfere o **saldo integral** (devedor e
   credor), só o **saldo devedor**, ou só o **saldo credor**?
2. Qual CFOP a NF-e de transferência usa? O parâmetro hoje sugere 5601, 5602 e
   5605.

A segunda pergunta tem consequência prática: é esse CFOP que a aba
TRANSFERÊNCIAS instrui a emitir, e é por ele que a conferência da competência
seguinte vai reencontrar a nota.

**Padrão assumido:** `saldo_integral`, com a regra marcada `homologado: false` em
`filiais.yaml`. O relatório avisa que o resultado é rascunho.

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

## 13. 🟡 CFOP 2923 — a transmissão de propriedade em armazém é produção ou revenda?

O CFOP 1923/2923 é a entrada de mercadoria recebida do vendedor remetente em
venda à ordem. Na prática da empresa, ele documenta **transmissão de
propriedade de mercadoria depositada em armazém**, em referência a notas de
transferência entre unidades.

E é aí que fica indefinido. A transferência entre unidades já tem par no mapa —
1151/2151 para industrialização, 1152/2152 para comercialização —, mas o 2923
não distingue: o mesmo código serve para as duas.

**A pergunta não é dispensável.** A segregação por atividade é o que dimensiona
o benefício de Rio Brilhante, que incide só sobre o saldo devedor industrial.
Toda linha de crédito precisa cair em um dos baldes, e a escolha move dinheiro:

| Se o 2923 for… | Benefício de Rio Brilhante |
|---|---|
| Comercial | inalterado |
| Industrial | menor, porque o crédito industrial sobe e abate a base do incentivo |

**Perguntas:** o destino da mercadoria transferida define a atividade, como no
par 2151/2152? Se sim, dá para saber pelo produto, ou só pela nota de
transferência referenciada?

**Padrão assumido:** nenhum — o CFOP não está no mapa, e as linhas caem em
`SEM REGRA`, bloqueando o encerramento. É de propósito: adivinhar aqui aumenta
ou diminui o benefício sem que ninguém tenha decidido.


## 14. 🟡 Saldo credor de abertura — o número de julho e o que ele reduz

A linha 009 do Registro de Apuração é o crédito que veio do mês anterior. Ela
não está no Livro Fiscal e por isso é declarada em `parametros/saldos.yaml`.
Duas coisas ficaram em aberto.

**Primeira: a abertura de 07/2026 da Filial Guará não foi lida de documento.**
Ela é resíduo de conciliação. O Registro de Apuração de 07/2026 emitido pelo ERP
declara R$ 2.215.164,28 na linha 014; sobre o Livro de julho o motor apura
crédito de R$ 4.167.368,77 contra sub total de débito de R$ 2.059.825,46, o que
fecha em R$ 2.107.543,31. A diferença de R$ 107.620,97 é o que a linha 009
precisa ter para o registro fechar — mas ela também caberia nas linhas 002, 006
ou 007, que ninguém declarou.

**Pergunta:** o que a linha 014 do Registro de Apuração de 06/2026 traz para a
Filial Guará? Se for R$ 107.620,97, a abertura está confirmada. Se for outro
número, a diferença é ajuste de apuração e o cadastro muda de lugar.

**Padrão assumido:** R$ 107.620,97 como abertura de 07/2026, marcado
`homologado: false` no parâmetro. É o único arranjo que reproduz o documento
que existe; o que falta é a confirmação de onde o valor nasce.

**Segunda: a abertura reduz a dedução do benefício, ou também a base dele?**
Hoje o crédito presumido de Rio Brilhante é dimensionado sobre o saldo devedor
da atividade industrial, sem a abertura, e a abertura só limita quanto se deduz,
pela aritmética do livro — a linha 012 não passa da 011. Nenhuma competência
observada tem Rio Brilhante abrindo o mês com saldo credor, então a hipótese não
foi testada contra documento.

**Pergunta:** quando o estabelecimento incentivado abre o mês com saldo credor,
esse crédito entra no cálculo do benefício ou fica fora dele, abatendo só o
imposto a recolher?

**Padrão assumido:** fica fora do cálculo e abate só a dedução.
