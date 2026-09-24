# Próximas rodadas

> O caderno do que já se sabe que vem, **antes de estar desenhado**. Anotado
> pelo Compliance Tributário em 15/09/2026, para não se perder entre uma
> entrega e outra.
>
> Público: analista desenvolvedor + Compliance Tributário.

Isto **não** é o plano de entrega e **não** são decisões pendentes:

| Documento | O que guarda |
|---|---|
| [04 — Plano de entrega](04-plano-de-entrega.md) | o que está desenhado e em que ordem entra |
| [05 — Decisões pendentes](05-decisoes-pendentes.md) | perguntas fechadas, cada uma com **padrão assumido** rodando hoje |
| **este** | rumos que o time já enxerga e que ainda **não** foram desenhados |

Nenhum item daqui bloqueia o porte. Nenhum deles deve ser implementado por
conta própria: o que está escrito é a intenção, não a especificação.

---

## 1. O Resumo Executivo sai do porte e vira outra coisa · **feito em 22/09/2026**

> **Entregue.** O painel das duas frentes roda, com as três categorias, sobre
> o relatório já classificado — e foi conferido contra o relatório de produção
> da semana 38, bloco a bloco. O que ele mostra, de onde sai cada número e o
> que ele se recusa a contar estão em
> [07 — O Resumo Executivo](07-resumo-executivo.md).
>
> As três perguntas que estavam em aberto no fim desta seção foram
> respondidas: **uma terceira entrada no catálogo** dispara o resumo; **uma
> frente só é caso normal** — o painel monta com o que houver e diz o que não
> veio; **consolidado e detalhado continuam no mesmo documento**, e a separação
> segue em aberto.
>
> O que sobrou desta rodada é a aba `Resumo`, que é outra coisa: a série
> semanal, as médias por quinzena e os dois campos de texto. Ver § 6.

**Hoje:** é uma aba montada pela macro de mercadorias, com quatro gráficos e
duas categorias — Diretos e Indiretos.

**Vai ser:** um resumo **automático das duas frentes**, gerado depois que
mercadorias e serviços rodarem, com **três categorias — Diretos, Indiretos e
Serviços** —, e com o layout revisto.

Consequência imediata: **o Resumo Executivo deixa de ser a entrega 4 do porte.**
A entrega 4 continuava reproduzindo o painel do VBA, e reproduzir fielmente uma
tela que vai mudar de conteúdo e de forma é trabalho que nasce para ser jogado
fora. O bloco fica suspenso até esta rodada ser desenhada — e a análise de
viabilidade dos gráficos, que já está feita na § 4 do plano de entrega,
continua valendo para quando for a hora.

### O resumo depende de classificação completa, e por isso vem por último

`[FATO]` Decisão de 17/09/2026, depois de o relatório real da semana 37 entrar
na análise: **o resumo só faz sentido sobre um relatório totalmente
classificado** — e a classificação completa só existe depois que os relatórios
são gerados e remodelados à mão. Ele é o fim do ciclo da semana, não uma saída
da execução.

Duas consequências práticas:

- **Cada frente continua rodando sozinha.** Gerar só mercadorias e gerar só
  serviços são casos normais da semana, não exceções — o resumo não pode virar
  condição para rodar nenhum dos dois, e nenhuma das duas execuções espera pela
  outra.
- **A ordem de trabalho muda:** primeiro se automatiza o que dá para automatizar
  dentro dos dois relatórios — é o que encurta a remodelagem manual — e só
  depois se constrói o resumo. Quanto menos classificação manual sobrar, mais
  cedo o resumo da semana fica pronto, e menos ele depende de alguém ter
  terminado.

`[FATO]` O layout-alvo deixou de ser hipótese: o relatório da semana 37 traz o
painel em uso, e ele já é o de três categorias, com TOP 10 de Indiretos, TOP 5
de Diretos e TOP 5 de Serviços, média de dias pendente na tabela por categoria,
e as duas frentes no mesmo arquivo. **É esse painel que o resumo tem que
reproduzir** — não o do `.bas` v14, que tem duas categorias e outra área de
impressão.

O que ainda não está decidido: quem dispara o resumo (a Central, depois das
duas execuções? uma terceira entrada no catálogo?), o que acontece quando só
uma das duas frentes rodou na semana, e se o consolidado para a gerência e o
detalhado por unidade passam a ser dois documentos — sugestão que já estava em
aberto no dossiê de origem.

