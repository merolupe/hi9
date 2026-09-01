# Apurabot — roteiro de teste

Para quem vai testar a ferramenta na máquina antes de usá-la em produção.

São nove testes, na ordem. Cada um diz **o que fazer**, **o que tem que
acontecer** e **o que anotar se não acontecer**. Leva uns quinze minutos.

Não é preciso saber programar. O único passo com terminal é o preparo, e é uma
vez só.

---

## Antes de começar

**O que ter em mãos:**

| | |
|---|---|
| Um Livro Fiscal | extração **Movimento Livros Fiscais** do Sankhya, de uma competência fechada |
| Python 3.10 ou mais novo | confira com `python verificar.py`; a instalação "somente para este usuário" não exige administrador |
| A pasta do repositório | <https://github.com/merolupe/hi9> → **Code** → **Download ZIP** → extrair |

**Onde anotar:** abra um documento em branco. A cada teste que falhar, copie a
mensagem inteira, tire um print e anote em qual teste foi. Mensagem resumida de
memória não ajuda a achar o defeito.

---

## Preparo

Nenhum. Não há instalação.

As bibliotecas viajam junto com o código, então baixar a pasta basta. Se quiser
conferir antes que o Python da máquina serve, abra a pasta no Explorador, clique
na barra de endereço, digite `cmd` e Enter, e rode:

```
python verificar.py
```

**Tem que acontecer:** responde `OK` e o caminho do Python.

**Se responder que não serve:** a mensagem diz o motivo — Python antigo demais,
ou pasta baixada incompleta. É o único preparo possível, e ele é opcional.

---

## Teste 1 — a janela abre

**Faça:** dois cliques em **`Apurabot.bat`**, na raiz da pasta.

**Tem que acontecer:**

1. abre uma janela preta com um endereço `http://127.0.0.1:…`;
2. o navegador abre sozinho, em poucos segundos, numa página com o título
   **Apurabot** e uma área tracejada escrita *"Arraste aqui o Livro Fiscal"*.

**Se a janela preta abrir e fechar na hora:** o Python não foi encontrado, ou a
pasta veio incompleta. Abra o `cmd` na pasta e rode `python verificar.py` para
ler o motivo.

**Se o navegador não abrir sozinho:** copie o endereço da janela preta e cole no
navegador. Anote — não é bloqueante, mas é defeito.

> A janela preta é o Apurabot rodando. Ela precisa continuar aberta.

---

## Teste 2 — arrastar o arquivo

**Faça:** arraste o Livro Fiscal do Explorador para dentro da área tracejada.
(Ou clique nela e escolha o arquivo.)

**Tem que acontecer:** a área some, aparece um círculo girando e a palavra
*"Apurando…"*. Em até um minuto, o resultado.

**O ponto deste teste:** o arquivo pode estar em **qualquer pasta**, com
**qualquer nome**. Teste de propósito com o arquivo na sua área de trabalho, ou
em Downloads. Se a ferramenta exigir pasta ou nome específico, é defeito.

---

## Teste 3 — a faixa de situação

**Tem que acontecer:** no topo do resultado, uma faixa verde
**"Encerramento liberado — nenhuma pendência"** ou uma faixa vermelha
**"Encerramento bloqueado"** com a lista do que resolver.

As duas são resultado correto. A vermelha não é erro da ferramenta: é ela
cobrando o que não casou com regra. O que **não** pode acontecer é a tela ficar
em branco, ou o número aparecer sem a faixa.

---

## Teste 4 — os números da apuração

Na tabela **Apuração por estabelecimento**, confira contra o que você já
conhece da competência.

Se estiver testando com **Julho/2026**, estes são os alvos — todos conferidos
contra a apuração manual e a GIA entregue:

| Estabelecimento | Crédito bruto | Estorno | Débito |
|---|---|---|---|
| Registro (SP) | 286.030,83 | 50.481,97 | 522.662,52 |
| Guará (SP) | 4.167.368,77 | 426.771,68 | 1.633.053,78 |
| Barra do Garças (MT) | 50.309,07 | 50.309,07 | 0,00 |
| Londrina (PR) | 13.882,40 | 0,00 | 0,00 |
| Corumbá (MS) | 46.464,79 | 34.385,57 | 111.491,32 |
| Rio Brilhante (MS) | 469.903,05 | 331.236,11 | 505.991,41 |

