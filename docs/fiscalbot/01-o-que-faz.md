# Fiscalbot — auditoria do Livro Fiscal de ICMS

> Público: time Fiscal/Tributário. Antecessor: o módulo VBA `modFiscalbot`
> v3.2, que rodava dentro de `Base_Fiscalbot.xlsm`.

---

## 1. Para que serve

Conferir, registro a registro, se o lançamento do Livro Fiscal está enquadrado
como deveria. Entra o relatório *Movimento Livros Fiscais* extraído do Sankhya;
sai o mesmo relatório com nove colunas de auditoria e duas abas novas.

**É o fornecedor do Livro Fiscal validado que o Apurabot consome.** O que passa
por aqui como `Conforme` é o que a apuração de ICMS trata como bom.

Cada registro sai com um de três veredictos:

| Status | O que quer dizer |
|---|---|
| **Conforme** | O enquadramento bate com a regra que identifica a operação |
| **Advertência** | Alguma das seis dimensões diverge do esperado |
| **Validação manual** | Nenhuma regra identificou a operação, ou a regra pediu conferência humana |

## 2. As seis dimensões

Quando uma regra identifica o registro, seis coisas são conferidas. Cada uma
tem coluna própria na saída, para a divergência ser filtrável:

| Coluna | O que confere |
|---|---|
| `! CST` | o código de situação tributária esperado |
| `! Valor ICMS` | se há ICMS onde deveria haver, e zero onde não deveria |
| `! Produto` | se o produto pertence ao grupo que a regra exige |
| `! Aliquota` | a alíquota, por lista ou pela matriz origem × destino |
| `! Carga Efetiva` | `ICMS ÷ valor contábil`, dentro da tolerância |
| `! Outros` | parceiro, e as coerências da Camada 0 |

## 3. A ordem em que o motor decide

A ordem importa mais que as regras, porque três camadas passam por cima de tudo:

```
  1. CANCELADA          Origem = "Cancelada" → Conforme, e encerra.
                        Nota cancelada não se audita.

  2. FRETE SIMPLES      CT-e de parceiro na lista do SN → espera CST 90.
     NACIONAL           Sobrepõe qualquer regra de CFOP.

  3. CAVACO             Compra de MP (CFOP 1101/2101) de parceiro da lista:
                        intra → CST 51 e ICMS zero
                        inter → CST 00 e alíquota 7 ou 12

  4. IDENTIFICAÇÃO      Confronta com as regras ativas. Espera-se que
     (MECE)             exatamente uma case.
                          nenhuma casou, e é CT-e → "Frete nao mapeado"
                          nenhuma casou, e é NF   → Validação manual
                          mais de uma casou       → AMBIGUA (a base está errada)

  5. AS SEIS DIMENSÕES  Para a regra que casou.

  6. CAMADA 0           A rede embaixo de tudo, inclusive de registro sem
                        regra nenhuma:
                          regra A — CST que exige ICMS > 0 tem que ter ICMS;
                                    os demais CST exigem ICMS = 0
                          regra B — o 1º dígito do CFOP tem que combinar
                                    com a operação ser INTRA ou INTER

  7. CAMADA Ind         Produto cuja descrição começa com "Ind." só circula
                        em CFOP 1124/1125 (intra) ou 2124/2125 (inter).
```

A Camada 0 **não fala onde a regra já falou** — é o que evita contar a mesma
divergência duas vezes.

## 4. Como se escreve uma regra

Uma regra tem duas metades: a que **identifica** a operação e a que diz o que
se **espera** dela. Tudo é avaliado em `AND`.

### Identificação

| Campo | Sintaxe | Significado |
|---|---|---|
| E/S | `Entrada` / `Saida` | compara só a primeira letra |
| Espécie | `NF` / `CT` | vazio vale para as duas |
| CFOP | `1602;2602` | o CFOP tem que estar na lista |
| Cond. produto | `701000701` | código exato |
| | `INICIA:7010` | começa com — **diferencia maiúscula** |
| | `NAOINICIA:7010` | não começa com |
| | `TABELA:FRETE` | está na lista nomeada |
| | `TABELAEXCETO:FRETE:700000001,700000002` | está na lista, menos estes |
| Cond. UF | `SPxSP;MTxMT` | par origem × destino na lista |
| | `INTRA` / `INTER` | mesma UF / UF diferente |
| | `UFORIG:BA;PR` | UF de origem na lista, destino livre |
| | `NAOUFORIG:SC` | UF de origem fora da lista |
| | `NAOPARUF:SPxSP` | par fora da lista |
| Cond. parceiro | `INICIA:econet` | nome do parceiro começa com — ignora caixa |
| | `NAOINICIA:econet` | não começa com |

