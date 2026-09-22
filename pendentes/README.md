# Pendentes

Notas emitidas contra a Hinove que ainda **não** têm entrada lançada — de
mercadoria e de serviço. São duas rotinas semanais do time fiscal, hoje em duas
macros de Excel, e uma delas alimenta a cobrança formal às áreas guardiãs.

**Três ferramentas na tela, um projeto no disco.** Duas fazem a mesma coisa:
cruzam um universo de documentos com um registro de lançamento, dizem o que
sobrou e preservam o julgamento humano de uma semana para a outra. O que muda é
a chave do cruzamento — mercadorias tem `Chave Acesso`, serviços não tem chave
nenhuma e precisa construir quatro. A terceira, o **Resumo Executivo**, não
cruza nada: ela lê a saída das outras duas, já classificada, e devolve o painel
da semana dentro da própria planilha.

## Situação

**As três ferramentas já rodam**, na janela da Central e no terminal. O Resumo
Executivo saiu do porte em 15/09/2026 e voltou em 22/09/2026 como outra coisa:
o painel das **duas frentes**, com três categorias, montado sobre o relatório
já classificado — e conferido contra o relatório de produção da semana 38,
bloco a bloco. A planilha de mercadorias continua saindo sem painel, com as
sete abas inteiras; o painel é etapa separada e vem por último.

| Bloco | Situação |
|---|---|
| Reconhecimento de arquivo por âncora de cabeçalho | pronto |
| Leitura e mapeamento de coluna por nome, com sinônimos | pronto |
| Normalizações: texto, número de NFS-e, chave, CNPJ, data, farol | pronto |
| Livro de classificação (o estado que hoje vive dentro do `.xls`) | pronto |
| Snapshot semanal imutável | pronto |
| Escrita da planilha, com formato antes da escrita | pronto |
| Carga de fábrica dos parâmetros | pronta |
| **Motor de serviços** — cascata de confronto, vínculo, população inversa | **pronto** |
| **Motor de mercadorias** — limpeza, roteamento, conferência, herança, B1/B2 | **pronto** |
| Aba `Descartados` — o que A1 e A3 tiram, com o motivo | **pronta** |
| Tela de configuração das ferramentas | não entrou |
| **Resumo Executivo** — tabelas, os dois TOP N e os três gráficos | **pronto** |
| Aba `Resumo` — a série entre semanas, que o painel não cobre | não entrou |

O que trava o quê está em
[`docs/pendentes/04-plano-de-entrega.md`](../docs/pendentes/04-plano-de-entrega.md).

## O que o núcleo resolve