**Respondidas em 22/09/2026**, na ordem: uma terceira entrada no catálogo,
`Resumo Executivo`, que recebe a planilha da semana em vez de um export;
uma frente só é caso normal, e o painel diz na tela o que não veio; o
consolidado e o detalhado continuam no mesmo arquivo — separá-los continua em
aberto, e agora é decisão de quem lê o painel, não de quem o constrói.

## 2. Base de conhecimento para pré-categorizar · **a base existe desde 22/09/2026**

> **Feita, e fechada em 24/09/2026.** A base foi importada, medida e ligada; e
> desde 24/09 ela é **consultável e editável na tela** e **aprende sozinha** das
> planilhas que voltam classificadas. As três camadas — fotografia importada,
> aprendizado do livro e correção humana — e a razão de cada uma estão em
> [08 — A base de conhecimento](08-base-de-conhecimento.md).
>
> `[FATO]` Medida contra a semana 38, que a base não viu: **categoria acerta
> 44 de 44 com evidência firme**; **guardião acerta 77% e não tem nenhuma
> proposta firme**. Com esses números na mesa, o Compliance Tributário decidiu
> em 22/09/2026 **preencher as duas** — assumindo cerca de 12 guardiões
> errados em 67 notas como custo de conferência.
>
> As perguntas desta seção foram respondidas assim: a sugestão nasce **no
> campo definitivo**, e não em coluna própria; quem confirma é quem remodela a
> planilha, e o que a ferramenta preencheu sai **marcado em cor** para que ele
> saiba o que olhar. O que falta é a trilha do outro lado: hoje a semana
> seguinte não distingue, na volta, uma célula confirmada de uma célula
> proposta que ninguém olhou.

**Hoje:** Tipo de Operação, Guardião, Gestor de apoio e Categoria são 100%
manuais. O que a ferramenta faz é preservar o que foi digitado, nunca inferir —
[regra nº 4](../../CLAUDE.md) do repositório.

**Vai ser:** uma base que **propõe** classificação a partir do que já foi
classificado, em duas frentes distintas:

| Frente | A partir de | Confiança |
|---|---|---|
| **Tipo** | o CFOP do documento | alta — o CFOP é dado do documento, não opinião |
| **Guardião e Gestor** | o histórico do parceiro e da unidade | a medir |

O ponto delicado é a fronteira com a regra nº 4: **propor não é classificar.**
Uma sugestão que entra na planilha já preenchida vira, na prática, classificação
por adivinhação — alguém confirma sem olhar. As perguntas a responder quando
esta rodada for desenhada: a sugestão nasce em coluna própria ou no campo
definitivo? quem confirma, e isso fica carimbado? uma sugestão errada que passou
batido é rastreável depois?

O dossiê de origem já previa o primeiro pedaço disto — a agregação de 30 semanas
de histórico por parceiro. A chave (CNPJ inteiro ou raiz), o desempate quando o
histórico diverge e a precedência frente à herança do livro continuam em aberto.

**Respondido em parte, em 22/09/2026:** a chave é o **código do parceiro**, com
a unidade como desempate mais específico; o desempate quando o histórico diverge
é *não desempatar* — divergência vira sugestão com as alternativas à vista. A
precedência frente à herança do livro segue em aberto, e só importa quando a
base passar a preencher alguma coisa.

## 3. Pedido de compra na nota, e a validação contra a observação

**Hoje:** serviços já traz o pedido de compra mais recente do parceiro e o que
vem dele — comprador, requisitante, natureza, centro de resultado. Mercadorias
traz número do pedido e o farol de confirmação, vindos da Conferência de
Entradas.

**Vai ser:** trazer a informação do pedido **sempre que ela existir** e, onde
der, **conferir se ela bate com o que está escrito na observação da nota**.

`[FATO]` Em serviços isso é possível: a observação da nota já é lida e vai para
a planilha. Em mercadorias **ainda não** — a observação do documento não está
entre as colunas do relatório de importação de XML, então não há contra o que
conferir. Enquanto não houver, mercadorias fica só com o número do pedido, sem
validação.

## 4. Uma base de pedidos de compra, em vez de um recorte por semana

