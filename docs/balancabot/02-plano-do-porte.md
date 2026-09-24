# Balançabot — plano do porte para a Central

> Como o motor sai do VBA e entra na Central: onde mora, como se divide, o que
> muda, o que fica idêntico, como se prova e em que ordem.
>
> Público: analista desenvolvedor + Gerência Fiscal/Tributária.
>
> Pré-leitura: [01 — o que a ferramenta é hoje](01-o-que-faz-hoje.md) e
> [`../central/01-arquitetura.md`](../central/01-arquitetura.md).
>
> `[FATO]` = verificável no código ou no repositório · `[INFERÊNCIA]` =
> estimativa ou proposta a confirmar.

---

## 1. As decisões de enquadramento

| # | Decisão | Por quê |
|---|---|---|
| D1 | **Projeto próprio, `balancabot/`**, pacote `balancabot` | é uma ferramenta, não um módulo de outra. Nenhuma ferramenta importa outra (regra nº 7) |
| D2 | **A entrada `faturabot` sai do catálogo e entra `balancabot`** | o Faturabot como guarda-chuva de três conferências deixa de existir; a conferência de balança é a que existe. As outras duas não têm uma linha de código `[FATO]` |
| D3 | **Duas entradas na tela, um projeto no disco**: *Balançabot* (a conferência) e *Consolidado da balança* (a semana) | mesmo desenho do `pendentes/` com o Resumo Executivo: são dois rituais, com entradas diferentes — relatórios de origem numa, relatórios já gerados na outra. Um botão só que decidisse pelo arquivo seria adivinhação sobre a própria execução |
| D4 | **Trazer como está** — divergência zero contra a macro, com os mesmos textos, abas, colunas e fórmulas | é a regra de importação da Central. Defeito conhecido se mede antes de corrigir (§ 7) |
| D5 | **Parâmetro não é código**: tolerância, janela, trava, faixas do fator, lista de fora de escopo e prefixos de nota de venda saem do `.py` | o princípio da regra nº 2 — o que o time muda sem desenvolvedor não mora em `.py`. Mesmo modelo do `pendentes/` e do Fiscalbot (§ 5) |
| D6 | **A planilha tem que ser legível pela própria ferramenta sem passar pelo Excel** | o relatório da conferência volta como entrada da consolidação. É a mesma armadilha que já custou defeito no `pendentes/` (`CLAUDE.md`) — e aqui há um agravante, descrito em § 4 |

## 2. A arquitetura

```
        ┌──────────────────────────────────────────────────────┐
        │  Central — duas entradas de catálogo                 │
        │  Balançabot · Consolidado da balança                 │
        └──────────────┬────────────────────────┬──────────────┘
                       │                        │
        ┌──────────────▼───────────┐  ┌─────────▼──────────────┐
        │  conferencia/            │  │  consolidacao/         │
        │  cargas · saidas · mic · │  │  leitura dos relatórios│
        │  cruzamento · desvio ·   │  │  período · duplicidade │
        │  indicadores · relatorio │  │  base · resumo         │
        └──────────────┬───────────┘  └─────────┬──────────────┘
                       │                        │
        ┌──────────────▼────────────────────────▼──────────────┐
        │  o núcleo — como leio um relatório e como escrevo   │
        │  planilha · html · cabecalho · papeis · texto ·     │
        │  valores · oc · fator · parametros · escrita        │
        └──────────────────────────────────────────────────────┘
```

A fronteira, como no `pendentes/`: vai para o núcleo o que responde *como leio
e escrevo*; fica em `conferencia/` e `consolidacao/` o que responde *o que é um
desvio*.

### Os módulos

