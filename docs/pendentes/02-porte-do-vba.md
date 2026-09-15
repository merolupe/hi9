# O porte dos geradores de pendentes: do VBA para o Python

> Registro do que muda, do que fica igual e de como o porte se prova.
> Irmão de [`../fiscalbot/02-porte-do-vba.md`](../fiscalbot/02-porte-do-vba.md),
> e escrito com a mesma disciplina: **cada defeito corrigido precisa de medição
> antes de mexer, e cada comportamento preservado precisa de razão.**
>
> Público: analista desenvolvedor + Gerência Fiscal/Tributária.
>
> `[FATO]` = verificado no código VBA extraído · `[INFERÊNCIA]` = dedução ·
> `[MEDIR]` = número que só existe com o arquivo real, e que precisa ser medido
> **antes** de mexer.

---

## 1. O critério

Um porte destes não se declara pronto: se prova. O critério é **divergência
zero** contra a macro, célula a célula, e não "quase igual" — a planilha de
mercadorias vira cobrança formal por e-mail às áreas guardiãs e é evidência de
controle interno. Cada divergência é uma nota cobrada de quem não devia, ou não
cobrada de quem devia.

## 2. A procedência dos artefatos, e o que o diff respondeu

`[FATO]` Os dois binários foram abertos com `python3 -m oletools.olevba
--code`. Cada ferramenta tem **um único módulo** com código; `EstaPastaDeTrabalho`
e `Planilha1` estão vazios nos dois.

| Binário | Módulo | Linhas |
|---|---|---|
| `ferramenta-gerarnfependentes.xlam` | `GerarPendentes.bas` | 1.978 |
| `GerarServicosPendentes.xlsm` | `RelatorioServicosPendentes.bas` | 1.342 |

`[FATO]` Normalizando a codificação (os `.bas` entregues estão em **cp1252**; o
olevba devolve UTF-8) e removendo a linha `Attribute VB_Name` que o editor VBA
acrescenta na exportação, os arquivos são **byte a byte idênticos**:

```
diff -u bas_merc_v14.utf8.bas  xlam_GerarPendentes.bas           → 0 diferenças
diff -u bas_serv_v2.utf8.bas   xlsm_RelatorioServicosPendentes.bas → 0 diferenças
```

### O que estava em aberto, e a resposta

**O `.xlam` em produção é exatamente o `GerarPendentes_v14`. A rodada de
formatação de 17/08/2026 nunca entrou. Não existe v15.**

`[FATO]` Verificação item a item dos dez ajustes pedidos em 17/08:

| Ajuste pedido | Presente no `.xlam`? |
|---|---|
| Verde como cor padrão do título "Resumo executivo" | **não** — é `COR_NAVY` |
| Verde no título acima da pizza | **não** — é `COR_AZUL` |
| Pizza sem título, ocupando mais espaço | **parcial** — `HasTitle = False` já vinha da v13; a área segue `B4:E11` |
| Números em branco e negrito na pizza | **não** |
| Legenda da pizza ampliada (fonte 16, negrito) | **não** |
| Legendas suprimidas nos gráficos de barra | **não** — os três têm `HasLegend = True` |
| Números em branco nos gráficos de barra | **não** |
| `GapWidth = 35` no gráfico horizontal de guardião | **não** — a string não ocorre no arquivo |
| Zeros suprimidos ponto a ponto lendo `.Values` | **não** |
| `ReversePlotOrder` no eixo de categoria | **sim** |

`[INFERÊNCIA]` O único item presente veio junto com a v13, que introduziu a
ordenação por volume decrescente — a inversão de plotagem é a contrapartida
necessária daquela ordenação, e o comentário do código a justifica nesses
termos. `[FATO]` O histórico de versões embutido no módulo vai até
`v14.0 (dimensoes definidas pelo usuario)` e não menciona rodada posterior.

**Consequência prática:** o alvo do porte é a v14, e o estado visual de hoje é
o da v14. Se a rodada de 17/08 ainda for desejada, ela é pedido novo — e entra
na entrega do Resumo Executivo, não como "restaurar o que existia".

### As divergências que a implementação de serviços encontrou

`[FATO]` Ao portar linha a linha, apareceram cinco pontos em que a
documentação do porte e o `.bas` não diziam a mesma coisa. **Em todos, o VBA
venceu** — é ele que está em produção, e divergência de célula é divergência.

