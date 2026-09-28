# O Resumo Executivo

O painel semanal das **duas frentes**, montado sobre o relatório já
classificado. É a terceira rotina de `pendentes/`, e a única que recebe a
**saída** das outras duas em vez de um export do Sankhya.

> O Resumo Executivo do VBA saiu do porte em 15/09/2026. Este não é aquele:
> aquele era montado no meio da geração de mercadorias, com duas categorias, e
> derrubava a execução inteira quando falhava. Este roda por último, enxerga
> três categorias e não pode derrubar nada — quando ele falha, os dois
> relatórios da semana já estão gravados há muito tempo.

## De onde veio a especificação

Do relatório de produção da **semana 38**, aba `Resumo Executivo`, com a aba
`_AuxResumo` que a alimenta. Não é interpretação do que o painel deveria
mostrar: é a medição do que ele mostra, fórmula por fórmula.

`[FATO]` A conferência, rodando o módulo sobre o arquivo daquela semana — 67
notas de mercadoria e 74 de serviço:

| Bloco | Resultado |
|---|---|
| Tabela por categoria (quantidade, valor, média de dias) | **igual**, incluindo o ruído de ponto flutuante do Excel |
| Total das três | igual — R$ 1.650.848,99 em 141 notas |
| TOP 5 por tempo pendente | **as mesmas 5 notas, na mesma ordem** |
| TOP 5 por valor | as mesmas 5, na mesma ordem |
| Valor por unidade (as 3 séries × 4 unidades) | igual, célula a célula |
| Quantidade por guardião (as 3 séries × 8 do gráfico) | igual, e na mesma ordem |

A única diferença: onde o arquivo de origem tem a célula de `Gestor` em branco
para duas notas, a ferramenta escreve o que está no relatório
(`Guardião não encontrado`). Foi apagado à mão lá; aqui o painel mostra o dado.

## O que o painel mostra

```
B2  Notas Pendentes de Entrada - SEMANA nn  G2   Notas de maior tempo pendente
B3  [título da pizza]                       G3   cabeçalho
B4  ┌─ pizza: proporção por categoria       G4:8 as 5 mais antigas
B12 cabeçalho da tabela                     G10  Notas de maior valor pendente
B13 Diretos    ┐                            G11  cabeçalho
B14 Indiretos  ├ quantidade, valor, média   G12:16 as 5 maiores
B15 Serviços   ┘ de dias pendente
B16 Total                                   S2   Data de referência: 21/09/2026
B18 Valor de pendências por Unidade         G18  Quantidade por Guardião
B19 ┌─ colunas empilhadas (até a linha 35)  G19  ┌─ barras empilhadas
```

Cada gráfico é preso às células pelos **dois cantos**: a pizza ocupa B4:E11 e
para no cabeçalho da tabela; os de baixo vão da linha 19 à 35, cada um com a
largura exata do bloco de cima. Até 28/09/2026 os gráficos eram medidos em
centímetro, e a pizza passava da linha 12 e cobria a tabela por categoria.

As três categorias aparecem em duas ordens, e as duas são do arquivo de
origem: **Diretos, Indiretos, Serviços** na tabela; **Indiretos, Diretos,
Serviços** nas colunas da aba auxiliar, que é a ordem da legenda da barra
empilhada. Ficaram como estão. A cor não depende de nenhuma das duas: cada
fatia e cada série recebe a cor **pelo nome** da categoria.

## O desenho

`[FATO]` Medido no print do painel da semana 38, pixel a pixel, em 28/09/2026:

| Elemento | Como sai |
|---|---|
| Barras de título, cabeçalhos e linha do Total | fundo `393939`, letra branca em negrito |
| Diretos | `AB99D5` (lilás) — na fatia, na série e na célula da tabela |
| Indiretos | `193A62` (azul-escuro) — rótulo da barra em branco |
| Serviços | `8EACC3` (azul-acinzentado) |
| Grade das tabelas | fina, `D0D0D0` |
| Moldura e linhas de grade dos gráficos | fina, `898989`, **canto reto** |
| Rótulo da pizza | quantidade e proporção, fora da fatia: `10 7%` |
| Rótulo das barras | no meio da faixa; `R$ 147.386` nas unidades, a quantidade nos guardiões; **zero não é escrito** |
| Eixo do gráfico de guardiões | invertido: o maior no alto, a escala em cima |
| Legenda | à direita na pizza, embaixo nas barras |

Quando o `Gestor` só repete o `Guardião` — é o caso de `Guardião não
encontrado`, que o relatório escreve nas duas colunas — as duas células viram
uma só no TOP N, e linhas seguidas com o mesmo guardião viram um bloco. É o
que o print mostra.

