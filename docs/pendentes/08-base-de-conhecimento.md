# A base de conhecimento

O que o histórico já respondeu sobre cada parceiro — para **propor**
classificação, nunca para decidir por ela.

> A fronteira que dá nome a este documento está na § 2 de
> [06 — Próximas rodadas](06-proximas-rodadas.md): *propor não é
> classificar*. Uma sugestão que entra na planilha já preenchida vira, na
> prática, classificação por adivinhação — alguém confirma sem olhar. Tudo
> aqui existe para que isso não aconteça por acidente.

## De onde ela vem

Dois arquivos, produzidos fora do repositório a partir de todos os relatórios
de mercadoria do ano, e entregues em 22/09/2026:

| Arquivo | O que é | O que resolve |
|---|---|---|
| `parceiros.csv` | a lista **curada**: um guardião e uma categoria por parceiro | trocou nome de pessoa por nome de área — é o que se quer propor |
| `regras_classificacao.json` | o histórico **medido**: notas, semanas, concordância e alternativas | é o lastro — ou a falta dele |

`[FATO]` **Eles não dizem a mesma coisa, e é isso que torna a base honesta.**
Em 221 dos 696 parceiros o guardião proposto não aparece nenhuma vez no
histórico daquele parceiro. O caso típico: num parceiro com 159 notas, o
histórico registra **o primeiro nome de uma pessoa** em 72 delas, e a lista
curada propõe a **área** a que essa pessoa pertence. Não é erro de nenhum dos
dois — é uma pessoa sendo substituída pela área dela.

A importação, por isso, **não escolhe entre as duas fontes**. Guarda a
proposta de um lado, a evidência do outro, e deixa o cruzamento visível.

## Os quatro graus, e o que cada um pode fazer

| Grau | Quando | O que pode fazer |
|---|---|---|
| **ajustado** | alguém corrigiu na tela | preencher célula, **por cima de qualquer contagem** |
| **firme** | a proposta e o histórico dizem o mesmo, com **3 notas em 2 semanas** e 100% de concordância | preencher célula |
| **sugestão** | há proposta, mas o lastro é curto, diverge ou não existe | aparecer, com a evidência ao lado |
| **sem proposta** | nada a oferecer | dizer que não sabe |

`ajustado` não é um quarto nível de exigência, é o **mais forte**: quem abre a
tela para corrigir é exatamente quem viu o histórico errar. Por isso ele
preenche onde `firme` preenche e também onde só `sugestao` preencheria.
Desligar a coluna continua desligando tudo, inclusive o ajuste — quem desliga
não quer nada escrito ali.

`[FATO]` O limiar de 3 notas em 2 semanas é o que a própria fonte chama de
"repetida sem divergência". Ele mora em um lugar só, em
`conhecimento/base.py`, e está escrito em número, não em prosa.

A precedência das consultas é a da fonte: **parceiro + unidade** antes de
**parceiro**; e para `Tipo de Operação`, CFOP + parceiro + categoria → CFOP +
parceiro → CFOP + categoria → CFOP. Conjunto de CFOP casa por correspondência
exata do conjunto: nota com dois CFOP não herda a regra de um deles.

## O que a base acertaria — medido

`[FATO]` A base aprendeu **até a semana 37**, e o próprio arquivo diz isso.
Rodá-la contra o relatório da **semana 38** é medir contra uma semana que ela
não viu. Nas 67 notas de mercadoria daquela semana:

| Campo | Firme | Sugestão | Sem proposta |
|---|---|---|---|
| **Categoria** | **44 de 44 — 100%** | 6 de 8 — 75% | 15 |
| **Guardião** | nenhuma proposta | 40 de 52 — 77% | 15 |
| **Tipo de Operação** | **18 de 18 — 100%** | — | 49 |

Três leituras, e nenhuma delas é "a base funciona":

1. **Categoria é o campo maduro.** Dois terços das notas ganhariam categoria
   com evidência firme, e nas 44 não houve um erro sequer.
2. **Guardião não está pronto para preencher.** 77% de acerto quer dizer uma
   nota errada a cada quatro — e o guardião é quem recebe a cobrança. Ele
   sugere; quem decide é gente.
3. **Operação acerta tudo — depois que o conectivo deixou de contar.**
   `[FATO]` Na primeira medição ela aparecia com 4 de 18, e os 14 "erros"
   eram um só: a base diz `Compra Uso e Consumo`, a semana 38 diz `Compra Uso
   Consumo`. Normalizar levou a medida a **18 de 18**. Ver "O conectivo não é
   divergência", abaixo.

