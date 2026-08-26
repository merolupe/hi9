# Apurabot — Decisões com a Gerência Fiscal/Tributária

> Registro das decisões tributárias que o motor depende. As **em aberto** trazem
> o comportamento-padrão assumido enquanto não há resposta — nenhuma bloqueia o
> desenvolvimento. As **respondidas** ficam registradas com a decisão, não com o
> caminho até ela; a evidência numérica está em
> [05 — Achados de Julho/2026](05-achados-julho-2026.md).

---

## 1. ✅ Rio Brilhante — o alcance do benefício *(respondida)*

**Termo de Acordo n. 1.190/2018**, firmado em 19/09/2018, publicado no DOE 9.755.
Base legal: LC estadual 93/2001 e Lei 4.049/2011.

**O benefício alcança a atividade industrial**, como diz a leitura literal do
inciso I da cláusula terceira. Está assim na declaração: a dedução no Registro de
Apuração se chama *"Industrialização própria - Incentivo TA/CDI"*, e a base de
saídas incentivadas da GIA - Benefício Fiscal é a dos CFOP de produção própria.

```yaml
alcance:
  criterio: atividade_industrial
  rateio_do_credito: participacao_do_debito
```

O rateio pela participação do débito, que era premissa assumida, também se
confirmou contra a GIA. O regime está `homologado: true`.

**A cláusula quarta continua expirada** desde 31/12/2022: só há 67% e 80%, e só
sobre produção própria. Revenda não recebe crédito presumido.

## 2. ✅ MS — base do estorno proporcional *(respondida)*

MS não usa a mecânica de SP. Eram duas coisas distintas:

**a) A fórmula.** O estorno incide sobre o **valor do ICMS**, aplicando a parcela
não tributada da operação — não sobre o valor contábil, como em SP.

**b) O crédito de transferência é indevido.** A entrada de **CFOP 2152**
(transferência interestadual recebida) não é apropriada nem estornada: fica em
parcela própria, de forma que a identidade auditada passa a ser
`mantido + estorno + indevido = bruto`.

**Ainda em aberto:** o CFOP 2152 gera crédito indevido **sempre**, ou foi
específico de uma transferência? A regra está com `homologado: false`.

## 3. ✅ Os 0,941176% — não existem *(respondida)*

Procurados na apuração consolidada, na individualizada e no Termo de Acordo, não
foram encontrados em nenhum. O número vinha do escopo funcional v1.0 e a origem
não se sustentou.

**Decisão: esquecer.** O parâmetro saiu de `regimes.yaml` — não fica como "não
aplicado", porque não há regra a aplicar.

## 4. ✅ Carga efetiva — régua de valores nominais *(respondida)*

| | Cargas |
|---|---|
| **Homologadas** | 4 · 7 · 12 · 17 · 18 |
| **Toleradas** — advertência, sem bloquear | 19 · 20,5 · 25 |

Os 20,5% não devem constar na base: aparecem em CT-e de frete sobre compra de
insumos e foram aceitos na apuração manual. 19% e 25% não ocorrem nas operações
da Hinove e saíram das homologadas.

A equalização continua reconhecendo as toleradas, para que uma competência
antiga siga reproduzível. Todo documento que cair numa delas recebe o alerta
`CARGA NÃO HOMOLOGADA`, apontando para revisão do lançamento na origem.

## 5. ✅ Qual apuração é a oficial *(respondida)*

**Vale a apuração individualizada por estabelecimento.** A consolidada foi
montada no molde do equilíbrio fiscal de SP e não reflete a mecânica das outras
UFs. Onde as duas divergem, a individualizada é a correta.

A consolidada continua útil como referência de totais, mas não é a fonte da
verdade. Onde houver declaração retificadora, é ela que vale.

## 6. ✅ Saldo credor do período anterior *(respondida)*

Informado uma primeira vez e, a partir daí, puxado do que ficou apurado na
competência anterior. Sobrescrever manualmente continua possível, mas passa a ser
exceção registrada, não rotina.

**A implementar** junto com o encerramento de competência (Entrega 6) — é ele que
grava o saldo que a competência seguinte vai ler.

**Segue em aberto:** MICROBIO e HINOVE FERTILIZANTES ESPECIAIS entram no escopo
do Apurabot ou continuam controle à parte?

## 7. 🟡 PR — mantém 100% ou não credita?