| # | A documentação dizia | O VBA faz | O que se fez |
|---|---|---|---|
| V1 | a coluna 36 sem vínculo é `""`, `Sem cadastro de parceiro` ou `Nao encontrado` | confirmado — **e o caso "sem código de filial" cai em `Nao encontrado`**, indistinguível de "procurei e não achei" | preservado o rótulo do VBA; a distinção vai para a lista bloqueante da tela, com o CNPJ nomeado |
| V2 | o vínculo é filtrado por data e por valor | há **duas guardas a mais**, não registradas: a nota só é vinculável se a emissão for data interpretável **e** o valor for maior que zero; e o pedido candidato precisa ter valor maior que zero | reproduzidas as quatro condições |
| V3 | `mapQtdAsis` conta as notas do ASIS por CNPJ de prestador | confirmado — **e não descarta o CNPJ zerado**, ao contrário do lado do Portal de Compras, que descarta | preservada a assimetria, e registrada como preservado nº 25 |
| V4 | a herança lê `Nro Nota` + `Cod Parceiro` | confirmado no corpo do procedimento — mas o **comentário de cabeçalho do próprio `CarregarHerancaAnterior` diz "nota normalizada + CNPJ prestador"**, e contradiz o código logo abaixo | seguido o código; o comentário de cabeçalho está errado desde que foi escrito |
| V5 | `DecodificarSemaforo` tem "quatro estados" numa seção e "5 ramos" noutra | são **seis caminhos**: quatro códigos, o fallback de HTML desconhecido (vazio) e o fallback de texto cru | `farol.traduzir` implementa os seis; a carga de fábrica cadastra os quatro códigos, que é a parte parametrizável |

`[FATO]` E uma divergência entre a documentação da **entrega 1** e o que é
possível: `docs/pendentes/01-arquitetura.md` afirmava que a colisão silenciosa
de chave de herança entre dois prestadores sem cadastro *deixa de existir*
porque o livro guarda o CNPJ. Não deixa: a planilha que o time devolve editada
**não carrega CNPJ**, e a chave de ingestão continua sendo a única
reconstruível a partir dela. O que o livro entrega é a **detecção** — a
execução conta quando o dono de uma chave muda. Eliminar de vez exige uma
coluna nova na aba, que muda a largura de 36 e é invariante da prova. Virou a
[decisão pendente nº 14](05-decisoes-pendentes.md).

## 3. Onde o padrão-ouro mora

`competencias/pendentes/`, **fora do git**, exatamente como
`competencias/fiscalbot/` (regra nº 1). O `.gitignore` cobre a pasta inteira.

Duas provas, quando os arquivos chegarem:

1. **Mercadorias** — os três arquivos de uma semana real (`XML{N}.xls`,
   `CE{N}.xls`, `XMLAnterior.xls`) **e** o `Pendentes{N}.xls` que a macro gerou
   a partir deles. Comparação célula a célula nas abas `Pendentes` (38
   colunas), `PENDENTES FIS-FAT` (36), `CTe`, `Manifestados`, `Entradas 3os`
   (27 cada) e `Lançados` (33). O `Resumo Executivo` compara-se pelos
   **valores** — tabela por categoria, os dois TOP, as quatro séries do
   `_AuxResumo` —, nunca pela aparência.
2. **Serviços** — o par `ASIS.xlsx` + `PC27.xlsx` de 10/08/2026, a Conferência
   de Serviços e a semana anterior daquela data, **e** o
   `Notas_Servico_Pendentes_*.xlsx` daquela execução. Comparação célula a
   célula nas quatro abas.

`[FATO]` Dadas as mesmas entradas, os dois módulos são determinísticos — a
herança vem inteira do arquivo anterior e a cascata de serviços é, por desenho,
independente da ordem das linhas. A comparação é legítima e repetível.

**Sem esses arquivos o teste é pulado — e então ninguém pode dizer que o porte
está provado.** A frase é do documento do Fiscalbot e vale aqui sem alteração.

### Os números de referência, para quando houver arquivo

`[FATO segundo o dossiê]` `[INFERÊNCIA quanto à reprodutibilidade]` — vêm de
espelhos Python rodados contra arquivos que ainda não foram recebidos.