**A ressalva que a própria medição imprime na tela:** ela não sabe se quem
classificou a semana 38 consultou a mesma base. Se consultou, a taxa mede
concordância, não acerto. Isso é do processo, não do dado.

## O que a base não faz

* **não sobrescreve nada.** Ver "O que ela preenche", abaixo;
* **não mescla com a base anterior.** Duas fotografias de épocas diferentes
  somariam evidência das mesmas notas contadas duas vezes. Importar
  substitui;
* **não preenche a lista de guardiões que valida a semana.** Os guardiões
  observados ficam registrados e vão para a tela, mas quem cadastra é gente:
  encher a lista daqui faria a semana seguinte bloquear em cima de nome que
  ninguém conferiu;
* **não entra no git.** Código de parceiro, nome de fornecedor, nome de área e
  primeiro nome de gestor — é dado da empresa inteiro, regra nº 1. A base vive
  em `dados/pendentes/conhecimento/mercadorias.json` e nasce **vazia**: numa
  máquina nova nada é proposto até alguém importar.

## O que ela preenche

`[FATO]` Decisão do Compliance Tributário de 22/09/2026, tomada depois da
medição acima: **categoria preenche, guardião preenche** — as duas colunas, no
grau de sugestão —, e **`Tipo de Operação` entrou junto** depois que a
normalização do conectivo levou a medida dela a 18 de 18. Em 24/09/2026
**`Gestor de apoio` foi ligado também**, sem medição — ver "O gestor de apoio
sai do guardião", abaixo. O parâmetro é `pre_categorizacao`, um valor por
coluna (`firme`, `sugestao` ou `nao`), e é editável sem desenvolvedor.

Na semana 38 isso teria preenchido **52 categorias, 52 guardiões e 18 tipos
de operação** das 67 notas. Pelas taxas medidas, cerca de **12 guardiões sairiam errados** — é o
custo conhecido da decisão, e é por isso que as três travas abaixo não são
parâmetro:

### 1. Só preenche o que está vazio

A herança do livro e a regra B1 vêm antes e **nunca** são sobrescritas. O que
uma pessoa classificou, ou o que a semana passada devolveu, vale mais do que
qualquer histórico agregado.

### 2. A célula preenchida sai marcada

Fundo âmbar claro, nas abas `Pendentes` e `PENDENTES FIS-FAT`. Sem a marca a
planilha mentiria por omissão: o guardião proposto ficaria indistinguível do
guardião escrito por alguém que conhece a nota.

É **cor, e não coluna nova**: coluna mudaria um layout que dezenas de pessoas
leem, e a leitura de volta na semana seguinte ignora cor. A tela também conta,
por coluna e por grau, sob o título "confira antes de cobrar".

### 3. Roda entre B1 e B2, e a consequência está declarada

Depois da herança e de B1 — que preenchem primeiro —, e **antes** do split B2.
Quer dizer que um guardião proposto encaminha a nota para a `PENDENTES
FIS-FAT` exatamente como encaminharia um guardião escrito à mão.

A alternativa era preencher depois do split, e ela produz um arquivo que se
contradiz: uma nota na `Pendentes` com `Guardião = Faturamento`. Entre um
arquivo coerente cuja sugestão pode estar errada e um arquivo incoerente, o
primeiro é o que dá para conferir.

### O conectivo não é divergência

`[FATO]` `Compra Uso e Consumo` e `Compra Uso Consumo` são o mesmo tipo de
operação escrito por duas pessoas diferentes. A comparação passa a ignorar uma
lista **fechada e curta** de palavras de ligação (`e`, `de`, `da`, `do`, `com`,
`para`…), e nada além disso: `Compra MP` e `Compra Embalagem` continuam
diferentes, porque o que os separa é substantivo. Normalizar é tirar ruído
conhecido; casar por semelhança seria adivinhação, e é outra coisa.

Sobra a pergunta de qual das duas grafias **escrever**, e ela não pode ser
respondida pelo histórico — ele é justamente o que está defasado. A resposta
sai do **livro**: a grafia que mais aparece nas classificações que voltaram
das pessoas é a grafia em uso. Muda a redação, a ferramenta acompanha na
semana seguinte, sem ninguém cadastrar nada.

`Tipo de Operação` está ligado em `firme` — e como a base só oferece operação
quando a regra se repete sem divergência, `firme` e `sugestao` dão no mesmo.

### O gestor de apoio sai do guardião

`[FATO]` Ligado em 24/09/2026, a pedido do time, em `sugestao` — como o
guardião. Não é proposto por parceiro: a base guarda o **gestor vigente de
cada guardião** (o gestor com mais notas na última observação daquele
guardião), e a pergunta é feita com o guardião que a linha tem depois das
outras colunas — o herdado, o de B1 ou o que a base acabou de propor.