*Pontos de Atenção* diz "Créditos PR mantêm 100% s/ saídas diferidas", e a aba
ESTORNO mostra Londrina com crédito de frete marcado como mantido — mas o
totalizador da mesma aba zera o crédito mantido de Londrina, e no resultado final
PR aparece só com o saldo credor anterior.

**Pergunta:** o crédito de PR é mantido e acumulado como saldo credor, ou é
estornado?

**Padrão assumido:** mantido e acumulado, conforme *Pontos de Atenção*.

## 8. 🟢 Itens fora do processo produtivo para o DIFAL

O DIFAL usa o ICMS **do XML** nas compras de itens que não integram o processo
produtivo.

**Pergunta:** qual é o critério de "não integra o processo produtivo" — CFOP
(1556/2556 uso e consumo), grupo do produto (prefixo do código), ou lista
mantida à parte?

**Padrão assumido:** CFOP de uso e consumo + ativo, parametrizado em
`classificacao.yaml` e ajustável sem alterar código.

## 9. 🟢 Layout dos arquivos de XML e Base de Bens

O Livro Fiscal já está mapeado (ver `03-dicionario-livro-fiscal.md`).
**Faltam exemplos reais** dos outros dois arquivos de entrada. Sem eles, DIFAL e
CIAP ficam no desenho, não na construção.

**Pedido:** enviar um `.xlsx` de exemplo de cada — XML das entradas e Base de Bens.

## 10. 🟢 Aprovação de ajustes manuais

O escopo exige que só ajustes com status **Aprovado** alimentem a apuração, com
responsável e aprovador.

**Pergunta:** quem aprova, e a mesma pessoa pode lançar e aprovar? A ferramenta
deve apenas registrar, ou bloquear o fechamento quando lançador = aprovador?

**Padrão assumido:** registra os dois nomes, permite que sejam a mesma pessoa e
sinaliza no painel de auditoria — sem bloquear.

## 11. ✅ Complemento de ICMS — é regra *(respondida)*

**É regra, não acaso.** O complemento de ICMS acompanha a situação da nota
complementada, mesma lógica do complemento de preço (item 13). A carga aplicada é
a da nota que ele complementa, e a referência está na coluna `Observação` do
extrato.

**O crédito é apropriável.** O parâmetro está `homologado: true` e essas linhas
não geram alerta.

## 12. ✅ NBPT BLUE 20% — produto químico *(respondida)*

Tratado como **crédito comum sujeito a estorno**, e não como revenda com crédito
integral. Confirma `produto_quimico` — ver o critério no item 16 e em
`04-matriz-de-regras-icms.md`, item 2.1.

## 13. ✅ Complemento de preço — acompanha a nota complementada *(respondida)*

O complemento de preço acompanha a situação da nota que ele complementa. Saída de
matéria-prima, por exemplo, vai a 4%.