**Serviços — ASIS + PC27 de 10/08/2026:** 2.797 lançamentos indexados; 2.670
lançadas; 210 pendentes; 206 canceladas; 127 sem correspondência. Confronto por
procedimento: 2.467 / 0 / 191 / 12.

`[FATO]` Três identidades aritméticas fecham, e é isso que torna esses números
utilizáveis como linha de base:

* 2.467 + 0 + 191 + 12 = **2.670** = lançadas — e portanto **o proc 2 resolveu
  zero** naquela execução; o `—` do dossiê significa zero, não "não medido";
* 2.670 + 127 = **2.797** = lançamentos indexados — cada lançamento é consumido
  no máximo uma vez, e a aba inversa é exatamente o complemento;
* 2.670 + 210 + 206 = **3.086** = notas do ASIS processadas.

**Mercadorias — CE da semana 30:** 6.864 linhas, cabeçalho na linha 3, 6.844
chaves distintas, 17 chaves com múltiplas linhas e **zero** divergência de
pedido ou farol entre elas, farol 1.242 `Sim` / 143 `Não` / 5.459 vazio.

## 4. O que sai, e por quê

| Sai | Motivo | Entra no lugar |
|---|---|---|
| **Excel como motor** | a regra em `.bas` não tem diff, não tem revisão e não tem teste | motor em Python, com teste por invariante |
| **O ambiente inteiro** — ano `2026` no código, raiz do OneDrive, `LocalizarPastaSemana`, cópia para `%TEMP%`, `SetAttr` | a Central entrega o arquivo já gravado, local | nada; some |
| **`AbrirWorkbookRobusto`** e as três estratégias de abertura | não há Excel para reaproveitar workbook aberto | `planilha.ler` |
| **Os quatro `FileDialog`** de serviços | a interface é arrastar | reconhecimento por âncora de cabeçalho |
| **O `InputBox` do número da semana** | não há campo de texto na tela de execução | semana deduzida e **exibida** como ficha (pendência 7) |
| **O arquivo da semana anterior como fonte da verdade** | perder o anexo apagava a classificação de todos | o livro em `dados/pendentes/` |
| **`.xls` 97-2003 como saída** | `openpyxl` não escreve `.xls`; `xlwt` está abandonado; serviços **já** entrega `.xlsx` | `.xlsx`. A leitura de entrada continua aceitando `.xls` |
| **`AtualizarResumoExecutivo` como rotina** | round-trip por openpyxl descarta o XML de gráfico | vira **modo de execução**: a planilha é regerada do zero, e o problema deixa de existir |
| **`Application.StatusBar`, `ScreenUpdating` e `Calculation`** (serviços) | não há Excel para pôr em estado ruim nem para restaurar | nada; some. O progresso, quando fizer falta, é a barra da própria janela |
| **O `MsgBox` final com seis contagens** | mensagem que some ao clicar em OK, e que ninguém guarda | o `Resultado` da tela, e o `resumo.json` do snapshot, que fica |

## 5. O que fica idêntico, de propósito

* **Nomes, ordem e ordem de colunas das abas.** A planilha vai por e-mail para
  dezenas de pessoas que sabem onde cada coluna está, e várias mantêm PROCX e
  tabela dinâmica por cima. `[FATO]` 38 / 36 / 27 / 33 em mercadorias;
  12 / 36 / 16 / 7+N em serviços.
* **O `"Sem cadastro"`**, literal, nos dois domínios.
* **O `"não"` minúsculo** gravado em `Conf fisica` / `Conf fiscal` /
  `Incongruência` quando a nota não está na Conferência de Entradas (ver
  preservado 19).
* **O rótulo `Retorno semana {N-1}`**, com o número da semana **anterior**.
* **As larguras diferentes das abas auxiliares**, que são acidente do momento
  em que cada uma copia o cabeçalho — e são invariante da prova (pendência 8).
* **O `"Nao encontrado"`** da coluna `Pedido de compra mais recente` e da
  coluna 36, e o **`"CNPJ nao mapeado: {cnpj}"`** dentro da célula de filial —
  os três literais, com a grafia sem acento que o VBA usa.
* **A ordem de reordenação das colunas de origem** da aba inversa: as cinco
  pré-definidas, depois as que têm `CIDADE` no nome, depois as demais na ordem
  do arquivo. E o bloco de análise **antes** delas, não depois.