| Situação da linha | O que acontece com o gestor |
|---|---|
| `Gestor de apoio` já preenchido (herança ou pessoa) | nada — só preenche o que está vazio |
| sem guardião | fica vazio: não há de quem deduzir |
| guardião `Fiscal` ou `Faturamento` | fica vazio: a nota vai para a `PENDENTES FIS-FAT`, que não tem a coluna, e B1 esvazia o gestor de propósito |
| guardião escrito por alguém, gestor sem empate no histórico | preenche, **firme** |
| guardião só sugerido pela base | preenche, e o grau cai para **sugestão** — a dedução não fica mais firme do que aquilo de onde saiu |
| empate entre dois gestores no histórico | **sugestão** |

A célula sai marcada em âmbar, como as outras, e entra na contagem da tela.

`[FATO]` **O gestor não foi medido.** A medição contra a semana 38 cobriu
categoria, guardião e operação; o gestor entra sem taxa de acerto conhecida.
E ele herda o erro do guardião: se o guardião sugerido está errado — uma
nota a cada quatro, na semana 38 —, o gestor sai do guardião errado.

Onde a lista curada e o histórico discordam do gestor (4 guardiões na carga
de 22/09/2026, nomeados na tela da importação), quem é proposto é o do
**histórico**.

O padrão `sugestao` está também no código, e não só na carga de fábrica: a
base viva que já existia antes desta mudança tem a seção
`pre_categorizacao` sem a chave nova, e a fábrica não chega a ela. Para
desligar, `gestor_de_apoio: nao` na base viva.

## A tela: consultar e corrigir

A base inteira aparece na **tela de configuração** da entrada
**Base de conhecimento** 🧠, em três tabelas filtráveis: guardião e categoria
por parceiro (697 linhas na carga de 22/09, contando as regras por unidade),
gestor vigente de cada área (70) e `Tipo de Operação` por CFOP (1.310).

Cada linha mostra **três coisas lado a lado**, e só a última se digita:

| Coluna | O que é |
|---|---|
| `Guardião proposto` | o que a importação propôs — só leitura |
| `Evidência do guardião` | `Joana M.: 23 de 65 notas, 21 semana(s) · também: Balança 11, Facilities 6` — só leitura |
| `Guardião (vale)` | **editável**: o que a ferramenta vai escrever na planilha |
| `Corrigido por` | quem corrigiu e quando — só leitura |

A evidência aparece em português e não em número porque quem abre esta tela
está decidindo se confia na base: `23 de 65 notas, 21 semanas` responde isso,
`0,35` não. As alternativas vêm na mesma célula, porque é ali que se vê o
motivo da dúvida.

### As três camadas, e por que elas são três

A importação **substitui** a base inteira — somar duas fotografias de épocas
diferentes produziria uma terceira que nunca existiu, com evidência de
execuções que contaram as mesmas notas. Uma correção feita à mão não pode viver
dentro dessa fotografia, ou a próxima importação a levaria embora.

Então a base tem três camadas, e a leitura aplica uma sobre a outra **nesta
ordem**:

| Camada | Onde mora | O que faz |
|---|---|---|
| **fotografia** | `mercadorias.json`, ~660 KB | o que a importação trouxe; substituída inteira a cada importação |
| **aprendizado** | em nenhum arquivo — refeito do livro a cada leitura | soma evidência das semanas depois da fotografia |
| **correção** | `mercadorias-ajustes.json` | só o que gente corrigiu, com carimbo; vence as duas |

A correção vem por último porque vence as outras duas. O aprendizado vem no
meio porque **soma evidência** à fotografia, e não pode passar por cima de quem
corrigiu à mão. É o mesmo desenho que o resto do repositório usa entre carga de
fábrica e base viva, com uma diferença: aqui o que vem "de fábrica" é a
importação, e **quem manda é a pessoa**.

### Como a tela sabe o que foi corrigido

Ela **compara**, e não marca. Na hora de gravar, valor igual ao que a base diz
por si — fotografia **mais** aprendizado — não é ajuste; valor diferente é. A
comparação é contra o que a tela mostrou, e não contra a fotografia crua: se
fosse contra a crua, toda gravação transformaria o aprendizado inteiro em
correção humana, em silêncio. Isso está travado em teste. Três consequências, todas desejáveis:

* digitar de novo o valor original **desfaz** o ajuste, sem botão de desfazer;
* reimportar não ressuscita correção que a pessoa já tinha revertido;
* o arquivo guarda só o que difere — zero linhas quando ninguém mexeu em nada.