**Hoje:** o motor de serviços depende do relatório do Portal de Compras, e ele
precisa vir **desde o começo do ano** para que o histórico de parceiro, de
comprador e de requisitante esteja completo. Extrair isso toda semana é caro, e
é a maior fragilidade operacional da rotina de serviços.

**Vai ser:** uma base própria de pedidos, carregada uma vez com o histórico
inteiro e **atualizada por recortes curtos** — a semana, ou o mês corrente.

É o mesmo movimento que a classificação já fez ao sair do anexo de e-mail e ir
para o livro da ferramenta: o histórico passa a viver na ferramenta, e o arquivo
de entrada volta a ser só o movimento do período.

O que precisa ser decidido: onde a base mora (`dados/pendentes/`, como o livro),
o que é chave de pedido, o que acontece quando um pedido é alterado depois de
carregado, e por quanto tempo o histórico é mantido.

`[INFERÊNCIA]` Isto provavelmente resolve de lambuja a [pendência
nº 9](05-decisoes-pendentes.md) — o de-para de filiais que some quando a filial
não tem movimento no período, o caso Microbio. Com base própria, a filial não
depende de aparecer no recorte da semana.

## 5. Pedido não confirmado é pendência do Suprimentos · **feito em 24/09/2026**

> **Entregue como regra B1.5.** A decisão que faltava foi tomada pelo
> Compliance Tributário: **o Suprimentos entra como área normal**, na
> `Pendentes`, sem aba própria — ele herda, é cobrado e responde pelo retorno
> como qualquer outro guardião. A regra está em `classificacao.py`, com as três
> portas, e roda depois de B1 e antes da pré-categorização.
>
> As três portas, como foram pedidas: **pedido não confirmado** → Suprimentos;
> **pedido confirmado com incongruência preenchida** → Suprimentos; **pedido em
> branco** → não se toca na linha.
>
> `[FATO]` Medido nas 88 linhas classificadas à mão da semana 38: cinco notas
> passam pela segunda porta e o time marcou quatro delas como `Suprimentos`; a
> quinta, como `Manutenção Guará`. A **primeira porta não tem uma linha** naquela
> semana — entra sem medição, e a primeira semana real é que vai dizer.
>
> `[FATO]` Três linhas da `PENDENTES FIS-FAT` da semana 38 têm
> `NF-e Normal Compra` escrito em `Pedido confirmado?` — colunas deslocadas no
> arquivo montado à mão. A regra **não classifica** o que não reconhece: conta e
> avisa na tela (regra nº 4).
>
> O que sobrou em aberto está na decisão nº 16 de
> [05 — Decisões pendentes](05-decisoes-pendentes.md): quando B1 e B1.5 querem a
> mesma linha, hoje **B1.5 vence**, e esse cruzamento tem zero linhas na
> semana 38.

## 6. A aba `Resumo` — a série semanal, que o painel não cobre

**Hoje:** existe no relatório de produção, ao lado do `Resumo Executivo`, e é
mantida à mão. Ela mostra outra coisa: **a evolução entre semanas**.

`[FATO]` Medido no relatório da semana 38: a tabela tem uma linha por categoria
e uma coluna por semana (`Semana 35`, `36`, `37`, `38`), mais duas colunas de
média por quinzena (`1Q`, `2Q`); ao lado, a mesma grade em valor financeiro.
As semanas passadas estão **digitadas como número**, e só a coluna da semana
corrente tem fórmula. Embaixo, dois campos de texto livre — "Pontos de atenção
e riscos da semana" e "Pontos positivos da semana" — escritos por quem monta o
relatório.

**Vai ser:** montada pela ferramenta. O histórico que ela precisa já existe e
já é gravado: o **snapshot semanal imutável** guarda, de cada semana,
exatamente a contagem e o valor por categoria. A série deixa de ser digitada e
passa a ser lida de onde ela já está.

O que falta decidir: quantas semanas a tabela mostra; o que acontece com a
coluna de uma semana que não foi rodada; se as duas caixas de texto ficam em
branco para quem escreve (que é o que elas são hoje) ou se a ferramenta propõe
um rascunho a partir do que ela já sabe — e aí vale a mesma fronteira da § 2:
**propor não é afirmar**, e texto gerado que ninguém reescreve vira boletim
automático que ninguém lê.

## 7. A lista está aberta

Há mais coisa para ver. Esta seção existe para que o caderno não pareça fechado
quando não está — item novo entra aqui e ganha seção própria quando amadurecer.