Na prática o documento já resolve sozinho: ele sai com a base reduzida da
operação original, então a carga calculada é a da nota complementada. A ligação
com a nota original está na **observação** do documento (*"COMPLEMENTO DE PREÇO
REFERENTE A NF ..."*), e é por ela que a memória de cálculo aponta para ela.

## 14. 🟢 A tolerância da equalização está frouxa

A tolerância é de **2,5 pontos** e o maior vão entre degraus da régua é de 5
pontos (7→12 e 12→17), ou seja, exatamente o dobro. Na prática, qualquer carga
entre ~1,5% e ~27,5% encaixa em algum degrau e nada é sinalizado.

**Pergunta:** apertar a tolerância para 1,5 ponto? Isso passaria a sinalizar
cargas a mais de 1,5 ponto de qualquer degrau, sem bloquear o fechamento.

**Padrão assumido:** manter 2,5 até haver decisão — apertar sem combinar geraria
pendências novas no primeiro fechamento.

## 15. ✅ Arredondamento da parcela não tributada *(respondida)*

**Tanto faz.** Mantidos os percentuais **arredondados em quatro casas**, que são
os que a apuração usa.

A parcela é fórmula (`1 − carga_de_referencia / alíquota`), então o arredondamento
é um parâmetro só: `casas_decimais_da_parcela: 4`. Pôr `null` usa a fração exata.

## 16. ✅ A TOP — extração e classificação *(respondida)*

**A extração com TOP é o padrão mensal.** O extrato `Movimento Livros Fiscais` é
lido pelo motor, e um teste prova que ele produz apuração idêntica à extração
antiga. Ele traz ainda a `Observação` (que liga o complemento de preço à nota
complementada), as colunas de DIFAL e os documentos cancelados que a extração
antiga filtrava.

**A TOP não classifica.** Onde a TOP e a categoria do produto divergem, **vale a
categoria** — a classificação do motor está certa nesses casos.

E a divergência não é contradição:

- Uma entrada lançada como **"Compra de MP"** pode ser `produto_quimico`. Produto
  químico também é matéria-prima; o que separa os dois é o **enquadramento**.
  Matéria-prima, no sentido que importa aqui, é só a que se enquadra no artigo de
  equalização da carga a 4%. Algumas não se enquadram — por estarem fora do
  escopo do artigo, ou porque o fornecedor não tem registro no MAPA para
  vendê-las como enquadradas.
- Uma entrada lançada como **"Compra com Moeda Importação"** pode ser `revenda`,
  quando a finalidade da importação era revender. A TOP nomeia a moeda; a
  categoria nomeia a finalidade.

A TOP continua sendo lida, viaja na base tratada e serve para conferência.

O critério completo está em `04-matriz-de-regras-icms.md`, item 2, e os produtos
em `parametros/produtos.yaml`.

## 17. ✅ FADEFE / Pró-Desenvolve *(respondida)*

A cláusula terceira, parágrafo primeiro, do Termo condiciona a fruição a uma
contribuição mensal ao **Fundo de Apoio ao Desenvolvimento Econômico e de
Equilíbrio Fiscal do Estado**, sobre o benefício efetivamente utilizado.

- **Contribuição ao Pró-Desenvolve / FADEFE Desenvolvimento Econômico / FAI: 2%**
  sobre o benefício fruído.
- **Adicional FADEFE Equilíbrio Fiscal: 0%** — existe como campo próprio na GIA e
  hoje está zerado.
- **É guia avulsa**, calculada na própria GIA. **Não entra na conta gráfica** da
  apuração de ICMS.

Os dois percentuais são parâmetro com vigência, e o valor sai numa seção própria
do relatório.

## 18. 🟡 Corumbá — a segregação por atividade não tem documento

O mapa de atividades foi homologado contra os documentos de **Rio Brilhante**.
Corumbá usa o mesmo mapa, porque a UF é a mesma e a GIA de MS é a mesma — mas não
há GIA de Corumbá para conferir a segregação dela.

**Pergunta:** Corumbá também declara GIA segregada por atividade? Se sim, é
possível enviar uma para fechar a homologação?

**Padrão assumido:** aplicar o mesmo mapa e marcar como não conferido.

## 19. 🟡 MS tem centralização, e ela não está no motor

O Registro de Apuração de Rio Brilhante traz, em Outros Débitos, o *"Recebimento
de saldo devedor - estabelecimento centralizador"*. Ou seja: **Rio Brilhante
recebe saldo devedor de outro estabelecimento de MS.** Até aqui, o projeto tinha
centralização modelada apenas em SP, com Guará.

**Perguntas:** quem transfere para RB — Corumbá? A regra é a mesma de SP? Existe
ato formal de centralização em MS?

**Padrão assumido:** o valor entra como ajuste manual, na atividade
Prestacional/Outras, sem regra de centralização automática. A Entrega 4 trata
centralização e vai precisar dessa resposta.

## 20. 🟡 Enquadramento: é do produto ou do fornecedor?

O item 16 fixou que matéria-prima não enquadrada é `produto_quimico`, e que o não
enquadramento vem do produto **ou** do fornecedor. Para cada item hoje cadastrado
como produto químico, falta saber **qual dos dois motivos** se aplica.

A diferença é prática: se o motivo é o produto, a categoria vale sempre; se é o
fornecedor, o mesmo produto comprado de um fabricante de fertilizante enquadrado
volta a ser `materia_prima`. Já se observou o mesmo fornecedor vendendo item
enquadrado e item não enquadrado, então não dá para decidir pelo fornecedor
sozinho.

**Pergunta:** para cada produto químico do cadastro, o não enquadramento é do
produto ou do fornecedor?

**Padrão assumido:** cadastro por produto. O cadastro já aceita a chave por
produto + fornecedor, então mudar é editar o parâmetro, não o código.
