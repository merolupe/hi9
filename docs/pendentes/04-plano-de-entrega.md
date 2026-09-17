# Plano de entrega

> O que entrou agora, o que vem depois, em que ordem e o que trava o quê — com
> **esforço, risco e dependência externa** de cada bloco.
>
> Público: analista desenvolvedor + Gerência Fiscal/Tributária.
>
> `[FATO]` = verificável no repositório · `[INFERÊNCIA]` = estimativa minha.

---

## 1. Entrega 1 — a fundação · **concluída**

`[FATO]` O que está no repositório, com teste de comportamento:

| Bloco | Módulo | O que resolve |
|---|---|---|
| Reconhecimento de papel | `papeis.py` | qual arquivo é qual, pelas âncoras do cabeçalho; duplicado e ausente abortam nomeando |
| Leitura | `planilha.py` | `.xls`, `.xlsx` e `.xlsm` viram a mesma matriz, com espiada limitada para o reconhecimento |
| Cabeçalho e colunas | `cabecalho.py` | a linha do cabeçalho por âncora, a coluna por nome e sinônimo, e a lista **completa** das faltantes |
| Normalizações de texto | `texto.py` | `aparar` × `chave_de_texto` — o nome duplicado do VBA, resolvido |
| Número, data, data-hora | `valores.py` | as três notações de valor, parse explícito de data, e o texto original quando não interpreta |
| Chaves de identidade | `chaves.py` | chave de acesso, CNPJ e o número de NFS-e do Portal Nacional, com o corte de prefixo **contado** |
| Farol de emoji | `farol.py` | os três e os cinco ramos, por tabela, com o vazio que não é "Não" |
| Tabelas ordenadas | `tabelas.py` | a ordem como dado: `CORUMB` antes de `GUAR` deixa de ser armadilha |
| Parâmetros | `parametros.py` + `parametros_de_fabrica.yaml` | carga de fábrica versionada, base viva fora do git, gravação que mescla e carimba |
| O livro | `estado.py` | leitura por cabeçalho, as cinco regras da ingestão, carimbo de quem gravou |
| A foto da semana | `snapshot.py` | pasta imutável, `-2`/`-3`, SHA-256 das entradas, `encerravel` |
| Escrita | `escrita.py` | formato **antes** da escrita, largura calculada com teto, autofiltro, congelamento, ocultamento |

`[FATO]` Também nesta entrega, fora do projeto:

* `pendentes` entrou em `test_nenhuma_ferramenta_importa_outra` — a ferramenta
  nova nasce travada pela mesma trava das outras;
* `pendentes` entrou em
  `test_a_central_carrega_as_ferramentas_sem_nenhum_pacote_instalado`, porque
  ele **de fato** carrega sem nenhum pacote instalado;
* as duas entradas do catálogo continuam `A_IMPORTAR`, com o `detalhe` dizendo
  em que pé o porte está;
* `README.md` da raiz e § 8 de `docs/central/01-arquitetura.md` atualizados
  para "em importação" — nem "importado", nem intocado.

### Por que as duas entradas continuam apagadas

**Botão que não roda é pior do que botão apagado.** Acender agora entregaria
uma ferramenta que pede três arquivos, reconhece os três corretamente e não tem
o que fazer com eles. O estado `A_IMPORTAR` existe exatamente para isto: a
ferramenta aparece, apagada, com o nome e o que faz, e o time enxerga o que
está por vir.

### Por que não entrou CLI

`rodar.py` e `verificar.py` **não** ganharam `pendentes`, e é deliberado. Um
`python rodar.py pendentes …` que só dissesse qual arquivo é qual seria um
comando sem produto — nenhuma planilha sai desta entrega. `verificar.py`
responde "este Python consegue rodar as ferramentas?", e a lista dele é a das
ferramentas que a Central precisa carregar para abrir; `pendentes` ainda não é
uma delas. As duas linhas entram junto com o primeiro motor, na entrega 2 —
e entraram.

## 2. Entrega 2 — serviços · **concluída**

`[FATO]` O motor de serviços está no repositório, em `pendentes/servicos/`,
e a entrada `gerarservpend` do catálogo saiu de `A_IMPORTAR`: **o botão
acende**. O que entrou, bloco a bloco:

