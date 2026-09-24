# Balançabot — o que a ferramenta é hoje

> Levantamento da ferramenta **como ela está**, antes de qualquer porte: o que
> faz, como faz, o que pede e o que entrega.
>
> Público: analista desenvolvedor + Gerência Fiscal/Tributária + quem opera a
> conferência da balança.
>
> Fonte: `Faturabot.bas` (4.085 linhas, um módulo), `Faturabot.xlsm` (o painel)
> e o manual de uso de 23/09/2026, rev. 3.
>
> `[FATO]` = verificado no código ou no `.xlsm` · `[INFERÊNCIA]` = dedução a
> validar com quem opera.

---

## 1. Em uma frase

Para cada caminhão que passou pela balança de Guará, a ferramenta acha o
documento do sistema que corresponde àquela pesagem — o agendamento e a nota —
e mede quanto o peso da nota se afasta do peso da balança. O que passar da
tolerância aparece como divergência.

O nome no código ainda é Faturabot, "Conferência 3". As outras duas conferências
(relação de saídas e quantidades) estão reservadas no cabeçalho do módulo e não
têm nenhuma linha escrita `[FATO]`. Neste repositório a ferramenta se chama
**Balançabot**, que é o nome que já aparece na aba de abertura do `.xlsm`.

## 2. O que está nas mãos

| Peça | O que é | Observação |
|---|---|---|
| `Faturabot.xlsm` | painel: a aba `BLbot` com dois botões-imagem e a aba `Parâmetros` | não guarda resultado; está num SharePoint `[FATO]` |
| `Faturabot.bas` | todo o código, um módulo só | 4.085 linhas, 120 procedimentos |
| Manual | uso, regras de decisão e verificações feitas | rev. 3, consolidação semanal |

Os dois botões da aba `BLbot` apontam para `ConferirDesvioBalanca` (caminhão) e
`ConsolidarRelatorios` (a segunda imagem) `[FATO]`. Na caixa de Macros ficam
quatro rotinas:

| Macro | Para quê |
|---|---|
| `ConferirDesvioBalanca` | **a conferência**: lê os relatórios, cruza e grava o `.xlsx` |
| `ConsolidarRelatorios` | junta os relatórios de vários períodos da semana num só |
| `DiagnosticarRelatorio` | diz como um arquivo foi reconhecido e que colunas faltam |
| `TestarExtracaoOC` | autoteste do extrator de OC: 24 casos, tem que dar 24/24 |

**O que não foi verificado, segundo o próprio manual:** a execução do VBA no
Excel. "A primeira execução real fica com o operador." As verificações da
seção 12 do manual foram feitas sobre as fórmulas e as regras extraídas do
código, não sobre uma rodada da macro. Isso pesa no porte (ver
[02](02-plano-do-porte.md) § 8).

### Onde está o peso do código

`[FATO]` Do total, perto de 520 linhas são só aparência: a camada cosmética
(`Cos*`, `FmtCel`, `BordaCel`, cerca de 310 linhas) e o molde do `Resumo Geral`
gerado a partir da planilha do operador (cerca de 210). Outro tanto é Excel
puro — abrir e fechar pasta, `ModoRapido`, diálogo de arquivo, `MsgBox`,
tratador de erro com etapa e passo. O motor propriamente dito — leitura,
consolidação das saídas, cruzamento, desvio e indicadores — cabe em torno de
1.500 linhas.

## 3. O que ela pede

### 3.1 Os relatórios

Selecionados todos juntos, num diálogo só, em qualquer ordem. Cada arquivo é
reconhecido pelo cabeçalho da **primeira aba**, procurado nas primeiras 40
linhas e 400 colunas. A ordem das perguntas importa, porque o primeiro que casar
vence `[FATO]`:

