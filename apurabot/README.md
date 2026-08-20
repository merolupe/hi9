# Apurabot

Apuração mensal de ICMS da **Hinove Agrociência S.A.** a partir do Livro Fiscal
extraído do Sankhya e validado pelo Fiscalbot.

> **Situação: em planejamento.** O mapeamento técnico está concluído; o motor
> ainda não foi construído. Ver [plano de execução](../docs/apurabot/02-plano-de-execucao.md).

## O que faz

Lê o Livro Fiscal do mês, equaliza a carga efetiva de cada nota, classifica a
operação, aplica a regra tributária de cada UF, calcula créditos, débitos,
estornos, DIFAL, CIAP e o benefício fiscal de Rio Brilhante, centraliza os
saldos paulistas em Guará e entrega quatro painéis com a memória de cálculo
aberta.

| Painel | Conteúdo |
|---|---|
| 1 | Apuração por unidade |
| 2 | Auditoria das alterações no Livro para o DIFAL |
| 3 | Confecção do CIAP |
| 4 | Resumo e memória de cálculo |

## Estrutura

```
parametros/     A regra tributária. Editável e versionada — não é código.
  filiais.yaml         estabelecimentos, regimes e centralização
  regimes.yaml         SP equilíbrio · MS estorno + B.F. · MT/PR diferimento
  cargas.yaml          equalização da carga efetiva e tabelas de fertilizantes
  classificacao.yaml   como cada operação é classificada
  produtos.yaml        cadastro produto → categoria tributária

analise/        Scripts exploratórios. Reproduzem os números documentados.
src/            Motor. (a construir)
tests/          Regressão por competência + testes por regra. (a construir)
```

## Regimes por UF

| UF | Regime |
|---|---|
| SP | Equilíbrio fiscal — mantém até 4%, estorna o excedente, centraliza em Guará |
| MS | Estorno proporcional + crédito presumido em Rio Brilhante (Termo de Acordo) |
| MT | Diferimento — estorna 100% |
| PR | Diferimento — mantém 100% |

## Dados fiscais ficam fora do repositório

Livro Fiscal, XMLs, base de bens e apurações vivem em `competencias/AAAA-MM/`,
ignorada pelo git. O repositório guarda código, regra e documentação.
