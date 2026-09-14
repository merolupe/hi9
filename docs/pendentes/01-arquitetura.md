# Pendentes — arquitetura

> Documento técnico. Público: analista desenvolvedor + Gerência
> Fiscal/Tributária.
>
> Convenção: `[FATO]` = verificado no código VBA extraído ou no repositório ·
> `[INFERÊNCIA]` = dedução a validar com o time fiscal.

---

## 1. O problema, em uma frase

Duas macros de Excel respondem à mesma pergunta — *o que foi emitido contra a
Hinove e ainda não foi lançado?* —, cada uma do seu jeito, com cinco conceitos
duplicados entre elas, e **guardam o julgamento humano do time dentro do
arquivo da semana passada**. Quem renomeia errado esse arquivo perde a
classificação de todo mundo.

## 2. Duas ferramentas na tela, um projeto no disco

### Por que duas na tela

São dois rituais semanais diferentes, com fontes diferentes, públicos
diferentes e saídas diferentes. Quem roda precisa saber qual está rodando. Um
botão único que descobrisse o domínio pelos arquivos arrastados seria
classificação por adivinhação a respeito da própria execução — o que a regra
nº 4 do `CLAUDE.md` proíbe, com a agravante de que um erro de detecção seria
silencioso.

`id`, `nome` e `ícone` não mudam: `gerarpendentes` e `gerarservpend` são como o
time chama as ferramentas.

### Por que um projeto só

`[FATO]` O agente que leu o VBA identificou **cinco conceitos literalmente
duplicados** entre os dois módulos: detecção de cabeçalho, mapa de cabeçalho,
normalização de texto, tradução do farol de emoji e o literal `"Sem cadastro"`.
Nenhum código é compartilhado hoje.

Três desenhos eram possíveis:

| Desenho | Fere a regra nº 7 ("nenhuma ferramenta importa outra")? | Veredicto |
|---|---|---|
| Dois projetos, código duplicado | não | duplica o que já é duplicado. É o problema de hoje, transportado |
| Dois projetos + um projeto `nucleo` importado pelos dois | **sim** — é literalmente ferramenta importando ferramenta | descartado |
| **Um projeto, dois pontos de entrada** | não — não existe seta entre projetos porque não existe segundo projeto | **escolhido** |

`[FATO]` A regra nº 7 é sobre **projetos**, e o teste que a trava
(`test_nenhuma_ferramenta_importa_outra`) percorre `<projeto>/src/**/*.py`
procurando `import <vizinho>`. `pendentes` entrou nessa lista nesta entrega: a
ferramenta nova passa a ser travada pela mesma trava, e fica impedida de, por
exemplo, importar o Fiscalbot para ler um `.xls`.

O núcleo comum é um módulo interno, como `dixml/campos.py` é interno ao
DiXML — ninguém chamaria `dixml.campos` de "ferramenta que o DiXML importa".

## 3. As camadas

```
        ┌──────────────────────────────────────────────┐
        │  Central  —  duas entradas de catálogo       │
        └───────────────┬──────────────┬───────────────┘
                        │              │
        ┌───────────────▼──┐        ┌──▼───────────────┐
        │  mercadorias/    │        │  servicos/       │   ← o que é uma
        │  (entrega 3)     │        │  (entrega 2)     │     pendência aqui
        └───────────────┬──┘        └──┬───────────────┘
                        │              │
        ┌───────────────▼──────────────▼───────────────┐
        │  o núcleo — como leio uma planilha e como    │
        │  escrevo uma; onde mora o estado             │
        │                                              │
        │  papeis · planilha · cabecalho · texto ·     │
        │  valores · chaves · farol · tabelas ·        │
        │  parametros · estado · snapshot · escrita    │
        └──────────────────────────────────────────────┘
```

**A fronteira, em uma frase:** vai para o núcleo tudo que responde *como leio
uma planilha e como escrevo uma*; fica no domínio tudo que responde *o que é
uma pendência aqui*.

### A reconciliação obrigatória

