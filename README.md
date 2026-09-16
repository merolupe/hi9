# hi9

Monorepo de automações do time Fiscal/Tributário da **Hinove Agrociência S.A.**

Cada automação vive em sua própria pasta na raiz, com código, parâmetros e
testes próprios. A documentação de todas fica em `docs/`. A **Central Fiscal**
é a tela que reúne todas.

## Como se usa

Dois cliques em **`Hinove.bat`**. A Central abre no navegador, com as
ferramentas do setor para escolher: clique em uma, ela pede o arquivo de que
precisa e devolve o resultado na tela, com a planilha para baixar.

**Não há passo de instalação.** As bibliotecas viajam junto do código, e a
interface é o navegador: o servidor sobe em `127.0.0.1` pelo Python que já está
na máquina. Nenhum privilégio de administrador é pedido, nada é baixado, e o
dado fiscal não sai dali.

Só é preciso ter Python 3.10 ou mais novo. Para conferir: `python verificar.py`.

Quem só usa a apuração pode continuar indo direto por **`Apurabot.bat`**.

## Projetos

| Projeto | Pasta | Status | Descrição |
|---|---|---|---|
| **Central Fiscal** | `central/` | Em uso | A tela única: reúne as ferramentas abaixo e roda as rotinas por ela. |
| **Apurabot** | `apurabot/` | Em desenvolvimento | Apuração mensal de ICMS (e, em fase posterior, PIS/Cofins) a partir do Livro Fiscal. A competência de referência já é reproduzida da ingestão ao benefício fiscal, sem pendências, e a apuração de Rio Brilhante confere ao centavo com a GIA entregue. |
| **DiXML** | `dixml/` | Importado | Transforma lote de XMLs em planilha. Permite validar qualquer informação fiscal presente no arquivo da nota. |
| **Fiscalbot** | `fiscalbot/` | Importado, em teste | Confere o lançamento de cada nota e valida o Livro Fiscal. É o fornecedor do Livro Fiscal validado que o Apurabot consome. |
| **GerarServPend** | `pendentes/` | Importado, em teste | Confronta as notas de serviço emitidas contra a Hinove (ASIS) com os lançamentos do Sankhya e diz o que ainda não foi lançado, com o pedido de compra e o requisitante por trás de cada pendência. |
| _GerarPendentes_ | `pendentes/` | Em importação | Confronta dados e gera uma planilha de notas de mercadoria pendente de entrada. Compartilha o núcleo com a de cima — duas ferramentas na tela, um projeto no disco. O motor de mercadorias é a entrega seguinte. |
| _Faturabot_ | — | Em desenvolvimento | Conferências do time de expedição. Confere e consolida desvios da balança, escrituração de saídas e entradas de diretos. |

As ferramentas que ainda não foram importadas **aparecem na Central**, apagadas,
com o nome e o que fazem: o time enxerga o que falta em vez de descobrir na hora
em que for precisar. O GerarPendentes segue apagado enquanto o motor de
mercadorias não roda — botão que não roda é pior do que botão apagado —, mas o
texto dele na tela já diz em que pé o porte está.

## Como entra a próxima ferramenta

Uma de cada vez, e cada uma já nascendo dentro da Central. Para aparecer na
tela, ela declara três coisas — quem é, que arquivo pede e o que devolve. O
contrato está em
[`docs/central/01-arquitetura.md`](docs/central/01-arquitetura.md).

Ao importar, a regra é **trazer como está**: versionado, documentado e rodando
pela Central. O que se reescreve é só o que impede a ferramenta de rodar sem
instalação.

## Pelo terminal

```
python rodar.py                                       abre a Central
python rodar.py dixml "lote.zip" --saida "pasta"      lote de XML em planilha
python rodar.py fiscalbot "Movimento.xls"             auditoria do Livro Fiscal
python rodar.py apurabot apurar "livro.xls"           apuração de ICMS
```

O passo a passo do Apurabot está em
[`docs/apurabot/07-como-rodar.md`](docs/apurabot/07-como-rodar.md). Para testar
pela primeira vez, siga o
[roteiro de teste](docs/apurabot/08-roteiro-de-teste.md).

## Convenções

- **Nenhum dado fiscal no repositório.** Livro Fiscal, XMLs, base de bens e
  apurações ficam em `competencias/`, que é ignorada pelo git (ver `.gitignore`).
  Teste que precise de nota usa amostra fictícia montada no próprio teste.
- **Regra tributária é parâmetro, não é código.** Toda regra fica em arquivo
  declarativo, nunca embutida em `.py`. No Apurabot ela é versionada em
  `apurabot/parametros/`, com vigência e responsável. No Fiscalbot ela é
  cadastrada na tela da Central e fica em `dados/`, fora do git — a trilha de
  quem alterou passa a viver dentro do aplicativo. O porquê está em
  [`docs/central/01-arquitetura.md`](docs/central/01-arquitetura.md).
- **Toda mudança de regra passa por commit.** O histórico do git é a trilha de
  auditoria de "quem mudou o quê, quando e por quê".

- **Nenhuma ferramenta importa outra.** Quem costura é a Central. Há teste que
  trava isso.

## Documentação

- [`docs/central/`](docs/central/) — a arquitetura da Central e o contrato que
  uma ferramenta cumpre para entrar na tela.
- [`docs/apurabot/`](docs/apurabot/) — arquitetura, plano de execução, dicionário
  de dados, matriz de regras e decisões pendentes do Apurabot.
- [`docs/dixml/`](docs/dixml/) — o que o DiXML lê, o que ele decide sozinho e as
  colunas da Reforma Tributária.
- [`docs/fiscalbot/`](docs/fiscalbot/) — as camadas da auditoria, a linguagem
  das regras e o registro do porte que veio do VBA.
- [`docs/pendentes/`](docs/pendentes/) — as duas rotinas de notas pendentes de
  entrada: a arquitetura, o registro do porte, o que cada relatório responde, o
  plano de entrega e as decisões pendentes.
