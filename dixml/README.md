# DiXML

Transforma um lote de XML de nota (NF-e e CT-e) em planilha, para conferir
qualquer informação fiscal que esteja no arquivo da nota.

Entra um ou mais `.zip`; sai um `.xlsx` com a aba `NFe` (uma linha por item) e
a aba `CTe` (uma linha por documento).

## Como se usa

Dois cliques em **`Hinove.bat`**, na raiz, e escolha **DiXML** na tela. Arraste
os `.zip`, veja o resumo e baixe a planilha. Não há passo de instalação.

Pelo terminal:

```
python rodar.py dixml "caminho\do\lote.zip" --saida "pasta\de\saida"
```

## O que ele decide sozinho

- **Uma linha por item**, com os dados da nota repetidos — a conferência é por item.
- **Código continua texto** (chave, CNPJ, NCM, CFOP); **valor vira número**.
- **Data vira data**, com a hora em coluna ao lado.
- **`.zip` dentro de `.zip`** é lido sozinho; o caminho fica na coluna `Arquivo`.
- **Evento, carta de correção e inutilização** não entram na planilha, mas são
  contados e listados.
- **Grupo novo no XML vira coluna nova**, sem alteração de código — e as colunas
  da Reforma existem mesmo quando nenhuma nota do lote as usa.

O porquê de cada uma está em
[`docs/dixml/01-o-que-faz.md`](../docs/dixml/01-o-que-faz.md).

## Estrutura

```
src/dixml/
  campos.py      como um pedaço de XML vira coluna
  pacote.py      de um .zip até cada XML, inclusive .zip aninhado
  nfe.py         a NF-e e as colunas-semente da Reforma Tributária
  cte.py         o CT-e, achatado inteiro
  datas.py       data e hora em colunas separadas
  planilha.py    a escrita do .xlsx e a formatação
  extracao.py    a leitura de ponta a ponta
  cli.py         linha de comando

tests/           31 testes, com notas fictícias montadas no próprio teste
```

Descende do script `robozinho` v2.2. O que mudou na importação — saíram o
pandas e o tkinter — está na seção 4 do documento.

## Testes

```
python -m pytest
```
