# Apurabot

Apuração mensal de ICMS da **Hinove Agrociência S.A.** a partir do Livro Fiscal
extraído do Sankhya e validado pelo Fiscalbot.

> **Situação:** a competência de referência é reproduzida da ingestão ao
> benefício fiscal, **fecha sem nenhuma pendência**, e a apuração de Rio Brilhante
> bate ao centavo com a GIA entregue. 96 testes automáticos.
> Ver o [plano de execução](../docs/apurabot/02-plano-de-execucao.md).

## O que já faz

```bash
apurabot base-tratada <livro_fiscal.xlsx> --saida <pasta>
```

Lê o Livro Fiscal, equaliza a carga efetiva de cada linha, classifica a operação,
aplica a regra tributária de cada UF, segrega por atividade onde a UF exige e
entrega a apuração em `.xlsx`, com a memória de cálculo linha a linha.

| Aba da saída | Conteúdo |
|---|---|
| RESUMO | Procedência, volume, situação da equalização e categorias |
| APURAÇÃO POR FILIAL | Crédito bruto, estorno, crédito indevido, mantido, débito e saldo — mais a memória do benefício, o FADEFE e a segregação por atividade |
| BASE TRATADA | Uma linha por linha do Livro, com toda a rastreabilidade |
| PENDÊNCIAS | O que bloqueia o encerramento da competência |
| POR ESTABELECIMENTO E CARGA | O recorte que confere com a tabela dinâmica da apuração manual |

## O que falta

Ajustes manuais vindos de `ajustes.xlsx` (fecha a Entrega 2), centralização de
SP, DIFAL, CIAP e a interface para o time fiscal.

## Estrutura

```
parametros/     A regra tributária. Editável e versionada — não é código.
  filiais.yaml         estabelecimentos, regimes e centralização
  regimes.yaml         SP equilíbrio · MS estorno + B.F. · MT/PR diferimento
  cargas.yaml          equalização da carga efetiva e tabelas de fertilizantes
  classificacao.yaml   como cada operação é classificada
  produtos.yaml        cadastro produto → categoria tributária

src/apurabot/
  ingestao.py          lê os dois layouts de extração e valida o cabeçalho
  parametros.py        carrega os YAML
  nucleo/carga.py      equalização da carga efetiva
  nucleo/classificacao.py
  nucleo/estorno.py    regra tributária por regime
  nucleo/atividade.py  segregação por atividade (GIA de MS)
  nucleo/beneficio.py  crédito presumido do Termo de Acordo e FADEFE
  base_tratada.py      orquestra as camadas 1 a 4
  apuracao.py          consolida por estabelecimento e por atividade
  saida.py             escreve o .xlsx
  cli.py               linha de comando

tests/          96 testes: unidade + regressão contra a competência de referência
analise/        Scripts exploratórios que reproduzem os números documentados
```

## Regimes por UF

| UF | Regime | Mecânica |
|---|---|---|
| SP | Equilíbrio fiscal | `valor contábil × (carga − 4%)`; centraliza em Guará |
| MS · Corumbá | Estorno proporcional | `ICMS × (1 − 4/alíquota)` — a chave é a **alíquota**, não a carga |
| MS · Rio Brilhante | Mesmo estorno + benefício fiscal | Termo de Acordo 1.190/2018 — 67% intra, 80% inter, sobre o saldo devedor **industrial** |
| MT | Diferimento | Estorna 100% |
| PR | Diferimento | Mantém 100% |

## Entrada

O extrato **`Movimento Livros Fiscais`** é o padrão a partir de 08/2026 — traz a
coluna TOP, que nomeia a operação como ela foi lançada. A extração antiga da
apuração continua suportada, e um teste prova que as duas produzem apuração
idêntica.

## Dados fiscais ficam fora do repositório

Livro Fiscal, XMLs, base de bens e apurações vivem em `competencias/AAAA-MM/`,
ignorada pelo git. Os testes de regressão localizam os arquivos por variável de
ambiente e são pulados com explicação quando não os encontram.
