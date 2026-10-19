---
name: kpi-semanal
description: Monta e atualiza os slides da reunião semanal do time Fiscal da Hinove — Faturamento x Meta, Agendamentos (faturamento próprio, recebimento e 3ºs) e Monitoramento das Entradas Pendentes. Use sempre que a conversa trouxer números ou prints de uma semana do KPI, o deck REUNIAO_SEMANAL, um pedido tipo "faz a semana 42", "atualiza o slide de faturamento", "me devolve o de agendamentos", um ponto de atenção para registrar, ou ajuste visual nesses slides — mesmo que a pessoa só cole a tabela ou a imagem do painel sem dizer o que fazer com ela.
---

# KPI semanal — Fiscal/Faturamento/Tributário

O time apresenta os indicadores toda semana, sobre a semana que fechou.

**O `Snn` que aparece no deck é sempre a semana dos dados**, não a da reunião:
a capa do S41 diz `KPI SEMANAL – S41 (13/10)` e 13/10 cai na semana 42. Então
o número é o mesmo na capa, nos cartões, nos subtítulos e na última coluna da
tabela; só a data entre parênteses na capa anda uma semana à frente. Fazer a
semana 42 é trocar todo `41` por `42` e a data para a terça seguinte.

## O deck é o estado — não há nada guardado aqui

O container é efêmero e `competencias/` é ignorada pelo git (regra 1: dado
fiscal nunca é versionado). **O arquivo que a pessoa anexa é a única fonte
de verdade**: ele carrega o histórico da série, o layout, as cores e os
ajustes manuais que o time fez na semana anterior.

Daí três consequências que valem mais que qualquer instrução de formatação:

- **Nunca reconstrua um slide do zero.** O cabeçalho, o rodapé e a marca saem
  de imagens que só existem dentro do deck. Edite o que veio.
- **Leia o que mudou antes de escrever.** Entre uma semana e outra o time
  move caixa, troca texto, apaga faixa, põe rótulo no gráfico. Compare o
  arquivo recebido com o que você entregou da última vez e **preserve tudo**:
  esses ajustes são decisão deles, não ruído. Se não tiver o arquivo anterior,
  derive do próprio deck — ele é o padrão atual.
- **Se o deck não vier, peça.** Não dá para começar sem ele. Peça junto com
  um resumo dos números que você já extraiu, para a pessoa não repetir nada.

## O que chega e o que sai

Chega um print da planilha ou do painel, às vezes só uma linha de números.
Sai o deck atualizado, ou só os slides pedidos. Leia o pedido ao pé da letra:
"somente o slide de faturamento" quer dizer um arquivo com aquele slide
apenas — `Pacote.so_estes_slides()` e depois o `clean.py` da skill de pptx.

Números chegam no formato da planilha: `1.078.603,2`. `ler_numero()` aceita
os dois formatos e `br()` devolve nesse. Nunca digite percentual pronto —
calcule a partir dos números crus, é onde erro de conta aparece.

## Como editar

Carregue `scripts/pptx_cirurgia.py`. Ele resolve o que se repete toda semana:
abrir o pacote, achar a forma, trocar texto sem perder formatação, acrescentar
ponto no gráfico, reescrever a planilha embutida, alinhar a linha TOTAL com as
categorias.

```python
import sys; sys.path.insert(0, '.claude/skills/kpi-semanal/scripts')
from pptx_cirurgia import *

with Pacote('deck.pptx') as p:
    slide = p.slide_com('Faturamento x Meta')
    x = p.ler(slide)
    x = set_texto(x, 0.74, 0.05, 'Semana 42 · Out/26', par=1)
    p.grava(slide, x)
    graf = p.grafico_do(slide)
    append_ponto(p, graf, '42', [973083.5, 1148975.4])
    p.salvar('saida.pptx')
```

**Formas são localizadas pela posição, não pelo id.** O PowerPoint renumera
ids e arquivos de gráfico a cada salvamento — `chart1` não é sempre o mesmo
gráfico. Posição ele preserva. Os mapas de coordenadas de cada slide estão nas
referências abaixo; confira contra o arquivo recebido antes de confiar neles,
porque o time move caixa.

Para o slide de Faturamento existe um gerador fechado, `kpi/gerar_faturamento.py`,
que refaz tabela, cartões, gráfico e destaque a partir dos quatro números.
Use quando a semana for rotina. Quando o pedido tiver ajuste visual junto,
edite cirurgicamente — é mais rápido que torcer o gerador.

## Referências por slide

Leia a do slide que você vai mexer — cada uma traz o mapa de coordenadas, as
regras de cor e as fórmulas dos cartões:

- `references/faturamento.md` — Faturamento x Meta (e `kpi/PADRAO-FATURAMENTO.md`,
  que é o padrão visual congelado desse slide)
- `references/agendamentos.md` — Agendamentos de Faturamento e Recebimento
- `references/pendentes.md` — Monitoramento das Entradas Pendentes

A paleta e as convenções que valem para os três estão em
`references/visual.md`. Leia antes de criar qualquer elemento novo.

## Armadilhas que já custaram retrabalho

**Valor acima do topo do eixo some.** Quando uma série passa do `c:max`, a
linha sai cortada e o rótulo desaparece sem aviso. Rode `teto_do_eixo()` com
o maior valor da semana toda vez que acrescentar ponto.

**Coluna nova aperta a tabela.** Mais uma semana significa coluna mais estreita;
valores de 11 dígitos quebram linha. Reduza o corpo da fonte e confira no
render — nunca no XML.

**A planilha de origem às vezes não fecha.** Já veio total que não bate com a
soma das categorias e orçado semanal repetido em vez do delta do acumulado.
Confira a aritmética, use o que fecha e **diga qual divergência encontrou** —
não corrija em silêncio.

**Ponto de atenção da semana passada envelhece.** Sem ponto novo, limpe a
faixa em vez de deixar o texto anterior. O time preenche na hora.

## Conferir antes de entregar

Sempre, sem exceção — é barato e pega o que a leitura do XML não pega:

```bash
python <skill-pptx>/scripts/office/validate.py saida.pptx --original base.pptx
python <skill-pptx>/scripts/office/soffice.py --headless --convert-to pdf saida.pptx
pdftoppm -jpeg -r 110 saida.pdf pag
```

Depois **olhe a imagem**. Texto estourando caixa, rótulo cortado, número
quebrando em duas linhas, caixa encavalando outra — nada disso aparece no XML.

Se o `soffice` reclamar que não consegue carregar o arquivo, falta o módulo de
apresentação: `apt-get update -qq && apt-get install -y libreoffice-impress
poppler-utils`. É o ambiente, não o deck.

## Ao responder

Resuma o que mudou em números, não em processo. A pessoa quer conferir se os
valores estão certos, não saber como você editou o XML. Liste o que você
assumiu e qualquer divergência encontrada na origem — é o que ela precisa
corrigir antes da reunião.