`[FATO]` Os dois módulos têm uma função chamada `NormalizarTexto`, e elas fazem
coisas **diferentes**: a de mercadorias só colapsa espaços (preserva caixa e
acento); a de serviços sobe a caixa e remove acento. Ler o nome não diz qual
está sendo chamada.

No núcleo elas viram duas funções com dois nomes, e cada ponto de chamada passa
a dizer qual quer:

| Função | O que faz | Para quê |
|---|---|---|
| `texto.aparar` | colapsa espaços, **preserva** caixa e acento | **exibir** |
| `texto.chave_de_texto` | maiúsculas, sem acento, colapsa espaços | **comparar** |

Regra da casa: nunca comparar com `aparar`, nunca gravar com `chave_de_texto`.

## 4. Como o arquivo é reconhecido

Hoje mercadorias exige que os arquivos se chamem `XML{N}.xls`, `CE{N}.xls` e
`XMLAnterior.xls` na pasta da semana; serviços exige que a pessoa escolha
quatro diálogos **na ordem certa**, sem nenhuma conferência de que o arquivo
escolhido é o daquele diálogo.

Aqui os arquivos são arrastados juntos, em qualquer ordem, e cada um recebe o
papel cujo **conjunto de âncoras** ele satisfaz inteiro.

| Papel | Âncoras distintivas | Obrigatório? |
|---|---|---|
| XML (Sankhya, importação) | `Nro Nota` + `Situação da manifestação` + `Tomador CT-e` | sim (mercadorias) |
| Conferência de Entradas | `Chave Acesso` + `Conf. Fiscal` + `Motivo Incongruência` | sim (mercadorias) |
| Semana anterior — mercadorias | aba `Pendentes` + `Chave Acesso` + `Guardião` | não |
| ASIS / Portal Nacional | `Numero NFe` + `Codigo Verificador` + `Discriminacao` | sim (serviços) |
| Portal de Compras | `Nro. Unico` + `Tipo Operacao` + `CNPJ Empresa` | sim (serviços) |
| Conferência de Serviços | `Nro. Unico Servico` + `Dt. Hra. Ult. Anexo` | não |
| Semana anterior — serviços | aba `Pendentes` + `Nro Nota` + `Guardiao` | não |

Três âncoras, e não uma, porque `Chave Acesso` está no XML **e** na Conferência
de Entradas, e `Nro Nota` está no XML **e** na planilha da semana anterior. É o
conjunto que separa. A comparação é por `chave_de_texto`, que é o que já faz
`Guardião` casar com `Guardiao` no módulo de serviços.

### A âncora ausente — o que o desenho não previa

`[FATO]` A planilha da semana anterior de mercadorias **contém as 27 colunas do
XML**: ela é o XML acrescido das 6 colunas de conferência e das 5 de
classificação. O conjunto de colunas de um está **contido** no do outro, e
nenhuma âncora positiva separa os dois.

Então o papel do XML declara, além das âncoras que exige, uma que ele **não
pode ter**: `Guardião`, coluna que só existe na saída. É a única separação
honesta possível, e há teste que a trava
(`test_a_planilha_da_semana_anterior_nao_e_confundida_com_o_xml`).

### O que acontece quando dá errado

Nada é decidido por semelhança, por ordem ou por nome de arquivo — regra nº 4.

| Situação | Comportamento |
|---|---|
| Dois arquivos satisfazem o mesmo papel | **aborta antes de ler dado**, nomeando os dois arquivos e o papel |
| Um arquivo satisfaz dois papéis | **aborta**, nomeando o arquivo e os dois papéis |
| Papel obrigatório ausente | **aborta**, nomeando o papel e as âncoras procuradas |
| Papel opcional ausente | roda, e a tela traz uma `Lista` de tom `atencao` contada |
| Arquivo não casa com papel nenhum | roda com os demais, e o arquivo aparece na mesma `Lista` |
| Casa com o papel mas falta coluna obrigatória | **aborta** com a **lista completa** das faltantes |

