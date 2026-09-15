# Pendentes — Documentação

Notas emitidas contra a Hinove que ainda **não** têm entrada lançada — de
mercadoria (`GerarPendentes`) e de serviço (`GerarServPend`). Duas rotinas
semanais do time fiscal, hoje em duas macros de Excel, sendo portadas para a
Central.

## Situação

**O GerarServPend roda.** O núcleo comum das duas rotinas e o motor de serviços
estão no repositório, em `pendentes/`, com 168 testes de comportamento, e a
entrada do catálogo saiu de `A_IMPORTAR`. O motor de mercadorias é a entrega
seguinte, e por isso o **GerarPendentes continua apagado** na tela: botão que
não roda é pior do que botão apagado.

| | |
|---|---|
| Reconhecimento de arquivo por âncora de cabeçalho | pronto |
| Coluna por nome, com sinônimo e lista completa das faltantes | pronto |
| Normalizações (texto, número de NFS-e, chave, CNPJ, data, farol) | pronto |
| Livro de classificação, com carimbo | pronto |
| Snapshot semanal imutável | pronto |
| Escrita com formato antes da escrita | pronto |
| **Motor de serviços** — cascata por passos, vínculo de pedido, população inversa | **pronto** |
| Tela de configuração de serviços | entrega 3 |
| Motor de mercadorias | entrega 3 |
| Resumo Executivo | **suspenso** — vira resumo das duas frentes, com três categorias ([06](06-proximas-rodadas.md)) |
| **Divergência zero contra a macro** | **não provada** — faltam os arquivos reais |

O `.xlam` em produção é **byte a byte o v14**: a rodada de formatação de
17/08/2026 nunca entrou, e não existe v15.

## Por onde começar

| Documento | Para quem | O que responde |
|---|---|---|
| [01 — Arquitetura](01-arquitetura.md) | Desenvolvedor + Gerência | Por que duas ferramentas na tela e um projeto no disco, como o arquivo é reconhecido, onde mora o estado, o que é parâmetro e o que bloqueia |
| [02 — O porte do VBA](02-porte-do-vba.md) | Desenvolvedor + Gerência | O critério, o padrão-ouro, o que sai, o que fica idêntico, os defeitos corrigidos e os preservados — com a medição que cada um exige |
| [03 — O que cada relatório responde](03-o-que-cada-relatorio-responde.md) | **Fiscal/Tributário e as áreas** | O que a ferramenta responde, o ciclo da semana e o que continua sendo decisão de gente |
| [04 — Plano de entrega](04-plano-de-entrega.md) | Todos | O que entrou, o que vem, em que ordem, com esforço e risco de cada bloco |
| [05 — Decisões pendentes](05-decisoes-pendentes.md) | **Fiscal/Tributário** | As 14 perguntas em aberto, cada uma com o padrão assumido |
| [06 — Próximas rodadas](06-proximas-rodadas.md) | **Fiscal/Tributário** + Desenvolvedor | O que o time já enxerga e ainda não foi desenhado — entre isso, o Resumo Executivo repensado |

## A pendência vermelha

[A nº 1](05-decisoes-pendentes.md): **os arquivos reais de uma semana e a saída
que a macro produziu a partir deles.** Sem eles o porte pode ficar completo e
não estar provado — e seis defeitos conhecidos continuam no produto, porque
mexer neles sem medir seria trocar um defeito conhecido por um desconhecido.
