# O porte do Fiscalbot: do VBA para o Python

> Registro do que mudou, do que ficou igual e da prova de que ficou.

---

## 1. O critério

Um porte de motor fiscal não se declara pronto: se prova. O critério foi
**divergência zero** contra a macro, e não "quase igual" — cada divergência
seria uma nota auditada de outro jeito, e o Livro Fiscal que o Apurabot
consome sai daqui.

## 2. A prova

Padrão-ouro: um relatório real de **6.554 registros** já auditado pela macro
v3.2, que traz as duas abas — `original` (a entrada) e `Relatório` (a saída
dela). O motor Python rodou sobre a mesma entrada e as duas saídas foram
comparadas **linha a linha**, em dez colunas: status, operação, texto de
auditoria, tipo INTRA/INTER e as seis ocorrências.

| Conferência | Macro | Python |
|---|---|---|
| Registros | 6.554 | 6.554 |
| Conformes | 6.326 (96,5%) | 6.326 (96,5%) |
| Advertências | 137 (2,1%) | 137 (2,1%) |
| Validação manual | 91 (1,4%) | 91 (1,4%) |
| Ocorrências de CST | 101 | 101 |
| Ocorrências de Valor ICMS | 27 | 27 |
| Ocorrências de Produto | 0 | 0 |
| Ocorrências de Alíquota | 2 | 2 |
| Ocorrências de Carga Efetiva | 25 | 25 |
| Ocorrências de Outros | 30 | 30 |
| **Divergências linha a linha** | — | **0** |

O teste está em `fiscalbot/tests/test_regressao.py` e roda a cada alteração.
O arquivo tem dado fiscal real e **não é versionado**: fica em
`competencias/fiscalbot/`. Sem ele o teste é pulado — mas então ninguém pode
dizer que o porte está provado.

## 3. O que saiu, e por quê

| Saiu | Motivo | Entrou no lugar |
|---|---|---|
| **Excel como motor** | A regra em `.xlsm` não tem diff, não tem revisão e não tem conferência | Motor em Python, regra na base do aplicativo |
| **Excel como tela de regras** | Mesma razão, e a Central passou a ser a porta única | Tela de configuração, com validação ao salvar |
| **Popup de seleção de arquivo** | A interface passou a ser o navegador | Arrastar o arquivo na janela |
| **Gravar dentro do arquivo de entrada** | A macro renomeava a aba original e escondia | Sai um `.xlsx` novo; o original não é tocado |
| **`TOL_CARGA = 0,05` no código** | Número tributário embutido em código | Parâmetro editável na tela |

## 4. O que ficou idêntico, de propósito

* A **mini-linguagem das regras**, operador por operador. Quem sabia cadastrar
  regra continua sabendo, e as 64 regras existentes valem sem tradução.
* Os **textos de ocorrência** (`Advertencia de CST` e companhia), sem acento,
  como estavam. São comparados contra saídas antigas.
* A **ordem das 25 colunas** da aba `Relatório`, que é a ordem de conferência.
* A **carga efetiva como fórmula**, e não como valor gravado.

## 5. Duas coisas que o porte encontrou no original

Estão portadas **como estão**, não como deveriam ser: o padrão-ouro foi
auditado assim, e corrigir é decisão do fiscal, na tela — não do porte.

### `TABELAUF` na coluna errada, na regra E11

A regra **E11 (Frete creditado INTER)** tem `TABELAUF` em `EspICMS`. Esse
operador só funciona em `EspAliq`. Na coluna de ICMS o VBA tenta ler o valor
como número, não consegue, e **não faz nada** — a conferência de ICMS dessa
regra cai na Camada 0.

Provável erro de digitação. Se a intenção era conferir a alíquota pela matriz,
o valor deve ser movido para a coluna de alíquota — mas isso **muda a
auditoria**, e por isso não foi feito por conta própria.

### CFOP vazio no meio da lista para a conferência

O VBA conta quantos CFOP estão preenchidos e depois percorre essa
**quantidade** de posições. Numa lista como `1602;;2602`, ele confere `1602` e
a posição vazia — e nunca chega ao `2602`.

Reproduzido de propósito, pelo mesmo motivo. A tela agora **avisa** quando uma
regra tem CFOP vazio no meio da lista, para o caso ser corrigido com os olhos
abertos.

## 6. O que o porte ganhou

* **Conferência ao salvar** — ID repetido, duas regras que casariam com o
  mesmo registro, operador inventado, tabela inexistente. Antes, tudo isso só
  aparecia quando o relatório rodava.
* **Trilha de alteração** — a base carimba quem gravou e quando.
* **Testes** — 57 no Fiscalbot, entre unidade e a regressão contra a macro.
* **Separação do que é dado da empresa** — as listas de parceiros deixaram de
  viajar junto da regra tributária.

## 7. Desempenho

6.554 registros em **cerca de 18 segundos**, da leitura do `.xls` à planilha
gravada com formatação. O gargalo é a escrita das 504 mil células formatadas,
não a auditoria.
