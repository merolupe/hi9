# Pendentes — Documentação

Notas emitidas contra a Hinove que ainda **não** têm entrada lançada — de
mercadoria (`GerarPendentes`) e de serviço (`GerarServPend`). Duas rotinas
semanais do time fiscal, hoje em duas macros de Excel, sendo portadas para a
Central.

## Situação

**Esta é a entrega da fundação.** O núcleo comum das duas rotinas está no
repositório, em `pendentes/`, com 98 testes de comportamento. Os dois motores
de domínio — a cascata de confronto de serviços e o pipeline de mercadorias —
são as entregas seguintes, e por isso as duas entradas da Central continuam
**apagadas**: botão que não roda é pior do que botão apagado.

| | |
|---|---|
| Reconhecimento de arquivo por âncora de cabeçalho | pronto |
| Coluna por nome, com sinônimo e lista completa das faltantes | pronto |
| Normalizações (texto, número de NFS-e, chave, CNPJ, data, farol) | pronto |
| Livro de classificação, com carimbo | pronto |
| Snapshot semanal imutável | pronto |
| Escrita com formato antes da escrita | pronto |
| Motor de serviços · motor de mercadorias · Resumo Executivo | entregas 2, 3 e 4 |
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
| [05 — Decisões pendentes](05-decisoes-pendentes.md) | **Fiscal/Tributário** | As 13 perguntas em aberto, cada uma com o padrão assumido |

## A pendência vermelha

[A nº 1](05-decisoes-pendentes.md): **os arquivos reais de uma semana e a saída
que a macro produziu a partir deles.** Sem eles o porte pode ficar completo e
não estar provado — e seis defeitos conhecidos continuam no produto, porque
mexer neles sem medir seria trocar um defeito conhecido por um desconhecido.
