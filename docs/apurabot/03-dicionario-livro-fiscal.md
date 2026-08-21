# Apurabot — Dicionário do Livro Fiscal (Sankhya)

O Apurabot lê **dois layouts** de extração. Ambos foram conferidos contra
Julho/2026 e produzem apuração idêntica, centavo a centavo.

| Extração | Colunas | Cabeçalho | Situação |
|---|---|---|---|
| **Movimento Livros Fiscais** | 66 | linha 3 | **Padrão a partir de 08/2026** |
| Extração da apuração | 52 | linha 1 | Legado — usada na apuração manual de Julho/2026 |

A ingestão procura o cabeçalho nas 10 primeiras linhas e valida 14 colunas
essenciais. Se o Sankhya mudar o layout, ela falha com a lista do que faltou.

## Por que o extrato novo é melhor

Ele traz três coisas que o antigo não tinha:

| Coluna | Para quê |
|---|---|
| **`Tipo Operação` (TOP)** e `Descrição (Tipo de Operação)` | Nomeia a operação **como ela foi lançada**, em vez de deixá-la ser inferida de CFOP + prefixo do produto |
| `Observação` | Liga o complemento de preço à nota complementada (*"COMPLEMENTO DE PREÇO REFERENTE A NF 57081"*) |
| `Vlr. DIFAL UF Remet.` e `Vlr. DIFAL UF Destino` | Base para a Entrega 5 |

E inclui os **documentos cancelados**, que o extrato antigo filtrava — 51 em
Julho/2026, todos com ICMS zero. O motor os descarta na ingestão, mas tê-los na
base permite o controle de integridade "documentos cancelados" que o escopo pede.

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

| Estabelecimento | UF | Linhas em 07/2026 | Regime |
|---|---|---|---|
| HINOVE (FILIAL GUARÁ) | SP | 3.925 | Equilíbrio fiscal — **centralizadora** |
| HINOVE (REGISTRO) | SP | 1.030 | Equilíbrio fiscal — centralizado |
| HINOVE (MATRIZ) | SP | 181 | Equilíbrio fiscal — centralizado |
| HINOVE (RIO BRILHANTE) | MS | 767 | Estorno + **benefício fiscal (Termo de Acordo 1.190/2018)** |
| HINOVE (CORUMBÁ- MS) | MS | 123 | Estorno proporcional |
| HINOVE (BARRA DO GARÇAS - MT) | MT | 373 | Diferimento — estorna 100% |
| HINOVE (LONDRINA) | PR | 104 | Diferimento — mantém 100% |

> O nome aparece como `HINOVE  (REGISTRO)` (dois espaços) e `HINOVE (CORUMBÁ- MS)`
> (sem espaço antes de `MS`). A normalização compara os nomes ignorando espaçamento.

## Regra de relevância para ICMS

O discriminante real é **ICMS diferente de zero**, não o CST. Em Julho/2026 isso
capturou linhas de CST `00`, `20` e `90`, e deixou de fora — sem exceção — todas
as de CST `40`, `41`, `50`, `51` e `60`, nenhuma das quais tinha ICMS.

**Sobre o CST `90`:** das 1.805 linhas de CST 90 do mês, 1.800 têm ICMS zero e
saem. As 5 restantes entraram na apuração manual e são de apenas dois tipos:

| Tipo | CFOP | TOP | Linhas | Valor (R$) |
|---|---|---|---|---|
| Lançamento de crédito de ativo (CIAP) | 1604 | 2310 | 3 | 24.903,24 |
| Devolução de compra de uso e consumo | 5556 | 3001 | 2 | 13,59 |

CST 90 não é uma categoria tributária a tratar: é o CST que o Sankhya usa para
esses dois lançamentos, e ambos já têm regra própria na matriz.

> **Cuidado na equalização:** as linhas de CIAP e de complemento de ICMS têm
> **valor contábil e base iguais a zero** com ICMS diferente de zero. A fórmula
> `ICMS ÷ valor contábil` divide por zero nelas. São identificadas antes da
> equalização, pelo bloco `lancamentos_sem_contabil` de `classificacao.yaml`.

## O TOP — 75 tipos de operação em Julho/2026

O TOP nomeia a operação. Confere exato com o que o motor hoje deduz por
heurística:

| TOP | Descrição | Linhas | ICMS (R$) | Hoje deduzido de |
|---|---|---|---|---|
| 2310 | CIAP | 3 | 24.903,24 | CFOP 1604 |
| 2316 · 3216 | NF Complementar ICMS | 6 | 17.490,73 | produto 701000075 |
| 3217 | NF Complementar Preço | 22 | 2.181,70 | produto 401002106 |
| 49 · 51 · 59 | Fretes | 1.652 | 891.356,65 | espécie CT-e + descrição |
| 3297 · 8888 | Quebras (Acerto de Estoque) | 17 | — | CFOP 5927 |
| 2108 | Compra de Embalagem | 4 | 23.475,30 | prefixo `2` do produto |
| 2103 | Compra de MP | 214 | 368.978,94 | prefixo `1` do produto |
| 21200-21202 | Retorno de Industrialização | 106 | 16.464,48 | CFOP 2903/2906 |

**O TOP ainda não é usado na classificação.** A ingestão já o lê e ele viaja na
base tratada; usá-lo como sinal primário depende de uma decisão tributária —
ver `06-decisoes-pendentes.md`, item 16.
