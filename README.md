# hi9

Monorepo de automações do time Fiscal/Tributário da **Hinove Agrociência S.A.**

Cada automação vive em sua própria pasta na raiz, com código, parâmetros e
testes próprios. A documentação de todas fica em `docs/`.

## Projetos

| Projeto | Pasta | Status | Descrição |
|---|---|---|---|
| **Apurabot** | `apurabot/` | Em desenvolvimento | Apuração mensal de ICMS (e, em fase posterior, PIS/Cofins) a partir do Livro Fiscal. A competência de referência já é reproduzida da ingestão ao benefício fiscal, sem pendências, e a apuração de Rio Brilhante confere ao centavo com a GIA entregue. |
| _Fiscalbot_ | — | Existente, a ser importado | Confere o lançamento de cada nota. É o fornecedor do Livro Fiscal validado que o Apurabot consome. |

## Como se usa o Apurabot

Dois cliques em **`Apurabot.bat`**. A ferramenta abre no navegador: arraste o
Livro Fiscal, veja o resultado na tela e baixe a planilha.

**Não há passo de instalação.** As bibliotecas viajam junto do código, e a
interface é o navegador: o servidor sobe em `127.0.0.1` pelo Python que já está
na máquina. Nenhum privilégio de administrador é pedido, nada é baixado, e o
dado fiscal não sai dali.

Só é preciso ter Python 3.10 ou mais novo. Para conferir: `python verificar.py`.

O passo a passo, incluindo a linha de comando, está em
[`docs/apurabot/07-como-rodar.md`](docs/apurabot/07-como-rodar.md). Para testar
pela primeira vez, siga o
[roteiro de teste](docs/apurabot/08-roteiro-de-teste.md).

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
