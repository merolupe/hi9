# Fiscalbot

Audita o Livro Fiscal de ICMS: lê o relatório *Movimento Livros Fiscais*
extraído do Sankhya, identifica a operação de cada registro e confere o
enquadramento em seis dimensões — CST, valor de ICMS, produto, alíquota, carga
efetiva e outros.

É o fornecedor do Livro Fiscal validado que o **Apurabot** consome.

## Como se usa

Dois cliques em **`Hinove.bat`**, na raiz, e escolha **Fiscalbot**. Arraste o
relatório, veja o resumo e baixe a planilha auditada. Para cadastrar regra, o
botão **⚙ Regras e parâmetros** na mesma tela.

Pelo terminal:

```
python rodar.py fiscalbot "caminho\do\Movimento_Livros_Fiscais.xls" --saida "pasta"
```

## Onde as regras moram

Na base do aplicativo (`dados/fiscalbot/base.yaml`), **fora do git**, editada
pela tela. O que é versionado é a carga de fábrica
([`regras_de_fabrica.yaml`](regras_de_fabrica.yaml)): as 64 regras, os
parâmetros e a matriz de alíquotas, sem nenhum dado da empresa.

As **listas de parceiros não vêm no repositório** — trazem código e nome de
fornecedor real. Numa máquina nova, precisam ser cadastradas na tela.

## O que ele decide sozinho

- **Três camadas passam por cima de tudo**: nota cancelada, frete de parceiro
  do Simples Nacional e compra de cavaco.
- **Casamento MECE**: espera-se que exatamente uma regra case. Duas casando
  acusam a base, não o documento.
- **Camada 0** é a rede embaixo de tudo, inclusive de registro sem regra.
- **Coluna procurada por nome**, nunca por posição — o layout do Sankhya muda.

O porquê de cada uma está em
[`docs/fiscalbot/01-o-que-faz.md`](../docs/fiscalbot/01-o-que-faz.md). O
registro do porte, com a prova de equivalência contra a macro, está em
[`docs/fiscalbot/02-porte-do-vba.md`](../docs/fiscalbot/02-porte-do-vba.md).

## Estrutura

```
regras_de_fabrica.yaml   as 64 regras, versionadas, sem dado da empresa

src/fiscalbot/
  modelo.py        o que é uma regra e o que é a base
  predicados.py    a mini-linguagem das condições
  base.py          onde a base mora, e como é lida e gravada
  planilha.py      leitura do relatório, .xls ou .xlsx
  leitura.py       cabeçalho e colunas, por nome
  auditoria.py     o motor: as camadas e as seis dimensões
  saida.py         as abas Relatório e Resumo
  validacao.py     o que a tela confere antes de gravar
  configuracao.py  a ponte entre a base e a tela da Central
  execucao.py      a auditoria de ponta a ponta
  cli.py           linha de comando

tests/             59 testes, incluindo a regressão contra a macro VBA
  regras_da_macro.yaml   foto das regras que a macro rodava — não editar
```

Descende do módulo VBA `modFiscalbot` v3.2.

## Testes

```
python -m pytest
```

A regressão contra a macro precisa de um relatório real já auditado, em
`competencias/fiscalbot/`. Sem ele, é pulada com a mensagem explicando.
