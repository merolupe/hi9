# Contexto do repositório

Monorepo de automações do time Fiscal/Tributário da Hinove Agrociência S.A.
A **Central Fiscal** (`central/`) é a tela única que reúne as ferramentas.
Já dentro dela: **Apurabot** (apuração de ICMS), **DiXML** (lote de XML em
planilha) e **Fiscalbot** (auditoria do Livro Fiscal, que alimenta o Apurabot).
A importar, uma a uma: GerarPendentes e GerarServPend.

## Regras deste repositório

1. **Nunca versionar dado fiscal.** Livro Fiscal, XMLs, base de bens e apurações
   contêm dados reais da empresa. Ficam em `competencias/`, ignorada pelo git.
   Se precisar de um exemplo em teste, use uma amostra anonimizada.
2. **Regra tributária é parâmetro, não é código.** Alíquota, percentual de
   estorno e lista de CFOP nunca ficam embutidos em `.py`. Onde moram depende
   da ferramenta: o Apurabot versiona em `<projeto>/parametros/*.yaml`, com
   vigência; o Fiscalbot guarda na base do aplicativo (`dados/`, fora do git),
   cadastrada pela tela da Central, com carga de fábrica versionada em
   `<projeto>/regras_de_fabrica.yaml` — sem dado da empresa.
3. **Toda regra tem vigência.** Vale para o Apurabot: apuração de mês antigo
   tem que continuar reproduzível depois de mudança na legislação. Na ferramenta
   com tela de configuração, a trilha é o carimbo de quem gravou e quando.
4. **Nada de classificação por adivinhação.** Documento que não casar com regra
   recebe status `SEM REGRA` e bloqueia o encerramento da competência.
5. **Documentação em português.** O público é o time fiscal, não só o desenvolvedor.
6. **Roda sem instalar nada.** Máquina corporativa sem administrador: as
   bibliotecas viajam em `vendor/`, na raiz, e precisam ser Python puro.
   Dependência com extensão compilada (pandas, lxml) não entra.
7. **Nenhuma ferramenta importa outra.** Quem costura é a Central. Para entrar
   na tela, a ferramenta declara o que pede e o que devolve — o contrato está
   em `docs/central/01-arquitetura.md`.

## Antes de importar uma ferramenta nova

Leia `docs/central/01-arquitetura.md` — o contrato de ferramenta e por que a
ordem é uma de cada vez. A regra ao importar é trazer como está; reescreve-se
só o que impede de rodar sem instalação.

## Antes de mexer no motor de ICMS

Leia, nesta ordem:
- `docs/apurabot/01-arquitetura.md` — camadas e decisões de tecnologia
- `docs/apurabot/04-matriz-de-regras-icms.md` — a regra tributária
- `docs/apurabot/06-decisoes-pendentes.md` — o que ainda não foi respondido pelo fiscal

## Competência de referência

Julho/2026 é a competência analisada em detalhe e a base do teste de regressão.
Os números a reproduzir estão em `docs/apurabot/05-achados-julho-2026.md`.
