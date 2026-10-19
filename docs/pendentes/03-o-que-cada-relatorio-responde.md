# O que cada relatório responde

> Público: **time Fiscal/Tributário e as áreas guardiãs.** Este documento não
> fala de código. Fala do que a ferramenta responde, do que continua sendo
> decisão de gente, e de como fica o ciclo da semana.

---

## 1. As duas perguntas — e a terceira, que é sobre as outras duas

| Ferramenta | A pergunta |
|---|---|
| **GerarPendentes** (mercadoria) | *Quais notas emitidas contra a Hinove ainda não foram lançadas, de quem é a responsabilidade e há quantos dias estão paradas?* |
| **GerarServPend** (serviço) | *Quais notas de serviço ainda não foram lançadas, qual pedido de compra e qual requisitante estão por trás delas, e o quanto o ASIS deixa de capturar?* |

| **Resumo Executivo** (as duas) | *Onde está concentrado o que sobrou — em qual categoria, em qual unidade, com qual guardião — e quais notas são as mais antigas e as mais caras?* |

As duas primeiras fazem o mesmo movimento: pegam **tudo o que foi emitido**
contra a empresa, pegam **tudo o que foi lançado** no Sankhya, e mostram a
diferença. O que sobra é a pendência.

A terceira não cruza nada: ela lê o que as duas produziram, **depois** de a
classificação estar fechada, e responde onde a pendência dói. Está detalhada em
[07 — O Resumo Executivo](07-resumo-executivo.md).

## 2. GerarPendentes — mercadoria

### O que entra

| Relatório | De onde vem |
|---|---|
| Importação de XML | Sankhya — o universo de NF-e capturadas contra CNPJ da Hinove |
| Conferência de Entradas | Sankhya — o que já foi conferido física e fiscalmente |
| A planilha da semana passada | a sua, com as classificações preenchidas — **agora opcional** |

### O que sai

| Aba | O que tem nela | Quem olha |
|---|---|---|
| **Pendentes** | o que é das áreas de negócio | os guardiões |
| **PENDENTES FIS-FAT** | o que é do Fiscal e do Faturamento | o time fiscal |
| `CTe` · `Manifestados` · `Entradas 3os` · `Lançados` | o que saiu da lista, e **por quê** | quem precisa conferir uma saída |
| **Descartados** *(nova)* | XML de terceiro e NF-e destinada a transporte | quem quiser medir o descarte |

As cinco abas de baixo ficam ocultas, como hoje — são evidência de auditoria, e
continuam reexibíveis por clique direito. A aba `Descartados` é a única novidade:
hoje essas linhas somem sem deixar rastro, e não há como dizer quantas foram.

**O `Resumo Executivo` não vem nesta versão.** O painel deixou de ser cópia da
aba de hoje e virou outra coisa: um resumo automático das **duas** frentes —
mercadorias e serviços —, com três categorias (Diretos, Indiretos e Serviços) e
layout revisto. A decisão é de 15/09/2026, do Compliance Tributário, e está em
[06 — Próximas rodadas](06-proximas-rodadas.md).

Enquanto ele não vem, quem roda vê os números na própria tela da Central —
quantas pendências, de quem, quanto valem e o que exige revisão — e o e-mail
segue com as duas abas de sempre.

### A célula âmbar é sugestão da ferramenta

`[FATO]` Desde 22/09/2026 a ferramenta **preenche** `Categoria`, `Guardião` e
`Tipo de Operação` quando a célula está vazia e a base de conhecimento tem o
que propor. O que ela preencheu sai com **fundo âmbar claro**.

Três coisas que vale saber antes de confiar na cor:

* **o que você escreveu nunca é sobrescrito.** A célula âmbar estava vazia;
* **categoria e operação erram pouco, guardião erra mais.** Medido contra a
  semana 38: categoria acertou 44 de 44 e operação 18 de 18 no grau de
  evidência firme; guardião acerta cerca de três em cada quatro. Confira o
  guardião âmbar antes de cobrar alguém;
* **a operação sai na sua redação.** Se o time passa a escrever `Compra Uso
  Consumo` no lugar de `Compra Uso e Consumo`, a ferramenta acompanha na
  semana seguinte — ela escreve a grafia que o livro mais usa, não a que
  aprendeu;
* **um guardião proposto encaminha a nota** — se a base propõe `Faturamento`,
  a nota vai para a `PENDENTES FIS-FAT`, como iria se você tivesse escrito.

