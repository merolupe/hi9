# hi9

Monorepo de automações do time Fiscal/Tributário da **Hinove Agrociência S.A.**

Cada automação vive em sua própria pasta na raiz, com código, parâmetros e
testes próprios. A documentação de todas fica em `docs/`.

## Projetos

| Projeto | Pasta | Status | Descrição |
|---|---|---|---|
| **Apurabot** | `apurabot/` | Em desenvolvimento | Apuração mensal de ICMS (e, em fase posterior, PIS/Cofins) a partir do Livro Fiscal. Julho/2026 já é reproduzido da ingestão à apuração por estabelecimento, sem pendências. |
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
