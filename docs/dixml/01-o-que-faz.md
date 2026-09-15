# DiXML — lote de XML de nota em planilha

> Público: time Fiscal/Tributário. Antecessor: o script `robozinho` v2.2, que
> rodava por popup e pandas.

---

## 1. Para que serve

Transformar um lote de XML de nota em planilha, para conferir **qualquer**
informação que esteja no arquivo da nota — sem depender do que um relatório do
sistema decidiu mostrar.

Entra: um ou mais `.zip`. Sai: um `.xlsx` com duas abas.

| Aba | O que tem | Uma linha é |
|---|---|---|
| `NFe` | Nota fiscal eletrônica | **um item** da nota |
| `CTe` | Conhecimento de transporte | **um documento** |

## 2. As decisões que a leitura toma

### Uma linha por item, não por nota

A conferência fiscal é por item: CFOP, NCM, CST e alíquota mudam dentro da
mesma nota. O que é da nota — chave, emitente, totais — se repete em todas as
linhas dela, para a planilha poder ser filtrada por qualquer coluna sem perder
o contexto.

Por isso o resumo mostra dois números diferentes: **notas** (chaves distintas) e
**linhas de item**.

### Código é texto; valor é número

Chave de acesso tem 44 dígitos, CNPJ tem 14. Em coluna numérica o Excel os
exibe como `3,52604E+43`, perde os zeros à esquerda e faz o PROCV falhar contra
qualquer outra base. Então chave, CNPJ/CPF, número da nota, série, NCM, CFOP e
CST ficam **texto**, de propósito — e a coluna vai marcada com formato `@`,
que é a defesa para quando alguém editar a planilha depois.

Valor, quantidade e alíquota vão como **número**, prontos para somar.

### Data vira data, e a hora vai para o lado

O XML traz `2026-06-01T10:30:00-03:00`. Como texto, o Excel não filtra por
período, não ordena e não agrupa por mês. Vira duas colunas:

- `Emissao Data` — data de verdade, exibida como `dd/mm/aaaa`
- `Emissao Hora` — texto `hh:mm:ss`

A detecção é por conteúdo, não por nome: **qualquer** coluna cujos valores
sejam data ISO é convertida. Vale para `dhEmi`, `dhSaiEnt`, `dhRecbto` e para o
que a SEFAZ criar depois, sem manutenção de lista. O fuso não é convertido: a
data é a que está escrita no documento.

### O que não é nota não é erro

O lote da SEFAZ vem cheio de eventos, cartas de correção, cancelamentos e
inutilizações. Eles não entram na planilha, mas são **contados e listados** na
tela: quem confere precisa saber que estavam ali.

XML quebrado, `.zip` corrompido e `.zip` que não abre também não derrubam a
execução — ficam registrados e a leitura continua. Num lote de milhares de
notas, parar tudo por causa de um arquivo ilegível é pior do que seguir e avisar.

### O caminho dentro dos pacotes fica registrado

A coluna `Arquivo` guarda o caminho inteiro:
`XMLs_junho.zip::filial_02.zip::nota.xml`. É por ele que se acha a origem de
uma linha meses depois. `.zip` dentro de `.zip` é lido sozinho, em qualquer
profundidade até 8 níveis — o lote da contabilidade costuma vir aninhado por
filial.

## 3. Reforma Tributária

Os grupos IBS/CBS e Imposto Seletivo são lidos por **achatamento dinâmico**:
qualquer tag que a SEFAZ acrescentar ao XML vira coluna sozinha, sem alteração
de código.

Além disso há uma lista de **colunas-semente** (`dixml/src/dixml/nfe.py`):
colunas que aparecem na planilha **mesmo quando nenhuma nota do lote traz o
grupo**. É o que deixa a planilha comparável de um mês para o outro e o que
permite montar tabela dinâmica sem ela quebrar quando o campo começar a ser
preenchido.

Base das sementes: **NT 2025.002-RTC** (grupos UB / UT / totais W), conferida
em julho de 2026 — inclui `gDif`, `gDevTrib`, `gRed`, `gTribRegular`,
`gIBSCredPres`, `gCBSCredPres`, o grupo `IS`, `gCompraGov`, `vItem`, `ISTot` e
`vNFTot`.

Grupos raros — `gIBSCBSMono` (combustíveis), `gTransfCred`, `gCredPresIBSZFM`,
`gEstornoCred` — não são semeados, mas são capturados se aparecerem.

> **Ao mudar a lista de sementes:** ela é a única parte deste código que
> acompanha legislação. Uma NT nova acrescenta linhas às listas em `nfe.py` e
> uma linha nesta seção, com a NT e a data da conferência.

## 4. O que mudou do `robozinho` v2.2

A leitura é a mesma, coluna por coluna. Duas coisas saíram, e as duas por
causa da máquina onde a ferramenta roda:

| Saiu | Por quê | Entrou no lugar |
|---|---|---|
| **pandas** | Tem extensão compilada em C. Não pode viajar embarcado em `vendor/`, e sem ele instalado a ferramenta não abre na máquina do time fiscal | A planilha é escrita direto com `openpyxl` |
| **tkinter** (popup de seleção) | A interface passou a ser o navegador, na Central | Arrastar o arquivo na janela |

E uma coisa entrou, porque a ferramenta passou a receber arquivo pela janela:
teto de expansão dos `.zip` (2 GB descompactados, 8 níveis de aninhamento). Um
lote mensal fica muito abaixo disso.

## 5. Como se usa

**Dois cliques em `Hinove.bat`** → botão **DiXML** → arraste os `.zip` → baixe
a planilha.

Pelo terminal, quando for automatizar:

```
python rodar.py dixml "caminho\do\lote.zip" --saida "pasta\de\saida"
python rodar.py dixml lote_01.zip lote_02.zip --saida .
```

Vários `.zip` de uma vez vão para a **mesma** planilha, que é como a
conferência mensal é feita.

## 6. Onde fica cada coisa

```
dixml/src/dixml/
  campos.py      como um pedaço de XML vira coluna (namespace, texto × número)
  pacote.py      de um .zip até cada XML, inclusive .zip aninhado
  nfe.py         a NF-e e as colunas-semente da Reforma
  cte.py         o CT-e, achatado inteiro
  datas.py       data e hora em colunas separadas
  planilha.py    a escrita do .xlsx e a formatação
  extracao.py    a leitura de ponta a ponta
  cli.py         linha de comando
```