```
src/pendentes/
  texto.py         aparar × chave_de_texto — as duas normalizações que o VBA
                   chamava pelo mesmo nome, agora com nomes diferentes
  valores.py       número nas três notações, data com parse explícito, e o
                   texto original quando a data não é interpretável
  chaves.py        chave de acesso, CNPJ e o número de NFS-e do Portal Nacional
  farol.py         o semáforo de emoji do Sankhya — e o vazio que NÃO é "Não"
  planilha.py      .xls, .xlsx e .xlsm viram a mesma matriz
  cabecalho.py     a linha do cabeçalho por âncora, a coluna por nome, e a
                   mensagem que lista TODAS as colunas faltantes de uma vez
  papeis.py        qual arquivo é qual, pelo próprio cabeçalho
  tabelas.py       tabelas em que a ordem das linhas é a regra
  parametros.py    carga de fábrica versionada + base viva fora do git
  estado.py        o livro de classificação, com carimbo de quem gravou
  snapshot.py      a foto semanal imutável, que nunca é sobrescrita
  escrita.py       a aba formatada, com o formato aplicado ANTES da escrita
  cli.py           python rodar.py pendentes mercadorias|servicos|resumo …

src/pendentes/mercadorias/
  colunas.py       as 27 do XML, as 7 do CE e a ordem das 39 / 36 / 33 / 27 / 28
  fontes.py        o documento com as 27 colunas, e as DUAS chaves que ele tem
  limpeza.py       A1 (XML de terceiro), A2 (parceiro), A3 (transporte)
  roteamento.py    as 4 condições na ordem, e a segregação de `Lançados`
  conferencia.py   o lookup do CE, as 6 colunas e o farol de três estados
  classificacao.py a herança pelo livro, B1 (Fiscal) e B2 (split FIS-FAT)
  vocabulario.py   unidade, categoria e guardião: o que não é reconhecido
  execucao.py      o pipeline de ponta a ponta e o que a tela mostra

src/pendentes/resumo/
  colunas.py       onde cada coisa fica nas duas abas do painel
  fontes.py        as abas `Pendentes` e `Servicos` viram uma lista de notas
  painel.py        a conta — categorias, TOP N, unidade e guardião
  escrita.py       as duas abas e os três gráficos, sem uma fórmula
  execucao.py      o painel entra na planilha da semana, gravada ao lado

src/pendentes/servicos/
  colunas.py       o nome de cada coluna lida e a ordem exata das quatro abas
  fontes.py        as matrizes viram nota, lançamento e anexo
  chaves.py        as três chaves do confronto e o índice que CONSOME
  confronto.py     a cascata dos quatro procedimentos, POR PASSOS
  enriquecimento.py cadastro de parceiro, de-para de filial, pedido mais recente
  vinculo.py       a nota × o pedido da Conferência de Serviços (colunas 29-36)
  inversa.py       Sem Correspondencia ASIS: o que o ASIS deixou de capturar
  execucao.py      o pipeline de ponta a ponta e o que a tela mostra
```

## O que o motor de mercadorias responde

*Quais NF-e emitidas contra a Hinove ainda não têm conferência fiscal — e de
quem é a responsabilidade por cada uma.*

Aqui a chave é natural, e o trabalho não está no cruzamento: está em decidir
**o que entra no relatório**. É uma sequência de regras cuja ordem é a regra:

```
limpeza        A1 (XML de terceiro) → A3 (NF-e de transporte) → A2 (parceiro)
   ↓           o que A1 e A3 tiram vai para a aba `Descartados`, com o motivo
roteamento     4 condições; a primeira verdadeira consome a linha
   ↓           CTe · Manifestados · Entradas 3os — e o que sobra é pendência
conferência    o lookup do CE: 6 colunas, farol de TRÊS estados
   ↓           `Conf fiscal = Sim` sai para `Lançados`
classificação  a herança vem do livro → B1 (Fiscal) → B2 (split FIS-FAT)
```

A saída são sete abas: `Pendentes` (39 colunas) e `PENDENTES FIS-FAT` (36)
visíveis, e `CTe`, `Manifestados`, `Entradas 3os` (27 cada), `Lançados` (33) e
`Descartados` (28) ocultas — **ocultas, não apagadas**: elas são evidência para
auditoria, e reexibem-se por clique direito.

**`Descartados` é a única aba nova do porte.** Hoje as linhas que A1 e A3 tiram
somem sem rastro, sem contador e sem aba, e não há como medir o volume
descartado por semana. Agora há.

O que bloqueia o encerramento da semana é a ferramenta não conseguir dizer o
que uma coisa é: unidade não reconhecida, categoria fora da lista, guardião
fora da lista cadastrada e chave duplicada no CE cujas linhas divergem. Nota
que sobra depois das quatro condições **não** bloqueia: ela é o produto.

## O que o motor de serviços responde

*Quais notas de serviço emitidas contra a Hinove ainda não foram lançadas — e,
para cada uma, qual pedido de compra e qual requisitante estão por trás dela.*

Não existe chave natural entre o ASIS e o Sankhya. O confronto é uma cascata de
quatro procedimentos, do mais forte para o mais fraco, com **consumo**: cada
lançamento casa com no máximo uma nota.

| # | Chave | Força |
|---|---|---|
| 1 | número da nota + CNPJ do prestador | forte |
| 2 | número da **RPS** + CNPJ, contra o número de nota do Sankhya | forte |
| 3 | CNPJ + valor | fraca |
| 4 | número da nota + valor, **sem CNPJ** | fraca — sai marcada para revisão |

