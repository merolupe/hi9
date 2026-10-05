# KPI Semanal — gerador dos slides

Monta o slide **Faturamento x Meta** da reunião semanal a partir dos quatro
números da semana. O formato visual está congelado em
[`PADRAO-FATURAMENTO.md`](PADRAO-FATURAMENTO.md).

## O que entra e o que sai

| Arquivo | Onde fica | Versionado? |
|---|---|---|
| `gerar_faturamento.py` | `kpi/` | sim — é código |
| Padrão visual | `kpi/PADRAO-FATURAMENTO.md` | sim |
| Deck modelo (semana anterior) | `competencias/kpi/modelo.pptx` | **não** |
| Série acumulada | `competencias/kpi/faturamento.json` | **não** |
| Deck gerado | `competencias/kpi/` | **não** |

Modelo, histórico e saída carregam faturamento real da Hinove, então ficam em
`competencias/`, fora do git (regra 1 do `CLAUDE.md`).

## Rodando

```bash
python3 kpi/gerar_faturamento.py \
    --base      competencias/kpi/modelo.pptx \
    --historico competencias/kpi/faturamento.json \
    --saida     "competencias/kpi/REUNIAO_SEMANAL_-_S42_2026.pptx" \
    --semana 41 --capa 42 \
    --orc-acum 1.120.431,0 --real-acum 942.118,3 \
    --orc-sem     41.827,8 --real-sem    11.262,7
```

Tudo em **R$ mil**, no formato da planilha (ponto de milhar, vírgula decimal).
Depois de gerar, o deck novo vira o `modelo.pptx` da semana seguinte.

### Fechamento de trimestre

A coluna de fechamento não tem valor semanal — basta omitir as duas flags:

```bash
... --semana 4ºQ --orc-acum 1.412.908,0 --real-acum 1.030.774,2
```

A célula sai com `–` em cinza, e o atingimento do trimestre passa a ser medido
nessa coluna (congela ali, não acompanha mais o acumulado corrente).

### Metas

`--meta-3q` e `--meta-anual` só precisam ser passadas quando mudarem; o valor
fica guardado no histórico.

## O que o script calcula sozinho

Atingimento e déficit (acumulado e semanal), valores em `R$ … mi` / `R$ … Bi`,
a cor de cada célula da linha *Realizado Semanal* (vermelho abaixo da meta,
amarelo a partir de 95%), a largura das colunas, o tamanho da fonte da tabela,
o teto do eixo do gráfico e a posição do destaque tracejado.

Nenhum percentual é digitado à mão — só os quatro números da semana.

## Corrigindo uma semana já lançada

É só rodar de novo com o mesmo `--semana`: a coluna é sobrescrita no lugar,
sem duplicar.

## Dependências

Só a biblioteca padrão do Python. O `openpyxl` do `vendor/` é usado para
reescrever a planilha embutida do gráfico (a que o PowerPoint abre em
"Editar dados"); sem ele o slide sai igual, só a planilha fica desatualizada.