| Bloco | Módulo | O que resolve |
|---|---|---|
| Nome de coluna e ordem das abas | `colunas.py` | 12 / 36 / 16 / 7+N, literais, com o formato de cada coluna |
| As matrizes viram registro | `fontes.py` | nota, lançamento e anexo com valor, data e CNPJ já normalizados |
| Chaves do confronto e o consumo | `chaves.py` | os três índices; `consumir` devolve o primeiro lançamento livre e o marca |
| A cascata de 4 procedimentos, **por passos** | `confronto.py` | o laço externo é o passo; as canceladas saem antes do primeiro |
| Enriquecimento | `enriquecimento.py` | cadastro de parceiro, de-para dinâmico de filial + complemento estático, pedido de maior `Nro. Unico` |
| Vínculo com a Conferência (29–36) | `vinculo.py` | razão exata, múltiplo 2×–12×, filtro de data por dia, desempate por NU, rótulo de confiança |
| População inversa | `inversa.py` | bloco de análise antes das ~268 colunas de origem, nos três blocos de reordenação |
| Pipeline e o que a tela mostra | `execucao.py` | as quatro abas, o livro, o snapshot e o `Painel` |
| Entrada no catálogo + CLI | `central/ferramentas.py`, `rodar.py`, `verificar.py` | `_rodar_gerarservpend`, `python rodar.py pendentes servicos …` |

`[FATO]` 70 testes novos em `pendentes/`, mais 2 na Central, todos de
comportamento. O que eles travam:

* **a cascata por passos contra a cascata por linha** — o teste monta o caso em
  que as duas ordens divergem, roda a cascata ingênua dentro do próprio teste
  e compara os dois resultados. É a armadilha nº 1, e é a única que não se
  percebe olhando a planilha;
* **a independência da ordem das linhas** — o mesmo relatório embaralhado dá o
  mesmo resultado;
* nota com prefixo de ano do Portal Nacional; nota cujo número é o da RPS; RPS
  vazia ou zero, que não vira chave; CNPJ zerado descartado e contado;
  cancelada fora do confronto; parceiro sem cadastro; filial não mapeada;
  pedido ambíguo; pedido global × pedido exato;
* a degradação que **não** aborta: Conferência de Serviços ausente ou
  ilegível, planilha da semana anterior sem a outra metade da chave, arquivo
  que não casa com papel nenhum e rodapé de relatório que não vira nota;
* **as identidades aritméticas da § 11 do documento de estrutura**: lançadas +
  pendentes + canceladas = notas do ASIS; lançadas + sem correspondência =
  lançamentos indexados; a soma dos quatro procedimentos = lançadas;
* uma execução de ponta a ponta com arquivos sintéticos, que gera as quatro
  abas, grava o livro e o snapshot e devolve o `Resultado` — pela ferramenta e
  pela janela da Central.

### O que a entrega acrescentou ao núcleo

`[FATO]` Quatro coisas, e nenhuma delas é regra de serviços — por isso ficaram
no núcleo, e não no domínio:

| Onde | O quê |
|---|---|
| `papeis.ler_inteiro` | relê o arquivo já com o papel decidido — o reconhecimento espia 20 linhas, o motor precisa das outras |
| `parametros.semana_de` | deduz ano e semana; sem `InputBox`, e sem adivinhar em silêncio (pendência 7) |
| `parametros.confronto_de_servicos` / `.filiais` | as vistas dos parâmetros, com o padrão da fábrica |
| `estado`: `cnpj`, `ultimo_retorno`, `registrar_identidade` | o livro passa a guardar o CNPJ e a **contar** a colisão de chave |

### Três decisões desta entrega que vale registrar

**O que bloqueia o encerramento ficou exatamente onde o desenho previa.**
Confronto por procedimento 4, chave nota+CNPJ duplicada no Sankhya, vínculo de
pedido ambíguo e CNPJ de tomador sem filial. Nota que não casou com nada **não**
bloqueia: ela é o produto. A planilha é gravada de qualquer jeito, a lista
vermelha abre a tela, e o snapshot registra `encerravel: false`.

**A coluna 36 continua dizendo o que o VBA dizia.** Quando falta o código da
filial, o VBA grava `Nao encontrado` — não distingue esse caso do "procurei e
não achei". Seria fácil inventar um rótulo novo; não se inventou, porque
divergência de célula é divergência. Quem distingue é a tela, com o CNPJ
nomeado na lista bloqueante.

**O defeito 3 do porte foi corrigido nesta entrega.** Faltar qualquer coluna da
Conferência de Serviços passa a desligar só o bloco de vínculo, em vez de
abortar a execução inteira — hoje o resultado é *crash*, não resultado, e não
há o que comparar.

### O que ficou de fora, de propósito

