# Apurabot — Plano de execução

> Entregas incrementais. Cada uma termina com algo que o time fiscal consegue
> abrir, conferir e opinar — nunca com "está quase pronto".

**Situação em 25/08/2026:** Julho/2026 é reproduzido da ingestão ao benefício
fiscal, **fecha sem nenhuma pendência**, e Rio Brilhante bate ao centavo com a
GIA retificadora de 07/2026. 96 testes automáticos.

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

**Fechar Julho/2026 pela ferramenta e comparar com o que foi feito à mão.** Toda
entrega é medida por quanto do resultado real ela reproduz. Onde há diferença,
ela é exigida com valor exato no teste — nunca tolerada em silêncio.

---

## Entrega 0 — Mapeamento técnico ✅

Arquitetura, dicionário de dados, matriz de regras, achados de Julho/2026 e o
registro de decisões pendentes. Tudo em `docs/apurabot/`.

**Resultado principal:** a equalização de carga efetiva, maior risco técnico do
projeto, resolvida com **99,87%** de aderência ao trabalho manual.

---

## Entrega 1 — Base tratada e classificada ✅

Camadas 1 a 4: ingestão, normalização, equalização de carga e classificação.

| Verificação | Resultado |
|---|---|
| Linhas lidas do Livro Fiscal | 6.504 |
| Linhas relevantes para ICMS | **2.345** — igual à aba `ICMS` da planilha manual |
| Carga efetiva × classificação manual | **2.342 de 2.345 (99,87%)** |
| Totais por estabelecimento × entrada/saída × carga | idênticos à aba `Dinamica` |
| Pendências | **0** |
| Alertas (não bloqueiam) | 36 |

As 3 divergências de carga são as notas da ICL Aditivos, reclassificadas à mão
para aplicar a regra de MS. O teste **exige** que a diferença seja essa e de
R$ 9.019,01 — qualquer outra o quebra.

**Dois layouts suportados.** O extrato `Movimento Livros Fiscais`, padrão a partir
de 08/2026, e a extração antiga da apuração. Um teste prova que os dois produzem
apuração idêntica.

---

## Entrega 2 — Motor de ICMS 🟡

Camadas 5 a 8, por regime. **Falta só** ler os ajustes manuais aprovados de
`ajustes.xlsx`.

| Estabelecimento | UF | Estorno calculado | Referência | Diferença |
|---|---|---|---|---|
| Registro | SP | 50.481,97 | 50.481,97 | **0,00** |
| Guará | SP | 426.771,68 | 426.771,68 | **0,00** |
| Matriz | SP | 0,00 | 0,00 | **0,00** |
| Barra do Garças | MT | 50.309,07 | 50.309,07 | **0,00** |
| Londrina | PR | 0,00 | 0,00 | **0,00** |
| Corumbá | MS | 19.961,553359 | 19.961,553359 | **0,00** |
| Rio Brilhante | MS | 331.236,11 | 331.236,11 | **0,00** |

O crédito bruto bate nas sete e os débitos batem com a `Dinamica`. Corumbá é
conferido contra a **apuração individualizada (Empresa 9)**, não contra a
consolidada — que trazia R$ 26.503,24 de crédito mantido porque somava a ele o
crédito indevido de transferência.

**O estorno bate exato nas sete.** Rio Brilhante era a exceção enquanto o motor
chaveava na carga efetiva; passou a fechar quando a chave virou a alíquota — a
referência aqui é a linha 003 do Registro de Apuração, não mais a planilha.

---

## Entrega 3 — Benefício fiscal de Rio Brilhante ✅

**Concluída em 25/08/2026.** O alcance, que era a maior incógnita do projeto,
deixou de ser hipótese: três documentos oficiais de 07/2026 o fecharam.

Termo de Acordo n. 1.190/2018, cláusula terceira, em vigor até 31/12/2032: 67%
do saldo devedor, mais 13% nas interestaduais, **exclusivamente sobre a
atividade industrial**. A cláusula quarta segue expirada desde 31/12/2022 — a
revenda de R$ 93.717,23 de Julho não recebeu nada.

O motor reproduz a cadeia inteira:

| Etapa | Julho/2026 (R$) |
|---|---|
| Crédito industrial normal | 327.834,95 |
| (−) estorno industrial | 245.987,17 |
| (−) estorno de créditos (ajuste, linha 003 do Registro) | 3.865,30 |
| (=) crédito da parcela incentivada | 77.982,48 |
| Base do incentivo | 334.291,69 |
| **Benefício** (67% intra + 80% inter) | **261.431,90** |
| FADEFE 2% — guia avulsa, fora da conta gráfica | 5.228,64 |

Para chegar até aqui, três coisas mudaram no motor:

1. **A chave do estorno passou a ser a alíquota**, não a carga efetiva. A parcela
   virou fórmula: `1 − 4 / alíquota`. Vale R$ 73.843,39 nas importações de ureia.
2. **A apuração passou a ser segregada por atividade** onde a UF exige. Sem isso
   não existe "crédito da parcela incentivada".
3. **Os ajustes que não vêm do Livro** entram por `AjustesDaApuracao`, explícitos.

Travas do motor: o benefício nunca supera o saldo devedor que o gerou, atividade
indefinida bloqueia o encerramento, e tentar aplicar a cláusula quarta levanta
erro com a data de expiração na mensagem. A memória de cálculo vai na aba
`APURAÇÃO POR FILIAL`, passo a passo.

**O que sobrou em aberto** não é do motor, é de documento: o complemento de
R$ 5.249,34 (decisão nº 18), a segregação de Corumbá sem GIA (nº 19), a
centralização de MS (nº 20) e a origem dos créditos de ajuste (nº 21).

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