### O que se espera

| Campo | Sintaxe | Significado |
|---|---|---|
| CST esperado | `60` | tem que ser exatamente este |
| | `EM:00,20` | tem que estar entre estes |
| | `NAOEM:41,50` | não pode estar entre estes |
| ICMS esperado | `0` / `>0` | valor exato / tem que ser positivo |
| | `CARGA` | quem confere o ICMS é a carga efetiva |
| Alíquota | `7;12` | tem que ser uma destas |
| | `TABELAUF` | a esperada vem da matriz origem × destino |
| Carga % | `4` | carga efetiva alvo, dentro da tolerância |
| Outros | `PARCEIRO<20` | código do parceiro menor que 20 |
| | `PARCEIROINICIA:HINOVE` | nome do parceiro começa com |
| | `SEMPRE:texto` | advertência incondicional, com este texto |
| | `SECST:20:texto` | se o CST observado for 20, manda para validação manual |

> **Uma pegadinha herdada:** `EM:` e `NAOEM:` separam por **vírgula**. Todo o
> resto separa por **ponto e vírgula**. É assim desde o VBA, e mudar
> reclassificaria registros de meses fechados.

## 5. Onde as regras moram

**Não no git.** As regras são cadastradas na tela do Fiscalbot, dentro da
Central, e ficam em `dados/fiscalbot/base.yaml` — pasta ignorada, como
`competencias/`. Quem edita é o time fiscal, sem passar por commit.

O que **é** versionado é a **carga de fábrica**
(`fiscalbot/regras_de_fabrica.yaml`): as 64 regras, os parâmetros e a matriz de
alíquotas, sem nenhum dado da empresa. Ela existe para a ferramenta abrir
funcionando numa máquina nova — sem ela o Fiscalbot nasceria sem regra nenhuma.

**As listas de parceiros não vêm na carga de fábrica**, porque trazem código e
nome de fornecedor real. Numa máquina nova elas nascem vazias e precisam ser
cadastradas na tela. Enquanto isso não for feito, as camadas de frete SN e de
cavaco não rodam — e a tela avisa.

| Conteúdo | Vai para o git? | Por quê |
|---|---|---|
| Regras, parâmetros, matriz de alíquotas | Sim, como carga de fábrica | Regra tributária, acompanha legislação |
| A base viva, já editada | Não | É do aplicativo, e o time altera sem commit |
| Listas de parceiros | **Nunca** | Código e nome de fornecedor real |
| Relatório auditado | **Nunca** | Dado fiscal da empresa |

A trilha de quem alterou o quê fica dentro do aplicativo: a base carimba
**quem gravou e quando** a cada salvamento. É o que substitui o histórico que
o git daria.

## 6. O que a tela confere antes de gravar

No Excel, regra mal escrita só aparecia quando o relatório rodava — e aparecia
como registro não mapeado, que é o sintoma errado para a causa. A tela confere
na hora:

**Impedem a gravação:** ID repetido; duas regras ativas que identificam
exatamente os mesmos registros (é o que faria a auditoria marcar `AMBIGUA`);
operador que o motor não conhece; tabela de produto citada e inexistente;
`TABELAUF` com a matriz vazia; base sem nenhuma regra ativa.

**Avisam, mas gravam:** regra ativa sem CFOP (nunca vai casar); CFOP vazio no
meio da lista; CST esperado sem dois dígitos; lista de parceiros vazia.

## 7. Como se usa

**Dois cliques em `Hinove.bat`** → botão **Fiscalbot** → arraste o relatório →
baixe a planilha auditada. Para cadastrar regra, o botão **⚙ Regras e
parâmetros** na mesma tela.

Pelo terminal:

```
python rodar.py fiscalbot "caminho\do\Movimento_Livros_Fiscais.xls" --saida "pasta"
```

## 8. O que sai

Um `.xlsx` com duas abas. O arquivo de entrada **não é tocado** — diferente da
macro, que gravava a auditoria dentro dele.

* **`Relatório`** — 25 colunas na ordem de conferência (identificação do
  documento, veredicto, as seis ocorrências, o que explica o enquadramento e
  por fim os valores), e atrás as demais colunas do relatório original, na
  ordem em que vieram. A carga efetiva é **fórmula**, não valor gravado: quem
  confere quer ver a conta e poder simular.
* **`Resumo`** — os três números, a contagem por dimensão e o que ficou para
  validação manual, por operação.
