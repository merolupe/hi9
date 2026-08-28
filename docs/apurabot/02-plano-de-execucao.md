# Apurabot — Plano de execução

> Entregas incrementais. Cada uma termina com algo que o time fiscal consegue
> abrir, conferir e opinar — nunca com "está quase pronto".

**Situação:** a competência de referência é reproduzida da ingestão ao benefício
fiscal, **fecha sem nenhuma pendência**, e a apuração de Rio Brilhante bate ao
centavo com a GIA entregue e com o Registro de Apuração emitido pelo ERP. 168
testes automáticos.

| Entrega | Situação |
|---|---|
| 0 · Mapeamento técnico | ✅ concluída |
| 1 · Base tratada e classificada | ✅ concluída |
| 2 · Motor de ICMS: créditos, débitos e estornos | 🟡 falta só ajustes manuais |
| 3 · Benefício fiscal de Rio Brilhante | ✅ concluída — confere com a GIA |
| 4 · Centralização e transferência de saldo | ✅ concluída — regra de SP a homologar |
| 5 · DIFAL | ⏸ pausado |
| 6 · Interface e empacotamento | 🟡 janela no navegador e CLI entregues; falta o encerramento de competência |
| 7 · Homologação | ⬜ depende de 4 e 6 |
| 8 · CIAP | ⏸ pausado |
| 9 · Registro de Apuração e conferência | ✅ concluída |

---

## Princípio

**Toda entrega é medida por quanto de uma apuração real ela reproduz.** Onde há
diferença, ela é exigida com valor exato no teste — nunca tolerada em silêncio.

A conferência é feita contra a **apuração individualizada por estabelecimento**
sempre que ela existir; a consolidada serve de referência de totais, não de fonte
da verdade. Onde houver declaração retificadora, é ela que vale.

A competência de referência e os números que cada entrega reproduz estão em
[05 — Achados de Julho/2026](05-achados-julho-2026.md). Aqui fica o que cada
entrega faz e em que pé ela está.

---

## Entrega 0 — Mapeamento técnico ✅

Arquitetura, dicionário de dados, matriz de regras, achados da competência de
referência e o registro de decisões. Tudo em `docs/apurabot/`.

**Resultado principal:** a equalização de carga efetiva é feita por algoritmo,
com cada divergência contra a classificação manual exigida por teste.

---

## Entrega 1 — Base tratada e classificada ✅

Camadas 1 a 4: ingestão, normalização, equalização de carga e classificação.

O que a entrega garante, verificado por teste de regressão:

- a contagem de linhas relevantes para ICMS bate com a da planilha manual;
- os totais por estabelecimento × entrada/saída × carga são idênticos aos da
  tabela dinâmica da apuração;
- a carga efetiva reproduz a classificação manual, e **cada divergência é exigida
  com valor exato** — o teste quebra se aparecer outra;
- pendência de classificação bloqueia o encerramento da competência.

**Dois layouts suportados.** O extrato `Movimento Livros Fiscais`, que é o padrão,
e a extração antiga da apuração. Um teste prova que os dois produzem apuração
idêntica.

---

## Entrega 2 — Motor de ICMS 🟡

Camadas 5 a 8, por regime. **Falta só** ler os ajustes aprovados de
`ajustes.xlsx`.

### O que são esses ajustes

São os lançamentos do Registro de Apuração que **não nascem de documento no
Livro Fiscal**. Não é possível deduzi-los do movimento: são decisões da
apuração, tomadas e aprovadas pelo time fiscal.

| Linha do registro | O que costuma entrar |
|---|---|
| 002 Outros Débitos | débito que não veio de saída escriturada |
| 003 Estornos de Créditos | estorno decidido na apuração, além do que a regra calcula sobre o Livro |
| 006 Outros Créditos | crédito autorizado por dispositivo do RICMS, sem documento de entrada |
| 007 Estornos de Débitos | débito escriturado que a apuração devolve |
| 009 Saldo Credor do Período Anterior | o crédito transportado do mês anterior |

O motor já sabe o lugar de cada um: enquanto não vierem, o `REGISTRO` sai com
essas linhas zeradas e marcadas **AGUARDA AJUSTE**. Ele não inventa o número e
não esconde a falta.

Uma exceção que já saiu da lista: onde a UF centraliza por lançamento — MS —, o
recebimento de saldo devedor da linha 002 é **calculado** pela camada 9 a partir
do saldo do estabelecimento centralizado. Não é ajuste declarado.

### Como isso entra no fechamento do mês

