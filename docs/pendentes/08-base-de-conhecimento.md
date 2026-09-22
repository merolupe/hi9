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

## Os três graus, e o que cada um pode fazer

| Grau | Quando | O que pode fazer |
|---|---|---|
| **firme** | a proposta e o histórico dizem o mesmo, com **3 notas em 2 semanas** e 100% de concordância | preencher célula |
| **sugestão** | há proposta, mas o lastro é curto, diverge ou não existe | aparecer, com a evidência ao lado |
| **sem proposta** | nada a oferecer | dizer que não sabe |

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
| **Tipo de Operação** | 4 de 18 — 22% | — | 49 |

Três leituras, e nenhuma delas é "a base funciona":

1. **Categoria é o campo maduro.** Dois terços das notas ganhariam categoria
   com evidência firme, e nas 44 não houve um erro sequer.
2. **Guardião não está pronto para preencher.** 77% de acerto quer dizer uma
   nota errada a cada quatro — e o guardião é quem recebe a cobrança. Ele
   sugere; quem decide é gente.
3. **Os 14 "erros" de operação são um só, e não é erro de classificação.**
   `[FATO]` A base diz `Compra Uso e Consumo` e a semana 38 diz
   `Compra Uso Consumo`. O vocabulário mudou entre uma semana e outra. Casar
   os dois por semelhança seria adivinhação; o caminho é uma tabela de
   sinônimos cadastrada, como a que já existe para nome de coluna.

**A ressalva que a própria medição imprime na tela:** ela não sabe se quem
classificou a semana 38 consultou a mesma base. Se consultou, a taxa mede
concordância, não acerto. Isso é do processo, não do dado.

## O que a base não faz

* **não preenche nada, ainda.** Ela responde a quem perguntar; nenhuma etapa
  do relatório semanal a consulta. Onde a sugestão deve aparecer — em coluna
  própria ou no campo definitivo — é decisão de quem recebe a planilha, e
  agora ela pode ser tomada com número na mão;
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