**Tem que acontecer:** batem ao centavo.

**Se algum não bater:** anote **qual estabelecimento, qual coluna, o valor que
apareceu e o valor que você esperava**. É a informação que resolve o problema.

> O estorno de Corumbá aparece como 34.385,57 porque a tela soma o estorno
> (19.961,55) ao crédito indevido de transferência (14.424,02) — os dois saem
> da conta gráfica, e no Registro de Apuração moram na mesma linha.

---

## Teste 5 — o Registro de Apuração

**Faça:** na seção **Registro de Apuração**, clique no nome de um
estabelecimento para abrir.

**Tem que acontecer:** aparecem as entradas e as saídas separadas por
procedência (do Estado / de outros Estados / do Exterior) e o resumo em catorze
linhas, de `001` a `014`.

**Confira contra o PDF que o Sankhya emite** para o mesmo estabelecimento e a
mesma competência. Em Julho/2026, Rio Brilhante fecha assim:

| | Entradas | Saídas |
|---|---|---|
| Valores contábeis | 24.480.484,19 | 20.260.112,91 |
| Base de cálculo | 3.325.593,93 | 3.968.178,21 |
| Imposto | 469.903,05 | 505.991,41 |
| Isentas / N. Trib. | 12.337.052,49 | 13.235.819,33 |
| Outras | 8.861.582,25 | 3.056.115,37 |

**Duas coisas que você vai ver e são esperadas:**

**As etiquetas `aguarda ajuste`** nas linhas 003, 006, 007 e 009. Esses
lançamentos não nascem de documento no Livro Fiscal — são decisões da apuração,
aprovadas por vocês. A ferramenta ainda não os lê de arquivo, então os deixa
zerados e marcados em vez de inventar um total. É a Entrega 2.

**A linha 012 pode divergir do PDF** se o PDF for anterior a uma retificação.
Em Julho/2026 é o caso: o Registro emitido em 07/08 traz a inversão entre
Industrial e Comercial que a GIA retificadora de 25/08 corrigiu, e a ferramenta
reproduz a versão correta.

---

## Teste 6 — o totalizador

**Faça:** vá até o fim da seção Registro de Apuração.

**Tem que acontecer:** um bloco **TOTALIZADOR — todos os estabelecimentos**, já
aberto, somando as sete filiais.

É o que o PDF do Sankhya, emitido filial a filial, não entrega. Repare no aviso:
as linhas 011 a 014 são a **soma do resultado de cada filial**, não o recálculo
sobre os totais — crédito de uma UF não abate débito de outra.

---

## Teste 7 — as transferências

**Tem que acontecer:** a seção **Transferências a emitir depois do
encerramento** lista, por UF, o que precisa ser transferido para a
centralizadora.

Em Julho/2026:

```
SP — centraliza em HINOVE (FILIAL GUARÁ)          [regra não homologada]
  HINOVE (REGISTRO) → HINOVE (FILIAL GUARÁ):
  transferir saldo devedor de 287.113,66
  por NF-e de transferência de saldo, CFOP 5601 ou 5602 ou 5605

MS — centraliza em HINOVE (RIO BRILHANTE)
  HINOVE (CORUMBÁ- MS) → HINOVE (RIO BRILHANTE):
  transferir saldo devedor de 99.412,10
  por lançamento de ajuste no Registro de Apuração
```

**O que conferir:** a etiqueta *"regra não homologada"* em SP tem que aparecer.
Ela existe porque falta a Gerência Fiscal confirmar **o que** se transfere e por
**qual CFOP**. Enquanto não confirmar, o resultado de SP é rascunho.

**O que a ferramenta deliberadamente não faz:** cobrar a nota dentro da
competência apurada. A nota nasce do resultado da apuração — só pode ser emitida
depois do encerramento, e vai escriturada no mês seguinte. Se aparecer alguma
pendência de "NF-e não escriturada", é defeito.

---

## Teste 8 — baixar e abrir a planilha

**Faça:** clique em **Baixar a planilha**. Abra o arquivo no Excel.

