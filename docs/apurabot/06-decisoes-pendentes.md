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

## 7. 🟡 A centralização de MS não está no motor

O Registro de Apuração de Rio Brilhante traz, em Outros Débitos, o *"Recebimento
de saldo devedor - estabelecimento centralizador"*: **Rio Brilhante recebe saldo
devedor de outro estabelecimento de MS.** O projeto tem centralização modelada
apenas em SP, com Guará.

**Perguntas:** quem transfere para RB — Corumbá? A regra é a mesma de SP? Existe
ato formal de centralização em MS?

**Padrão assumido:** o valor entra como ajuste manual, na atividade
Prestacional/Outras, sem regra de centralização automática. A Entrega 4 trata
centralização e vai precisar dessa resposta.

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
