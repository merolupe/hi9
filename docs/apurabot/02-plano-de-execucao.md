# Apurabot — Plano de execução

> Entregas incrementais. Cada uma termina com algo que o time fiscal consegue
> abrir, conferir e opinar — nunca com "está quase pronto".

**Situação:** a competência de referência é reproduzida da ingestão ao benefício
fiscal, **fecha sem nenhuma pendência**, e a apuração de Rio Brilhante bate ao
centavo com a GIA entregue. 96 testes automáticos.

| Entrega | Situação |
|---|---|
| 0 · Mapeamento técnico | ✅ concluída |
| 1 · Base tratada e classificada | ✅ concluída |
| 2 · Motor de ICMS: créditos, débitos e estornos | 🟡 falta só ajustes manuais |
| 3 · Benefício fiscal de Rio Brilhante | ✅ concluída — confere com a GIA |
| 4 · Centralização de São Paulo | ⬜ pode começar |
| 5 · DIFAL | ⬜ falta o `.xlsx` de XML |
| 6 · Interface e empacotamento | ⬜ pode começar |
| 7 · Homologação | ⬜ depende de 4 e 6 |
| 8 · CIAP | ⬜ falta a Base de Bens |

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

## Entrega 4 — Centralização de São Paulo ⬜

Não depende de nada em aberto.

- Saldo individual antes da centralização, por estabelecimento paulista
- Classificação credor/devedor e valor transferível
- Controle das NF-e de transferência (8 validações do escopo, item 7.1)
- Consolidação em Guará e resultado da centralizadora
- Travas: `saldo individual = transferido + residual` e
  `recebido em Guará = soma das NF-e emitidas`

---

## Entrega 5 — DIFAL ⬜

Falta o `.xlsx` de exemplo do XML das entradas. O extrato novo já traz
`Vlr. DIFAL UF Remet.` e `Vlr. DIFAL UF Destino`, que ajudam na conciliação.

- Cruzamento Livro Fiscal × XML pela chave da NF-e
- Recálculo com o ICMS do XML nas compras fora do processo produtivo
- Valor sem arredondamento, arredondado por documento e total consolidado
- SP em conta gráfica · MS em guia avulsa
- **Painel 2** — auditoria das alterações no Livro para o DIFAL

---

## Entrega 6 — Interface e empacotamento ⬜

Janela local com os 4 comandos, seleção de competência, arrastar-e-soltar,
painel de pendências com bloqueio do encerramento, empacotamento para duplo
clique e manual do usuário.

---

## Entrega 7 — Homologação ⬜

Regressão de uma segunda competência, treinamento do time e aceite formal.

---

## Entrega 8 — CIAP ⬜

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
Entrega 1 ✅ ──► Entrega 2 🟡 ──► Entrega 4 ⬜ ──► Entrega 6 ⬜ ──► Entrega 7 ⬜
                     │
                     ├──►  Entrega 3 ✅  concluída, confere com a GIA
                     ├──►  Entrega 5 ⬜   precisa: .xlsx de exemplo do XML
                     └──►  Entrega 8 ⬜   precisa: .xlsx da Base de Bens
```

As entregas **4 e 6 podem começar imediatamente**, e fechar a 2 depende só de
definir o formato do `ajustes.xlsx`. Nenhuma delas espera resposta do fiscal.
