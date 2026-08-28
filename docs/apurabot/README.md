# Apurabot — Documentação

Apuração mensal de ICMS da Hinove Agrociência S.A. a partir do Livro Fiscal.

## Situação

**A competência de referência é reproduzida da ingestão ao benefício fiscal,
fecha sem nenhuma pendência, e a apuração de Rio Brilhante bate ao centavo com a
GIA entregue e com o Registro de Apuração do ERP.** 168 testes automáticos.

| | |
|---|---|
| Equalização de carga | por algoritmo, com cada divergência exigida por teste |
| Estorno por filial | exato nas 7 |
| Segregação por atividade (MS) | industrial, comercial e prestacional conferidos contra a GIA |
| Benefício de Rio Brilhante | cadeia inteira, do crédito industrial ao FADEFE |
| Centralização | saldo consolidado na centralizadora, com a NF-e de transferência cobrada |
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
| [06 — Decisões pendentes](06-decisoes-pendentes.md) | **Fiscal/Tributário** | 11 perguntas em aberto, cada uma com o padrão assumido |
| [07 — Como rodar](07-como-rodar.md) | **Quem vai usar** | Instalar, rodar e ler o resultado, do zero |

## Fases

- **Fase 1 — ICMS:** Entregas 0, 1, 3 e 4 concluídas, e a ferramenta já roda de
  ponta a ponta — ver [07 — Como rodar](07-como-rodar.md). A 2 fecha quando o
  relatório de ajustes for lido; falta a interface gráfica. **DIFAL e CIAP estão
  pausados.**
- **Fase 2 — PIS/Cofins:** não iniciada.
- **Benefício fiscal de MS:** concluído. Alcança a **atividade industrial**, e o
  motor cobre a cadeia inteira, do crédito industrial ao FADEFE.
