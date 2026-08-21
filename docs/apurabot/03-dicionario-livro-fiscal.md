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

Uma linha entra na apuração de ICMS quando tem carga efetiva — o que equivale a
CST `00`, `20` ou `90`(?) **com ICMS diferente de zero**. Ficam de fora, sem exceção
observada em Julho/2026, as linhas de CST `40`, `41`, `50`, `51` e `60`.