| Módulo | Vem de (VBA) | O que faz |
|---|---|---|
| `planilha.py` | `Workbooks.Open`, `LerColuna` | `.xls` (xlrd), `.xlsx`/`.xlsm` (openpyxl) viram a mesma matriz; formato decidido pelo **conteúdo** |
| `html.py` | `LerTextoArquivo`, `LinhasHTML`, `CelulasHTML`, `TextoHTML` | a tabela do MIC; UTF-8 e, na falha, cp1252 — a leitura de reserva do VBA |
| `cabecalho.py` | `AcharCabecalho`, `ColPorCabecalho`, `ColObrigatoria`, `ColOpcional` | linha do cabeçalho nas 40 primeiras, coluna por nome e sinônimo, homônimo desempatado por preenchimento nas 500 primeiras |
| `papeis.py` | `IdentificarRelatorio`, `EhRelatorioMIC`, `DiagnosticarRelatorio` | o papel de cada arquivo, na mesma ordem de perguntas, e o `conferir` da Central |
| `texto.py` | `NormalizarTexto`, `NormalizarPlaca`, `ChaveASCII` | as três normalizações, fiéis — com o nome dizendo para quê cada uma serve |
| `valores.py` | `ValNum`, `ComoData`, `ValBR`, `DataHoraBR` | número, data **em dd/mm/aaaa explícito** (A12), número brasileiro, serial do Excel |
| `oc.py` | `ExtrairOC` | a varredura por âncora, com o motivo |
| `fator.py` | `FatorXML` | a faixa física, lida dos parâmetros |
| `conferencia/cargas.py` | `CarregarBL`, `CarregarAgFat`, `CarregarAgRec`, `CarregarSankhya` | cada relatório vira uma lista de registros tipados (`Pesagem`, `Agendamento`) — não mais vetores paralelos de módulo |
| `conferencia/saidas.py` | `AcumularNotasSaida`, `ConsolidarSaidas`, `EhNotaVenda` | as quatro regras de consolidação por OC, com o tratamento de cada nota |
| `conferencia/mic.py` | `CarregarMIC`, `CompletarMIC` | notas do MIC, aptas e excluídas |
| `conferencia/cruzamento.py` | `CruzarTudo`, `Cruzar`, `MarcarFonte` | os grupos de candidatos, as duas passadas, o veto, a precedência de H, a confiança |
| `conferencia/desvio.py` | `ClassificarEscopo`, `DefinirPeriodo` e a fórmula de L | escopo, período, H, L e o status — **calculados em Python** |
| `conferencia/indicadores.py` | `EscreverFormulasResumo`, `ContarNoPeriodo`, `EscreverDetalhamento` | os números do `Resumo Geral`, em Python, para a tela e para a frase-síntese |
| `conferencia/relatorio.py` | `EscreverDesvios`, `MontarMoldeResumo`, `EscreverExcecoes` e companhia | as dez abas, com as fórmulas e o layout do operador |
| `consolidacao/*` | `ConsolidarRelatorios` e o que ela chama | § 6 do documento 01 |
| `parametros.py` + `configuracao.py` | `GarantirPainel`, `LerTolerancia`, `LerJanela`, `LerTrava`, `CarregarPadroesFora` | carga de fábrica, base viva e a tela (§ 5) |
| `execucao.py` | `ConferirDesvioBalanca` | `conferir()` e `gerar()` → o texto puro que a Central traduz em `Ficha` e `Lista` |
| `cli.py` | — | `python rodar.py balancabot …` |

**Duplicação consciente.** `planilha.py`, `cabecalho.py` e `texto.py` têm
irmãos em `pendentes/`, e o Balançabot não pode importá-los (regra nº 7). O
caminho é o mesmo que o `pendentes/` tomou: cada ferramenta tem o seu núcleo. O
que se compartilha é `vendor/`. E há razão além da regra: o `planilha.py` do
`pendentes/` **recusa** HTML de propósito, e aqui o HTML é um dos relatórios.

**Só Python puro** (regra nº 6): `xlrd` e `openpyxl`, que já estão em
`vendor/`; o MIC com `html.parser`, da biblioteca padrão. Nada novo entra em
`vendor/`.

**Os vetores paralelos viram registros.** O VBA guarda a pesagem em doze
vetores de módulo (`mPlaca()`, `mOper()`, `mLinH()`…) e a linha de cada aba
de apoio como índice. No porte, a pesagem é um objeto que conhece o
agendamento e o documento com que casou. As **linhas** continuam existindo —
são elas que vão para as colunas O e P da `BL` e para os `INDEX` de
`Desvios` —, mas deixam de ser a única ligação entre as partes.

## 3. O contrato com a Central

### 3.1 Balançabot (a conferência)