Duas armadilhas do openpyxl, contornadas no código e com teste: ele grava o
separador do rótulo como atributo (`<separator val=" "/>`), que o Excel não
lê, e grava o formato do rótulo sem `sourceLinked="0"` — aí o rótulo herda o
formato da célula, sai `233122,19` e o zero aparece. E sem `delete = False`
os eixos não aparecem: foi por isso que o gráfico de unidades saía sem o nome
das unidades.

## De onde sai cada número

| No painel | Em `Pendentes` | Em `Servicos` |
|---|---|---|
| categoria | `Categoria` | é sempre `Serviços` |
| guardião | `Guardião` | `Guardiao` |
| gestor | `Gestor de apoio` | `Gestor de apoio` |
| parceiro | `Nome Parceiro (Parceiro)` | `Parceiro` |
| valor | `Valor da Nota` | `Valor NFSe (Valor Bruto)` |
| emissão | `Dh. Emissão` | `Emissao` |
| unidade | trecho do `Nome Fantasia` | trecho da `Filial` |

O nome do parceiro passa por um reparo **só no painel**: entidade de HTML
crua vira o caractere. `[FATO]` Na semana 39 o relatório de serviços trouxe
`CUSHMAN amp; WAKEFIELD` — o `&amp;` perdeu o `&` num sistema de origem. A aba
`Servicos` continua como veio; o painel mostra `CUSHMAN & WAKEFIELD`.

### O que o painel não conta

* **A `PENDENTES FIS-FAT`.** De mercadorias o painel lê só a aba
  `Pendentes`: ela é achada pelo conjunto `Categoria` + `Chave Acesso` +
  `Valor da Nota` + `Nome Fantasia`, e a FIS-FAT não tem `Categoria`. Há
  teste (`test_a_aba_pendentes_fis_fat_nao_entra_no_painel`).
* **Serviço em fila de lançamento** (desde 28/09/2026). Quando a nota está
  anexada a um pedido da Conferência de Serviços com vínculo `Exato`, o
  GerarServPend escreve `Em fila de lançamento` na coluna de retorno — não
  falta cobrar ninguém, falta lançar. O painel pula essas linhas e a tela diz
  quantas foram. A coluna é achada pelo começo do nome, então `Retorno` e
  `Retorno semana 39` valem igual.

### A média de dias sai da emissão, nas duas frentes

`[FATO]` No arquivo de origem a média de mercadorias vem de `Dias Emissão
Doc` — a coluna que o VBA grava sem conversão e formata como data — e a de
serviços vem de `referência − média das emissões`. As duas contas dão o mesmo
número porque a coluna quebrada guarda o serial do Excel, e serial e contagem
de dias coincidem nessa faixa.

Aqui as duas saem da emissão. Medido na semana 38: Indiretos 10,684211,
Diretos 3,4, Serviços 16,743243 — os três números do painel. A escolha não
muda resultado e tira do caminho uma coluna que a pendência nº 2 ainda pode
mudar.

### O desempate dos TOP N

`[FATO]` O painel original desempata com `V + LIN()/1000000` e `MAIOR(...)`.
O efeito: entre notas com o mesmo valor ou o mesmo tempo, vence a que está
**mais embaixo** na lista. Aqui é uma chave de ordenação explícita, e a ordem
da lista é mercadorias primeiro, serviços depois — como lá.

### A data de referência

A mesma `data_de_referencia` que decide o número da semana. Um relatório
gerado na terça sobre a posição de segunda conta os dias a partir de segunda,
senão o painel envelhece todas as notas em um dia. Sem data cadastrada, vale
hoje — e a data usada fica escrita na célula `T2`, à vista.

## Quatro decisões

### 1. Valores, não fórmulas

O arquivo de origem é feito de `CONT.SES` e `SOMASES` apontando para
`Pendentes!$D$2:$D$68`. Aqui a conta é feita em Python e o que vai para a
célula é o número.

* o intervalo `$2:$68` é a semana 38 e mais nenhuma. Fórmula com intervalo
  fixo é a mesma armadilha do índice de coluna fixo que o porte tirou do VBA:
  na semana seguinte ela aponta para o lugar errado **sem errar**;
* fórmula só vira número depois que o Excel abre e calcula — quem recebe por
  e-mail e olha no celular vê o painel montado;
* o valor gravado é o valor que a ferramenta afirma, e erro reproduzível é
  erro corrigível.

O que se perde: o painel não se corrige sozinho quando alguém edita uma linha
depois. É deliberado — o resumo é gerado **depois** da classificação fechar, e
editar o relatório depois disso pede rodar o resumo de novo, não confiar num
recálculo silencioso. Rodar de novo troca as duas abas; não empilha.

### 2. O painel entra na planilha da semana

