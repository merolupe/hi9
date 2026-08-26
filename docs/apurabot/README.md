# Apurabot — Documentação

Apuração mensal de ICMS da Hinove Agrociência S.A. a partir do Livro Fiscal.

## Situação

**A competência de referência é reproduzida da ingestão ao benefício fiscal,
fecha sem nenhuma pendência, e a apuração de Rio Brilhante bate ao centavo com a
GIA entregue.** 96 testes automáticos.

| | |
|---|---|
| Equalização de carga | por algoritmo, com cada divergência exigida por teste |
| Estorno por filial | exato nas 7 |
| Segregação por atividade (MS) | industrial, comercial e prestacional conferidos contra a GIA |
| Benefício de Rio Brilhante | cadeia inteira, do crédito industrial ao FADEFE |
| Pendências no fechamento | **0** |
| Extração | `Movimento Livros Fiscais` é o padrão; a antiga continua suportada |

Os números de cada verificação estão em
[05 — Achados de Julho/2026](05-achados-julho-2026.md).

## Por onde começar

| Documento | Para quem | O que responde |
|---|---|---|
| [01 — Arquitetura](01-arquitetura.md) | Desenvolvedor + Gerência | Como a ferramenta é construída e por quê |
| [02 — Plano de execução](02-plano-de-execucao.md) | Todos | O que já entregou, o que falta e o que trava o quê |
| [03 — Dicionário do Livro Fiscal](03-dicionario-livro-fiscal.md) | Desenvolvedor | Os dois layouts, coluna a coluna |
| [04 — Matriz de regras de ICMS](04-matriz-de-regras-icms.md) | **Fiscal/Tributário** | Toda a regra tributária, para homologação |
| [05 — Achados de Julho/2026](05-achados-julho-2026.md) | Todos | O que a análise da apuração real revelou |
| [06 — Decisões](06-decisoes-pendentes.md) | **Fiscal/Tributário** | 20 registradas: 12 respondidas, 8 em aberto |

## Fases

- **Fase 1 — ICMS:** Entregas 0, 1 e 3 concluídas; a 2 fecha quando os ajustes
  manuais deixarem de ser parâmetro e passarem a vir de `ajustes.xlsx`. Faltam
  centralização de SP, DIFAL, CIAP e a interface.
- **Fase 2 — PIS/Cofins:** não iniciada.
- **Benefício fiscal de MS:** concluído. O alcance, que era a maior incógnita do
  projeto, está fixado pela declaração — é a **atividade industrial**, e o motor
  reproduz a cadeia inteira, do crédito industrial ao FADEFE.