A única aba nova é **`Descartados`**, em mercadorias: as linhas excluídas pelas
regras A1 (XML de terceiro) e A3 (NF-e destinada a transporte), com a coluna do
motivo. `[FATO]` Hoje elas somem sem rastro, sem contador e sem aba. É
**acréscimo**, não alteração: nenhuma aba existente muda.

## 6. Os defeitos que o porte corrige

### 6.1 Sem medição — porque não mudam resultado nenhum, só caminho de falha

| # | Defeito | Correção | Por que dispensa medição |
|---|---|---|---|
| 1 | `ConstruirResumoExecutivo` aborta sem criar a aba, e a etapa 18c executa `Sheets(SHEET_RESUMO).Activate` em seguida → **erro 9 não tratado, o `SaveAs` nunca ocorre, a execução inteira é perdida** | a planilha é gravada independentemente do painel; falha no painel vira `Lista` de tom `erro` | em execução bem-sucedida a saída é idêntica. Muda só o caminho de falha, onde hoje o resultado é *nenhuma saída* |
| 2 | Mercadorias não tem `On Error GoTo`: qualquer erro deixa 3 workbooks abertos, `ScreenUpdating=False`, `DisplayAlerts=False` e temporários no disco | sai de graça — não há Excel, e o `servidor.py` já envolve a chamada em `try/except` | não existe Excel para deixar em estado ruim |
| 3 | Conferência de Serviços: a guarda protege só `Parceiro` e `Empresa`; faltar **qualquer uma das outras seis** levanta erro e **aborta a execução inteira** | tratamento uniforme: falta de qualquer coluna do bloco → o bloco não roda, as colunas 29–36 saem vazias e o aviso vai para a tela | hoje o resultado é *crash*, não resultado. Não há o que comparar |
| 4 | Mercadorias **aborta** se `XMLAnterior.xls` não existir | com o livro, a ausência do arquivo é normal | idem |
| 5 | `SEP = Chr(1)` + `Split` com índices fixos: um `Chr(1)` colado em qualquer célula desloca os cinco campos em silêncio | desaparece — em Python cinco campos são cinco campos | a técnica não existe mais |
| 6 | Validação de colunas: mercadorias lista **todas** as faltantes, serviços aborta na **primeira** | uniformiza na ergonomia de mercadorias | o mesmo conjunto de execuções aborta; muda a mensagem |
| 7 | Ano `2026` no código: em 01/2027 cai no seletor manual toda execução | desaparece com o ambiente | não há resolução de caminho |

`[FATO]` Os itens 1 a 7 desta tabela **estão todos resolvidos**. Os itens 2, 4,
5 e 7 caíram com o ambiente, na entrega 1; o 6 veio do núcleo, na mesma
entrega.

`[FATO]` **Os itens 1 e 3 fecharam na entrega de serviços**, e os dois merecem
o registro de como:

* **item 3** — a falta de qualquer coluna da Conferência de Serviços agora
  desliga só o bloco de vínculo. `execucao.gerar` envolve a leitura da
  Conferência num `try` que captura coluna faltante e cabeçalho não
  localizado, as colunas 29 a 36 saem vazias e a tela recebe o aviso com o
  motivo. Há teste: `test_sem_a_conferencia_a_planilha_sai_com_as_colunas_de_vinculo_vazias`;
* **item 1** — a planilha de serviços é gravada antes de o livro e o snapshot
  serem escritos, e nenhuma dessas três etapas depende de painel nenhum. O
  equivalente exato do defeito (o `Activate` depois de a aba do resumo não ter
  sido criada) é de mercadorias e fecha na entrega 3; o que a entrega de
  serviços prova é que a ordem escolhida — gravar primeiro, enfeitar depois —
  já está no código.

### 6.2 Com medição obrigatória antes de mexer

**Nenhum destes foi mexido.** Todos ficam como estão hoje, defeito e tudo, até
a medição existir — é o padrão assumido da pendência nº 1.

