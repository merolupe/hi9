# Vitrine da Central Fiscal

Uma página só que apresenta a **Central Fiscal** e as oito ferramentas que giram
em volta dela — para mostrar ao time, à gerência e a quem chega o que cada uma
faz e, principalmente, **como ela decide**.

Abre com dois cliques em `index.html`, offline. Não usa CDN, fonte remota nem
imagem: as fontes (Inter e JetBrains Mono, licença OFL) viajam em `fontes/`, e
se faltarem o sistema assume.

## O que tem

| Seção | O que mostra |
|---|---|
| Abertura e herói | as três bolas da Hinove se encaixando na marca; as oito ferramentas em órbita em volta da Central (clique num planeta para ir até ela) |
| 01 · Central | o contrato de quatro linhas — quem é, o que pede, o que devolve, o que se configura — e uma reencenação da tela rodando sozinha |
| 02 · Fluxo | o mapa de origem → ferramenta → entrega, com os documentos em trânsito; passe o cursor numa ferramenta para acender o caminho dela |
| 03 · Ferramentas | um capítulo por ferramenta, cada um com um instrumento animado que reproduz a regra dela (a cascata do Fiscalbot, a equalização do Apurabot, a esteira do GerarPendentes, as quatro peneiras do GerarServPend, a balança do Faturabot…) |
| 04 · Princípios | as regras do repositório, cada uma com uma animação curta |
| 05 · Números | contagens tiradas do próprio repositório |

## De onde vêm os números

Nada de dado fiscal. A página usa só o que já está na documentação:

- **contagens do repositório** — 742 testes (`def test_` em cada `*/tests`),
  ~19,5 mil linhas de motor em `*/src`;
- **medições publicadas nos docs** — 99,87% de equalização e as sete filiais com
  diferença zero (`docs/apurabot/05-achados-julho-2026.md`), 44/44 · 18/18 · 77%
  da base de conhecimento (`docs/pendentes/08-base-de-conhecimento.md`), a
  conferência da semana 38 (`docs/pendentes/07-resumo-executivo.md`), as regras
  do extrator de OC e da tolerância (`docs/balancabot/01-o-que-faz-hoje.md`).

Nenhum valor em R$ aparece. As animações que simulam fluxo (proporções,
placas, pesos, chaves e parceiros) são **fictícias** e dizem isso na legenda.

Ao atualizar uma contagem, atualize também a legenda que a cita.

## Detalhes

- Tema escuro e claro, com o botão no canto; a escolha fica no navegador.
- Respeita `prefers-reduced-motion`: as animações param no estado final.
- Cada instrumento só anima quando está na tela.
- Responsiva de 375 px a desktop.