`[FATO]` A configuração de serviços **não** ganhou tela nesta entrega: a
`Ferramenta` do catálogo entrou sem `Configuracao`. Os parâmetros são lidos da
carga de fábrica e da base viva, e o motor os honra — o que falta é a tela que
os edita, que é trabalho de interface e não de motor. Enquanto ela não vem, o
de-para estático de filiais (pendência 9) e a semana cadastrada (pendência 7)
só se alteram editando `dados/pendentes/parametros.yaml` à mão.

### Por que serviços veio primeiro, revisto depois de feito

`[FATO]` A aposta era que serviços seria o módulo mais barato: sem resolução de
caminho, sem mitigação de OneDrive, sem gráfico, sem aba oculta, já entregando
`.xlsx`, já com handler global de erro e já lendo por array. Confirmou-se.

`[FATO]` E a aposta sobre a aba inversa também: `[INFERÊNCIA]` dizia que as
~275 colunas não seriam caras, porque em VBA cada célula é um acesso COM e em
Python não. A aba sai da mesma função de escrita das outras três, sem nenhum
tratamento especial além da reordenação das colunas de origem.

O que **não** estava na estimativa: o motor precisou de quatro acréscimos ao
núcleo (tabela acima). Nenhum deles é grande, e todos serviriam igualmente ao
motor de mercadorias — o que sugere que a entrega 3 encontrará o núcleo mais
completo do que esta encontrou.

## 3. Entrega 3 — mercadorias, sem painel · **concluída**

`[FATO]` O motor de mercadorias está no repositório, em `pendentes/mercadorias/`,
e a entrada `gerarpendentes` do catálogo saiu de `A_IMPORTAR`: **o botão
acende**. O que entrou, bloco a bloco:

| Bloco | Módulo | O que resolve |
|---|---|---|
| Nome de coluna e ordem das abas | `colunas.py` | 27 do XML, 7 do CE; 38 / 36 / 33 / 27 / 28 de saída, com o formato de cada coluna |
| As matrizes viram registro | `fontes.py` | o documento com as 27 colunas inteiras, e as **duas** chaves que ele tem |
| Limpeza A1/A2/A3 + aba `Descartados` | `limpeza.py` | a ordem A1 → A3 → A2, e o motivo de cada descarte |
| Roteamento parametrizado | `roteamento.py` | as 4 condições na ordem, a primeira verdadeira consome; e a segregação de `Lançados` |
| Lookup do CE, 6 colunas, farol de 3 estados | `conferencia.py` | primeira ocorrência vence, duplicadas contadas, divergência bloqueia |
| B1 e B2, e a herança pelo livro | `classificacao.py` | a única regra que sobrescreve, e o split que **move** |
| Unidade, categoria e guardião | `vocabulario.py` | o que a ferramenta não reconhece, contado e nomeado |
| Pipeline e o que a tela mostra | `execucao.py` | as sete abas, o livro, o snapshot e o painel |
| Entrada no catálogo + CLI | `central/ferramentas.py`, `pendentes/cli.py` | `_rodar_gerarpendentes`, `python rodar.py pendentes mercadorias …` |

`[FATO]` 94 testes novos em `pendentes/`, mais 2 na Central, todos de
comportamento. O que eles travam:

* **as três ordens que carregam correção de defeito antigo** — a limpeza antes
  do roteamento (o teste monta o XML de terceiro **de entrada** e roda a ordem
  invertida ali mesmo, para mostrar que ele sobreviveria em `Entradas 3os`);
  A1 antes de A3; a herança antes de B1 e B1 antes de B2;
* **a ordem do roteamento**, nos dois sentidos: o registro que satisfaz duas
  condições vai para a primeira, e inverter a tabela muda o destino;
* as assimetrias de comparação que o VBA tem e que **não** foram uniformizadas:
  A3 tolera caixa e espaço mas não acento; as condições 3 e 4 são exatas; a
  etapa 15 é exata e B2 não é;
* os três estados do farol; a chave do CE com várias linhas, em que a primeira
  vence, as duplicadas são contadas e a divergência de pedido ou de farol entre
  elas **bloqueia**;
* B1 sobrescrevendo classificação herdada, e **não** disparando para nota que
  nem estava no CE; B2 movendo e não copiando;
* a herança que atravessa a semana pelo livro — inclusive quando a nota deixa
  de ser pendente, e quando o arquivo da semana passada não vem;
