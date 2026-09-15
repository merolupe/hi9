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

## 1. O Resumo Executivo sai do porte e vira outra coisa

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

O que ainda não está decidido: quem dispara o resumo (a Central, depois das
duas execuções? uma terceira entrada no catálogo?), o que acontece quando só
uma das duas frentes rodou na semana, e se o consolidado para a gerência e o
detalhado por unidade passam a ser dois documentos — sugestão que já estava em
aberto no dossiê de origem.

## 2. Base de conhecimento para pré-categorizar

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

## 5. Pedido não confirmado é pendência do Suprimentos

**Hoje:** o farol de pedido tem três estados — confirmado, não confirmado e sem
pedido vinculado —, e o não confirmado não tem dono. Ele aparece na planilha e
não vira cobrança de ninguém.

**Vai ser:** **pedido de compra não confirmado é pendência do Suprimentos**, com
guardião próprio, como qualquer outra pendência com responsável, prazo e próxima
ação esperada.

O que falta decidir: se o Suprimentos entra na lista de guardiões como área
normal (e então herda, é cobrado e responde pelo retorno) ou se vira uma
população separada, como o `PENDENTES FIS-FAT` é hoje para Fiscal e Faturamento.
A segunda forma é a que o VBA já sabe fazer.

## 6. A lista está aberta

Há mais coisa para ver. Esta seção existe para que o caderno não pareça fechado
quando não está — item novo entra aqui e ganha seção própria quando amadurecer.