| # | Defeito | Correção proposta | A medição `[MEDIR]` |
|---|---|---|---|
| 8 | **A herança de mercadorias lê as colunas 1 a 5 por posição fixa**, sem consultar cabeçalho — o mesmo antipadrão que a v7 removeu da etapa 15, e o contrário da convenção do próprio projeto | ler por cabeçalho, com nomes canônicos e sinônimos | rodar as duas leituras sobre um `Pendentes{N-1}.xls` real e confirmar herança **idêntica para 100% das chaves**. Se divergirem, a leitura posicional já estava errada e o time precisa saber desde quando |
| 9 | `lastRow = Cells(Rows.Count, 6).End(xlUp).Row` (coluna 6 no código) e `colChaveNova = colChaveAtual + 5` | âncora por nome de coluna | a mesma medição do item 8, no mesmo arquivo |
| 10 | **Comparações assimétricas no roteamento e na etapa 15**: a condição 1 sem `Trim`, a 2 com `LCase` mas sem `Trim`, as 3 e 4 exatas e sensíveis a caixa, a etapa 15 com `= "Sim"` exato — enquanto B1 e B2 usam `vbTextCompare` | uma disciplina só: comparar por `chave_de_texto` em todas | contar, no XML e no CE reais, quantas linhas têm valor que difere dos literais **só** por caixa, acento ou espaço. Se for **zero**, a uniformização não muda destino nenhum. Se for maior que zero, **o código de hoje está perdendo linhas**, e o número vai para o time fiscal antes da troca |
| 11 | **Chave de acesso comparada sem normalização** (`CStr` dos dois lados); a integridade é sustentada só por `NumberFormat = "@"` | normalizar para só-dígitos dos dois lados | contar quantas chaves mudam ao normalizar e quantos confrontos XML × CE passam a casar. Esperado: zero e zero. Confronto novo = nota hoje reportada como pendente indevidamente — achado relevante, não detalhe técnico |
| 12 | `ConverterDataHora` devolve `""` quando não interpreta, enquanto `ConverterDataBR` devolve o texto original e o deixa visível | uniformizar no comportamento de `ConverterDataBR`, e contar na tela | contar quantos valores são ininterpretáveis nos arquivos reais. Se for zero, a troca é inócua; se não, ela **revela** dado que hoje some |

`[FATO]` O item 12 está implementado **com o defeito preservado**:
`valores.data_hora` devolve vazio, e o docstring da função registra a
assimetria e aponta para esta tabela. Há teste que trava o comportamento de
hoje — para que a mudança, quando vier, seja deliberada.

`[FATO]` O motor de serviços acrescentou a **medição que falta** ao item 12 sem
mexer no comportamento: a tela passa a contar as datas de emissão do ASIS que
não foram interpretáveis e ficaram como texto. Quando o número aparecer numa
execução real, a decisão deixa de ser hipótese.

O item 11 tem função pronta (`chaves.chave_de_acesso`) mas **não aplicada ao
confronto**: ela é usada apenas no livro de classificação, que é nosso e não
tem macro com que divergir.

### 6.3 O que a entrega de serviços corrigiu, e que não estava na lista

`[FATO]` Três coisas que o VBA faz em silêncio e que agora têm número na tela.
Nenhuma delas muda uma célula da planilha: mudam o que a pessoa sabe depois de
rodar.

| O quê | Hoje | Agora |
|---|---|---|
| Lançamento TOP 2020/2111 com CNPJ vazio ou zerado | não é indexado em lugar nenhum, some da análise e da aba inversa, **sem contagem e sem aviso** | contado e exibido em `Ficaram de fora da análise` |
| Número de nota que sofreu o corte de prefixo de ano | o corte é premissa declarada em comentário, e invisível na execução | contado — quando um número legítimo de 13+ dígitos começando em `20` for mutilado, o número aparece |
| Nota que recebeu pedido de compra de outra filial | `mapPedido` é indexado só por CNPJ do parceiro e ninguém percebe | contado; é a medição que fundamenta a pendência 5 |

`[FATO]` E uma quarta, que o VBA conta mas não mostra a lista: **os quatro
procedimentos de confronto** aparecem discriminados na tela. A `MsgBox` da
macro só avisa que o procedimento 4 exige revisão; aqui os quatro números vêm
com a contagem, e a soma tem de dar `Lançadas` — é o teste de regressão
visível, que dispensa abrir teste para conferir.

## 7. O que o porte preserva de propósito