* `CORUMB` antes de `GUAR`, provado nos dois sentidos;
* **os invariantes estruturais da § 11.1**: 27 / 7 / 38 / 36 / 33 / 28, o bloco
  de conferência sempre logo depois de `Chave Acesso`, o de categorização
  sempre nas cinco primeiras posições, sete abas com duas visíveis;
* uma execução de ponta a ponta com dez notas sintéticas, uma por caminho do
  pipeline, que gera as sete abas, grava o livro e o snapshot e devolve o
  `Resultado` — pela ferramenta e pela janela da Central.

### O que a entrega acrescentou ao núcleo

`[FATO]` Duas coisas, e nenhuma delas é regra de mercadorias:

| Onde | O quê |
|---|---|
| `chaves.SEM_CADASTRO` | o **quinto** conceito duplicado entre os dois módulos VBA; os outros quatro já estavam no núcleo desde a entrega 1 |
| `cabecalho.ate_a_ultima` | o corte de rodapé do relatório, que estava dentro de `servicos/fontes.py` e serve aos dois domínios |

### A herança pelo livro mata três defeitos por construção

`[FATO]` Os defeitos 8 e 9 do registro do porte — a leitura das cinco colunas
de classificação **por posição fixa**, o `Cells(Rows.Count, 6)` com a coluna 6
no código e o `colChaveNova = colChaveAtual + 5` — não têm onde existir quando
a herança vem do livro: o livro tem campo com nome, a planilha devolvida é lida
por cabeçalho e a chave é um campo do documento, não um deslocamento.

`[FATO]` Os dois offsets são o **mesmo antipadrão que a v7 já havia removido**
da etapa 15, onde `colChaveAtual + 2` quebrou quando o bloco de conferência
passou de 3 para 6 colunas. Ele sobreviveu na etapa 17 porque ninguém mexeu
nela desde então.

A medição que os defeitos 8 e 9 pedem **continua pendente**, e continua valendo
a pena: ela responde se a leitura posicional de hoje estava certa, e desde
quando. O que mudou é que a resposta deixou de ser pré-requisito para portar.

### Três decisões desta entrega que vale registrar

**A aba `Descartados` é a única aba nova, e é acréscimo.** Nenhuma aba
existente muda. Ela nasce oculta, como as outras auxiliares, e recebe as 27
colunas do XML mais o motivo. `[FATO]` Hoje essas linhas somem: a exclusão é
física, não há contador, não há aba e a mensagem final não reporta volume
descartado — o próprio dossiê registra que *não há como medir volume descartado
por semana*. Agora há.

**As comparações assimétricas do roteamento ficaram como estão.** Os três
operadores da tabela (`preenchido_e_diferente`, `igual_a_algum`, `igual`) são
os três jeitos com que o VBA compara, com o alcance que cada um tem hoje —
inclusive o espaço à esquerda que manda a nota para `CTe`. Uniformizar é o
defeito 10, e ele exige medição sobre arquivo real **antes** de mexer.

**A derivação de unidade e de categoria sobreviveu ao painel.** O Resumo
Executivo saiu do porte, e com ele a agregação, os TOP N e os quatro gráficos.
A derivação ficou, em `vocabulario.py`, porque ela não é ornamento: é o que
permite dizer que a ferramenta **não** reconheceu alguma coisa — e é isso que
bloqueia o encerramento da semana, como a regra nº 4 pede.

### O que ficou de fora, de propósito

`[FATO]` A configuração de mercadorias **não** ganhou tela nesta entrega, pelo
mesmo motivo de serviços: a `Ferramenta` do catálogo entrou sem `Configuracao`.
Os parâmetros são lidos da carga de fábrica e da base viva, e o motor os honra
— o que falta é a tela que os edita. Enquanto ela não vem, a tabela de
unidades (pendência 6) e a lista de guardiões só se cadastram editando
`dados/pendentes/parametros.yaml` à mão, e **enquanto elas estiverem vazias
nada é validado**, que é o comportamento de hoje.

`[FATO]` E não entrou nada de Resumo Executivo: sem painel, sem gráfico, sem
`_AuxResumo`, sem esboço. Ver § 4.

### A entrega sai utilizável sem o painel

As abas `Pendentes` e `PENDENTES FIS-FAT` são o que vai anexado ao e-mail, e as
fichas da Central cobrem, para quem roda, boa parte do que o painel responde —
quantas pendências, de quem, quanto vale e o que trava. Quem recebe o e-mail é
que sente falta do painel; e é por isso que a rodada nova dele
([06 — Próximas rodadas](06-proximas-rodadas.md) § 1) não deve demorar.