| # | Papel | Sistema | Reconhecido por | Obrigatório |
|---|---|---|---|---|
| 1 | **BL** — Pesagens por Período | balança | `Ticket` **e** `Peso Liquido` | **sim** |
| 2 | **AGFAT** — Agenda faturamento | Sankhya | `Nro. Único OC` | um dos dois, AGFAT ou AGREC |
| 3 | **AGREC** — Agendamento recebimento | Sankhya | `Qtd. Total XML` | um dos dois |
| 4 | **PMI** — Portal de Movimentação Interna | Sankhya | `Nro. Ordem de Carregamento` **e** `Dt. necessidade` | não |
| 5 | **Portal de Vendas** — Cabeçalho da Nota | Sankhya | `Nro. Ordem de Carregamento` (sem `Dt. necessidade`) | não; sem ele avisa |
| — | **MIC** | MIC | arquivo HTML com `<table` e `Placa Cavalo` nos primeiros 20 mil caracteres | não |

O MIC chega com extensão `.xls`, mas é uma página HTML. A macro o lê como texto,
sem abrir no Excel, para fugir da conversão de número que depende do idioma da
máquina (`34,540` é 34,54 t em português e 34.540 em inglês) `[FATO]`.

Cabeçalho é comparado depois de normalizado: sem acento, maiúsculas, espaços
colapsados, `º`/`ª`/`°` removidos. Quando o relatório tem **duas colunas com o
mesmo nome** — o Cabeçalho da Nota tem duas `Placa` e duas `Observação` —,
vence a que tem mais células preenchidas nas primeiras 500 linhas `[FATO]`.

### 3.2 As colunas que cada um precisa ter

Coluna obrigatória ausente interrompe a execução nomeando o arquivo e a
coluna; coluna opcional ausente só deixa a aba de apoio mais pobre.

| Relatório | Obrigatórias | Opcionais |
|---|---|---|
| BL | `Ticket`, `Operação`, `Placa`, `Cliente/Fornec.`, `Produto`, `Data Peso Tara`, `Peso Tara`, `Peso Bruto`, `Peso Liquido`, `Observação` | `P. Final`, `Peso Liq. NF` |
| AGFAT | `Placa`, `Clientes`, `Produtos`, `Quantidades`, `Nro. Único OC`, `Local de Coleta`, `Peso Inicial`, `Peso Final`, `Peso liquido`, `Data e Hora`, `Fim do carregamento` | — |
| AGREC | `Placa OC`, `Nome Parceiro`, `Produtos`, `Nro. OC`, `Nro. Nota`, `Qtd. Total XML`, `Peso Entrada (KG)`, `Peso Final (KG)`, `Peso Saída (KG)`, `Dt. Hra. chegada caminhão` | `Peso da Nota (KG)`, ou `Peso Liquido` no lugar dele |
| Portal de Vendas e PMI | `Nro. Ordem de Carregamento`, `Peso`, `Dt. Entrada/Saída`, `Status NF-e`, `Descrição (Tipo de Operação)` | `Placa`, `Nro. Nota`, `Nome Parceiro (Parceiro)`, `Descrição (Produto)`, `Local de coleta`, `Número Pedido`, `Peso bruto`, `Vlr. Nota` |
| MIC | `N° NF`, `Data`, `Quant.`, `Placa Veículo` | `Hora`, `Placa Cavalo`, `Produto`, `Operação`, `Empresa Envio`, `N° D.I.`, `Chave de Acesso (NF-e)`, `Situação` |

No MIC a coluna é achada por uma chave só de letras e dígitos (`N° NF` vira
`NNF`, `Operação` vira `OPERAO`), que funciona tanto na leitura UTF-8 quanto na
leitura de reserva, byte a byte, em que o acento chega trocado `[FATO]`.

### 3.3 Quando falta alguma coisa

| Falta | O que acontece |
|---|---|
| BL | interrompe, com a lista do que faltou |
| AGFAT **e** AGREC | interrompe |
| só um deles, ou o Portal de Vendas | roda parcialmente e escreve "conferência parcial" no log |
| arquivo não reconhecido | é ignorado e listado; a mensagem manda rodar `DiagnosticarRelatorio` |

### 3.4 O painel de parâmetros

Aba `Parâmetros` do `.xlsm`. **O código lê endereços fixos** `[FATO]`:

| Célula lida | Parâmetro | Padrão no código | Aceita |
|---|---|---|---|
| `C5` | tolerância de desvio (±) | 0,50% | maior que 0 e menor que 100% |
| `C6` | janela de data do passe 2, em dias | 3 | de 1 a 60 |
| `C7` | pasta de destino | pasta do `.xlsm`; se for OneDrive, Documentos | texto |
| `C8`, `C9` | início e fim do período do Resumo | menor e maior data de pesagem | data |
| `C10` | trava de sanidade | 25% | maior que 0 e menor que 1.000% |
| `B27` a `B86` | trechos de produto fora de escopo | `PALETE`, `PALLET`, `CAVACO`, `MADEIRA` | texto |

> **Achado — o painel que está no `.xlsm` está deslocado.** `[FATO]` No arquivo
> recebido, a tolerância está em `B3` e a janela em `B4`, e em `C5` está o texto
> "em branco = mesma pasta deste arquivo". Como `C5` tem texto, a macro não
> recria o painel e usa o padrão do código. **Mudar a célula que o operador vê
> não muda nada.** Hoje não aparece, porque os valores de lá (0,5% e 3 dias)
> são os mesmos padrões do código. A trava (`C10`) e a lista de exclusão (a
> partir de `B27`) estão no lugar certo e são lidas. A lista da coluna `A`
> (linhas 24 a 27) é uma cópia que ninguém lê.

## 4. Como ela decide

A conferência corre em nove etapas, sempre na mesma ordem.

### 4.1 A pesagem (BL)

Linha sem `Operação` ou sem `Placa` é totalização e sai `[FATO]`. De cada
pesagem ficam: a placa normalizada (só letras e dígitos: `SFE-5B10` é
`SFE5B10`), a operação normalizada (`COLETA`, `RECEBIMENTO`), a **data do peso
tara** e a **OC**, extraída da `Observação`.

**A extração da OC** é uma varredura sem expressão regular `[FATO]`:

1. procura, nesta ordem, as âncoras `ORDEM DE CARREGAMENTO`, `ORDEM
   CARREGAMENTO`, `ORD. CARREG`, `ORD CARREG`, `O.C.` e `OC`;
2. a âncora não pode estar colada em letra — `BLOCO` e `ESTOCADO` não contam;
3. depois da âncora, pula até seis separadores (espaço, `:`, `;`, `-`, `=`,
   `#`, `.`, `,`, `/`, tabulação, quebra de linha);
4. lê os dígitos, absorvendo ponto de milhar (`71.145` é 71145); vírgula
   encerra;
5. vale se tiver de 4 a 8 dígitos. Número solto, sem âncora, nunca vira OC.

Registra o motivo: `ANCORA_OC`, `SEM_ANCORA`, `TAMANHO_INVALIDO`, `OBS_VAZIA`.
Os 24 casos do autoteste são a especificação executável dessa regra.

### 4.2 Os agendamentos (AGFAT e AGREC)

Linha sem placa sai. Cada agendamento vira um candidato ao cruzamento com
placa, OC e data:

| | Placa | OC | Data da janela | Peso do sistema (coluna G) |
|---|---|---|---|---|
| AGFAT | `Placa` | `Nro. Único OC` | `Fim do carregamento` | `Peso liquido` |
| AGREC | `Placa OC` | `Nro. OC` | `Dt. Hra. chegada caminhão` | `Peso Final (KG)` |

No AGREC a ferramenta ainda calcula o **peso documental** de cada linha, que é
o candidato à coluna H dos recebimentos `[FATO]`:

1. `Peso da Nota (KG)` (ou `Peso Liquido`), se existir e for maior que zero —
   já vem em quilo;
2. senão, `Qtd. Total XML` × fator pela faixa física de carga;
3. senão, "sem base".

**O fator pela faixa física de carga** decide a unidade sem olhar a balança:

| Quantidade no documento | Lida como | Fator |
|---|---|---|
| 5 a 80 | tonelada | × 1.000 |
| 5.000 a 80.000 | quilo | × 1 |
| qualquer outra | não interpretável | nenhum — vai para análise |

### 4.3 As saídas (Portal de Vendas + PMI)

