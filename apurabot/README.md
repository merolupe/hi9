# Apurabot

Apuração mensal de ICMS da **Hinove Agrociência S.A.** a partir do Livro Fiscal
extraído do Sankhya e validado pelo Fiscalbot.

> **Situação:** a competência de referência é reproduzida da ingestão ao
> benefício fiscal, **fecha sem nenhuma pendência**, e a apuração de Rio Brilhante
> bate ao centavo com a GIA entregue e com o Registro de Apuração do ERP.
> 199 testes automáticos.
> Ver o [plano de execução](../docs/apurabot/02-plano-de-execucao.md).

## O que já faz

```bash
python rodar.py apurar <livro_fiscal.xlsx> --saida <pasta>
```

**Não há passo de instalação.** Em máquina corporativa, instalar esbarra em
permissão de administrador e em política de executável, então as bibliotecas
viajam junto do código, em `src/apurabot/vendor` — todas Python puro. Ver
[`src/apurabot/vendor/LEIA-ME.md`](src/apurabot/vendor/LEIA-ME.md).

Quem tem a máquina livre pode usar `pip install -e apurabot`: as dependências
estão declaradas no `pyproject.toml`, e as do sistema têm precedência sobre as
embarcadas.

Passo a passo completo em [07 — Como rodar](../docs/apurabot/07-como-rodar.md),
e o [08 — Roteiro de teste](../docs/apurabot/08-roteiro-de-teste.md) para a
primeira validação na máquina.

Lê o Livro Fiscal, equaliza a carga efetiva de cada linha, classifica a operação,
aplica a regra tributária de cada UF, segrega por atividade onde a UF exige e
entrega a apuração em `.xlsx`, com a memória de cálculo linha a linha.

| Aba da saída | Conteúdo |
|---|---|
| RESUMO | Procedência, volume, situação da equalização e categorias |
| REGISTRO | Espelho do Registro de Apuração: entradas e saídas por CFOP, resumo em 14 linhas, um bloco por filial e o totalizador do grupo |
| APURAÇÃO EFETIVA | CFOP → alíquota → produto, com operação, parcela não tributada, ICMS a estornar, a apropriar e o CHECK |
| APURAÇÃO POR FILIAL | Crédito bruto, estorno, crédito indevido, mantido, débito e saldo — mais a memória do benefício, o FADEFE e a segregação por atividade |
| TRANSFERÊNCIAS | O que transferir para a centralizadora depois de fechar a competência |
| PENDÊNCIAS | O que bloqueia o encerramento da competência |
| POR ESTABELECIMENTO E CARGA | O recorte por carga efetiva |
| BASE TRATADA | Uma linha por linha do Livro, com toda a rastreabilidade |

O comando `apurabot base-tratada` para no tratamento e na classificação, sem
apurar — serve para conferir o Livro antes de fechar o mês.

## Como se usa

Dois cliques em `Apurabot.bat`, na raiz do repositório: abre a janela do
Apurabot no navegador, onde se arrasta o Livro Fiscal e se baixa a planilha.

Nada é instalado e nenhum privilégio é pedido — a interface é o navegador, e o
servidor sobe em `127.0.0.1` pelo Python que já está na máquina. O dado não sai
dali. Ver `web/servidor.py` para o desenho.

Pelo terminal, `python rodar.py apurar <livro> --saida <pasta>` continua
valendo.

## O que falta

A leitura de `ajustes.xlsx` (fecha a Entrega 2). Sem os
ajustes declarados, as linhas 003 por ajuste, 006, 007 e 009 do registro saem
marcadas **AGUARDA AJUSTE** — zeradas, nunca inventadas.
**DIFAL e CIAP estão pausados** por decisão de escopo.

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
  nucleo/centralizacao.py  transferência de saldo entre estabelecimentos
  nucleo/registro.py   Registro de Apuração — livro por CFOP e resumo de 14 linhas
  base_tratada.py      orquestra as camadas 1 a 4
  apuracao.py          consolida por estabelecimento e por atividade
  conferencia.py       registro, apuração efetiva e transferências
  saida.py             escreve o .xlsx
  cli.py               linha de comando
  _dependencias.py     põe `vendor/` ao alcance do import
  vendor/              openpyxl, et_xmlfile, xlrd e PyYAML, embarcadas
  web/servidor.py      a janela: servidor local e navegador
  web/painel.py        o que a janela mostra
  web/pagina.html      a interface

tests/          199 testes: unidade + regressão contra a competência de referência
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
