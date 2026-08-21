# Apurabot — Plano de execução

> Entregas incrementais. Cada uma termina com algo que o time fiscal consegue
> abrir, conferir e opinar — nunca com "está quase pronto".

---

## Princípio

**Fechar Julho/2026 pela ferramenta, e comparar com o Excel de Julho/2026 feito à
mão.** Toda entrega é medida por quanto do resultado real ela já reproduz.
Julho é a competência de referência porque foi a analisada em detalhe; Junho
entra depois como teste de regressão independente (exigência do escopo).

---

## Entrega 0 — Mapeamento técnico ✅ concluída

O que já está neste repositório:

- Arquitetura em camadas e decisão de tecnologia — `01-arquitetura.md`
- Dicionário das 52 colunas do Livro Fiscal — `03-dicionario-livro-fiscal.md`
- Matriz de regras de ICMS por UF e categoria — `04-matriz-de-regras-icms.md`
- Achados da análise de Julho/2026 — `05-achados-julho-2026.md`
- 10 decisões pendentes com o time fiscal — `06-decisoes-pendentes.md`

**Resultado principal:** a equalização de carga efetiva, que era o maior risco
técnico, foi resolvida com **99,87% de aderência** ao trabalho manual.

---

## Entrega 1 — Base tratada e classificada ✅ concluída

**Escopo:** camadas 1 a 4 (ingestão, normalização, equalização de carga,
classificação).

**Resultado medido contra Julho/2026:**

| Verificação | Resultado |
|---|---|
| Linhas lidas do Livro Fiscal | 6.504 |
| Linhas relevantes para ICMS | 2.345 — igual à aba `ICMS` da planilha manual |
| Carga efetiva × classificação manual | 2.342 de 2.345 (99,87%) |
| Totais por estabelecimento × entrada/saída × carga | idênticos à aba `Dinamica` |
| Pendências | 22 linhas (`COMPLEMENTO DE PREÇO`, R$ 2.181,70) |
| Testes | 24, dos quais 9 de regressão |

As 3 divergências de carga são as notas da ICL Aditivos, reclassificadas à mão
para aplicar a regra de MS. O teste de regressão **exige** que a diferença seja
exatamente essa e de R$ 9.019,01 — qualquer outra falha o teste.

- Leitura do Livro Fiscal `.xlsx` com validação de cabeçalho — falha clara se o
  layout do Sankhya mudar
- Congelamento da base bruta + hash do arquivo de entrada
- Equalização de carga efetiva
- Classificação da operação (frete compra/venda/transferência, MP, embalagem,
  produto químico, revenda, retorno de industrialização, CIAP, quebra,
  devolução), com `SEM REGRA` para o que não se encaixar
- Cadastro inicial dos 829 produtos com categoria tributária

**Entregável:** `.xlsx` com a base tratada, uma linha por linha do Livro, todas as
colunas de rastreabilidade e uma aba de pendências.

**Critério de aceite:** a base tratada reproduz a aba `ICMS` de Julho/2026
(2.345 linhas) e a classificação bate com a aba `Dinamica` por
estabelecimento × entrada/saída × carga.

---

## Entrega 2 — Motor de ICMS: créditos, débitos e estornos ✅ parcial

**Escopo:** camadas 5 a 8, por regime.

**Resultado medido contra Julho/2026 — crédito bruto, estorno e crédito mantido
por estabelecimento:**

| Estabelecimento | UF | Estorno calculado | Estorno manual | Diferença |
|---|---|---|---|---|
| Registro | SP | 50.481,97 | 50.481,97 | **0,00** |
| Guará | SP | 426.771,68 | 426.771,68 | **0,00** |
| Matriz | SP | 0,00 | 0,00 | **0,00** |
| Barra do Garças | MT | 50.309,07 | 50.309,07 | **0,00** |
| Londrina | PR | 0,00 | 0,00 | **0,00** |
| Corumbá | MS | 19.960,51 | 19.961,55 | −1,04 |
| Rio Brilhante | MS | 322.288,31 | 331.236,11 | −8.947,80 |

O **crédito bruto bate em todas as sete**, e os débitos de saída batem com a aba
`Dinamica`. As duas diferenças são conhecidas e o teste exige o valor exato de
cada uma:

- **Corumbá, R$ 1,04** — resíduo da planilha manual, decisão pendente nº 2.
- **Rio Brilhante, R$ 8.947,80** — os R$ 9.019,01 da ICL Aditivos reclassificados
  à mão, menos o resíduo de R$ 71,21 da planilha.