```python
Ferramenta(
    id="balancabot",
    nome="Balançabot",
    resumo="Desvio entre o peso da balança e o peso da nota, caminhão a caminhão.",
    icone="⚖️",
    estado=DISPONIVEL,
    entrada=Entrada(
        rotulo="Arraste os relatórios do período",
        apoio="as <code>Pesagens por Período</code> da balança e o AGFAT e/ou "
              "o AGREC são obrigatórios; Portal de Vendas, PMI e o MIC "
              "entram se houver…",
        extensoes=(".xls", ".xlsx", ".xlsm"),
        varios=True,
    ),
    verbo="Cruzando as pesagens com o sistema…",
    executar=_rodar_balancabot,
    conferir=_conferir_balancabot,
    configuracao=_configuracao_do_balancabot(),
)
```

**O que a tela devolve** (`Resultado`):

| | Conteúdo |
|---|---|
| título | "N pesagens conferidas, de dd a dd/mm/aaaa" |
| fichas | Pesagens processadas · Com desvio apurado · Divergentes (os dois lados) · Para analisar · Sem correspondência · Fora de escopo |
| listas | relatórios reconhecidos, com quantos registros cada um trouxe; avisos de conferência parcial (falta Portal de Vendas etc.); parâmetros usados — tolerância, janela, trava, período; arquivos não reconhecidos |
| planilha | o `.xlsx` para baixar |

A mensagem final da macro vira isto. O que era aviso de formatação desaparece:
a escrita não falha pela metade como no Excel (§ 4).

### 3.2 Duas coisas que o contrato de hoje não expressa

`[FATO]` Hoje um `Documento` da `Conferencia` é obrigatório ou opcional, e
**dois arquivos no mesmo papel bloqueiam** ("repetido"). O Balançabot precisa de
duas coisas que isso não diz:

| Precisa | Caso | Proposta |
|---|---|---|
| **"um dos dois"** | AGFAT **ou** AGREC | a `Conferencia` ganha `bloqueios: list[str]`, pendências que a ferramenta nomeia sem estarem presas a um arquivo — "Falta o AGFAT ou o AGREC." |
| **vários arquivos no mesmo papel** | Portal de Vendas e PMI somam (achado A3); a consolidação recebe vários relatórios | `Documento` ganha `varios: bool` — com ele, mais de um anexo é `ok`, não `repetido` |

As duas mexem em `central/src/central/ferramentas.py` e na página. São
pequenas e aditivas — quem não declara continua como está —, mas **mudam o
contrato**, e contrato se muda com teste e com a seção 4 de
`docs/central/01-arquitetura.md` atualizada no mesmo commit.

A alternativa sem mexer no contrato — AGFAT e AGREC opcionais e a execução
falhando quando faltam os dois — acende o botão para depois recusar. Botão que
acende e falha é o que a Central evita desde o `pendentes/`.

### 3.3 Consolidado da balança

Mesmo formato, com `Entrada` de `.xlsx`/`.xlsm`/`.xls` e um único documento,
"Relatórios do Balançabot", com `varios=True`. O reconhecimento é o da macro:
aba `Desvios` com as nove colunas. Sem `configuracao` própria — usa a
tolerância e a trava do Balançabot, como a macro usa as do mesmo painel.

## 4. Fórmula ou valor: a decisão que mais pesa

`[FATO]` A macro grava `Desvios` inteira como **fórmula** — `INDEX` nas abas de
apoio pela linha registrada na `BL` —, o `Resumo Geral` como fórmula e a `Base
Consolidada` com seis colunas de fórmula. O Excel calcula na hora de gravar, e
o arquivo sai com o resultado dentro.

`[FATO]` O Python escreve a fórmula mas **não a calcula**. O arquivo sai sem
resultado guardado e o Excel calcula quando alguém abre. Isso tem duas
consequências:

1. **a tela precisa dos números** e não pode esperar o Excel — o motor calcula
   tudo em Python de qualquer jeito;
2. **a consolidação lê o relatório de volta.** Um relatório gerado pela Central
   e consolidado sem ter sido aberto no Excel chegaria com as colunas F, G, H e
   L **vazias** para quem lê com `openpyxl`. A consolidação sairia zerada, sem
   erro.

A proposta:

| Aba | Hoje | No porte | Por quê |
|---|---|---|---|
| Desvios, A a H | fórmula (`=BL!$F3`, `INDEX(…)`) | **valor**, calculado em Python | é consulta, não conta: a trilha continua nas colunas O, P e S da `BL`. E some o achado A11 — reordenar uma aba deixa de quebrar os números |
| Desvios, I a L | fórmula | **fórmula**, como hoje | dependem da tolerância e da trava; mudar `C6` no relatório tem que continuar recolorindo |
| Desvios, L sem peso documental | fórmula que devolve "Analisar…" ou vazio | **valor** | esse ramo não depende nem da tolerância nem da trava; gravado como valor, a consolidação o lê sem precisar da `BL` |
| Resumo Geral | fórmula + quatro valores | igual | layout do operador; a tela usa os mesmos números, calculados em Python |
| Base Consolidada, K a P | fórmula | igual | idem |

E a consolidação, ao ler um `Desvios`: se a coluna L é fórmula sem resultado
guardado, recalcula `H ÷ F − 1` com a mesma regra. Testado com os dois tipos de
arquivo — o que passou pelo Excel e o que não passou.

**Como se prova que as fórmulas dão os mesmos números que o Python.** Neste
ambiente de desenvolvimento há LibreOffice `[FATO]`: o teste recalcula a
planilha gerada e compara célula a célula com os números do motor. Sem
LibreOffice o teste é pulado, como a regressão do Fiscalbot sem o arquivo real.
Não roda na máquina do time e não precisa: é prova do desenvolvedor.

## 5. Os parâmetros

Mesmo desenho do `pendentes/parametros.py`:

| Onde | O que tem | Versionado? |
|---|---|---|
| `balancabot/parametros_de_fabrica.yaml` | valores de partida | sim |
| `dados/balancabot/parametros.yaml` | a base viva, editada pela tela, com carimbo de quem gravou e quando | não |

| Parâmetro | Fábrica | Na tela? | De onde vinha |
|---|---|---|---|
| Tolerância de desvio (±) | 0,5% | sim | `C5` (lido do lugar errado, A1) |
| Janela do cruzamento por placa | 3 dias (1 a 60) | sim | `C6` (idem) |
| Trava de sanidade | 25% | sim | `C10` |
| Produtos fora de escopo | `PALETE`, `PALLET`, `CAVACO`, `MADEIRA` | sim, lista editável | `B27` em diante |
| Faixa de tonelada / faixa de quilo | 5–80 / 5.000–80.000 | sim | constantes `FAT_*` no código |
| Prefixos de nota de venda | `VENDA`, `REVENDA`, `REV. RET`, `REV RET` | sim, lista editável | `EhNotaVenda` no código |
| Âncoras da OC e tamanho do número (4 a 8) | as seis âncoras | **não** — ficam no código, travadas pelos 24 casos | `ExtrairOC` |
| Período do Resumo | automático | ver § 9, pergunta 6 | `C8`, `C9` |
| Pasta de destino | — | **sai** | `C7` — a Central entrega o arquivo para baixar |

As âncoras da OC ficam em código de propósito: não são decisão do time, são a
defesa contra confundir OC com NF — e mudar uma delas sem os 24 casos rodando
é como se desfaz essa defesa.

A lembrança do `CLAUDE.md` vale aqui também: a carga de fábrica **só semeia a
base na primeira abertura**. Correção que precise chegar a quem já roda vai no
código, não no `.yaml`.

## 6. O que sai, o que entra no lugar, o que fica idêntico

### Sai

| Sai | Entra no lugar |
|---|---|
| `.xlsm` com botão, importar `.bas`, compilar, "Desbloquear" | a entrada no catálogo da Central |
| painel `Parâmetros` no `.xlsm` | tela de configuração, com validação ao salvar |
| diálogo de arquivos, `MsgBox` final | arrastar na janela; a lista do que veio e do que falta; o `Resultado` na tela |
| `DiagnosticarRelatorio` | o próprio `conferir`: cada arquivo aparece com o papel reconhecido ou, se não casou, com as colunas que faltaram |
| `TestarExtracaoOC` rodado à mão | os 24 casos viram teste, rodando a cada alteração |
| camada cosmética que registra falha e segue | escrita com `openpyxl`, que não falha pela metade; o formato é declarado antes de escrever |
| `ModoRapido`, cache de cabeçalho, `ADODB.Stream`, fuga do OneDrive | nada: o problema não existe fora do Excel |
| gravação em pasta de destino | o arquivo para baixar, com o nome preservado |

### Fica idêntico, de propósito

* as **dez abas**, os nomes, a ordem, as colunas e a linha de origem de
  `Desvios` — a consolidação e o operador leem essa planilha;
