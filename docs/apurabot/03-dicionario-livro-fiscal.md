# Apurabot — Dicionário do Livro Fiscal (Sankhya)

O Apurabot lê **dois layouts** de extração. Um teste prova que os dois produzem
apuração idêntica, centavo a centavo.

| Extração | Colunas | Cabeçalho | Situação |
|---|---|---|---|
| **Movimento Livros Fiscais** | 66 | linha 3 | **Padrão** |
| Extração da apuração | 52 | linha 1 | Legado — a que a apuração manual usava |

A ingestão procura o cabeçalho nas 10 primeiras linhas e valida 14 colunas
essenciais. Se o Sankhya mudar o layout, ela falha com a lista do que faltou.

## Por que o extrato novo é melhor

Ele traz três coisas que o antigo não tinha:

| Coluna | Para quê |
|---|---|
| **`Tipo Operação` (TOP)** e `Descrição (Tipo de Operação)` | Nomeia a operação **como ela foi lançada**, em vez de deixá-la ser inferida de CFOP + prefixo do produto |
| `Observação` | Liga o complemento de preço à nota complementada (*"COMPLEMENTO DE PREÇO REFERENTE A NF 57081"*) |
| `Vlr. DIFAL UF Remet.` e `Vlr. DIFAL UF Destino` | Base para a Entrega 5 |

E inclui os **documentos cancelados**, que o extrato antigo filtrava. O motor os
descarta na ingestão, mas tê-los na base permite o controle de integridade
"documentos cancelados" que o escopo pede.

## Colunas essenciais

Sem estas o motor não roda:

`Nro único Nota` · `Nome Fantasia (Empresa)` · `Dt. do movimento` · `CFOP` ·
`Cód. de tributação` · `Vlr. contábil` · `Base do ICMS` · `Alíquota ICMS` ·
`Vlr. do ICMS` · `UF de Origem` · `UF de Destino` · `Entrada/Saída` ·
`Espécie do documento` · `Produto`

## As colunas que o motor usa

| Coluna | Uso no Apurabot |
|---|---|
| **Nro único Nota** | Chave interna do documento; agrupa os itens |
| **Nome Fantasia (Empresa)** | Estabelecimento apurado |
| **Dt. do movimento** | Define a competência |
| **CFOP** + Descrição da CFOP | Classificação da operação e exceções (quebra, devolução, retorno) |
| **Cód. de tributação (CST)** | Apoio à relevância; o discriminante real é ICMS ≠ 0 |
| **Produto** | O prefixo indica a categoria: `1` produto · `2` embalagem · `6` ativo · `7` frete |
| **Descrição (Produto)** | Nos CT-e, traz a **finalidade do frete** |
| **Vlr. contábil** | Base do estorno em SP |
| **Base do ICMS** | `ICMS ÷ base = alíquota exata` |
| **Alíquota ICMS** | Teto da carga nominal na equalização |
| **Vlr. do ICMS** | Crédito, débito e base do estorno em MS |
| **UF de Origem / Destino** | Intra × interestadual — decide o adicional de 13% do benefício de RB |
| **Entrada/Saída** | Separa crédito de débito |
| **Espécie do documento** | `NF` ou `CT` — separa mercadoria de frete |
| **Dt. Cancelamento** | Preenchida = documento excluído da apuração |
| **Chave NF-e** | Cruzamento com o XML no DIFAL |
| **Tipo Operação (TOP)** | Operação como lançada — ver seção abaixo |
| **Observação** | Referência da nota complementada |

Colunas de IPI, ST, FCP, cidades de CT-e, conta contábil e contatos são lidas e
preservadas na base tratada para rastreabilidade, mas não entram no cálculo de
ICMS.

## Estabelecimentos

| Estabelecimento | UF | Regime |
|---|---|---|
| HINOVE (FILIAL GUARÁ) | SP | Equilíbrio fiscal — **centralizadora** |
| HINOVE (REGISTRO) | SP | Equilíbrio fiscal — centralizado |
| HINOVE (MATRIZ) | SP | Equilíbrio fiscal — centralizado |
| HINOVE (RIO BRILHANTE) | MS | Estorno + **benefício fiscal (Termo de Acordo 1.190/2018)** |
| HINOVE (CORUMBÁ- MS) | MS | Estorno proporcional |
| HINOVE (BARRA DO GARÇAS - MT) | MT | Diferimento — estorna 100% |
| HINOVE (LONDRINA) | PR | Diferimento — mantém 100% |

> O nome aparece como `HINOVE  (REGISTRO)` (dois espaços) e `HINOVE (CORUMBÁ- MS)`
> (sem espaço antes de `MS`). A normalização compara os nomes ignorando espaçamento.

## Regra de relevância para ICMS

O discriminante real é **ICMS diferente de zero**, não o CST. Na prática isso
captura linhas de CST `00`, `20` e `90`, e deixa de fora as de CST `40`, `41`,
`50`, `51` e `60`, que não têm ICMS.

**Sobre o CST `90`:** a esmagadora maioria vem com ICMS zero e sai. As que ficam
são de apenas dois tipos:

| Tipo | CFOP | TOP |
|---|---|---|
| Lançamento de crédito de ativo (CIAP) | 1604 | 2310 |
| Devolução de compra de uso e consumo | 5556 | 3001 |

CST 90 não é uma categoria tributária a tratar: é o CST que o Sankhya usa para
esses dois lançamentos, e ambos já têm regra própria na matriz.

> **Cuidado na equalização:** as linhas de CIAP e de complemento de ICMS têm
> **valor contábil e base iguais a zero** com ICMS diferente de zero. A fórmula
> `ICMS ÷ valor contábil` divide por zero nelas. São identificadas antes da
> equalização, pelo bloco `lancamentos_sem_contabil` de `classificacao.yaml`.

## A TOP

A TOP nomeia a operação **como ela foi lançada**, e por isso confere com o que o
motor deduz por CFOP, produto e descrição:

| TOP | Descrição | O motor deduz de |
|---|---|---|
| 2310 | CIAP | CFOP 1604 |
| 2316 · 3216 | NF Complementar ICMS | produto 701000075 |
| 3217 | NF Complementar Preço | produto 401002106 |
| 49 · 51 · 59 | Fretes | espécie CT-e + descrição |
| 3297 · 8888 | Quebras (Acerto de Estoque) | CFOP 5927 |
| 2108 | Compra de Embalagem | prefixo `2` do produto |
| 2103 | Compra de MP | prefixo `1` do produto |
| 21200-21202 | Retorno de Industrialização | CFOP 2903/2906 |

**A TOP não classifica.** Ela é lida, viaja na base tratada e serve para
conferência. Onde ela e a categoria do produto divergem, vale a categoria — o
que não é contradição, e está explicado em `06-decisoes-pendentes.md`, item 16.
