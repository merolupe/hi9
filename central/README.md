# Central Fiscal

A janela única do time Fiscal/Tributário: uma tela com as ferramentas do setor.
Escolhe-se uma, ela pede o arquivo de que precisa e devolve o resultado.

## Como se usa

Dois cliques em **`Hinove.bat`**, na raiz. A tela abre no navegador. Não há
passo de instalação: nada é baixado, nada é instalado, e o dado não sai da
máquina.

## Como uma ferramenta entra na tela

Declarando até quatro coisas em [`src/central/ferramentas.py`](src/central/ferramentas.py):

1. **quem é** — nome, resumo de uma linha e estado;
2. **o que pede** — `Entrada`: extensões aceitas, um arquivo ou vários;
3. **o que devolve** — `Resultado`: os números do resumo, as listas do que
   ficou de fora e, quando houver, a planilha para baixar;
4. **o que se configura nela** — `Configuracao`, quando a ferramenta guarda
   estado. Nasceu com o Fiscalbot, cujas regras tributárias são cadastradas
   numa tela em vez de planilha.

A ferramenta não sabe que existe navegador, não monta HTML e não conhece as
outras. Quem costura é a central.

Ferramenta que ainda **não** foi importada também é declarada, com estado
`A_IMPORTAR`: aparece apagada na tela, com o nome e o que faz. O time enxerga o
que falta em vez de descobrir na hora em que for precisar.

O contrato inteiro, com exemplo, está em
[`docs/central/01-arquitetura.md`](../docs/central/01-arquitetura.md).

## Estrutura

```
src/central/
  ferramentas.py   o catálogo e o contrato de ferramenta
  servidor.py      a janela: servidor local, envio de arquivo e execução
  janelas.py       ferramenta com tela própria (hoje só o Apurabot)
  pagina.html      a interface
  cli.py           linha de comando
  _dependencias.py acha `vendor/` e as ferramentas, e põe no sys.path

tests/             33 testes, incluindo a prova de que roda sem instalação
```

## Testes

```
python -m pytest
```
