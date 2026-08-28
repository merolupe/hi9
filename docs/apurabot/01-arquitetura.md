# Apurabot — Arquitetura

> Documento técnico. Público: analista desenvolvedor + Gerência Fiscal/Tributária.
> Base: escopo funcional v1.0, fluxograma Apurabot GRC e a conferência contra
> uma apuração real — ver [05 — Achados](05-achados-julho-2026.md).

---

## 1. O problema, em uma frase

Transformar o Livro Fiscal do Sankhya (≈6.500 linhas/mês, 52 colunas) na apuração
de ICMS de 7 estabelecimentos em 4 UFs, com 4 regimes de apuração diferentes,
de forma **reproduzível, auditável e operável por qualquer pessoa do setor**.

## 2. Decisão central: motor em Python, regra em parâmetro, saída em Excel

O documento de escopo sugere Power Query + VBA. **Recomendo não seguir por esse
caminho**, pelos motivos abaixo — e a decisão é reversível, porque a saída
continua sendo um `.xlsx` idêntico ao que o time já usa.

| Critério | Power Query + VBA | Python + parâmetros + Excel |
|---|---|---|
| Versionamento da regra | `.xlsm` é binário: sem diff, sem code review | Texto puro no git: cada mudança de alíquota é um commit revisável |
| Critério de aceite "reproduzir Junho/2026" | Conferência manual a cada alteração | Teste de regressão automático que roda em segundos |
| Manutenção por outro analista | Depende de abrir o editor VBA e ler macro | Código + testes + documentação lado a lado |
| Crescimento de volume | Degrada com fórmulas voláteis | Irrelevante nesta escala |
| Cruzamento com XML das notas | Trabalhoso | Nativo |
| Risco de "caixa-preta" | Alto: regra escondida em fórmula | Baixo: memória de cálculo linha a linha é uma saída obrigatória |

**O que fica igual para o usuário:** ele continua recebendo um `.xlsx` com os
painéis e a memória de cálculo. O Python é o motor, não a interface.

### 2.1. Por que não banco de dados / sistema web (por enquanto)

Volume é pequeno (milhares de linhas), o uso é mensal, o dado é fiscal e
sensível, e um servidor cria dependência de TI e de rede. A ferramenta roda
**local, na máquina do responsável**, sem o dado sair dali. Se um dia houver
integração direta com o Sankhya, o motor não muda — só ganha outra fonte de
entrada.

## 3. Camadas

Cada camada só lê a anterior e nunca escreve nela. Isso é o que garante que
"dado importado", "dado calculado" e "dado ajustado" nunca se misturem — a
exigência central do documento de escopo.

```
  ENTRADA (.xlsx)                       O QUE ACONTECE                      SAÍDA
┌──────────────────┐
│ Livro Fiscal     │──┐
│ (do Fiscalbot)   │  │   1. INGESTÃO      valida layout, congela cópia
├──────────────────┤  │                    bruta, calcula hash do arquivo
│ XML das entradas │──┤
├──────────────────┤  │   2. NORMALIZAÇÃO  tipos, datas, CFOP, UF, filial
│ Base de Bens     │──┘
└──────────────────┘      3. EQUALIZAÇÃO   carga efetiva bruta → carga nominal
                             DE CARGA      (4 / 7 / 12 / 17 / 18 / 20,5)

                          4. CLASSIFICAÇÃO frete-compra, frete-venda, MP,
                                           embalagem, químico, revenda, CIAP,
                                           quebra, devolução, transferência
                                           → sem regra = pendência

                          5. REGRAS        por UF/regime e vigência
                             TRIBUTÁRIAS     + segregação por ATIVIDADE onde a
                                             UF exige (industrial, comercial,
                                             importados, prestacional/outras)

                          6. CÁLCULO       crédito bruto, crédito mantido,
                                           estorno, débito, DIFAL, CIAP, B.F.

                          7. AJUSTES       aplica só ajustes APROVADOS
                             (ajustes.xlsx)

                          8. APURAÇÃO      saldo individual por estabelecimento
                             POR FILIAL

                          9. CENTRALIZAÇÃO consolida o saldo do grupo por UF e
                                           emite a instrução de transferência

                         10. CONCILIAÇÃO   travas de integridade e coerência
                             E AUDITORIA   tributária → pendências
                                                                    ┌──────────────┐
                         11. RELATÓRIOS    Registro de Apuração      │ Apuracao     │
                                           Apuração efetiva          │ AAAA-MM.xlsx │
                                           Transferências a emitir   │              │
                                           Resumo + memória          └──────────────┘
```