Uma OC pode ter várias notas, nos dois relatórios. As notas são juntadas e
consolidadas **por OC** `[FATO]`:

1. a mesma nota (número + tipo de operação) nos dois relatórios conta uma vez —
   vale a primeira que chegou;
2. só entra nota com `Status NF-e = Aprovada` e OC maior que zero;
3. se a OC tem nota de **venda**, soma-se **só a venda** — conta e ordem e
   transferência vinculada emitem mais de uma nota para a mesma carga;
4. sem nota de venda, somam-se as demais notas aprovadas.

"Nota de venda" é a que o tipo de operação começa por `VENDA`, `REVENDA`,
`REV. RET` ou `REV RET` — "Rev. Ret. Simb. Armazém" conta como venda `[FATO]`.

Cada nota recebe o seu tratamento por escrito ("somada: nota de venda",
"excluída: Status NF-e diferente de Aprovada", "excluída: mesma carga da nota
de venda — prevalece a venda" e assim por diante). A placa e a data da OC
consolidada são as da primeira nota somada.

Dessas OCs saem **dois** grupos de candidatos, com as mesmas linhas:

* todas as OCs — para a coluna H das **coletas**;
* só as OCs que têm nota aprovada do PMI — para a coluna H dos
  **recebimentos por transferência**.

### 4.4 O MIC

Notas filhas da nacionalização. Entra como candidata só a nota com situação
`A` (quando a coluna existe), quantidade dentro da faixa física e data legível.
O peso é a quantidade × fator. Como o MIC não tem OC, ele só cruza pela placa,
e duas vezes: primeiro pela **placa do veículo**, depois pela **placa do
cavalo** — e registra qual casou, porque ainda não se sabe qual das duas a
balança anota `[FATO]`.

### 4.5 O cruzamento

Para cada grupo de candidatos, duas passadas sobre **todas** as pesagens da
operação, uma depois da outra — nunca pesagem por pesagem, que inverteria a
precedência `[FATO]`:

1. **por OC** — a pesagem com OC casa com o primeiro candidato livre de mesma
   OC. Confiança **Alta**. Placa diferente não impede, só fica anotada;
2. **por placa**, dentro da janela de dias, pegando o candidato de data mais
   próxima. Confiança **Média**. Se a pesagem e o candidato têm OC e as OCs são
   diferentes, aquele candidato é **vetado**.

Cada candidato é usado por uma pesagem só. A primeira passada não olha data.

A ordem em que os grupos são tentados é o que define de onde vem cada peso:

| Operação | Coluna G (peso do sistema) | Coluna H (peso documental), em ordem |
|---|---|---|
| Coleta | AGFAT | Saídas por OC |
| Recebimento | AGREC | MIC pela placa do veículo → MIC pela placa do cavalo → PMI → o mesmo AGREC da coluna G |

A confiança da pesagem é **Média** se G ou H casou por placa; **Alta** se algum
casou por OC e nenhum por placa; "Sem correspondência" se nada casou. A fonte
de H (`SAIDAS`, `MIC`, `PMI`, `AGREC`) e o motivo de cada casamento ficam
escritos na aba `BL`.

Operação da balança que não seja `COLETA` nem `RECEBIMENTO` não entra em
nenhum cruzamento e fica sem correspondência `[FATO]`.

### 4.6 O escopo

Recebimento cujo produto **contém** algum trecho da lista do painel (comparado
sem acento e sem caixa) sai da aba `Desvios` e vai para a aba oculta `Fora de
Escopo` — produto que não é matéria-prima vem no XML em peça, metro ou quilo, e
a conversão produziria divergência que não existe. Coleta nunca sai do escopo
`[FATO]`.

### 4.7 O período

O período vem de `C8` e `C9`; lado em branco usa a menor ou a maior data de
pesagem; fim antes do início volta às datas das pesagens. **O período filtra só
os indicadores do `Resumo Geral`.** A aba `Desvios` traz todas as pesagens —
inclusive as da noite anterior, que a balança costuma exportar junto `[FATO]`.

### 4.8 O desvio

Na aba `Desvios`, por pesagem em escopo:

* **H** — o peso documental, lido da fonte registrada na `BL`;
* **L = H ÷ F − 1**, e:
  * vazio, se a pesagem não casou com nada;
  * "Analisar confronto de peso", se casou mas o documento não tem peso
    interpretável;
  * "Analisar confronto de peso", se |L| passa da **trava** (25%) — desvio
    real de balança é de poucos por cento, e mais que isso é unidade ou fonte
    errada;
  * o número, nos demais casos: verde dentro da tolerância, vermelho fora.

### 4.9 Os indicadores

O `Resumo Geral` reproduz o layout do relatório manual do operador de 18 a
19/09. Por operação (Coleta, Recebimento, Total), dentro do período:

| Linha | Indicador | Conta |
|---|---|---|
| 12 | Pesagens processadas | pesagens em escopo |
| 13 | Com desvio apurado | as que têm L numérico |
| 14 | Não divergente positiva | linha 13 − linha 15 |
| 15 | Divergente positiva | L **maior** que a tolerância |
| 16 | % divergente positiva | 15 ÷ 13 |
| 17 | Desvio médio (com sinal) | média de L |
| 18 | Desvio médio absoluto | média de \|L\| |
| 19 | Maior desvio positivo | maior L acima da tolerância |
| 20 a 22 | Cruzamento por OC, por placa, sem correspondência | contagem da confiança |
| 23 | Soma \|Peso BL − Peso Saídas\| | \|F − H\|, fora os "Analisar" |
| 24 | Fora de escopo | pesagens tiradas pela lista |

E, abaixo, o bloco das **divergências nos dois sentidos**: quantas, a diferença
absoluta total em kg, o maior desvio absoluto, a frase-síntese e uma linha por
divergência (data, placa, parceiro, NF, produto, pesos, diferença e desvio).

> **Atenção à convenção do operador** `[FATO]`: as linhas 14 a 19 contam só
> o lado **positivo** (nota maior que a balança). Uma divergência negativa —
> balança maior que a nota — entra em "Não divergente positiva", e só aparece
> no bloco de detalhamento, que conta os dois lados. O manual chama isso de
> convenção; o porte preserva e pergunta ([02](02-plano-do-porte.md) § 9).

Os indicadores das linhas 12 a 19, 23 e o bloco de divergências são
**fórmulas** apontando para `Desvios`, com os nomes definidos `TOL_DESVIO`
(ligado a `'Resumo Geral'!C6`), `TRAVA_DESVIO`, `PER_INI` e `PER_FIM`. Mudar
`C6` no relatório recolore a planilha e refaz os indicadores. As linhas 20 a 22
e 24 são **valores** gravados pela macro.

## 5. O que ela entrega

Um `.xlsx` sem macro, `Faturabot_Desvio_Balanca_AAAA-MM-DD_HHMM.xlsx`, na pasta
de destino, com estas abas nesta ordem:

| Aba | Conteúdo | Valor ou fórmula |
|---|---|---|
| Resumo Geral | parâmetros, indicadores, divergências e a frase-síntese | fórmulas, com quatro linhas de valor |
| Desvios | uma linha por pesagem em escopo, colunas A a L (linha 1: de onde vem cada coluna; linha 2: cabeçalho) | **fórmulas** (`INDEX` nas abas de apoio, pela linha registrada na `BL`) |
| Sem Correspondência | agendamentos, OCs consolidadas e pesagens sem par | valores |
| BL | as pesagens, e nas colunas M a S: OC extraída, origem, linha de G, linha de H, confiança, motivo e fonte de H | valores |
| AG. Faturamento | os agendamentos de coleta | valores |
| AG. Recebimento | os de recebimento, e nas colunas K a N: peso da nota, fator, peso documental e a base dele | valores |
| Saídas (OC) | uma linha por OC consolidada | valores |
| Saídas | todas as notas, com o tratamento de cada uma | valores |
| MIC | só quando o MIC vem: nota, peso, tratamento, placa que casou e pesagem | valores |
| Fora de Escopo | oculta quando tem linha; visível e vazia quando a regra não pegou nada | valores |

Qualquer número de `Desvios` é rastreável até a nota: coluna S da `BL` (fonte),
coluna P (linha na fonte) e a linha na aba da fonte.

E uma mensagem final com o arquivo gravado, os relatórios reconhecidos e
quantos registros cada um trouxe, o período apurado e os avisos de formatação
("ajustes visuais não aplicados; os números não são afetados").

## 6. A consolidação semanal

A segunda macro. Recebe relatórios **gerados pela conferência** — os da macro e
também os que o operador ajustou à mão — e devolve
`Faturabot_Consolidado_Balanca_AAAA-MM-DD_HHMM.xlsx`.

**Entrada.** Qualquer arquivo com aba `Desvios` que tenha as colunas `Data Peso
Tara`, `Placa`, `Remetente`, `Produto`, `Operação`, `PESO BALANÇA`, `PESO AG.
FAT.`, `PESO SAÍDAS` e `Percentual de desvio`. O que não tiver é ignorado e
listado.

**Período de cada relatório**, na ordem `[FATO]`:

1. o texto "Período…" de `B3` da aba `Resumo Geral` ou `Resumo` ("Período: 18 a
   19/09/2026", "Período 16 a 17/09/2026", "Período analisado: 14/09/2026 a
   15/09/2026", "30/09 a 01/10/2026", um dia só);
2. o nome do arquivo ("BALANÇA GUARÁ 14 a 15-09.xlsx");
3. a menor e a maior data das pesagens.

**Regras.** Relatórios ordenados pelo início do período; dentro de cada um, a
ordem da aba `Desvios`. A mesma pesagem — placa, data e hora ao minuto, peso da
balança — em dois relatórios entra uma vez, a do relatório mais antigo. Todas
as linhas entram, inclusive as da noite anterior. O status é **recalculado**
com a tolerância e a trava do painel; linha marcada "Analisar" no relatório de
origem e sem peso da nota mantém a marcação, porque não há como recalculá-la.

**Saída.** Duas abas:

* **Base Consolidada** — uma linha por pesagem: Período, Arquivo origem,
  Data/Hora, Placa, Parceiro, Produto, Operação, Peso Balança, Peso Sistema,
  Peso NF/Saídas como valores; Tolerância kg, Diferença Sistema, Diferença NF,
  Desvio %, Status e Desvio Abs % como fórmulas. Status: Conforme, Divergente,
  "Analisar confronto de peso" ou "Sem correspondência", cada um com sua cor;
* **Resumo Consolidado** — título ("CONSOLIDADO GERAL — BALANÇA GUARÁ"),
  período total e tolerância, a leitura rápida numa frase com singular e
  plural, os indicadores gerais, o resumo por período e o resumo por operação.
  Tudo fórmula. "Analisar" fica fora das somas em kg.

Diferente da conferência, o desvio aqui é **Peso NF ÷ Peso Balança − 1**
calculado de novo na fórmula — mesma conta, outra origem.

## 7. O que é Excel, e não regra

Tudo isto existe porque a ferramenta mora dentro do Excel, e some fora dele:

| No VBA | Por quê existe |
|---|---|
| `ModoRapido` (cálculo manual, tela congelada, eventos e alertas desligados) | velocidade e silêncio do Excel durante a escrita |
| cache do bloco de cabeçalho por planilha | cada leitura de célula é uma chamada COM cara; relatório Sankhya tem mais de 300 colunas |
| camada cosmética que registra a falha e segue | formatação que falha no Excel não pode derrubar o cálculo já feito |
| tentativa dupla de formatação condicional, ativando a aba | o Excel resolve referência relativa contra a célula ativa |
| gravação das fórmulas de `Desvios` em bloco e, se falhar, uma a uma | achar qual fórmula o Excel recusou |
| `ADODB.Stream`, com leitura byte a byte de reserva | ler UTF-8 em VBA |
| `PastaDestino` com fuga do OneDrive para Documentos | `SaveAs` falha em endereço `https` |
| `GetOpenFilename`, `MsgBox`, congelar painel, ativar aba | a interface é o próprio Excel |
| instalação: importar `.bas`, compilar, rodar o autoteste, "Desbloquear" o arquivo | é assim que código chega a uma planilha |

## 8. Achados da leitura

O que a leitura do código mostrou e o manual não diz. Nenhum foi medido contra
dado real — não houve dado real nesta etapa.

| # | Achado | Tipo | Efeito hoje |
|---|---|---|---|
| A1 | O painel do `.xlsm` está deslocado: tolerância e janela editáveis em `B3`/`B4`, lidas de `C5`/`C6` (§ 3.4) | defeito `[FATO]` | nenhum enquanto os valores forem os padrões; mudar a tolerância **não tem efeito** |
| A2 | Dois arquivos do mesmo papel (BL, AGFAT, AGREC ou MIC): o **último vence em silêncio**. Se o segundo for menor, as linhas que sobram do primeiro continuam na aba de apoio sem entrar na conta | defeito `[FATO]` | só quando alguém anexa dois do mesmo |
| A3 | Portal de Vendas e PMI, ao contrário, **somam**: vários arquivos de cada viram uma lista só, com a nota repetida contada uma vez | comportamento `[FATO]` | — |
| A4 | Operação da balança diferente de Coleta e Recebimento não cruza com nada e não aparece nos indicadores por operação | comportamento `[FATO]`; se existe na prática, `[INFERÊNCIA]` a validar | desconhecido |
| A5 | Uma OC consolidada com nota do PMI pode servir de peso documental a **uma coleta e a um recebimento** ao mesmo tempo — os dois grupos de candidatos compartilham as linhas e marcam "usado" cada um no seu | comportamento `[FATO]`; se é intencional, `[INFERÊNCIA]` | transferência entre unidades pesada na saída e na chegada em Guará |
| A6 | "Divergente positiva" conta um lado só (§ 4.9) | convenção `[FATO]` | divergência negativa some das linhas 14 a 19 |
| A7 | Na extração da OC, a primeira âncora achada com número de tamanho errado **encerra** a busca: `OC 12 / OC 71145` não acha 71145 | defeito menor `[FATO]` | raro |
| A8 | Número de 7 dígitos depois de "OC" é aceito — o próprio autoteste espera `OC 1.059.307` → 1059307, que tem cara de NF | regra `[FATO]` | depende de como o campo Observação é preenchido |
| A9 | A primeira passada, por OC, não olha data: uma OC antiga no export do sistema casa | comportamento `[FATO]` | baixo, se o export cobre só o período |
| A10 | Pesagem sem correspondência que está **fora de escopo** entra também na aba `Sem Correspondência` | comportamento `[FATO]` | uma linha a mais no relatório |
| A11 | A aba `Desvios` é fórmula que aponta para outras abas **pela posição da linha**. Reordenar a `BL` ou uma aba de apoio no relatório gerado quebra os números sem erro visível | fragilidade `[FATO]` | só se alguém reordenar |
| A12 | Data que chega como texto é lida pela configuração regional do Windows (`IsDate`/`CDate`) | fragilidade `[FATO]` | nenhum numa máquina em português |
| A13 | "Balança Guará" está escrito no código, no título do consolidado | literal `[FATO]` | — |
| A14 | Os indicadores de maior desvio usam `MAXIFS`/`MINIFS` (Excel 2019 ou 365) e o Resumo usa a fonte Aptos (Office 365) | compatibilidade `[FATO]` | já documentado no manual |

## 9. Resumo do que se tem nas mãos

* **Uma regra de conferência bem definida e bem documentada**, com decisões
  explícitas e rastreáveis — fonte de cada peso, confiança de cada casamento,
  tratamento de cada nota. É o que se porta.
* **Um autoteste de verdade** (os 24 casos da OC) e fórmulas conferidas em oito
  casos reais — que viram teste do porte.
* **Nenhuma execução real da macro ainda**, e portanto nenhum padrão-ouro de
  "entrada → saída da macro". É a pendência que decide quando o porte pode ser
  chamado de provado.
* **Um painel que não é lido onde é editado** (A1) — a primeira coisa a dizer
  ao operador, antes mesmo do porte.