`[FATO]` Medido na carga real: ler as 2.077 linhas das três tabelas leva 69 ms,
gravar leva 29 ms, e gravar sem mexer em nada produz **zero** ajustes.

Corrigir parceiro que a importação não trouxe é permitido, e a tela avisa: a
correção passa a ser a única regra dele. Código repetido na mesma unidade é
**erro** e não grava nada — correção pela metade classificaria a semana com um
valor que ninguém escolheu.

## O que a base aprende sozinha

A fotografia vai até uma semana — hoje a 37. Da 38 em diante o time continua
classificando, e essas decisões entram na base **sem ninguém importar nada**.

### Por que não somando o que a planilha devolve

Porque uma nota pendente aparece na planilha de várias semanas seguidas. Somar
evidência a cada execução contaria a mesma decisão humana cinco, seis, dez
vezes, e a base ficaria cada vez mais confiante sem ninguém ter decidido nada
de novo.

Guardar a lista do que já foi absorvido resolveria, ao preço de dezenas de
milhares de chaves dentro da base — e de um jeito novo de errar: a lista e a
evidência podem sair de sincronia.

### O que se faz em vez disso

Aprende-se do **livro de classificação**, não da planilha. O livro já é
indexado pela nota e guarda **uma linha por nota, para sempre**, com a
classificação mais recente que uma pessoa deu. Recalcular a evidência a partir
dele é **idempotente por construção**: rodar duas vezes dá o mesmo número,
porque a nota é uma linha tanto na primeira vez quanto na segunda.

E para não recontar o que a fotografia já contou, aprende-se **só das semanas
depois de `ultimo_relatorio_classificado`**. As duas metades não se sobrepõem,
então somá-las é legítimo — e nenhuma precisa saber da outra.

Para isso o livro passou a guardar o **contexto da nota**: código do parceiro,
CFOP, unidade e a semana. Sem eles o livro sabe *o que* foi decidido e não
*sobre o que*, e a evidência não se refaz. O contexto não é julgamento humano:
o valor mais recente vence em silêncio, e ele não conta como "alterada" na
ingestão.

### O que ele pode criar, e o que não pode

Ele **soma evidência** a uma regra que existe, e pode **criar** a proposta de
uma regra que não tinha nenhuma — quando o livro mostra o mesmo valor em três
notas de duas semanas, sem divergência. É o mesmo limiar da fotografia,
aplicado aos mesmos dados: decisões humanas. Não é adivinhação (regra nº 4); é
a leitura de um histórico que agora tem dono. Para a tabela de gestores o
limiar é o dela — o que impede é o **empate** —, senão uma troca de gestor
nunca seria aprendida.

O que ele **não** faz é derrubar proposta que já existe. Onde as semanas novas
discordam da lista curada, a proposta cai para `sugestao` com as alternativas
ao lado, e quem decide é a pessoa na tela. Uma máquina que trocasse a proposta
sozinha estaria decidindo classificação.

### Medido no ciclo real

`[FATO]` Fotografia até a semana 37 (488 parceiros) mais as 88 linhas
classificadas à mão da semana 38:

| O que mudou | Quanto |
|---|---|
| parceiros que a fotografia não tinha | **+10** |
| parceiros cuja evidência de categoria cresceu | **32** |
| guardiões observados | 20 → **23** |
| regras de guardião que passaram a existir | **0** — uma semana só dá uma semana, e o limiar pede duas |
| idempotente sobre os 498 parceiros | **sim** |

A última linha é a que importa: a base aprende, e aprender duas vezes dá o
mesmo número.

## Como se usa

Pela Central, na entrada **Base de conhecimento**, ou pelo terminal:

```
pendentes conhecimento parceiros.csv regras_classificacao.json   # importa
pendentes conhecimento Pendentes38.xlsx                          # mede
```

Qual das duas coisas acontece é decidido pelo **conteúdo** do que chega —
planilha é gabarito, `.csv` e `.json` são fonte —, como todo o resto do
projeto. A importação carimba de onde veio: nome, tamanho e SHA-256 de cada
arquivo, mais quem importou e quando.

## O que a importação teve a dizer sobre a carga de 22/09/2026

`[FATO]` 488 parceiros, 209 deles com regra própria por unidade, 1.310 regras
de operação por CFOP, 20 guardiões observados. E um desacordo que vale
registrar: em **4 guardiões** a lista curada e o histórico apontam gestores
diferentes. A base guarda os dois e não escolhe — a tela nomeia quais são, e
quem resolve é quem conhece a área.