### 3.0. A trava que a auditoria valida

Em toda entrada com ICMS vale:

```
crédito mantido + estorno + crédito indevido = crédito bruto
```

O **crédito indevido** fica em parcela própria porque não é estorno: é crédito
que não podia ter sido tomado. Somá-lo ao crédito mantido esconderia o problema
dentro do resultado.

### 3.1. Rastreabilidade obrigatória

Toda linha que sai de qualquer camada carrega, além do valor:

`arquivo_origem` · `linha_origem` · `nro_unico_nota` · `estabelecimento` ·
`cfop` · `cst` · `categoria` · `regra_aplicada` · `vigencia_da_regra` ·
`base` · `aliquota` · `valor_calculado` · `ajuste_aplicado` · `status`

É isso que permite clicar em qualquer número do painel e chegar na nota que o
gerou — o Anexo B do escopo, atendido por construção e não por relatório extra.

## 4. As quatro execuções

O fluxograma prevê quatro comandos. Eles são **independentes e idempotentes**:
rodar duas vezes produz o mesmo resultado.

| Comando | Precisa de | O que faz |
|---|---|---|
| **Rodar Apuração** | Livro Fiscal | Camadas 1–11. É a execução principal. |
| **Rodar DIFAL** | Livro Fiscal + XMLs | Recalcula o DIFAL das compras de itens fora do processo produtivo usando o ICMS **do XML**, não o do Livro. |
| **Rodar CIAP** | Base de Bens | Monta o CIAP: índice = saídas tributadas / total de saídas. _Fora do escopo da primeira entrega._ |
| **Atualizar Ajustes** | `ajustes.xlsx` | Rotula os ajustes manuais e recalcula a apuração sem reimportar nada. |

### 4.1. DIFAL nunca altera o Livro Fiscal

O Livro traz o ICMS em branco nas compras de itens que não entram no processo
produtivo; o valor correto está no XML. A ferramenta **não sobrescreve o Livro**:
grava uma *camada de correção* (`difal_ajustado`) e o **Painel 2** mostra, nota a
nota, o que foi alterado e por quê. Esse é exatamente o "Audit de alteração no
Livro para DIFAL" do fluxograma.

## 5. Onde mora cada coisa

```
apurabot/
├── src/apurabot/
│   ├── ingestao/        leitura e validação de layout dos .xlsx
│   ├── nucleo/          equalização de carga, classificação, cálculo
│   ├── regimes/         sp_equilibrio.py · ms_estorno.py · ms_beneficio_rb.py
│   │                    mt_diferimento.py · pr_diferimento.py
│   ├── centralizacao/   saldos transferíveis e NF-e de Guará
│   ├── auditoria/       travas de integridade e pendências
│   └── saida/           montagem dos 4 painéis em .xlsx
├── parametros/          ← A REGRA TRIBUTÁRIA VIVE AQUI (YAML, versionado)
│   ├── filiais.yaml
│   ├── regimes.yaml
│   ├── cargas.yaml
│   ├── classificacao.yaml
│   └── produtos.yaml    cadastro produto → categoria tributária
├── tests/
│   ├── unidade/         cada regra isolada
│   └── regressao/       Junho e Julho/2026 como referência
└── analise/             scripts que geraram os achados documentados

competencias/            (fora do git)
└── 2026-07/
    ├── entrada/         livro_fiscal.xlsx · xml_entradas.xlsx · base_bens.xlsx
    ├── ajustes.xlsx     ajustes manuais com justificativa e aprovador
    ├── saida/           Apuracao_2026-07.xlsx
    └── execucao.json    versão, data, usuário, hash dos arquivos de entrada
```

### 5.1. Regra é parâmetro, não é código

Nenhuma alíquota, percentual de estorno ou lista de CFOP entra em arquivo `.py`.
Tudo fica em YAML com **vigência**, para que a apuração de um mês antigo continue
reproduzível depois de uma mudança de legislação:

```yaml
# parametros/regimes.yaml (trecho ilustrativo)
sp_equilibrio_fiscal:
  vigencia_inicio: 2025-01-01
  carga_saida_referencia: 4.0
  base_do_estorno: valor_contabil
  isentos_de_estorno: [materia_prima, produto_acabado, revenda,
                       retorno_indl, ciap, devolucao_venda]
```