| # | Comportamento | Por que preservar |
|---|---|---|
| 13 | **"Primeira ocorrência vence"** nos 12 dicionários dos dois módulos | `[FATO]` medido: no CE da semana 30, 17 chaves têm múltiplas linhas e **zero** divergem em pedido ou farol. A regra é segura com os dados reais. Muda só o que falta: passa a **contar e listar** as duplicadas, e divergência de conteúdo entre linhas fica bloqueante |
| 14 | **Segregar canceladas antes da cascata** (serviços), mesmo sabendo que isso infla `Sem Correspondencia ASIS` | o comentário do VBA justifica: uma cancelada que casasse por CNPJ+valor consumiria lançamento de outra nota. O efeito colateral é real, mas o remédio seria pior. Vira limitação documentada |
| 15 | **Comparação antes/depois estrita** — emissão do ASIS na mesma data do `Dt. Neg.` não conta nem como antes nem como depois | o código decidiu e o dossiê só duvidava. Mudar move contagens das 127 linhas de referência. Pendência 4 |
| 16 | **`Diferenca = Entradas − ASIS`**, comparando universos diferentes | confirmado no código. É métrica aproximada e o time já a lê assim. Preservo o número e documento a aproximação |
| 17 | **`mapPedido` indexado só por CNPJ do parceiro**, sem filtro de filial nem de período, vencendo o maior `Nro. Unico` | mudar muda colunas que o time lê (Pedido, Comprador, Requisitante). Preservo e **conto** os casos de pedido de filial diferente. Pendência 5 |
| 18 | **`Lancadas` coluna 8 = `"Nao"` em 100% das linhas** | coluna sem informação por construção, mas removê-la muda 12 colunas para 11 — invariante da prova, e possível alvo de fórmula de terceiro |
| 19 | **Notas ausentes do CE recebem `"não"` minúsculo** em `Conf fisica` / `Conf fiscal` / `Incongruência` | `[INFERÊNCIA]` afirma ausência onde não há informação — mas é **por efeito colateral dessa afirmação** que a regra B1 não dispara para nota fora do CE. Trocar para vazio faria `zero_ou_vazio` devolver True e **reclassificaria notas para Fiscal indevidamente**. Preservo o literal e torno a condição de B1 explícita no código (*esteve no CE* **e** *física = Sim* **e** *incongruência vazia ou zero*), documentando que o resultado é o mesmo. `[MEDIR]` confirmar divergência zero nessa reescrita |
| 20 | **A ordem das regras**: A1 antes de A3; limpeza antes do roteamento; B1 depois da herança e antes de B2; a cascata de serviços **por passos**, não por linha | são as ordens que carregam a correção de defeitos antigos, e o VBA documenta cada uma. Cada ordem vira um teste nomeado |
| 21 | **O fallback de unidade e de categoria devolve o texto original** | é a regra nº 4 em ação: *nenhum registro desaparece silenciosamente do resumo* é o comentário do próprio VBA. Preservo o valor e acrescento o bloqueio |
| 22 | **`Dias Emissão Doc` está em `dateCols` e em `fmtDateCols`** — se for contagem de dias, o valor 30 exibe `30/01/1900` | `[INFERÊNCIA]` não confirmada. Preservar um defeito visível é melhor do que corrigir por suposição. Pendência 2 |
| 23 | **`Dt. Conf. Física` e `Dt. ult. anexo` retêm hora e exibem só data** | mudar formato é visível para todo mundo que recebe a planilha. Pendência 3 |
| 24 | **A coluna 36 grava `Nao encontrado` quando falta o código da filial** — o VBA não distingue esse caso do "procurei e não achei" | inventar um rótulo novo seria divergência de célula. Quem distingue é a tela, com o CNPJ nomeado na lista bloqueante |
| 25 | **`mapQtdAsis` conta todo CNPJ de prestador não vazio, inclusive o zerado** — assimétrico com o lado do Portal de Compras, que descarta o zerado | é o universo que a coluna `Qtde notas do parceiro (ASIS)` sempre mediu; mudar muda o número que o time lê |
| 26 | **O RPS do procedimento 2 não passa pelo corte de prefixo de ano** que o número da nota sofre | assimetria registrada no código. Um RPS com prefixo de ano não casaria; medir exige arquivo real |

`[FATO]` Os itens 14 a 18 e 20 são de serviços, e **todos têm teste nomeado**
desde esta entrega: a segregação das canceladas antes da cascata, a comparação
antes/depois estrita, a `Diferenca` entre universos diferentes, o
`mapPedido` por CNPJ e a coluna 8 literal da `Lancadas`.

