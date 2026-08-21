# Apurabot — Dicionário do Livro Fiscal (Sankhya)

> Layout observado na extração de Julho/2026: **52 colunas**, uma linha por item
> de documento fiscal. A ingestão valida este cabeçalho e falha com mensagem
> clara se o Sankhya mudar o layout.

| # | Coluna | Uso no Apurabot |
|---|---|---|
| A | Report | — |
| B | Status | Situação do documento |
| C | Data Inclusão/Alteração | Auditoria de inclusão posterior |
| D | **Nro único Nota** | **Chave interna do documento.** Agrupa os itens |
| E | Diferença ICMS | Sinal de divergência vinda do Fiscalbot |
| F | Sequência | Nº do item dentro da nota |
| G | Empresa | Código do estabelecimento |
| H | **Nome Fantasia (Empresa)** | **Estabelecimento apurado** |
| I | Dt. do documento | Data de emissão |
| J | **Dt. do movimento** | **Define a competência** |
| K | Empresa/Parceiro | Código do parceiro |
| L | Descrição Parceiro/Empresa | Nome do parceiro |
| M | Nro. da nota | Número do documento |
| N | **CFOP** | **Classificação da operação** |
| O | Descrição da CFOP | Apoio à classificação |
| P | **Cód. de tributação (CST)** | **Filtro de relevância para ICMS** |
| Q | **Produto** | **Código — o prefixo indica a categoria** |
| R | Descrição (Produto) | Nos CT-e, traz a **finalidade do frete** |
| S | **Vlr. contábil** | **Base do cálculo do estorno** |
| T | Base do ICMS | `ICMS ÷ base = alíquota exata` |
| U | **Alíquota ICMS** | Teto da carga nominal na equalização |
| V | **Vlr. do ICMS** | Crédito ou débito |
| W | Carga | `ICMS ÷ valor contábil` — carga bruta, com artefatos |
| X | **Carga efetiva** | **Carga nominal.** Hoje manual; passa a ser calculada |
| Y | Isentas de ICMS | Conciliação |
| Z | Outras ICMS | Conciliação |
| AA | Vlr. do IPI | Compõe o valor contábil |
| AB | **UF de Origem** | Intra × interestadual |
| AC | **UF de Destino** | Intra × interestadual |
| AD | Série da nota | Identificação |
| AE | Destino | `Empresa` (transferência) ou `Parceiro` |
| AF | Dt. Cancelamento | **Preenchida = documento excluído da apuração** |
| AG | **Espécie do documento** | `NF` ou `CT` — separa mercadoria de frete |
| AH | Tipo de ICMS | Com/sem crédito ou débito |
| AI | Base retenção | ST |
| AJ | ICMS retenção | ST |
| AK | Tipo de IPI | — |
| AL | Base do IPI | — |
| AM | Alíquota de IPI | — |
| AN | Isentas de IPI | — |
| AO | Outras IPI | — |
| AP | **Entrada/Saída** | **Separa crédito de débito** |
| AQ | Modelo do Documento | `55` NF-e · `57` CT-e · `22` telecom · `06` energia |
| AR | **Chave NF-e** | **Cruzamento com o XML no DIFAL** |
| AS | Chave CT-e | Cruzamento de fretes |
| AT | Chave CT-e de Referência | CT-e complementar/substituto |
| AU | Cód. Cid. Início CT-e | Rota do frete |
| AV | Nome (Cidade de Origem) | Rota do frete |
| AW | Cód. Cid. Fim CT-e | Rota do frete |
| AX | Nome (Cidade de Destino) | Rota do frete |
| AY | Vlr. ICMS Complemento | Complemento de ICMS |
| AZ | Nome Fantasia (Empresa Origem) | Origem em transferências |

## Estabelecimentos encontrados (Julho/2026)

| Estabelecimento | UF | Linhas | Regime |
|---|---|---|---|
| HINOVE (FILIAL GUARÁ) | SP | 3.925 | Equilíbrio fiscal — **centralizadora** |
| HINOVE (REGISTRO) | SP | 1.030 | Equilíbrio fiscal — centralizado |
| HINOVE (MATRIZ) | SP | 181 | Equilíbrio fiscal — centralizado |
| HINOVE (RIO BRILHANTE) | MS | 767 | Estorno + **benefício fiscal (Termo de Acordo)** |
| HINOVE (CORUMBÁ- MS) | MS | 123 | Estorno proporcional |
| HINOVE (BARRA DO GARÇAS - MT) | MT | 373 | Diferimento — estorna 100% |
| HINOVE (LONDRINA) | PR | 104 | Diferimento — mantém 100% |

> Atenção ao cadastro: o nome aparece como `HINOVE  (REGISTRO)` (dois espaços) e
> `HINOVE (CORUMBÁ- MS)` (sem espaço antes de `MS`). A normalização casa o
> estabelecimento por **código da empresa** (coluna G), não pelo nome.

## Regra de relevância para ICMS

O discriminante real é **ICMS diferente de zero**, não o CST. Em Julho/2026 isso
capturou linhas de CST `00`, `20` e `90`, e deixou de fora — sem exceção — todas
as de CST `40`, `41`, `50`, `51` e `60`, nenhuma das quais tinha ICMS.

**Sobre o CST `90`:** das 1.805 linhas de CST 90 do mês, 1.800 têm ICMS zero e
saem. As 5 restantes entraram na apuração manual e são de apenas dois tipos:

| Tipo | CFOP | Linhas | Valor (R$) | Onde apareceu na apuração manual |
|---|---|---|---|---|
| Lançamento de crédito de ativo (CIAP) | 1604 | 3 | 24.903,24 | linhas "CIAP" da aba ESTORNO — RB 2.146,57 · Registro 10.545,88 · Guará 12.210,79 |
| Devolução de compra de uso e consumo | 5556 | 2 | 13,59 | ajuste de crédito de Registro |

Ou seja, CST 90 não é uma categoria tributária a tratar: é o CST que o Sankhya usa
para esses dois lançamentos. Ambos são relevantes e ambos já têm regra própria na
matriz — CIAP mantém 100% conforme saídas tributadas; devolução de uso e consumo
estorna o crédito da compra.

> **Cuidado na equalização:** as 3 linhas de CIAP têm **valor contábil e base
> iguais a zero** com ICMS diferente de zero. A fórmula `ICMS ÷ valor contábil`
> divide por zero nelas. Por isso a carga dessas linhas não é numérica: elas são
> identificadas pelo CFOP `1604` e recebem a marca `CIAP` antes da equalização,
> exatamente como na planilha manual.
