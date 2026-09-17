# Pendentes — decisões pendentes

> Perguntas que só o time fiscal responde. Cada uma traz o **comportamento-padrão
> assumido** enquanto a resposta não vem — nenhuma bloqueia o desenvolvimento, e
> nenhuma delas é código.
>
> 🟢 responder quando puder · 🟡 responder antes da entrega que depende dela ·
> 🔴 **trava a prova do porte**
>
> A nº 14 nasceu na entrega do motor de serviços e a nº 15 na de mercadorias;
> as treze primeiras vêm da leitura do VBA.
>
> O que o código já respondeu, e por isso **não** é pendência, está no fim.

---

## 1. 🔴 Os arquivos reais de uma semana e a saída da macro correspondente

O Fiscalbot provou o porte com **divergência zero** contra 6.554 registros
reais. Aqui não há como fazer menos: a planilha vira cobrança formal às áreas e
é evidência de controle interno.

**Pedido — de uma semana só:**

* mercadorias: `XML{N}.xls`, `CE{N}.xls`, `XMLAnterior.xls` **e** o
  `Pendentes{N}.xls` que a macro gerou a partir deles;
* serviços: o par `ASIS.xlsx` + `PC27.xlsx` de 10/08/2026, a Conferência de
  Serviços, a semana anterior **e** o `Notas_Servico_Pendentes_*.xlsx` daquela
  execução.

Os arquivos vão para `competencias/pendentes/`, que é ignorada pelo git — não
entram no repositório em nenhuma hipótese.

**Padrão assumido:** as entregas saem provadas **só** por invariantes
estruturais e planilhas fictícias, e a documentação diz, com todas as letras,
que a divergência zero **não está provada**. As seis medições do documento do
porte ficam pendentes, e os comportamentos correspondentes ficam **como estão
hoje, defeito e tudo**.

**O que isso custa em concreto:** seis defeitos conhecidos continuam no
produto — a herança lida por posição, os dois offsets fixos, as comparações
assimétricas do roteamento, a chave de acesso comparada sem normalização e a
data-hora que some quando não é interpretável.

## 2. 🟡 `Dias Emissão Doc` é contagem de dias ou é data?

A coluna está simultaneamente na lista de datas (escrita como valor nativo) e
na de formatos `DD/MM/YYYY`. Se for contagem de dias, o valor 30 exibe
`30/01/1900`.

**Pergunta:** o que essa coluna traz no export do Sankhya?

**Padrão assumido:** preservar exatamente como está, inclusive o possível
defeito, até ver um export real. **Preservar um defeito visível é melhor do que
corrigir por suposição.**

## 3. 🟡 Data de conferência física e data do último anexo guardam hora

O valor retém hora; a exibição é só `dd/mm/aaaa`. Filtro por igualdade de data
exata falha, e é limitação que o próprio dossiê já registra.

**Pergunta:** exibir `dd/mm/aaaa hh:mm`, truncar a hora no valor, ou separar em
duas colunas — como o DiXML faz com `Emissao Data` / `Emissao Hora`?

**Padrão assumido:** preservar valor e formato de hoje. As três saídas mudam
uma coluna que dezenas de pessoas leem.

## 4. 🟢 Emissão do ASIS na mesma data do `Dt. Neg.`

`[FATO]` O código é estrito: `<` conta como "antes", `>` conta como "depois", e
**igual não conta como nenhum dos dois**. O dossiê marcava isso como nunca
validado; o código respondeu.

**Pergunta:** é o desejado, ou data igual deveria contar como "depois"
(lançamento no mesmo dia da emissão)?

**Padrão assumido:** preservar o estrito. Mudar move as contagens das 127
linhas de referência e invalidaria o padrão-ouro.

## 5. 🟡 O "pedido de compra mais recente" pode ser de outra filial

`mapPedido` é indexado **só** por CNPJ do parceiro, sem filtro de empresa nem
de período, e vence o maior `Nro. Unico`. O pedido mostrado pode pertencer a
outra filial e a outro mês.