```
1. exportar o Livro Fiscal do Sankhya
2. rodar a ferramenta                     → REGISTRO com AGUARDA AJUSTE
3. preencher ajustes.xlsx com o que foi aprovado
4. rodar de novo, com --ajustes           → REGISTRO fechado, linha 013 final
5. esse número vai para a GIA e para o EFD
```

O passo 3 é o único trabalho humano, e ele é pequeno: são poucos lançamentos por
competência. O que a ferramenta acrescenta é que **nenhum deles passa
despercebido** — sem a declaração, o registro não fecha.

Cada linha de `ajustes.xlsx` traz estabelecimento, atividade, linha do registro,
valor, descrição, responsável e aprovador — a exigência de rastreabilidade do
escopo, e o que a decisão nº 4 disciplina.

O estorno é conferido estabelecimento a estabelecimento contra a apuração
individualizada, **com valor exato em todos os sete**. Onde existe apuração
individualizada, é ela que vale — a consolidada foi montada no molde do
equilíbrio fiscal de SP e não reflete a mecânica das outras UFs.

Os números da conferência estão em
[05 — Achados de Julho/2026](05-achados-julho-2026.md).

---

## Entrega 3 — Benefício fiscal de Rio Brilhante ✅

Crédito presumido do Termo de Acordo n. 1.190/2018 sobre o saldo devedor da
atividade industrial, e a contribuição ao FADEFE que condiciona a fruição.

O que a entrega cobre:

- **segregação por atividade** — Industrial, Comercial, Importados e
  Prestacional/Outras, exigida pela GIA de MS e sem a qual não existe crédito da
  parcela incentivada;
- **cadeia do benefício** — do crédito industrial à base do incentivo, com o
  rateio intra/inter pela participação do débito, conferida ao centavo contra a
  GIA;
- **ajustes que não vêm do Livro Fiscal**, por `AjustesDaApuracao`;
- **FADEFE** como saída informativa, em guia avulsa, fora da conta gráfica.

A regra está em [04 — Matriz de regras](04-matriz-de-regras-icms.md), item 4.5.

**Travas:** o benefício nunca supera o saldo devedor que o gerou; atividade
indefinida bloqueia o encerramento; aplicar a cláusula quarta, expirada, levanta
erro com a data na mensagem. A memória de cálculo vai na aba
`APURAÇÃO POR FILIAL`, passo a passo.

**Depende de resposta do fiscal:** a segregação de Corumbá não tem GIA que a
confirme (decisão nº 6) e a centralização de MS não está modelada (nº 7).

---

## Entrega 4 — Centralização e transferência de saldo ✅

Camada 9. Consolida os saldos individuais no estabelecimento centralizador e
**emite a instrução** do que precisa ser transferido.

O que a entrega cobre:

- **saldo individual** de cada estabelecimento, antes da centralização;
- **valor transferível** conforme a regra da UF — saldo integral, só devedor ou
  só credor, parametrizado;
- **mecanismo por UF** — NF-e em SP, ajuste de apuração em MS;
- **consolidação** na centralizadora, com o saldo final do grupo;
- **instrução de transferência**, na aba `TRANSFERÊNCIAS`: origem, destino,
  valor, mecanismo e CFOP sugerido.

A transferência não é cobrada dentro da competência apurada, e isso é
deliberado: o documento nasce do resultado da apuração e só pode ser emitido
depois do encerramento. Cobrá-lo no livro que está sendo apurado seria pedir
que o efeito precedesse a causa. A conferência do documento é da competência
seguinte — ver item 6.6 da matriz de regras.

A regra está em [04 — Matriz de regras](04-matriz-de-regras-icms.md), item 6.

**Depende de resposta do fiscal:** a regra de transferência de SP não está
homologada (decisão nº 11), e o caso do saldo credor em MS segue em aberto
(nº 7).

---

## Entrega 5 — DIFAL ⏸ *(pausado)*

Falta o `.xlsx` de exemplo do XML das entradas. O extrato novo já traz
`Vlr. DIFAL UF Remet.` e `Vlr. DIFAL UF Destino`, que ajudam na conciliação.

- Cruzamento Livro Fiscal × XML pela chave da NF-e
- Recálculo com o ICMS do XML nas compras fora do processo produtivo
- Valor sem arredondamento, arredondado por documento e total consolidado
- SP em conta gráfica · MS em guia avulsa
- **Painel 2** — auditoria das alterações no Livro para o DIFAL

---

## Entrega 6 — Interface e empacotamento 🟡

**Entregue:** a janela do navegador e a linha de comando.