**Tem que acontecer:** um `.xlsx` chamado `Apuracao_AAAA-MM.xlsx`, com oito
abas nesta ordem:

| Aba | Confira |
|---|---|
| **RESUMO** | competência, arquivo e o SHA-256 do que foi lido |
| **REGISTRO** | o mesmo da tela, com o detalhe por CFOP que a tela resume |
| **APURAÇÃO EFETIVA** | a coluna **CHECK** — tem que ser **zero em todas as linhas** |
| **APURAÇÃO POR FILIAL** | a memória do benefício, passo a passo |
| **TRANSFERÊNCIAS** | o mesmo da tela, em tabela |
| **PENDÊNCIAS** | vazia, se a faixa estava verde |
| **POR ESTABELECIMENTO E CARGA** | o recorte por carga efetiva |
| **BASE TRATADA** | uma linha por linha do Livro, com a regra aplicada em texto |

**O teste mais importante da planilha:** na aba `APURAÇÃO EFETIVA`, use o filtro
na coluna **CHECK** e procure qualquer valor diferente de zero. Não pode haver
nenhum — o CHECK é `ICMS a estornar + ICMS a apropriar − ICMS creditado`, e
valor diferente de zero é erro de motor, não de escrituração. Se achar, anote a
linha inteira.

**Compare com a sua planilha manual.** A `APURAÇÃO EFETIVA` foi montada no
formato que vocês usam — **uma linha por produto, não por documento**, como a
tabela dinâmica. Em Julho/2026, Rio Brilhante sai com os mesmos onze produtos da
planilha manual e o mesmo Total Geral: 9.341.752,63 de contábil, 3.325.593,93 de
BC, 469.903,05 de ICMS, 331.236,11 de estorno e 138.666,94 a apropriar.

**Repare que a terceira coluna muda de nome** entre os blocos: **Alíquota** nos
de MS, **Carga efetiva** nos de SP. Não é inconsistência — é a chave da regra de
cada regime, e agrupar pela grandeza errada esconderia o que se quer conferir.

---

## Teste 9 — o que tem que dar errado

Testar o caminho feliz não basta. Faça de propósito:

| Faça | Tem que acontecer |
|---|---|
| Arraste um **PDF** ou um **Word** para a área tracejada | mensagem dizendo que não é planilha, e um botão para escolher outro arquivo — **não** pode travar nem sumir |
| Arraste uma **planilha qualquer**, que não seja Livro Fiscal | mensagem explicando que faltam colunas, dizendo **quais** |
| Clique em **Apurar outro livro** e mande o mesmo arquivo de novo | funciona, e o resultado é idêntico |
| Feche a **janela preta** e volte à página do navegador | ao tentar apurar, a página avisa que perdeu contato |

---

## Encerrar

Clique em **Encerrar**, no rodapé da página, ou feche a janela preta.

**Tem que acontecer:** a página confirma o encerramento. A pasta temporária que
guardava o arquivo enviado é apagada — nada do Livro Fiscal fica na máquina.

---

## O que reportar

Para cada teste que falhou:

1. **qual teste** (o número);
2. **a mensagem inteira**, copiada, não resumida;
3. **um print** da tela;
4. se for número errado: **qual estabelecimento, qual coluna, o valor que
   apareceu e o valor esperado**.

E uma coisa que vale mais que qualquer defeito: **onde a ferramenta te fez
parar para pensar.** Um rótulo ambíguo, uma coluna que você precisou conferir
duas vezes, uma seção que você não entendeu para que servia. Isso não aparece em
teste automático e é o que decide se o time vai usar a ferramenta ou voltar para
o Excel.

---

## O que ainda não está pronto

Para não reportar como defeito:

| | |
|---|---|
| **Leitura de `ajustes.xlsx`** | as linhas marcadas `aguarda ajuste` dependem disto — é a Entrega 2 |
| **Encerramento de competência** | o saldo credor ainda não é transportado para o mês seguinte |
| **DIFAL** e **CIAP** | pausados por decisão de escopo |
| **Regra de transferência de SP** | calculada, não homologada — a tela avisa |
| **Local de expedição** | o cruzamento com o relatório de expedição não está implementado (decisão pendente nº 12) |