**Pergunta:** restringir o pedido à mesma filial da nota? E a uma janela de
tempo?

**Padrão assumido:** preservar a regra e **contar** na tela quantas notas
receberam pedido de filial diferente da sua. O número é o que vai fundamentar a
resposta.

## 6. 🟡 Quais são as categorias e os guardiões válidos?

Hoje qualquer texto entra. Sem lista fechada, "categoria não reconhecida" não
existe e a regra nº 4 fica sem dente.

**Perguntas:** a lista de categorias é exatamente `Diretos` e `Indiretos`? Qual
é a lista de guardiões/áreas? E `Fiscal` e `Faturamento` continuam sendo os dois
que vão para a `PENDENTES FIS-FAT`?

**Padrão assumido:** categorias `Diretos` / `Indiretos` / vazio já vêm
cadastradas na carga de fábrica — qualquer outra coisa bloqueia o encerramento.
Guardião **sem validação** até a lista chegar (comportamento de hoje), com a
lista já pronta para ser cadastrada na tela.

**Um aviso honesto:** a mesma lógica vale para a tabela de **unidades**, que é
dado da empresa e por isso **nasce vazia** — o repositório não carrega nome de
unidade. Enquanto ela não for cadastrada, a derivação de unidade não acontece.
O cadastro são cinco linhas, e a ordem delas importa: `CORUMB` **antes** de
`GUAR`, senão a fantasia de Corumbá cai em Guará.

## 7. 🟢 De onde vem o número da semana, agora que não há `InputBox`

`[FATO]` A semana hoje é digitada e determina o nome dos arquivos e o rótulo
`Retorno semana {N-1}`. Sem `InputBox`, a Central precisa deduzi-la — e deduzir
em silêncio é adivinhação.

**Padrão assumido:** número da semana do arquivo anterior **+ 1**; sem arquivo
anterior, a semana ISO da data de execução. **Sempre exibida como `Ficha` na
tela** ("Semana 31") e corrigível na configuração antes de rodar de novo.

## 8. 🟢 Harmonizar a largura das abas auxiliares

`CTe`, `Manifestados` e `Entradas 3os` têm 27 colunas e `Lançados` tem 33, por
acidente do momento em que cada uma copia o cabeçalho. Igualar todas em 38 é
trivial.

**Pergunta:** alguém tem fórmula, PROCX ou tabela dinâmica apontando para essas
abas?

**Padrão assumido:** **não harmonizar.** São invariantes da prova de regressão,
e a mudança só paga depois da divergência zero.

## 9. 🟢 O de-para estático de filiais

`[FATO]` Não existe mapa estático: o de-para é construído do próprio export do
Portal de Compras, e é por isso que a filial **sem movimento no período**
desaparece e vira `"CNPJ nao mapeado: ..."` dentro da célula.

**Pedido:** a relação CNPJ → nome e código de filial, para o complemento
estático. Ela é dado da empresa: vai para a base, fora do git, cadastrada na
tela — não entra no repositório.

**Padrão assumido:** só o mapa dinâmico. CNPJ que ele não resolve entra em
**lista bloqueante** na tela, em vez de virar texto dentro da planilha.

## 10. 🟢 Guardar quanto tempo de snapshot, e onde

**Pergunta:** os snapshots semanais ficam na máquina de quem roda, ou numa
pasta sincronizada que a área de Controles Internos alcance? Por quantas
semanas?

**Padrão assumido:** `dados/pendentes/semanas/`, na pasta do repositório,
**sem expurgo automático**. Apagar evidência por iniciativa da ferramenta seria
pior do que ocupar disco.

`[INFERÊNCIA]` O custo é de espaço: uma planilha de mercadorias com ~2.500
linhas × 38 colunas mais um YAML de alguns milhares de chaves dá poucos
megabytes por semana. Cinquenta semanas cabem folgadamente.