A tela conta quantas células foram preenchidas, por coluna, sob o título
"confira antes de cobrar". Quem não quiser o preenchimento desliga por coluna
no parâmetro `pre_categorizacao`.

### Por que uma nota sai da lista

A ordem importa, e a **primeira** explicação que serve é a que vale:

| Ordem | Se a nota… | Ela vai para |
|---|---|---|
| 1 | tem tomador de CT-e | `CTe` |
| 2 | está com manifestação *desconhecida* ou *operação não realizada* | `Manifestados` |
| 3 | está cancelada | `Manifestados` |
| 4 | é entrada de terceiro | `Entradas 3os` |
| — | já tem conferência fiscal = `Sim` | `Lançados` |
| — | **nada disso** | fica em `Pendentes` — **é a cobrança** |

E duas saem antes de tudo, sem chegar a ser roteadas: a nota sem `Nome
Fantasia` (XML emitido contra outro CNPJ, importado por engano) e a NF-e
destinada a transporte (em que a Hinove aparece no grupo `<transporta>`, mas
não é a destinatária).

## 3. GerarServPend — serviço

### O que entra

| Relatório | De onde vem | Obrigatório? |
|---|---|---|
| ASIS / Portal Nacional | as notas de serviço emitidas contra a Hinove | sim |
| Portal de Compras | os lançamentos de serviço do Sankhya | sim |
| Conferência de Serviços | para achar o pedido a que a nota está anexada | não |
| A planilha da semana passada | a sua, com as classificações | não |

### O que sai

| Aba | O que responde |
|---|---|
| **Lancadas** | casou: a nota já está lançada, e por qual critério |
| **Pendentes** | **não casou** — é a cobrança, com pedido, comprador e requisitante |
| **Canceladas** | a nota foi cancelada; não é pendência nem lançamento |
| **Sem Correspondencia ASIS** | o inverso: o Sankhya lançou e o ASIS não capturou |

A última aba é a que mede o **buraco da fonte externa**. Ela não é lista de
pendência: é a resposta para "o ASIS está pegando tudo?". Na execução de
referência, 127 lançamentos não tinham contraparte.

### O que sai do relatório, e por quê

`[FATO]` Duas regras do time fiscal, de 22/09/2026. As duas tiram a nota da
`Pendentes` **depois** do confronto, e as duas escrevem por quê:

**A nota cancelada na prefeitura que a nossa base não sabe.** Acontece de a
NFS-e ser cancelada na prefeitura e o evento de cancelamento nunca chegar à
base de serviços. Do lado de cá a nota continua emitida, nunca é lançada, e
volta toda semana como pendência de alguém. Quando isso é descoberto, quem
remodela a planilha escreve `cancelada` em **`Guardiao`, `Gestor de apoio` e
no `Retorno`** — os três, porque um campo sozinho é digitação e os três juntos
são uma afirmação. Na semana seguinte a nota sai da `Pendentes` e vai para a
aba `Fora do relatorio`.

A marca vive no **livro de classificação**, que é onde a classificação da
semana passada já mora, e a aba é lida de volta junto com a `Pendentes`. São
dois caminhos para a mesma conclusão: perder o arquivo não faz a nota voltar,
e escrever direto na aba também funciona.

**A exceção cadastrada.** Parceiro e valor que o time decidiu não cobrar — por
exemplo, um prestador cuja nota de valor fixo é tratada por fora. Não é regra
derivável de nada: é decisão, e por isso é **cadastro**, com parceiro, valor e
o motivo que vai para a planilha. Nasce vazia, e vazia não exclui nada.

**Nenhuma das duas apaga.** A aba `Fora do relatorio` traz a nota inteira — as
36 colunas da `Pendentes` — mais a coluna `Motivo`, e a tela conta quantas
saíram por cada motivo. É a mesma decisão da aba `Descartados` de mercadorias:
esconder, e não apagar, para que o volume excluído seja mensurável.

### Como o confronto casa uma nota com um lançamento

Não existe chave comum entre o ASIS e o Sankhya — nem chave de acesso, nem
dígito verificador. Então o confronto tenta quatro caminhos, **do mais forte
para o mais fraco**, e cada um percorre a lista inteira antes de o seguinte
começar:

| # | Casa por | Força |
|---|---|---|
| 1 | número da nota + CNPJ do prestador | forte |
| 2 | número da **RPS** + CNPJ — para as prefeituras que informam a RPS como número da nota | forte |
| 3 | CNPJ + valor | média |
| 4 | número da nota + valor, **sem CNPJ** | **fraca — exige revisão** |