**Falta nesta entrega:** ajustes manuais aprovados lidos de `ajustes.xlsx`, e o
benefício fiscal de Rio Brilhante, que é a Entrega 3 e depende do Termo de Acordo.

- SP — equilíbrio fiscal (estorno do excedente sobre 4%)
- MS — estorno proporcional (Corumbá e Rio Brilhante)
- MT — estorno integral sobre saídas diferidas
- PR — manutenção integral sobre saídas diferidas
- Regras transversais: quebra (CFOP 5927), devolução, CIAP, retorno de
  industrialização, revenda
- Ajustes manuais aprovados, lidos de `ajustes.xlsx`
- Apuração e saldo individual por estabelecimento

**Entregável:** Painel 1 (apuração por unidade) + Painel 4 (resumo e memória de
cálculo) em `.xlsx`.

**Critério de aceite:** estorno e crédito mantido de Julho/2026 reproduzidos por
estabelecimento e por carga, com divergências explicadas linha a linha.

---

## Entrega 3 — Benefício fiscal de Rio Brilhante

Separada da Entrega 2 porque **depende de resposta do time fiscal**
(`06-decisoes-pendentes.md`, itens 1 e 2) e do texto do Termo de Acordo.

- Crédito presumido: 67% intra / 80% inter sobre o saldo devedor
- Controle de crédito outorgado (código de ajuste `MS090004`): saldo anterior,
  créditos recebidos por transferência, utilizados no período, saldo a transportar
- Recolhimento mínimo e deduções, se aplicável

**Critério de aceite:** reproduzir o B.F. de Julho/2026 (R$ 283.766,56) dentro da
tolerância acordada, com a memória de cálculo aberta.

---

## Entrega 4 — Centralização de São Paulo

- Saldo individual antes da centralização, por estabelecimento paulista
- Classificação credor/devedor e valor transferível
- Controle das NF-e de transferência (8 validações do escopo, item 7.1)
- Consolidação em Guará e resultado da centralizadora
- Travas: `saldo individual = transferido + residual` e
  `recebido em Guará = soma das NF-e emitidas`

**Critério de aceite:** reproduzir a centralização de Julho/2026 e apontar as
mesmas NF-e a emitir.

---

## Entrega 5 — DIFAL

Depende do arquivo de XML das entradas (`06-decisoes-pendentes.md`, item 9).

- Cruzamento Livro Fiscal × XML pela chave da NF-e
- Recálculo do DIFAL com o ICMS do XML nas compras fora do processo produtivo
- Valor sem arredondamento, arredondado por documento e total consolidado
- SP em conta gráfica · MS em guia avulsa

**Entregável:** Painel 2 — auditoria das alterações no Livro para o DIFAL.

---

## Entrega 6 — Interface e empacotamento

- Janela local com os 4 comandos, seleção de competência e arrastar-e-soltar
- Painel de pendências com bloqueio do encerramento
- Empacotamento para duplo clique (sem instalar Python, sem linha de comando)
- Manual do usuário e documentação de manutenção

---

## Entrega 7 — Homologação

- Regressão de Junho/2026 (segunda competência, exigência do escopo)
- Treinamento do time
- Aceite formal e fechamento da Fase 1

---

## Entrega 8 — CIAP

Depende da Base de Bens. Índice = saídas tributadas ÷ total de saídas;
crédito apropriável = parcela mensal × índice. **Painel 3.**

---

## Fora desta fase

PIS/Cofins (Fase 2 do escopo), geração de EFD, transmissão de obrigações,
geração de guias, integração por API com o Sankhya, lançamento automático no ERP,
PER/DCOMP e emissão automática de NF-e de transferência.

---

## O que destrava o quê

```
Entrega 1  ──►  Entrega 2  ──►  Entrega 4  ──►  Entrega 6  ──►  Entrega 7
                    │
                    ├──►  Entrega 3   (precisa: respostas 1 e 2 + Termo de Acordo)
                    ├──►  Entrega 5   (precisa: .xlsx de exemplo do XML)
                    └──►  Entrega 8   (precisa: .xlsx da Base de Bens)
```

As entregas 3, 5 e 8 estão bloqueadas por insumos externos. As entregas 1, 2, 4,
6 e 7 podem começar imediatamente.
