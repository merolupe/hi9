# Pendentes

Notas emitidas contra a Hinove que ainda **não** têm entrada lançada — de
mercadoria e de serviço. São duas rotinas semanais do time fiscal, hoje em duas
macros de Excel, e uma delas alimenta a cobrança formal às áreas guardiãs.

**Duas ferramentas na tela, um projeto no disco.** As duas fazem a mesma coisa:
cruzam um universo de documentos com um registro de lançamento, dizem o que
sobrou e preservam o julgamento humano de uma semana para a outra. O que muda é
a chave do cruzamento — mercadorias tem `Chave Acesso`, serviços não tem chave
nenhuma e precisa construir quatro.

## Situação

**Esta entrega é a fundação.** O núcleo comum das duas rotinas está no
repositório, com teste; os dois motores de domínio ainda não. As duas entradas
da Central continuam apagadas (`A_IMPORTAR`) de propósito — botão que não roda
é pior do que botão apagado.

| Bloco | Situação |
|---|---|
| Reconhecimento de arquivo por âncora de cabeçalho | pronto |
| Leitura e mapeamento de coluna por nome, com sinônimos | pronto |
| Normalizações: texto, número de NFS-e, chave, CNPJ, data, farol | pronto |
| Livro de classificação (o estado que hoje vive dentro do `.xls`) | pronto |
| Snapshot semanal imutável | pronto |
| Escrita da planilha, com formato antes da escrita | pronto |
| Carga de fábrica dos parâmetros | pronta |
| **Motor de serviços** — cascata de confronto, vínculo, população inversa | entrega 2 |
| **Motor de mercadorias** — limpeza, roteamento, conferência, B1/B2 | entrega 3 |
| **Resumo Executivo** — tabelas, TOP N e os quatro gráficos | entrega 4 |

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
```

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

98 testes, com planilhas fictícias montadas no próprio teste — CNPJ, chave de
acesso e nome de fornecedor inventados, regra nº 1 do `CLAUDE.md`.

**A divergência zero contra a macro ainda não foi provada**, porque os arquivos
reais de uma semana e a saída correspondente da macro ainda não chegaram. É a
[decisão pendente nº 1](../docs/pendentes/05-decisoes-pendentes.md), e é a
única vermelha.

## Documentação

[`docs/pendentes/`](../docs/pendentes/) — a arquitetura, o registro do porte, o
que cada relatório responde para o time fiscal, o plano de entrega com a
viabilidade de cada bloco, e as decisões pendentes.