**Isso não muda o contrato da Central.** `Entrada(rotulo, apoio, extensoes,
varios=True)` já basta, e o `servidor.py` preserva o nome original de cada
arquivo — que é tudo de que o reconhecimento precisa.

## 5. Onde mora o estado

### O livro de classificação

`dados/pendentes/classificacao/<domínio>.yaml`, **fora do git**, com carimbo de
quem gravou e quando. É o modelo do Fiscalbot (`base.py`), e não o do Apurabot:
a classificação é dado da empresa — nome de guardião, de gestor, de parceiro —,
muda toda semana e não tem vigência legal. Versionar isso feriria a regra nº 1
sem discussão.

```yaml
- chave: "35260612345678000199550010000001231000001234"
  tipo_de_operacao: "Compra direta"
  guardiao: "Suprimentos"
  gestor_de_apoio: "Maria"
  categoria: "Indiretos"
  retornos:
    29: "aguardando fornecedor"
    30: "nota substituída"
  origem: "retorno da semana 30"
  gravado_por: "luan"
  gravado_em: "2026-09-08 09:14:22"
```

### O ciclo da semana não muda

```
segunda    arrasta os relatórios da semana  →  a Central gera a planilha
           (o livro preenche as 5 colunas de classificação)
a semana   o time edita as colunas na planilha e cobra por e-mail,
           exatamente como hoje
quarta,    arrasta a planilha editada de volta  →  a Central INGERE as
sexta      colunas no livro, carimba, e REGERA a planilha inteira
```

A planilha nunca é a fonte da verdade e nunca é editada no lugar. É ida e
volta: sai do livro, volta para o livro.

### As cinco regras da ingestão

1. As colunas são lidas **por cabeçalho**, nunca por posição.
2. Onde o arquivo diverge do livro, **o arquivo vence** — é a edição humana
   mais recente — e a divergência entra numa `Lista` contada.
3. Onde o arquivo está vazio e o livro tem valor, **o livro vence**.
4. Chave que não existe no livro entra como registro novo, com a origem.
5. A ingestão é **idempotente**.

`[FATO]` A regra 3 conserta um defeito real: hoje uma nota que saiu de
`Pendentes` — porque foi lançada, cancelada ou roteada — não tem a
classificação lida por ninguém, e se voltar na semana seguinte, volta vazia. O
livro guarda todo mundo, para sempre. Há teste
(`test_a_classificacao_sobrevive_a_semana_em_que_a_nota_sai_de_pendentes`).

`[FATO]` Um ganho de graça em serviços: a chave de herança do VBA é
`NormNota | Cod Parceiro` porque *a aba `Pendentes` anterior não carrega o CNPJ
do prestador* — e o próprio comentário do VBA diz isso. O livro é nosso: ele
guarda o CNPJ, que a execução conhece. `[INFERÊNCIA]` A colisão silenciosa
entre fornecedores distintos que compartilham o literal `"Sem cadastro"` deixa
de existir. O par `NormNota | Cod Parceiro` continua, mas só como ponte de
ingestão de arquivo antigo, onde é a única identidade disponível.

### A primeira execução

O livro nasce vazio, e isso **não é erro** — hoje o módulo de mercadorias
**aborta** quando `XMLAnterior.xls` não existe. Duas situações:

* **sem arquivo de semana anterior:** tudo entra sem classificação, a tela
  mostra a ficha "Sem classificação" e explica que é a primeira execução;
* **com um `Pendentes{N-1}.xls` da macro:** a ingestão roda antes de tudo e o
  livro nasce semeado. **É a migração, e ela custa um arrastar de arquivo.**

### O snapshot semanal imutável

`dados/pendentes/semanas/<domínio>/<AAAA>-S<NN>/` recebe, a cada execução: a
planilha entregue, o livro **como estava naquele momento**, o nome/tamanho/
SHA-256 de cada arquivo de entrada com o papel reconhecido, e o resumo da tela
com `encerravel`.

