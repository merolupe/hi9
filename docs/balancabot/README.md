# Balançabot — Documentação

Conferência do desvio entre o peso da balança de Guará e o peso das notas,
caminhão a caminhão. Hoje é uma macro de Excel (o antigo Faturabot,
"Conferência 3"); está sendo planejada a entrada dela na Central.

## Situação

**Planejamento.** Nenhuma linha de código entrou ainda. A ferramenta foi lida
por inteiro — o `.bas` de 4.085 linhas, o painel `.xlsm` e o manual de
23/09/2026 — e o plano do porte está escrito.

| | |
|---|---|
| Levantamento da ferramenta como ela é | pronto ([01](01-o-que-faz-hoje.md)) |
| Plano do porte | pronto ([02](02-plano-do-porte.md)) |
| Projeto `balancabot/` e a entrada no catálogo | não começou |
| **Divergência zero contra a macro** | **sem padrão-ouro** — a macro ainda não rodou no Excel |

## Por onde começar

| Documento | Para quem | O que responde |
|---|---|---|
| [01 — O que a ferramenta é hoje](01-o-que-faz-hoje.md) | Desenvolvedor + Gerência + operador | O que pede, como decide, o que entrega, o que é só Excel, e os 14 achados da leitura |
| [02 — Plano do porte](02-plano-do-porte.md) | Desenvolvedor + Gerência | Onde mora, como se divide, o que muda no contrato da Central, fórmula ou valor, parâmetros, prova, perguntas ao time e a ordem das entregas |

## As duas coisas a dizer antes do porte

1. **O painel do `.xlsm` não é lido onde é editado.** A tolerância e a janela
   que o operador vê em `B3` e `B4` não são as células que a macro lê. Hoje não
   faz diferença, porque os valores coincidem com os padrões do código; mudar a
   tolerância no painel **não muda nada** ([01](01-o-que-faz-hoje.md) § 3.4).
2. **Falta o padrão-ouro.** O porte se prova contra uma execução real da macro:
   os relatórios que entraram e o `.xlsx` que saiu. Sem isso ele pode ficar
   completo e não estar provado ([02](02-plano-do-porte.md) § 8).