O time fiscal revisa o YAML (ou uma exportação dele em Excel, se preferir), e o
`git log` responde "quem mudou, quando e por quê" sem controle paralelo.

## 6. Interface para quem opera o fechamento

Uso mensal, por pessoa não técnica. A interface é uma **janela no navegador,
servida pela própria máquina**: dois cliques em `Apurabot.bat`, e a página abre
em `127.0.0.1`.

```
┌─────────────────────────────────────────────────────┐
│  Apurabot — Apuração de ICMS                        │
│                                                     │
│         ┌───────────────────────────────┐           │
│         │   Arraste aqui o Livro Fiscal │           │
│         │   ou clique para escolher     │           │
│         └───────────────────────────────┘           │
│                                                     │
│  ✓ Encerramento liberado — nenhuma pendência        │
│                                                     │
│  [ Baixar a planilha ]  [ Apurar outro livro ]      │
│                                                     │
│  Apuração por estabelecimento · Registro de         │
│  Apuração · Transferências a emitir · Benefício     │
└─────────────────────────────────────────────────────┘
```

### 6.1. Por que o navegador, e não um programa instalado

A máquina do time fiscal é corporativa e **sem elevação de administrador**. Um
executável novo e sem assinatura é barrado pela política de segurança. Já o
Python e o navegador são programas aprovados, e rodam.

Então a interface não vem de um programa novo: o Python abre um servidor em
`127.0.0.1`, numa porta escolhida pelo sistema, e manda o navegador abrir a
página. `Apurabot.bat` é um arquivo de texto, não um binário — o duplo clique
não cria nada na máquina.

O que o desenho garante:

| | |
|---|---|
| **nada é instalado** | nenhum binário novo, nenhum privilégio pedido |
| **o dado não sai da máquina** | o servidor só aceita conexão de `127.0.0.1`; o arquivo enviado vive em pasta temporária e é apagado no encerramento |
| **a página não busca nada fora** | zero CDN, zero fonte externa — funciona com a máquina desconectada; há teste que verifica isso |
| **outra sessão não alcança** | cada janela nasce com uma chave aleatória na URL, e requisição sem ela é recusada |

**Uma solução hospedada foi descartada.** Livro Fiscal, XML e base de bens são
dado fiscal real da empresa; subi-los para servidor fora da máquina contraria a
primeira regra do repositório e o princípio de que o dado não sai dali.

## 7. Como a ferramenta prova que está certa

O critério de aceite do escopo é "reproduzir os resultados de Junho/2026".
Isso vira um teste automático:

1. **Regressão por competência.** Julho/2026 e Junho/2026 entram como fixtures.
   Qualquer alteração no motor que mude um centavo desses meses faz o teste
   falhar e mostrar exatamente qual estabelecimento e qual regra divergiram.
2. **Testes de unidade por regra.** Cada regra da matriz (frete SP×SP 12% estorna
   8%, quebra estorna 100%, MT estorna 100%, etc.) tem seu próprio caso.
3. **Travas de coerência tributária.** Ausência de `#VALOR!` não é prova de nada.
   As travas verificam identidades reais: `crédito mantido + estorno = crédito
   bruto`, `saldo individual = valor transferido + saldo residual`,
   `transferências recebidas em Guará = soma das NF-e emitidas`.
4. **Pendência crítica bloqueia o encerramento.** Documento sem regra,
   NF-e de transferência não emitida ou ajuste não aprovado impedem fechar a
   competência.

## 8. O que esta arquitetura assume

- **Dois layouts de extração são suportados.** O `Movimento Livros Fiscais`
  (66 colunas, padrão a partir de 08/2026, traz o TOP) e a extração antiga da
  apuração (52 colunas). A ingestão procura o cabeçalho nas 10 primeiras linhas
  e valida 14 colunas essenciais, falhando com mensagem clara se faltar alguma.
  Um teste prova que os dois produzem apuração idêntica.
- O Fiscalbot já entregou o Livro com os lançamentos conferidos. O Apurabot
  apura, não corrige lançamento.
- MS/Rio Brilhante entra **agora** (mudança estratégica em relação ao escopo v1.0,
  que previa Fase 3), o que puxa o benefício fiscal e o Termo de Acordo para a
  primeira entrega. Ver `06-decisoes-pendentes.md`.