**A pasta nunca é sobrescrita.** Uma segunda execução da mesma semana grava
`-2`, `-3`, e a mais alta é a vigente. É o que responde "qual era a posição em
08/09?" sem depender de alguém ter guardado o anexo do e-mail.

## 6. O que é parâmetro e o que é código

A regra nº 2 do `CLAUDE.md` fala de **regra tributária**, e **nada nos dois
geradores é regra tributária**: não há alíquota, não há base, não há crédito. O
que existe é código de configuração do ERP, limiar de heurística, vocabulário
de relatório e dado da empresa.

Então vale o princípio por trás da regra, que o Fiscalbot já explicitou ao
tirar `TOL_CARGA` do código: **o que o time fiscal muda sem precisar de
desenvolvedor não pode morar em `.py`**. É um critério mais exigente que a
regra nº 2, não menos, porque abrange o que não é tributário.

O critério simétrico: **o que é a gramática de uma fonte externa, ou a mecânica
do algoritmo, fica no código** — mudá-lo exige teste, não edição de tela.

| # | Item | Vai para | Onde |
|---|---|---|---|
| 1 | TOPs de lançamento de serviço (`2020`, `2111`) | parâmetro | fábrica |
| 2 | Tolerância da razão de valor (`0,005`) | parâmetro | fábrica |
| 3 | Faixa de múltiplos inteiros (`2` a `12`) | parâmetro | fábrica |
| 4 | Prefixo de descrição de pedido (`PC`) | parâmetro | fábrica |
| 5 | CNPJ descartado (`00000000000000`) | parâmetro | fábrica |
| 6 | Palavras-chave de unidade **e a ordem** | parâmetro | **base** (dado da empresa) |
| 7 | O *fallback* da unidade (devolve o texto original) | **código** | `mercadorias/resumo.py` |
| 8 | De-para de filiais | os dois: motor no código, complemento em parâmetro | **base** |
| 9 | Ordem de roteamento (as 4 condições) | parâmetro | fábrica |
| 10 | Entidades HTML do farol | parâmetro | fábrica |
| 11 | O princípio dos três estados do farol | **código** | `farol.py` |
| 12 | Normalização do número da NFS-e | **código** | `chaves.py` |
| 13 | Colunas exigidas de cada fonte, com sinônimos | parâmetro | fábrica |
| 14 | Semana, data de referência, limite de dias | parâmetro | fábrica (valores neutros) |
| 15 | Categorias válidas | parâmetro | fábrica |
| 16 | Guardiões válidos | parâmetro | **base**, nasce vazia |
| 17 | Cores da paleta do Resumo | **código** | `mercadorias/graficos.py` |
| 18 | Ano `2026`, raiz do OneDrive, pasta `Mercadorias\`, TEMP | **desaparece** | — |
| 19 | A1, A2, A3, B1, B2, a cascata de 4 procs, o consumo | **código** | domínio |

### Duas leituras em que esta entrega divergiu do desenho

1. **O roteamento (item 9) veio para a carga de fábrica**, e não só para a
   base. O desenho o colocava na base; mas as quatro condições são vocabulário
   do export do Sankhya, sem nenhum dado da empresa, e uma base que nasce sem
   elas nasce sem roteamento nenhum. O mesmo raciocínio vale para as
   categorias (item 15).
2. **Unidade, filial e guardião ficam de fora da fábrica**, como o desenho
   manda e a regra nº 1 exige: numa máquina nova nascem vazios. O preço é que a
   derivação de unidade só funciona depois do cadastro — e está registrado na
   pendência 6.

### A ordem como dado visível

`[FATO]` A derivação de unidade testa `CORUMB` **antes** de `GUAR`. Inverter os
dois faz qualquer fantasia de Corumbá que contenha "GUAR" virar Guará, sem erro
e sem aviso. Hoje essa ordem é uma sequência de `ElseIf` enterrada no código.

Aqui ela vira uma coluna `ordem`, visível e editável na mesma tela, e há teste
que prova a armadilha **nos dois sentidos** — com a ordem certa a fantasia cai
em Corumbá, com a ordem invertida cai em Guará
(`test_corumba_vem_antes_de_guara_e_e_isso_que_decide`).

## 7. O que a janela devolve, e o que bloqueia

### O `SEM REGRA` deste domínio

A regra nº 4 diz que documento que não casa com regra recebe `SEM REGRA` e
bloqueia o encerramento. A tradução exige cuidado: **nota que não casa com nada
não é `SEM REGRA` — é o produto.** Uma NF-e que sobra depois das quatro
condições de roteamento é uma pendência; uma NFS-e que não casa nos quatro
procedimentos é uma pendência. Confundir as duas coisas faria a ferramenta
bloquear a si mesma toda semana.

O `SEM REGRA` daqui é **quando a ferramenta não consegue dizer o que uma coisa
é**. Três níveis:

| Nível | O que é | O que acontece |
|---|---|---|
| Impede a execução | papel ausente ou duplicado; coluna obrigatória sem sinônimo; arquivo ilegível | aborta antes de gravar, nomeando o que falta |
| **Impede o encerramento da semana** | ver abaixo | **grava a planilha**, mas a `Lista` de tom `erro` vem primeiro e o snapshot registra `encerravel: false` |
| Informa | degradações previstas, contagens, herança | `Lista` de tom `atencao` ou `neutro` |

O que bloqueia o encerramento:

| Domínio | Bloqueia | Hoje |
|---|---|---|
| Mercadorias | unidade não reconhecida | passa em silêncio; o texto cru vai para o resumo |
| Mercadorias | categoria fora da lista | passa em silêncio |
| Mercadorias | sem guardião, com a lista cadastrada | vira `(sem guardião)` no resumo |
| Serviços | confronto por nota + valor, sem CNPJ (proc 4) | a `MsgBox` final manda revisar, e acabou |
| Serviços | chave nota+CNPJ duplicada no Sankhya | vai para a coluna `Obs` e ninguém conta |
| Serviços | vínculo de pedido ambíguo | fica na coluna 36 |
| Serviços | filial não mapeada | grava `"CNPJ nao mapeado: ..."` dentro da célula |
| Os dois | data não interpretável, mantida como texto | fica visível na célula, sem contagem |

**A palavra "bloqueia" precisa de honestidade:** a Central não tem botão de
"encerrar semana". O que existe é o snapshot. Então bloquear significa,
concretamente: a semana é gravada com `encerravel: false`, a tela abre com a
lista vermelha, e a **execução seguinte lista o que ficou aberto na semana
anterior**. É a trava possível neste desenho, e ela entrega o que a regra nº 4
quer: ninguém encerra sem saber.

## 8. O que desaparece com o ambiente

`[FATO]` Cerca de um terço do código VBA de mercadorias é ambiente, e some
inteiro:

| Sai | Por quê |
|---|---|
| `raizAno` com o literal `2026` e a raiz do OneDrive | a Central entrega o arquivo |
| `LocalizarPastaSemana` e o seletor manual de pasta | idem |
| A cópia para `%TEMP%` e o `SetAttr` contra o OneDrive | o arquivo já chega local |
| `AbrirWorkbookRobusto`, com as três estratégias de abertura | não há Excel |
| Os quatro `FileDialog` de serviços | o arquivo é arrastado |
| `ScreenUpdating`, `DisplayAlerts`, `Calculation`, `StatusBar` | não há estado global de Excel |
| `AtualizarResumoExecutivo` como rotina reexecutável | vira **modo de execução**: arrastar a planilha da semana junto com os relatórios |

## 9. Nada disso está provado contra a macro

O padrão-ouro — os arquivos reais de uma semana e o `Pendentes{N}.xls` que a
macro produziu a partir deles — ainda não chegou. Enquanto não chegar, a
documentação diz, com todas as letras, que a **divergência zero não está
provada**, e os comportamentos que dependem de medição ficam **como estão
hoje**, defeito e tudo. Ver
[02 — O porte do VBA](02-porte-do-vba.md) e a
[decisão pendente nº 1](05-decisoes-pendentes.md).
