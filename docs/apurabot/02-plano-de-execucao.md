# Apurabot — Plano de execução

> Entregas incrementais. Cada uma termina com algo que o time fiscal consegue
> abrir, conferir e opinar — nunca com "está quase pronto".

**Situação:** a competência de referência é reproduzida da ingestão ao benefício
fiscal, **fecha sem nenhuma pendência**, e a apuração de Rio Brilhante bate ao
centavo com a GIA entregue. 111 testes automáticos.

| Entrega | Situação |
|---|---|
| 0 · Mapeamento técnico | ✅ concluída |
| 1 · Base tratada e classificada | ✅ concluída |
| 2 · Motor de ICMS: créditos, débitos e estornos | 🟡 falta só ajustes manuais |
| 3 · Benefício fiscal de Rio Brilhante | ✅ concluída — confere com a GIA |
| 4 · Centralização e transferência de saldo | ✅ concluída — regra a homologar |
| 5 · DIFAL | ⏸ pausado |
| 6 · Interface e empacotamento | 🟡 CLI e instalação entregues; interface gráfica pendente |
| 7 · Homologação | ⬜ depende de 4 e 6 |
| 8 · CIAP | ⏸ pausado |

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

Camadas 5 a 8, por regime. **Falta só** ler os ajustes manuais aprovados de
`ajustes.xlsx`.

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
cobra a NF-e que documenta cada transferência.

O que a entrega cobre:

- **saldo individual** de cada estabelecimento, antes da centralização;
- **valor transferível** conforme a regra da UF — saldo integral, só devedor ou
  só credor, parametrizado;
- **consolidação** na centralizadora, com o saldo final do grupo;
- **travas da NF-e** — saldo a transferir sem documento escriturado, ou
  documento de valor diferente do saldo, viram pendência e bloqueiam o
  encerramento.

A regra está em [04 — Matriz de regras](04-matriz-de-regras-icms.md), item 6.

**Depende de resposta do fiscal:** a regra de transferência de SP não está
homologada (decisão nº 11), e a de MS não está modelada (nº 7).

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

**Entregue:** instalação com um comando e a linha de comando completa.

```
pip install -e apurabot
apurabot apurar <livro_fiscal> --saida <pasta>
```

A execução mostra a apuração por estabelecimento, a segregação por atividade, a
memória do benefício, a centralização e as pendências — e grava o caderno em
`.xlsx`. O passo a passo está em [07 — Como rodar](07-como-rodar.md).

**Falta:** a janela para quem não usa terminal, e o encerramento de competência
que grava o saldo credor para o mês seguinte.

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