## 8. As onze armadilhas que uma reimplementação ingênua cairia

`[FATO]` Todas verificadas no código. As que já têm defesa nesta entrega estão
marcadas.

| # | A armadilha | Defesa |
|---|---|---|
| 1 | Rodar a cascata de serviços **por linha** em vez de **por passo** — o laço externo é o passo. Invertido, uma chave fraca consome o lançamento de um match forte, e o resultado passa a depender da ordem das linhas | **`confronto.confrontar`, com dois testes**: um monta o caso em que as duas ordens divergem e roda a cascata ingênua dentro do próprio teste para comparar; o outro embaralha as linhas e exige o mesmo resultado |
| 2 | Achar que aplicar o formato **depois** de escrever resolve. `Insert Shift:=xlToRight` faz a coluna nova herdar o formato da vizinha, e gravar data em célula Texto converte o valor sem levantar exceção | **`escrita.preparar_aba` formata antes, e há teste** |
| 3 | Buscar a pasta da semana recursivamente — encontraria `Serviços\Semana 30` querendo `Mercadorias\Semana 30` | o ambiente desapareceu |
| 4 | Tratar o farol vazio como "Não" — são três estados, e vazio significa *sem pedido vinculado* | **`farol.py`, com teste** |
| 5 | Supor que o número da nota no ASIS é o número do lançamento — há prefixo de ano de 4 dígitos, e prefeituras que informam a RPS como número da nota | **`chaves.analisar_numero_de_nfse`, com teste** |
| 6 | Assumir que a chave de herança de serviços é nota + CNPJ. É nota + **Cod Parceiro** | **`execucao._chave_de_heranca`, com teste de ida e volta.** O livro guarda o CNPJ e **conta** a colisão — eliminá-la exige uma coluna nova na planilha, que é decisão pendente |
| 7 | Assumir que as abas auxiliares têm o mesmo número de colunas da principal | documentado como invariante |
| 8 | Assumir que `Canceladas` (serviços) é `Pendentes` + 2 colunas. É layout próprio de 16 | **`colunas.CANCELADAS`, com teste que compara as duas ordens internas** |
| 9 | Assumir que a herança de mercadorias lê por cabeçalho. Lê as **colunas 1 a 5 por posição** | **`estado.extrair_da_planilha` lê por cabeçalho, com teste** — e o defeito 8 mede a diferença |
| 10 | Assumir que `NormalizarTexto` faz a mesma coisa nos dois módulos | **`aparar` × `chave_de_texto`, com teste lado a lado** |
| 11 | Achar que `Retorno semana N` se refere à semana corrente. É `semana - 1` | **`estado.semana_do_rotulo`, com teste** |

E uma décima segunda, que o desenho do porte não previa e o código revelou:

| 12 | Achar que âncoras positivas bastam para reconhecer o arquivo. A planilha da semana anterior **contém as 27 colunas do XML** | **âncora ausente (`Guardião`), com teste** |

## 9. O que o porte ganha

* **A classificação deixa de morar no anexo do e-mail.** O livro guarda todo
  mundo, para sempre, com carimbo de quem gravou.
* **A semana vira evidência.** O snapshot imutável guarda a planilha, o livro e
  a impressão digital de cada entrada.
* **O que hoje some passa a ser contado**: linhas descartadas pelas regras A1 e
  A3, chaves duplicadas, lançamentos com CNPJ zerado, números de NFS-e que
  sofreram corte de prefixo de ano, datas não interpretáveis.
* **A coluna renomeada deixa de parar a rotina semanal.** Cadastra-se o
  sinônimo na tela.
* **Teste.** 167 em `pendentes/`, todos sobre comportamento — 98 do núcleo, 69
  do motor de serviços.

## 10. Desempenho — a expectativa, não a medição

`[INFERÊNCIA]` O gargalo será a escrita, não o cálculo: foi assim no Fiscalbot
(18 s para 6.554 registros, "o gargalo é a escrita das 504 mil células
formatadas"). Mercadorias escreve ~2.500 × 38 células mais o painel; serviços,
~127 × 275 na aba inversa. Ambos da mesma ordem.

`[FATO]` A leitura célula a célula do VBA — 27 acessos COM por linha na etapa
10 — desaparece. `[INFERÊNCIA]` A expectativa é ficar **mais rápido** que a
macro. A medir, com arquivo real.
