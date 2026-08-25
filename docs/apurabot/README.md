# Apurabot — Documentação

Apuração mensal de ICMS da Hinove Agrociência S.A. a partir do Livro Fiscal.

## Situação em 25/08/2026

**Julho/2026 é reproduzido da ingestão ao benefício fiscal, fecha sem nenhuma
pendência, e a apuração de Rio Brilhante bate ao centavo com a GIA
retificadora.** 96 testes automáticos.

| | |
|---|---|
| Linhas do Livro Fiscal | 6.555 · 2.345 relevantes para ICMS |
| Equalização de carga | 99,87% de aderência ao trabalho manual |
| Estorno por filial | **exato nas 7**, incluindo Rio Brilhante |
| Segregação por atividade (MS) | industrial, comercial e prestacional conferidos contra a GIA |
| Benefício de Rio Brilhante | R$ 261.431,90 — igual ao declarado |
| FADEFE (guia avulsa) | R$ 5.228,64 |
| Pendências no fechamento | **0** |
| Extração | `Movimento Livros Fiscais` é o padrão; a antiga continua suportada |

## Por onde começar

| Documento | Para quem | O que responde |
|---|---|---|
| [01 — Arquitetura](01-arquitetura.md) | Desenvolvedor + Gerência | Como a ferramenta é construída e por quê |
| [02 — Plano de execução](02-plano-de-execucao.md) | Todos | O que já entregou, o que falta e o que trava o quê |
| [03 — Dicionário do Livro Fiscal](03-dicionario-livro-fiscal.md) | Desenvolvedor | Os dois layouts, coluna a coluna |
| [04 — Matriz de regras de ICMS](04-matriz-de-regras-icms.md) | **Fiscal/Tributário** | Toda a regra tributária, para homologação |
| [05 — Achados de Julho/2026](05-achados-julho-2026.md) | Todos | O que a análise da apuração real revelou |
| [06 — Decisões pendentes](06-decisoes-pendentes.md) | **Fiscal/Tributário** | 22 registradas: 11 respondidas, 11 em aberto |

## Fases

- **Fase 1 — ICMS:** Entregas 0, 1 e 3 concluídas; a 2 fecha quando os ajustes
  manuais deixarem de ser parâmetro e passarem a vir de `ajustes.xlsx`. Faltam
  centralização de SP, DIFAL, CIAP e a interface.
- **Fase 2 — PIS/Cofins:** não iniciada.
- **Benefício fiscal de MS:** concluído. O alcance, que era a maior incógnita do
  projeto, foi fechado em 25/08/2026 contra o Registro de Apuração e as duas
  GIAs de 07/2026 — é a **atividade industrial**, e o motor reproduz a cadeia
  inteira, do crédito industrial ao FADEFE.