## 4. Entrega 4 — o Resumo Executivo · **suspensa**

> **Decisão de 15/09/2026 do Compliance Tributário: o Resumo Executivo sai do
> porte.** Ele deixa de ser a reprodução da aba que a macro de mercadorias
> monta e passa a ser um resumo automático das **duas frentes**, gerado depois
> que mercadorias e serviços rodarem, com **três categorias — Diretos,
> Indiretos e Serviços** — e layout revisto. Ver
> [06 — Próximas rodadas](06-proximas-rodadas.md) § 1.
>
> Reproduzir fielmente uma tela que vai mudar de conteúdo e de forma é trabalho
> que nasce para ser jogado fora. **A análise abaixo continua valendo** — ela é
> sobre o que o openpyxl faz e quanto custa, não sobre o layout de hoje — e é
> por onde a rodada nova começa quando for desenhada.

`[FATO]` `vendor/openpyxl/chart/` traz `pie_chart`, `bar_chart`, `axis`,
`label`, `legend`, `print_settings`, `series` e `reference`. **Gráfico nativo é
viável.**

| Elemento | Como | Esforço | Risco |
|---|---|---|---|
| Barras de título mescladas, cores, fontes | `merge_cells` + `PatternFill` + `Font` | baixo | baixo |
| Tabela por categoria + linha Total | escrita direta | baixo | baixo |
| TOP Indiretos / TOP Diretos (`G3:L13`, `G16:L26`) | escrita direta; a regra dos 5-ou-10 é lógica pura | baixo | baixo |
| Formatação condicional do tempo (`> $S$3`) | `formatting.rule.CellIsRule` | baixo | baixo |
| `_AuxResumo` com as quatro séries | escrita direta | baixo | baixo |
| Larguras e alturas | `column_dimensions` / `row_dimensions` | baixo | baixo |
| Área de impressão `$A$1:$M$40` | `ws.print_area` | baixo | baixo |
| Pizza com percentual e legenda à direita | `PieChart` + `DataLabelList` + `Legend` | médio | médio |
| 2 colunas empilhadas + 1 barra empilhada | `BarChart(type=…, grouping="stacked")` | médio | médio |
| `ReversePlotOrder` | `y_axis.scaling.orientation = "maxMin"` | médio | médio |
| Cor por série e por fatia | `GraphicalProperties` em `Series` / `DataPoint` | médio | médio |
| **Proporção e posição dos gráficos** | o VBA deriva `Left/Top/Width/Height` do *range*; openpyxl ancora numa célula e recebe tamanho **em centímetros** | **alto** | **alto** |

**A avaliação dos gráficos, em uma frase: o caro não é desenhar os quatro
gráficos — é fazê-los parecerem os de hoje.** A conversão *range* → centímetros
é aritmética simples, mas o acerto fino é por tentativa e olho, e **não tem
teste automático**: nenhuma asserção diz "este gráfico está bonito". Todo o
resto do painel é dado, e dado se testa.

**Recomendação:** a primeira parte do Resumo traz tudo que é dado — tabelas,
TOP, séries auxiliares, formatação condicional, área de impressão — e
**nenhum gráfico**; a segunda traz os quatro. A planilha sai utilizável desde o
começo, e o bloco sem prova automática fica isolado em `mercadorias/graficos.py`,
onde pode ser refeito sem tocar em regra.

**E não perseguir o pixel.** Reproduzir a informação e a paleta; parar aí. É o
único bloco cujo esforço cresce sem limite claro. `[FATO]` Lembrando que o alvo
é a **v14** — a rodada de formatação de 17/08/2026 nunca entrou em produção, e
se ainda for desejada é pedido novo.

## 5. Entrega 5 — depende do time fiscal

| Bloco | Depende de |
|---|---|
| Lista fechada de categorias e de guardiões (torna os bloqueios efetivos) | pendência 6 |
| De-para estático de filiais, complementar ao dinâmico | pendência 9 |
| Harmonizar as abas auxiliares em 38 colunas | pendência 8, e só depois da divergência zero |
| Base de categorização por parceiro | pendência 13 |
| Separar consolidado × detalhado para o e-mail | sugestão em aberto no dossiê |

## 6. O que trava o quê

