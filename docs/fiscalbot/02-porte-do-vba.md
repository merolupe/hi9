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

A comparação usa `fiscalbot/tests/regras_da_macro.yaml`, uma **foto congelada**
das regras como a macro as tinha. É deliberado: o que se prova aqui é que o
motor faz o mesmo que a macro **dadas as mesmas regras**. Se a regressão usasse
a base viva, uma correção legítima de regra apareceria como quebra do porte —
que é outra coisa. As listas de parceiros, essas, vêm da base local, porque não
podem ser versionadas.

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

## 5. Dois defeitos que o porte encontrou, e corrigiu

Os dois foram medidos antes de mexer. Nenhum dos dois muda veredicto na
competência de referência — por isso foram corrigidos em vez de virarem aviso
na tela, que era como estavam na primeira versão do porte.

### `TABELAUF` na coluna errada, na regra E11

A regra **E11 (Frete creditado INTER)** tinha `TABELAUF` em `EspICMS`. Esse
operador só funciona em `EspAliq`: ele diz "a alíquota esperada vem da matriz
origem × destino". Na coluna de ICMS o motor tenta ler o valor como número,
não consegue e não faz nada — de modo que a alíquota era conferida contra a
lista literal `7;12`, uma aproximação frouxa da matriz.

**A medição:** 730 registros casam com a E11 nesta competência. Para **todos**
os pares de UF presentes, a matriz devolve exatamente 7 ou 12 — as duas formas
dão o mesmo veredicto, registro a registro.

**A correção:** o operador foi movido para a coluna de alíquota. Nenhum
veredicto mudou; mudou o texto da coluna `Auditoria`, que agora diz o que a
regra realmente pede. Daqui para a frente a conferência fica mais apertada: um
frete `MSxSP` lançado a 7% passava pela lista `7;12` e agora é acusado, porque
a matriz manda 12.

Há um teste que trava isso: `test_corrigir_a_regra_e11_nao_mudou_nenhum_veredicto`.

### CFOP depois de posição vazia deixava de valer

O VBA contava quantos CFOP estavam preenchidos e depois percorria essa
**quantidade** de posições. Numa lista como `1602;;2602`, ele conferia `1602`,
conferia a posição vazia e **nunca chegava ao `2602`**.

Isso é defeito, não regra: um CFOP cadastrado deixava de valer por causa de um
ponto e vírgula a mais, em silêncio. Nenhuma regra da base tinha CFOP vazio no
meio, então o defeito estava armado e não disparado — a correção não muda
auditoria nenhuma.

**A correção:** o motor confere todos os CFOP preenchidos, e a tela limpa as
posições vazias ao salvar.

## 6. O que o porte ganhou

* **Conferência ao salvar** — ID repetido, duas regras que casariam com o
  mesmo registro, operador inventado, tabela inexistente. Antes, tudo isso só
  aparecia quando o relatório rodava.
* **Trilha de alteração** — a base carimba quem gravou e quando.
* **Testes** — 59 no Fiscalbot, entre unidade e a regressão contra a macro.
* **Separação do que é dado da empresa** — as listas de parceiros deixaram de
  viajar junto da regra tributária.

## 7. Desempenho

6.554 registros em **cerca de 18 segundos**, da leitura do `.xls` à planilha
gravada com formatação. O gargalo é a escrita das 504 mil células formatadas,
não a auditoria.
