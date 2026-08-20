# Contexto do repositório

Monorepo de automações do time Fiscal/Tributário da Hinove Agrociência S.A.
Projeto ativo: **Apurabot** (apuração de ICMS). O Fiscalbot, já existente, será
importado depois — ele valida o Livro Fiscal que o Apurabot consome.

## Regras deste repositório

1. **Nunca versionar dado fiscal.** Livro Fiscal, XMLs, base de bens e apurações
   contêm dados reais da empresa. Ficam em `competencias/`, ignorada pelo git.
   Se precisar de um exemplo em teste, use uma amostra anonimizada.
2. **Regra tributária é parâmetro, não é código.** Alíquota, percentual de
   estorno e lista de CFOP vão para `<projeto>/parametros/*.yaml`, com vigência.
   Nenhum número tributário embutido em `.py`.
3. **Toda regra tem vigência.** Apuração de mês antigo tem que continuar
   reproduzível depois de mudança na legislação.
4. **Nada de classificação por adivinhação.** Documento que não casar com regra
   recebe status `SEM REGRA` e bloqueia o encerramento da competência.
5. **Documentação em português.** O público é o time fiscal, não só o desenvolvedor.

## Antes de mexer no motor de ICMS

Leia, nesta ordem:
- `docs/apurabot/01-arquitetura.md` — camadas e decisões de tecnologia
- `docs/apurabot/04-matriz-de-regras-icms.md` — a regra tributária
- `docs/apurabot/06-decisoes-pendentes.md` — o que ainda não foi respondido pelo fiscal

## Competência de referência

Julho/2026 é a competência analisada em detalhe e a base do teste de regressão.
Os números a reproduzir estão em `docs/apurabot/05-achados-julho-2026.md`.