```
núcleo (feito) ──┬─► serviços (feito) ──► catálogo + CLI (feito)
                 │
                 ├─► estado + snapshot (feito) ──┬─► serviços (feito)
                 │                               └─► mercadorias (feito)
                 │
                 └─► mercadorias (feito) ──┬─► catálogo + CLI (feito)
                                           └─► Resumo Executivo — SUSPENSO

arquivos reais ──► as 6 medições ──► fechamento das correções 8, 9, 10, 11, 12, 19
arquivos reais + saída da macro ──► divergência zero ──► "o porte está provado"
```

**A única dependência externa dura é a última.** Sem os arquivos reais e a
saída correspondente da macro, o porte pode estar completo e **não estar
provado**. Tudo o mais é trabalho interno.

## 7. O que só se resolve com arquivo real

| O quê | Por quê |
|---|---|
| **Divergência zero contra a macro** | é a prova de verdade, e não há substituto |
| **As seis medições** (defeitos 8, 9, 10, 11, 12 e 19) | cada uma pergunta "quantas linhas mudam?", e a resposta não existe sem dado |
| **Os números de referência de serviços** — 2.797 / 2.670 / 210 / 206 / 127, e o confronto 2.467 / 0 / 191 / 12 | são a linha de base declarada, e as identidades aritméticas já foram conferidas |
| **Os números de referência de mercadorias** — CE30 com 6.864 linhas, 6.844 chaves, farol 1.242 / 143 / 5.459 | idem |
| **`Dias Emissão Doc` é contagem de dias ou data?** | pendência 2: preservar um defeito visível é melhor do que corrigir por suposição |
| **Desempenho** | a expectativa é ficar mais rápido que a macro; sem arquivo, é expectativa |

## 8. O que pode não valer a pena reproduzir

| Item | Recomendação |
|---|---|
| **Paridade visual exata dos quatro gráficos** | reproduzir a informação e a paleta; **não** perseguir o pixel |
| **Aba `_AuxResumo` visível** | mantida por fidelidade e porque é a fonte dos gráficos, mas é subproduto — se um dia atrapalhar, é a primeira a sair |
| **`Lancadas` coluna 8 (`"Nao"` em 100% das linhas)** | preservada por invariante, mas é coluna sem informação. Candidata natural a sair quando houver combinação com o time |
| **As 27 colunas das abas auxiliares ocultas** | reproduzidas como estão; harmonizar não paga antes da prova |
| **`AtualizarResumoExecutivo` como rotina separada** | não reproduzir. Vira **modo de execução**, não rotina |

## 9. Riscos que sobrevivem ao porte

| # | Risco | Por que sobrevive | O que o porte faz |
|---|---|---|---|
| R1 | A abrangência do ASIS não é 100% | limitação da fonte externa | a aba inversa continua medindo, e o número vira ficha na tela |
| R2 | O quarto procedimento é chave fraca | remover perderia matches legítimos | deixa de ser frase em `MsgBox` e vira **lista bloqueante** com contagem |
| R3 | O de-para de filiais depende do que aparece no export | o mapa dinâmico é o que o mantém atual | complemento estático opcional, e CNPJ não resolvido bloqueia |
| R4 | Canceladas que foram lançadas inflam `Sem Correspondencia ASIS` | consequência da segregação antes da cascata, que é correta pelo motivo oposto | documentado; o número é aproximado por construção |
| R5 | `Diferenca` compara universos diferentes | mudar muda o significado de uma coluna que o time lê | documentado como aproximação |
| R6 | O teto de atualidade é humano | nenhuma automação muda isso | — |
| R7 | Paridade visual do painel é por olho | não existe asserção para aparência de gráfico | isolado em `graficos.py`; o resto do painel é dado e tem teste |
| R8 | A classificação só volta para o livro se a planilha editada for arrastada | o time trabalha em planilha, e a planilha vive fora da ferramenta | a ingestão é idempotente e o livro guarda todo mundo; o pior caso é o de hoje |
| R9 | A semana é deduzida, não digitada | o contrato da Central não tem campo de texto na tela de execução | sempre exibida como ficha e corrigível na configuração (pendência 7) |
| R10 | `NormNota` pode mutilar um número legítimo de 13+ dígitos começando em `20` | é a gramática do Portal Nacional | passa a **contar** quantos sofreram corte — `analisar_numero_de_nfse` já devolve isso |
| R11 | Excel continua sendo o entregável, e o e-mail continua manual | fora de escopo declarado | — |
| R12 | A regra nº 3 (vigência) não é atendida para estes parâmetros | vale a mesma exceção que o Fiscalbot abriu | o **snapshot semanal** é mais forte que vigência: guarda os parâmetros e o livro tal como estavam no dia |