## 11. 🟢 Uma coluna de retorno ou o histórico inteiro na planilha?

O livro guarda **todos** os retornos, semana a semana. A planilha, hoje,
carrega um (`Retorno semana {N-1}`).

**Pergunta:** vale acrescentar `Retorno semana {N-2}`, para o guardião ver a
própria resposta anterior?

**Padrão assumido:** **uma** coluna, para preservar as 38 e as 36 colunas. O
histórico completo fica no livro e no snapshot.

## 12. 🟢 A ingestão deve aceitar planilha editada por qualquer pessoa?

O time todo edita a planilha e a devolve por e-mail. Se duas versões da mesma
semana forem arrastadas, a segunda vence a primeira onde divergirem.

**Pergunta:** aceitar várias devoluções por semana (o desenho atual) ou exigir
uma consolidada?

**Padrão assumido:** aceitar várias, gravando **de quem veio cada alteração**
(o carimbo) e listando as divergências na tela. Nunca sobrescrever em silêncio.

## 13. 🟢 Base de categorização por parceiro

O roadmap de curto prazo do dossiê pede uma relação parceiro → categoria,
agregada de 30 semanas de histórico. Ficaram em aberto: a chave (CNPJ completo
ou raiz), quais campos a base determina, o desempate para histórico divergente
e a precedência frente à herança.

**Padrão assumido:** não implementar. O livro de classificação é o pré-requisito
dela — com 30 semanas de livro, a base sai por consulta, não por projeto novo.

## 14. 🟡 A `Pendentes` de serviços deveria carregar o CNPJ do prestador?

`[FATO]` A identidade de uma nota entre uma semana e a outra é
`número normalizado | Cod Parceiro` — e é assim porque a aba `Pendentes`
**não carrega o CNPJ do prestador**. O comentário do VBA registra a decisão com
essas palavras.

`[FATO]` A consequência: todo prestador sem cadastro no Sankhya compartilha o
literal `Sem cadastro` como segunda metade da chave. Duas notas de fornecedores
distintos, ambos sem cadastro, com o mesmo número normalizado, produzem **a
mesma chave** — e a classificação de uma passa a valer para a outra.

`[FATO]` A entrega de serviços não elimina isso; ela **tira o silêncio**. O
livro passa a guardar o CNPJ de quem emitiu (`estado.registrar_identidade`), e
quando o dono de uma chave muda entre execuções o caso é contado e vai para a
tela. Eliminar de vez exige uma **coluna a mais** na aba — e a largura de 36 é
invariante da prova de regressão, além de alvo provável de PROCX de terceiro.

**Pergunta:** acrescentar `CNPJ Prestador` como 37ª coluna da `Pendentes` de
serviços, depois da prova de divergência zero? Ou basta a contagem?

**Padrão assumido:** **não acrescentar.** A planilha continua com 36 colunas, o
livro continua guardando o CNPJ, e a colisão continua possível — porém contada
e visível. Se a contagem vier zerada nas primeiras execuções reais, a pergunta
se responde sozinha.

## 15. 🟡 O que a regra B1 escreveu deve voltar para o livro?

`[FATO]` O livro de classificação existe para guardar **julgamento humano**: o
que o time digitou em `Tipo de Operação`, `Guardião`, `Gestor de apoio`,
`Categoria` e no retorno da semana. A regra B1 é a única do módulo de
mercadorias que escreve numa dessas colunas sozinha — ela grava `Fiscal` em
`Guardião` e esvazia `Gestor de apoio` quando a mercadoria foi conferida
fisicamente sem divergência.

`[FATO]` Quando o time devolve a planilha editada, essas linhas voltam com
`Fiscal` escrito. A ingestão não sabe distinguir quem escreveu o quê: ela lê a
célula e grava no livro. **O livro passa a guardar, junto com o julgamento
humano, o que a máquina derivou.**

