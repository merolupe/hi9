# Apurabot — Plano de execução

> Entregas incrementais. Cada uma termina com algo que o time fiscal consegue
> abrir, conferir e opinar — nunca com "está quase pronto".

**Situação em 21/08/2026:** Julho/2026 é reproduzido da ingestão até a apuração
por estabelecimento, e **fecha sem nenhuma pendência**. 63 testes automáticos.

| Entrega | Situação |
|---|---|
| 0 · Mapeamento técnico | ✅ concluída |
| 1 · Base tratada e classificada | ✅ concluída |
| 2 · Motor de ICMS: créditos, débitos e estornos | 🟡 falta só ajustes manuais |
| 3 · Benefício fiscal de Rio Brilhante | 🔴 bloqueada por decisão, não por insumo |
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
| Rio Brilhante | MS | 322.288,31 | 331.236,11 | −8.947,80 |

O crédito bruto bate nas sete e os débitos batem com a `Dinamica`. Corumbá é
conferido contra a **apuração individualizada (Empresa 9)**, não contra a
consolidada — que trazia R$ 26.503,24 de crédito mantido porque somava a ele o
crédito indevido de transferência.

A única diferença que sobra é Rio Brilhante: os R$ 9.019,01 da ICL Aditivos
reclassificados à mão, menos R$ 71,21 de resíduo da planilha.

---

## Entrega 3 — Benefício fiscal de Rio Brilhante 🔴

**A regra é conhecida.** Termo de Acordo n. 1.190/2018, cláusula terceira: 67%
do saldo devedor nas operações com produtos de **própria industrialização**,
mais 13% nas interestaduais (80%), até 31/12/2032.

**Está bloqueada por uma decisão, não por falta de insumo.** Aplicando a regra
como o Termo escreve, o benefício de Julho seria R$ 228.357,72; foram lançados
R$ 283.766,56 — **R$ 55.408,84 de diferença**, aparentemente por incluir revenda
de terceiros e remessas na base, que a cláusula terceira não alcança e cuja
cobertura pela cláusula quarta terminou em 31/12/2022.

Implementar antes da resposta seria escolher um número de R$ 55 mil no lugar do
fiscal. Ver `06-decisoes-pendentes.md`, item 1.

Falta ainda: rateio do crédito entre operações beneficiadas e não beneficiadas,
o controle de crédito outorgado (`MS090004`) e a contribuição ao **FADEFE**, que
é condição de fruição.

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
                     ├──►  Entrega 3 🔴  precisa: decisão sobre os R$ 55 mil
                     ├──►  Entrega 5 ⬜   precisa: .xlsx de exemplo do XML
                     └──►  Entrega 8 ⬜   precisa: .xlsx da Base de Bens
```

As entregas **4 e 6 podem começar imediatamente**, e fechar a 2 depende só de
definir o formato do `ajustes.xlsx`.
