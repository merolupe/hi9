# Apurabot — Documentação

Apuração mensal de ICMS da Hinove Agrociência S.A. a partir do Livro Fiscal.

## Situação em 21/08/2026

**Julho/2026 é reproduzido da ingestão até o benefício fiscal, e fecha sem
nenhuma pendência.** 84 testes automáticos.

| | |
|---|---|
| Linhas do Livro Fiscal | 6.504 · 2.345 relevantes para ICMS |
| Equalização de carga | 99,87% de aderência ao trabalho manual |
| Estorno por filial | exato em 6 das 7; Rio Brilhante difere pelos R$ 8.947,80 já explicados |
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
| [06 — Decisões pendentes](06-decisoes-pendentes.md) | **Fiscal/Tributário** | 17 registradas: 10 respondidas, 7 em aberto |

## Fases

- **Fase 1 — ICMS:** Entregas 0 e 1 concluídas; a 2 fecha com os ajustes
  manuais e a 3 tem o motor pronto, à espera de decisão sobre o alcance do
  benefício. Faltam centralização de SP, DIFAL, CIAP e a interface.
- **Fase 2 — PIS/Cofins:** não iniciada.
- **Benefício fiscal de MS:** trazido para a Fase 1 por decisão estratégica. O
  Termo de Acordo n. 1.190/2018 está analisado e os dois critérios de alcance,
  implementados — falta escolher qual vale.