* os **textos**: "Analisar confronto de peso", "Sem correspondência", "Alta",
  "Média", os motivos do cruzamento, o tratamento de cada nota e de cada linha
  do MIC. A consolidação compara texto;
* os **nomes definidos** `TOL_DESVIO`, `TRAVA_DESVIO`, `PER_INI`, `PER_FIM`, e
  `TOL_DESVIO` ligado a `'Resumo Geral'!C6`;
* o **layout do `Resumo Geral`**, célula a célula — o manual registra 155/155
  de estilo contra o do operador;
* o **formato de período** em `B3` ("Período: 18 a 19/09/2026"), que é o que a
  consolidação procura primeiro.

### Muda, e é dito

* o prefixo do arquivo: `Balancabot_Desvio_Balanca_…` e
  `Balancabot_Consolidado_Balanca_…`, e o título de `B2`. A consolidação
  reconhece o relatório pela aba `Desvios` e acha o período pelo `B3`, nunca
  pelo prefixo — relatórios antigos `Faturabot_…` continuam consolidando;
* `Desvios` A a H como valor (§ 4).

## 7. O que fazer com cada achado

Critério do `pendentes/` e do Fiscalbot: **defeito que não muda número na
competência de referência se corrige; defeito que muda número se mede antes**.

| Achado | Tratamento | Muda número? |
|---|---|---|
| A1 painel deslocado | some com o painel; a tela passa a ser o que vale. **Avisar o operador já**, antes do porte | não, enquanto os valores forem os padrões |
| A2 arquivo repetido, último vence | vira "repetido" na tela, que bloqueia até tirar um | não, com um arquivo por papel |
| A3 Portal de Vendas e PMI somam | preservado (`varios`) | — |
| A4 operação fora de Coleta e Recebimento | preservado; entra na lista da tela quando aparecer, com a contagem | não |
| A5 mesma OC para coleta e recebimento | preservado; pergunta 5 | — |
| A6 divergência positiva | preservado; pergunta 3 | — |
| A7 primeira âncora com tamanho errado encerra | preservado até medir; é caso novo nos testes, marcado como defeito conhecido | pode, raramente |
| A8 OC de 7 dígitos | preservado — é o que o autoteste espera | — |
| A9 passada por OC sem data | preservado | — |
| A10 fora de escopo em Sem Correspondência | preservado; pergunta 7 | — |
| A11 `Desvios` por posição | resolvido por construção (§ 4) | não |
| A12 data pelo idioma do Windows | resolvido: data em texto só em `dd/mm/aaaa` | não, numa máquina em português |
| A13 "Guará" no código | preservado no título do consolidado | — |
| A14 `MAXIFS`, Aptos | preservado | — |

## 8. Como se prova

**O critério é o de sempre: divergência zero contra a macro.**

`[FATO]` Hoje não existe padrão-ouro: o manual diz que a macro nunca rodou no
Excel. Existem os relatórios manuais do operador (18 a 19/09 e o consolidado de
14 a 19/09), contra os quais o manual comparou o `Resumo Geral` e a `Base
Consolidada`.

O que precisa chegar, para `competencias/balancabot/` (fora do git, regra nº 1):

1. **uma execução real da macro**: os relatórios de entrada exatamente como
   foram selecionados, e o `.xlsx` que ela gravou;
2. de preferência, a de 18 a 19/09 — é a que tem o relatório manual para
   comparar também;
3. os três relatórios de 14 a 19/09 e o consolidado que a macro fez com eles.

O teste de regressão compara, linha a linha:

| Aba | Colunas |
|---|---|
| BL | M a S — OC, origem, linhas cruzadas, confiança, motivo, fonte |
| Desvios | A a L, pelo valor que o Excel calculou |
| Saídas | o tratamento de cada nota |
| Saídas (OC) | peso consolidado e notas consideradas |
| AG. Recebimento | K a N |
| MIC | tratamento, placa que casou e pesagem |
| Sem Correspondência | todas |
| Resumo Geral | valores de C12 a E24, B30, E30, H30, o detalhamento e a frase |
| Base Consolidada e Resumo Consolidado | todas |

Sem os arquivos, o teste é pulado — e o porte pode ficar **completo sem estar
provado**, como os motores de `pendentes/` estão hoje. A entrada no catálogo
dirá isso no `detalhe`.

**Antes do padrão-ouro**, o que dá para travar com teste:

* os 24 casos da OC;
* os oito casos reais das fórmulas de H e L, que o manual cita — se vierem,
  anonimizados;
* casos construídos para cada regra de `saidas.py`, do cruzamento (as duas
  passadas, o veto, a precedência de H, "cada documento uma vez só") e do
  período (os três formatos, virada de mês, dia único, nome de arquivo);
* as fórmulas contra o Python, pelo LibreOffice (§ 4);
* fixtures **sintéticas**, montadas no próprio teste — nenhuma placa, OC ou
  nome de parceiro real entra no repositório.

## 9. Perguntas ao time, com o padrão assumido

Cada uma tem um padrão, para o porte não parar esperando resposta. O padrão é
sempre o comportamento da macro.

| # | Pergunta | Padrão assumido |
|---|---|---|
| 1 | **Podem mandar os arquivos de uma execução real e a saída?** (§ 8) | sem eles, porte "em teste" |
| 2 | O painel está deslocado (A1). Os valores que valem hoje são os de `B3`/`B4`? | 0,5% e 3 dias — são iguais aos padrões, então nada muda |
| 3 | "Divergente positiva" contar só nota > balança é o que o controle quer? | sim, como a macro |
| 4 | A balança registra outra operação além de Coleta e Recebimento? | não; se aparecer, sai listada na tela |
| 5 | A mesma OC do PMI servir a uma coleta e a um recebimento é intencional? | sim, como a macro |
| 6 | O período do Resumo precisa ficar fixado entre execuções, como no painel? | não: automático pelas pesagens, com campo opcional na tela e aviso no resultado quando estiver preenchido — período esquecido no painel filtraria a semana seguinte em silêncio |
| 7 | Pesagem fora de escopo sem correspondência deve aparecer em Sem Correspondência? | sim, como a macro |
| 8 | Chega relatório em `.csv`? O diálogo da macro aceita | não; entra quando aparecer um |
| 9 | Dois exports da balança no mesmo período devem se juntar, ou é engano? | engano: bloqueia |

## 10. A ordem das entregas

Uma de cada vez, cada uma com teste e documentação. Esforço relativo
`[INFERÊNCIA]`: P, M, G.

| # | Entrega | Conteúdo | Esforço | Trava |
|---|---|---|---|---|
| 0 | **Este planejamento** | 01 e 02 | — | — |
| 1 | **Fundação** | projeto `balancabot/`, `planilha`, `html`, `cabecalho`, `texto`, `valores`, `oc` (24 casos), `fator`, `papeis` + `conferir`; parâmetros de fábrica; catálogo: `faturabot` sai, `balancabot` entra `A_IMPORTAR`; `test_entrega` passa a conhecer `balancabot`; `README.md`, `CLAUDE.md` e § 8 da arquitetura da Central | M | — |
| 2 | **Contrato** | `bloqueios` e `varios` na `Conferencia` (§ 3.2), com teste na Central e na página | P | decisão sobre o contrato |
| 3 | **Motor** | cargas, saídas, MIC, cruzamento, escopo, período, desvio, indicadores; `execucao.gerar` devolvendo o painel; `rodar.py balancabot` | G | — |
| 4 | **Relatório** | as dez abas, fórmulas de I a L, `Resumo Geral` com o layout do operador; prova Python × fórmula no LibreOffice; entrada `DISPONIVEL`, "em teste" | G | — |
| 5 | **Consolidação** | segunda entrada; leitura dos dois tipos de relatório (§ 4), período, duplicidade, base, resumo | M | — |
| 6 | **Configuração** | tela com os parâmetros de § 5 | P | — |
| 7 | **Prova** | regressão contra a macro; o "em teste" sai do `detalhe` | M | **pergunta 1** |

O motor (3) vem antes do relatório (4) porque a tela precisa dos números e a
planilha é só uma das formas de mostrá-los. A configuração (6) vem depois
porque, até lá, os parâmetros de fábrica são os mesmos que a macro usa — a
ferramenta roda certa sem a tela, só não é editável.

## 11. O que este plano não resolve

* **As outras duas conferências do antigo Faturabot** (relação de saídas e
  quantidades). Se vierem, entram como ferramentas próprias, pelo mesmo
  contrato.
* **A série entre semanas** — o consolidado junta os períodos de uma semana; a
  comparação de uma semana com a outra não existe na macro e não entra aqui.
