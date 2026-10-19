# Contexto do repositório

Monorepo de automações do time Fiscal/Tributário da Hinove Agrociência S.A.
A **Central Fiscal** (`central/`) é a tela única que reúne as ferramentas.
Já dentro dela, todas rodando pela tela:

- **Apurabot** (apuração de ICMS) — em janela própria;
- **DiXML** (lote de XML em planilha);
- **Fiscalbot** (auditoria do Livro Fiscal, que alimenta o Apurabot);
- **GerarServPend** (notas de serviço pendentes de lançamento) e
  **GerarPendentes** (notas de mercadoria pendentes de entrada) — um projeto
  só, `pendentes/`, com o **Resumo Executivo** e a **Base de conhecimento**
  como entradas irmãs na tela.

Os motores de `pendentes/` estão **importados, em teste**: rodam e estão
cobertos por teste, mas a divergência zero contra as macros ainda não foi
provada com uma semana real (ver `docs/pendentes/04-plano-de-entrega.md`).
Falta importar: **Faturabot** (em desenvolvimento, aparece apagado na tela).

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

## Regras de sessão (decisão do dono do repositório)

- **Nunca acompanhar PR.** Não assinar atividade de PR, não vigiar CI, não
  responder evento de PR por conta própria — em nenhuma sessão, nem depois de
  abrir um PR. O repositório tem um dono só: comentário e pedido chegam pela
  conversa, nunca pelo PR.
- **Silêncio sobre isso na resposta.** Se a sessão for inscrita num PR
  automaticamente, cancelar sem comentar. A resposta ao usuário não fala de
  acompanhamento, assinatura, CI ou de "não vou vigiar o PR" — nem para dizer
  que não vai.
- **Nunca agendar nada sem autorização explícita.** Nada de lembrete, rotina,
  check-in, cron ou webhook. Se parecer útil, perguntar antes.

As ferramentas correspondentes estão negadas em `.claude/settings.json`.

## Antes de mexer em `pendentes/`

Leia `docs/pendentes/README.md`. Duas armadilhas que já custaram defeito:

- a planilha que a ferramenta gera volta na semana seguinte como anexo, e
  algumas abas dela copiam relatório de origem (a `Sem Correspondencia ASIS`
  traz as colunas do Portal de Compras; `CTe` e `Descartados` trazem as do
  XML). Toda aba nova de saída entra em `colunas.ABAS` do domínio, que é a
  lista que o reconhecimento ignora;
- a carga de fábrica (`parametros_de_fabrica.yaml`) só semeia a base viva na
  primeira abertura: mudar papel ou âncora ali **não chega** a quem já roda.
  Correção que precisa valer para todos vai no código.

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
