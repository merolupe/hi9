# hi9

Monorepo de automações do time Fiscal/Tributário da **Hinove Agrociência S.A.**

Cada automação vive em sua própria pasta na raiz, com código, parâmetros e
testes próprios. A documentação de todas fica em `docs/`.

## Projetos

| Projeto | Pasta | Status | Descrição |
|---|---|---|---|
| **Apurabot** | `apurabot/` | Em desenvolvimento | Apuração mensal de ICMS (e, em fase posterior, PIS/Cofins) a partir do Livro Fiscal. A competência de referência já é reproduzida da ingestão ao benefício fiscal, sem pendências, e a apuração de Rio Brilhante confere ao centavo com a GIA entregue. |
| _Fiscalbot_ | — | Existente, a ser importado | Confere o lançamento de cada nota. É o fornecedor do Livro Fiscal validado que o Apurabot consome. |

## Convenções

- **Nenhum dado fiscal no repositório.** Livro Fiscal, XMLs, base de bens e
  apurações ficam em `competencias/`, que é ignorada pelo git (ver `.gitignore`).
- **Regra tributária é parâmetro, não é código.** Toda regra fica em arquivos
  declarativos versionados (`<projeto>/parametros/`), com vigência e responsável.
- **Toda mudança de regra passa por commit.** O histórico do git é a trilha de
  auditoria de "quem mudou o quê, quando e por quê".

## Documentação

- [`docs/apurabot/`](docs/apurabot/) — arquitetura, plano de execução, dicionário
  de dados, matriz de regras e decisões pendentes do Apurabot.