**O laço externo é o passo, nunca a nota.** Cada procedimento varre todas as
notas antes de o seguinte começar; invertido, uma chave fraca consumiria o
lançamento de um match forte e o resultado passaria a depender da ordem das
linhas no relatório. Dois testes travam isso.

A saída são quatro abas — `Lancadas` (12 colunas), `Pendentes` (36),
`Canceladas` (16, layout próprio) e `Sem Correspondencia ASIS` (7 + N) —, e o
que a ferramenta não consegue explicar **bloqueia o encerramento da semana**:
confronto por chave fraca, chave nota+CNPJ duplicada no Sankhya, vínculo de
pedido ambíguo e CNPJ de tomador sem filial. Nota que não casou com nada não
bloqueia: ela é o produto.

## Três decisões que não são detalhe

**O arquivo é reconhecido pelo cabeçalho, não pelo nome nem pela ordem.**
Arraste os três (ou quatro) arquivos da semana em qualquer ordem. Papel
duplicado ou obrigatório ausente aborta nomeando o arquivo; papel opcional
ausente roda e avisa, contado.

**O julgamento humano sai da planilha e vai para o livro.** Guardião, gestor,
categoria, tipo de operação e retorno passam a morar em
`dados/pendentes/classificacao/`, fora do git. A planilha vira ida e volta: sai
do livro, volta para o livro. Perder o anexo do e-mail deixa de apagar o
histórico, e a nota que sumiu de `Pendentes` numa semana volta classificada na
seguinte — o que hoje não acontece.

**O formato da coluna é aplicado antes de qualquer escrita.** Não é estética:
chave de acesso em coluna numérica vira `3,52604E+43` e o PROCX para de casar;
data gravada em célula formatada como Texto vira string literal, e formatar
depois não reverte.

## Como se usa

Pela janela: `Hinove.bat`, ferramenta **GerarPendentes** ou **GerarServPend**,
e arraste os relatórios da semana. Pelo terminal, com os arquivos em qualquer
ordem:

```
python rodar.py pendentes mercadorias XML31.xls CE31.xls Pendentes30.xls
python rodar.py pendentes servicos ASIS.xlsx PC27.xls Conferencia.xls
```

O código de saída é `1` quando a semana ficou **não encerrável** — há item que
exige revisão manual — e `2` quando a execução nem chegou a gerar planilha.

## Onde as coisas moram

| O quê | Onde | Versionado? |
|---|---|---|
| Valores de partida, sem dado da empresa | `parametros_de_fabrica.yaml` | sim |
| A base viva, editada pela tela | `dados/pendentes/parametros.yaml` | não |
| O livro de classificação | `dados/pendentes/classificacao/*.yaml` | não |
| A foto semanal imutável | `dados/pendentes/semanas/<domínio>/<AAAA>-S<NN>/` | não |
| O padrão-ouro do porte | `competencias/pendentes/` | não |

## Testes

```
python -m pytest
```

301 testes, com planilhas fictícias montadas no próprio teste — CNPJ, chave de
acesso e nome de fornecedor inventados, regra nº 1 do `CLAUDE.md`.

**Um pedaço deixou de ser só estrutural.** O painel semanal foi conferido
contra o relatório de produção da semana 38 e reproduz os seis blocos dele —
tabela por categoria, os dois TOP 5, valor por unidade e quantidade por
guardião — dígito a dígito. A conferência está em
[`docs/pendentes/07-resumo-executivo.md`](../docs/pendentes/07-resumo-executivo.md);
o arquivo, por ser dado real, não entra no repositório.

**A divergência zero contra a macro ainda não foi provada**, porque os arquivos
reais de uma semana e a saída correspondente da macro ainda não chegaram. É a
[decisão pendente nº 1](../docs/pendentes/05-decisoes-pendentes.md), e é a
única vermelha.

## Documentação

[`docs/pendentes/`](../docs/pendentes/) — a arquitetura, o registro do porte, o
que cada relatório responde para o time fiscal, o plano de entrega com a
viabilidade de cada bloco, as decisões pendentes e o painel semanal.