Dois cliques em `Apurabot.bat` abrem a ferramenta no navegador: arrasta-se o
Livro Fiscal, vê-se o resultado na tela — apuração por estabelecimento, Registro
de Apuração, transferências a emitir, memória do benefício e pendências — e
baixa-se a planilha. Sem caminho para digitar, sem pasta com nome fixo.

### Por que o navegador, e não um executável

A máquina do time fiscal é corporativa e **sem elevação de administrador**. O
executável que o `pip` cria é barrado pela política de segurança — o sintoma é
*"Acesso negado"*. Um `.exe` empacotado teria o mesmo destino: é binário novo e
sem assinatura.

O navegador e o Python, ao contrário, já são programas aprovados. Então a
interface passa a ser a página, e o Python sobe um servidor em `127.0.0.1` numa
porta que o sistema escolhe. `Apurabot.bat` é arquivo de texto: o duplo clique
não cria nada na máquina.

| | |
|---|---|
| **nada é instalado** | nenhum binário novo, nenhum privilégio pedido |
| **o dado não sai da máquina** | conexão só de `127.0.0.1`; o arquivo enviado vive em pasta temporária e é apagado no encerramento |
| **a página não busca nada fora** | zero CDN, zero fonte externa — funciona desconectado, e há teste que verifica |
| **outra sessão não alcança** | cada janela nasce com uma chave aleatória na URL |

**Uma solução hospedada foi descartada:** Livro Fiscal, XML e base de bens são
dado fiscal real, e subi-los para fora da máquina contraria a primeira regra do
repositório.

A linha de comando continua inteira, para automatizar. O passo a passo está em
[07 — Como rodar](07-como-rodar.md).

**Falta:** o encerramento de competência, que grava o saldo credor para o mês
seguinte.

---

## Entrega 7 — Homologação ⬜

Regressão de uma segunda competência, treinamento do time e aceite formal.

---

## Entrega 8 — CIAP ⏸ *(pausado)*

Falta a Base de Bens. Índice = saídas tributadas ÷ total de saídas; crédito
apropriável = parcela mensal × índice. **Painel 3.**

---

## Fora desta fase

PIS/Cofins (Fase 2 do escopo), geração de EFD, transmissão de obrigações,
geração de guias, integração por API com o Sankhya, lançamento automático no ERP,
PER/DCOMP e emissão automática de NF-e de transferência.

---

## O que destrava o quê

```

---

## Entrega 9 — Registro de Apuração e conferência ✅

Camada 11. Três relatórios que respondem a perguntas diferentes sobre o mesmo
mês, no mesmo arquivo.

**`REGISTRO`** — espelho do Registro de Apuração do ICMS: entradas e saídas por
CFOP com os cinco valores fiscais, subtotais por procedência e destino, e o
resumo em quatorze linhas. Um bloco por estabelecimento e um **totalizador do
grupo** — que é justamente o que o PDF do ERP, emitido filial a filial, não
mostra.

O bloco de entradas e saídas é soma pura do Livro Fiscal, e é conferido contra
o registro emitido pelo ERP **ao centavo, nas cinco colunas e nos três grupos de
procedência**. O resumo é apuração, e traz marcado o que depende de ajuste.

**`APURAÇÃO EFETIVA`** — a conferência que o time fiscal montava à mão: CFOP →
alíquota → produto, com a operação, a alíquota de entrada, a parcela não
tributada, o ICMS a estornar, o ICMS a apropriar e a coluna **CHECK**. O CHECK é
`a estornar + a apropriar − ICMS creditado`, e o teste exige que feche em todas
as linhas de todos os estabelecimentos.

**`TRANSFERÊNCIAS`** — o que emitir depois de fechar a competência.

**Trava entre os dois primeiros:** o imposto creditado somado por CFOP no
registro tem que ser o crédito bruto da apuração. Se divergir, um dos dois leu o
Livro errado.

Entrega 1 ✅ ──► Entrega 2 🟡 ──► Entrega 4 ✅ ──► Entrega 6 🟡 ──► Entrega 7 ⬜
                     │
                     ├──►  Entrega 3 ✅  benefício fiscal de MS
                     ├──►  Entrega 5 ⏸  DIFAL — pausado
                     └──►  Entrega 8 ⏸  CIAP — pausado
```

A ferramenta já roda de ponta a ponta na máquina do time — ver
[07 — Como rodar](07-como-rodar.md). O que falta para a Fase 1 fechar é a
interface gráfica (Entrega 6) e a leitura do relatório de ajustes (Entrega 2).
DIFAL e CIAP estão pausados por decisão de escopo.