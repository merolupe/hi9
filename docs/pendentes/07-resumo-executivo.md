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
B2  Resumo executivo                        G2   Notas de maior tempo pendente
B3  [título da pizza]                       G3   cabeçalho
B4  ┌─ pizza: proporção por categoria       G4:8 as 5 mais antigas
B12 cabeçalho da tabela                     G10  Notas de maior valor pendente
B13 Diretos    ┐                            G11  cabeçalho
B14 Indiretos  ├ quantidade, valor, média   G12:16 as 5 maiores
B15 Serviços   ┘ de dias pendente
B16 Total                                   S2   Data de referência: 21/09/2026
B18 Valor de pendências por Unidade         S3   Destacar acima de (dias): 10
B19 ┌─ colunas empilhadas                   G19  ┌─ barras empilhadas
```

As três categorias aparecem em duas ordens, e as duas são do arquivo de
origem: **Diretos, Indiretos, Serviços** na tabela; **Indiretos, Diretos,
Serviços** nas colunas da aba auxiliar, que é o que decide a cor de cada faixa
da barra empilhada. Ficaram como estão.

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
tela diz que são cinco linhas na tela de configuração. Unidade cadastrada sem
pendência aparece **zerada**, porque zero é uma resposta.

### 4. O "destacar acima de" passa a fazer alguma coisa

No arquivo de origem ele é um número escrito num canto, e nada acontece com
ele. Aqui ele pinta a célula de dias das notas acima do limite. Um controle
que não controla nada é pior que não existir: quem lê supõe que existe regra.

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
| `destacar_acima_de_dias` | 10 | acima disso, a célula de dias sai marcada |
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
* **área de impressão e cor por série.** O painel sai com a paleta padrão do
  Excel. Perseguir a paleta é o único bloco cujo esforço cresce sem limite
  claro, e não tem teste automático: nenhuma asserção diz "este gráfico está
  bonito".