Porque é ela que é enviada. Painel em arquivo separado obriga alguém a copiar
aba entre planilhas toda semana — o tipo exato de passo manual que a
ferramenta existe para tirar do caminho.

O arquivo de entrada **não é alterado**: o relatório é relido e gravado ao
lado, com `Resumo Executivo` na frente e `_AuxResumo` oculta no fim.

`[FATO]` O openpyxl não preserva gráfico nem imagem das abas que ele apenas
relê. O relatório, como a ferramenta o gera, não tem nenhum dos dois — mas um
gráfico colado à mão em outra aba não sobrevive. Está dito na tela, contado.
Tudo o mais atravessa: medido contra o arquivo da semana 38, as outras oito
abas saíram com **zero** diferença de conteúdo, fórmula, largura e filtro.

### 3. A unidade vem da tabela cadastrada, ou não vem

`[FATO]` O arquivo de origem tem a lista de unidades **digitada à mão** na aba
auxiliar, e conta com `CONT.SES(...;"*"&unidade&"*")`. Aqui a lista é a tabela
de unidades da ferramenta, com a ordem que ela já exige (`CORUMB` antes de
`GUAR`), e o mesmo de-para serve às duas frentes: `HINOVE (FILIAL GUARÁ)` e
`HINOVE (MATRIZ)` casam pelo mesmo mecanismo.

Tabela vazia — que é como ela nasce, porque nome de unidade é dado da empresa
— **não** inventa unidade: o bloco sai vazio, o gráfico não é desenhado e a
tela manda cadastrar em `⚙ Parâmetros das pendentes`. Unidade cadastrada sem
pendência aparece **zerada** na conta e na aba auxiliar, porque zero é uma
resposta — mas **não** no gráfico (desde 28/09/2026): com onze unidades
cadastradas e quatro com pendência, eram sete colunas vazias ocupando o
gráfico. O gráfico lê o bloco `AI:AL`, que só tem as unidades com pendência.

### 4. O "destacar acima de" saiu

No arquivo de origem ele é um número escrito num canto, e nada acontece com
ele. De 22/09 a 28/09/2026 ele pintou de rosa a célula de dias acima do
limite; saiu porque o painel passou a seguir o print da semana 38, que não
pinta nada — e no TOP de tempo pendente, que já são as mais antigas, a
pintura marcava as cinco linhas. Sem pintura, o controle não controlaria nada,
e por isso saiu também da tela de parâmetros. Uma base que ainda tenha
`destacar_acima_de_dias` gravado não quebra: a chave é ignorada.

## O que bloqueia

Nota de mercadoria cuja `Categoria` não é `Diretos` nem `Indiretos`.

`[FATO]` No arquivo de origem ela simplesmente não é contada — o `CONT.SE`
conta as duas e mais nada, e a nota **desaparece do painel sem deixar rastro**.
Aqui ela continua fora da conta (mudar isso mudaria os números do painel), mas
sai nomeada na tela e a execução fica **não encerrável**. É a regra nº 4
aplicada ao painel: o que a ferramenta não sabe dizer o que é não some.

Serviço não precisa de categoria: a frente **é** a categoria, e não há coluna
de categoria no relatório de serviços para ler.

## Os parâmetros

Em `resumo:`, na carga de fábrica. Nenhum muda número — mudam o que cabe na
tela de quem lê o painel na segunda-feira.

| Parâmetro | Fábrica | O que faz |
|---|---|---|
| `linhas_do_top` | 5 | quantas notas cada TOP mostra |
| `guardioes_no_grafico` | 8 | quantas barras o gráfico de guardião mostra |
| `guardioes_fora_do_ranking` | `[]` | quem não entra no ranking do gráfico |

`guardioes_fora_do_ranking` nasce vazia porque nome de área é dado da empresa.
`[FATO]` Na semana 38 ela tem três entradas — `Guardião não encontrado`,
`cancelada` e `RH PJ`. As duas primeiras são marcadores de que a classificação
não fechou; a terceira é decisão do time. As notas dos excluídos **continuam**
nas contas de categoria, unidade e total: sair do ranking é sair do gráfico,
não sair da semana.

## O que ficou de fora

* **a aba `Resumo`**, que é outra coisa: a série semanal (`Semana 35`,
  `36`, `37`, `38`), as médias por quinzena e os dois campos de texto de
  atenções e pontos positivos. Ela depende de histórico entre semanas — que é
  exatamente o que o snapshot semanal guarda — e é a próxima rodada natural;
* **área de impressão.** A cor por série entrou em 28/09/2026, medida no
  print (ver *O desenho*); a área de impressão continua de fora. O que os
  testes garantem do desenho é o verificável — cor de cada série e célula,
  canto reto, âncora que não cobre a tabela, eixo visível —, não que o
  gráfico esteja bonito.