Um lançamento casa com no máximo uma nota, e uma nota com no máximo um
lançamento. O que casou pelo caminho 4 sai marcado, e passa a **bloquear o
encerramento da semana** até alguém olhar — hoje isso é uma frase na mensagem
final e mais nada.

## 4. O que continua sendo decisão de gente

**Tudo o que classifica.** A ferramenta não inventa guardião, não adivinha
categoria e não decide tipo de operação. Ela:

| Faz sozinha | Não faz — e não vai fazer |
|---|---|
| diz o que está pendente e há quantos dias | dizer de quem é a culpa |
| traz a classificação que **você** deu na semana passada | classificar uma nota nova |
| manda para `PENDENTES FIS-FAT` o que está marcado como Fiscal ou Faturamento | decidir que algo é do Fiscal, salvo a regra abaixo |
| agrupa por unidade, por categoria e por guardião | criar unidade ou categoria que não existe no cadastro |

**A única classificação automática** é a regra que já existe hoje: mercadoria
com conferência **física = Sim** e **sem incongruência** é pendência de
lançamento fiscal, não da área requisitante — então o guardião vira `Fiscal` e
o gestor de apoio é esvaziado. É a única regra que sobrescreve o que uma pessoa
escreveu, e ela roda **depois** de a classificação da semana passada ser
aplicada.

## 5. O ciclo da semana

```
segunda    você arrasta os relatórios da semana na Central
           ↳ sai a planilha, já com as classificações que o time deu antes

a semana   o time edita as colunas de classificação na planilha e cobra as
           áreas por e-mail — exatamente como hoje

quarta,    você arrasta a planilha editada de volta, junto com os relatórios
sexta      ↳ a Central guarda o que mudou e REGERA a planilha inteira,
             já com o painel e as abas atualizados
```

**O que muda para quem usa:**

* **arraste na ordem que quiser.** Cada arquivo é reconhecido pelas colunas que
  ele tem, não pelo nome. Não existe mais "renomear para `XMLAnterior.xls`";
* **perder a planilha da semana passada deixou de ser um problema.** A
  classificação não mora mais dentro dela — mora na ferramenta, com registro de
  quem preencheu e quando;
* **uma nota que sumiu e voltou volta classificada.** Hoje, se a nota sai de
  `Pendentes` numa semana (foi lançada, cancelada, roteada) e volta na
  seguinte, ela volta **em branco**;
* **quarta e sexta continuam sendo quarta e sexta** — só que agora as abas
  `Pendentes` e `PENDENTES FIS-FAT` também saem atualizadas, o que hoje não
  acontece: só o painel era recalculado;
* **a versão de segunda continua existindo, intacta.** Cada execução guarda uma
  cópia imutável da semana, para o dia em que alguém perguntar qual era a
  posição numa data.

## 6. O que a tela mostra antes de você abrir a planilha

Quatro números em destaque e, abaixo deles, as listas — na ordem em que
importam.

**Vermelho — trava o encerramento da semana.** É o que alguém precisa olhar
antes de a semana ser dada por fechada: unidade que a ferramenta não
reconheceu, categoria fora da lista, confronto feito pelo caminho fraco,
vínculo de pedido ambíguo, CNPJ de filial que não está no cadastro.

**Amarelo — ficou de fora, e você precisa saber.** Relatório opcional que não
veio, lançamento com CNPJ zerado, data que não deu para interpretar e ficou
como texto na célula.

**Neutro — o que aconteceu.** Quanto foi herdado do livro, quanto foi alterado
pelo retorno, quantas notas entraram sem classificação, e — em serviços —
quantas casaram por cada um dos quatro caminhos.

Essa última lista tem uma função extra: **é a conferência do porte à vista.**
A soma dos quatro caminhos tem de dar exatamente o número de notas lançadas. Se
um dia não der, o número aparece errado na tela antes de aparecer errado na
planilha.

## 7. O que a ferramenta não conserta

| | Por quê |
|---|---|
| A abrangência do ASIS não é 100% | é limitação da fonte. Nenhum software conserta um dado que não foi capturado — o que dá para fazer é medir o buraco, e a aba inversa mede |
| O pedido de compra mostrado pode ser de outra filial | a regra de hoje escolhe o pedido mais recente do fornecedor, sem olhar filial nem período. Mudar isso muda colunas que o time lê — é a pendência 5 |
| A conferência física só existe depois que alguém confere | o teto de atualidade é humano |
| O e-mail continua sendo enviado por você | está fora do escopo, nos dois documentos de origem |