`[FATO]` O efeito visível é o mesmo de hoje: no VBA a reclassificação também
volta na semana seguinte, porque ela está na aba `PENDENTES FIS-FAT` do arquivo
anterior e o PROCX a lê de lá. E como B1 roda **depois** da herança e é
recalculada do zero a cada execução, a célula entregue é sempre a que a regra
decidiu nesta semana, não a da semana passada.

`[FATO]` O que muda é o conteúdo do livro. Uma nota que num mês foi conferida
fisicamente e voltou como `Fiscal`, e no mês seguinte deixa de ser conferida,
carrega `Fiscal` no livro — e não o `Suprimentos` que alguém tinha digitado
antes de B1 passar por cima.

**Pergunta:** o livro deve distinguir o que a pessoa escreveu do que a regra
derivou — guardando os dois, e devolvendo o humano quando a regra deixar de
disparar?

**Padrão assumido:** **não distinguir.** É o que reproduz o comportamento de
hoje, e distinguir exigiria uma coluna a mais na planilha para marcar a origem
de cada valor — a mesma objeção da decisão nº 14: a largura de 38 é invariante
da prova de regressão e alvo provável de PROCX de terceiro. Se a pergunta vier
a valer a pena, o lugar dela é o livro, não a planilha: o registro já tem
carimbo de quem gravou, e `gravado_por` poderia dizer `regra B1`.

---

## Já respondidas pelo código — não entram como pendência

| Pergunta que estava em aberto | Resposta |
|---|---|
| As categorias são uma lista de nomes? | **Não**, são uma tabela com ordem: `NormalizarCategoria` é teste de subcadeia e testa `indireto` **antes** de `direto` |
| A herança de mercadorias lê só a aba `Pendentes` anterior? | **Não** — lê também a `PENDENTES FIS-FAT` do mesmo arquivo, e a `Pendentes` tem precedência |
| A condição 2 do roteamento compara duas grafias? | **Três** — `desconhecida`, `operação não realizada` e `operacao nao realizada`, porque a comparação é `LCase` e não remove acento |
| A rodada de formatação de 17/08/2026 entrou em produção? | **Não.** O `.xlam` é byte a byte idêntico à v14; 8 dos 10 ajustes estão ausentes. **Não existe v15** |
| Layout da aba `Canceladas` (serviços) | **16 colunas**, layout próprio — **não** é a `Pendentes` mais duas |
| Integração com a Conferência de Serviços | **totalmente implementada**: colunas 29–36, com filtro de data, valor exato ou múltiplo 2×–12×, desempate por maior NU e rótulo de confiança |
| De-para completo CNPJ tomador → filial | **não existe mapa estático**; é construído do próprio export |
| Regra de data igual no bloco antes/depois | **estrita** |
| Sentido da coluna `Diferenca` | **Entradas − ASIS** |
| Chave de identidade entre semanas (serviços) | `NormNota(Nro Nota) \| Cod Parceiro` — **não** nota + CNPJ do prestador |
| `Lancadas` tem 11 ou 12 colunas? | **12** — a 12ª é `Obs` |
| `Pendentes` (serviços) tem 27 colunas? | **36** |
| Quantas o proc 2 resolveu na execução de referência? | **zero** — 2.467 + 191 + 12 = 2.670 fecha exatamente |
| A coluna 36 distingue "sem filial mapeada" de "não encontrei"? | **não.** Os dois casos gravam `Nao encontrado`; quem distingue, agora, é a lista bloqueante da tela |
| O vínculo exige mais do que data e valor? | **sim**: emissão interpretável **e** valor da nota maior que zero, e valor do pedido maior que zero. Não estava registrado em lugar nenhum |
| "Colunas nunca por posição" | **falso para a herança de mercadorias**, que lê as colunas 1 a 5 por posição |
| As 16 "principais" + 11 "complementares" do XML têm exigência diferente? | **não** — as 27 são igualmente obrigatórias |
