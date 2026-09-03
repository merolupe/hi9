# Apurabot — como rodar

Windows, máquina corporativa, sem elevação de administrador.

> Vai **testar** a ferramenta pela primeira vez? Siga o
> [08 — Roteiro de teste](08-roteiro-de-teste.md): são nove testes com o
> resultado esperado de cada um.

---

## 1. Requisitos

**Python 3.10 ou mais novo.** Confira com `python --version`.

Se precisar instalar, baixe em [python.org/downloads](https://www.python.org/downloads/)
e **marque "Add Python to PATH"** na primeira tela. É a causa mais comum de tudo
falhar depois, e o erro que aparece não indica isso.

> `python --version` abrindo a Microsoft Store é o atalho falso que o Windows
> instala de fábrica. Instale pelo site e o problema some.

---

## 2. Baixar

<https://github.com/merolupe/hi9> → **`Code`** → **`Download ZIP`** → extrair.

Pega o `main`. Deixe a pasta onde extraiu — não precisa mover para lugar nenhum.

Quem usa Git: `git clone https://github.com/merolupe/hi9.git`

---

## 3. Preparar

Nada. Não há passo de instalação.

As bibliotecas de que o Apurabot depende **viajam junto com o código**, em
`apurabot/src/apurabot/vendor`. Baixar a pasta é instalar.

> Isto mudou depois de o `pip install` falhar duas vezes na máquina real — uma
> barrado pela política de segurança, outra acertando um Python diferente do que
> a ferramenta abre. Nas duas a pessoa tinha feito tudo certo. O passo que mais
> falhava era o que menos precisava existir.

Só é preciso ter **Python 3.10 ou mais novo** na máquina. Para conferir se o
seu serve, sem abrir a ferramenta:

```
python verificar.py
```

Responde `OK` e o caminho do Python, ou diz exatamente o que falta.

---

## 4. Usar

**Dois cliques em `Apurabot.bat`.**

Abre uma janela preta — deixe-a aberta, é o Apurabot rodando — e o navegador
abre sozinho na página da ferramenta.

Na página:

1. **arraste o Livro Fiscal** para a área tracejada, ou clique para escolher.
   Qualquer arquivo, de qualquer pasta: não existe nome nem estrutura de pasta
   obrigatória;
2. espere alguns segundos;
3. o resultado aparece na tela — apuração por estabelecimento, Registro de
   Apuração, transferências a emitir, memória do benefício e as pendências, se
   houver;
4. **Baixar a planilha** salva o `.xlsx` completo em Downloads.

Para fechar: o botão **Encerrar** no rodapé da página, ou feche a janela preta.

O Apurabot lê os dois formatos de extração do Sankhya — o **Movimento Livros
Fiscais**, que é o padrão, e a extração antiga da apuração — e reconhece qual é
sozinho.

### O que a janela garante

| | |
|---|---|
| **nada é instalado** | `Apurabot.bat` é arquivo de texto, não programa; nenhum binário novo é criado |
| **o dado não sai da máquina** | o servidor só aceita conexão de `127.0.0.1`; o arquivo que você arrasta vive em pasta temporária e some no encerramento |
| **funciona sem internet** | a página não busca nada fora da máquina |
| **outra sessão não alcança** | cada janela nasce com uma chave própria no endereço |

### Pelo terminal, se preferir

O caminho antigo continua valendo, e é o que serve para automatizar:

```
python rodar.py apurar "caminho\do\livro.xls" --saida "pasta\de\saida"
python rodar.py base-tratada "caminho\do\livro.xls" --saida "pasta\de\saida"
```

Aspas são obrigatórias em caminho com espaço. `Shift` + botão direito no arquivo
→ **"Copiar como caminho"** copia já com elas. A pasta de `--saida` precisa
existir.

`base-tratada` para no tratamento e na classificação, sem apurar — serve para
conferir o Livro antes de fechar o mês.

> Os arquivos da competência não vão para o Git. O `.gitignore` exclui
> `competencias/` de propósito: nenhum dado fiscal da empresa é versionado.

---

## 5. O que sai

Um `.xlsx`, com as abas na ordem da conclusão para o detalhe:

| Aba | Conteúdo |
|---|---|
| **RESUMO** | Procedência do arquivo, período que o livro cobre, volume, equalização e categorias |
| **REGISTRO** | Espelho do Registro de Apuração: entradas e saídas por CFOP, resumo em 14 linhas, um bloco por estabelecimento e o totalizador do grupo |
| **AJUSTES** | Formulário: as parcelas sem documento e a conferência de cada estabelecimento |
| **APURAÇÃO EFETIVA** | Crédito, estorno e apropriação por CFOP → carga efetiva → produto, com a operação, o % da regra, o % efetivo e o CHECK |
| **APURAÇÃO POR FILIAL** | Crédito, estorno, débito e saldo por estabelecimento; segregação por atividade, memória do benefício e FADEFE |
| **TRANSFERÊNCIAS** | O que transferir para a centralizadora depois de fechar a competência |
| **PENDÊNCIAS** | O que bloqueia o encerramento — as mesmas que a tela mostra |
| **POR ESTABELECIMENTO E CARGA** | O recorte por carga efetiva |
| **BASE TRATADA** | Uma linha por linha do Livro — o extrato inteiro, a regra aplicada e as colunas de ajuste |

Três delas respondem a perguntas diferentes sobre o mesmo mês:

**REGISTRO** — *quanto deu?* É o espelho do livro, conferível contra o PDF que o
ERP emite. Diferente do PDF, sai num arquivo só e com totalizador do grupo.
Linhas do resumo marcadas `AGUARDA AJUSTE` dependem de lançamento aprovado que
não nasce do Livro Fiscal.

**APURAÇÃO EFETIVA** — *por que deu isso?* Uma linha por produto, como na
apuração manual: não é o Livro repetido, é o Livro somado. A coluna **CHECK** é
`a estornar + a apropriar − ICMS creditado`: qualquer valor diferente de zero,
em vermelho, é erro do motor.

A terceira coluna muda de nome conforme o regime, porque cada um tem a sua
chave: **Alíquota** em MS, onde o estorno é `1 − 4/alíquota`; **Carga efetiva**
em SP, onde é o excedente sobre a carga de saída. Ver
[04 — Matriz de regras](04-matriz-de-regras-icms.md), item 3.1.

**BASE TRATADA** — *o que o motor leu?* Uma linha por linha do Livro, com carga
efetiva, categoria, regime e a regra aplicada, em texto.

### Os ajustes, e como devolver o arquivo

As linhas **002, 003, 006 e 007** do Registro não vêm de documento: são
decisões da apuração. Enquanto ninguém as declarar, o `REGISTRO` mostra
`AGUARDA AJUSTE` — o total sai, mas não é o final.

Declarar é preencher e **devolver o mesmo arquivo**:

```
1. rode o Livro Fiscal              → sai o Apuracao_AAAA-MM.xlsx
2. preencha os ajustes nesse arquivo
3. arraste o próprio arquivo de volta na janela
4. sai um novo .xlsx, com o registro fechado
```

Não precisa do Livro original na volta: a `BASE TRATADA` leva o extrato inteiro
dentro, com todas as colunas do Sankhya. É um arquivo só, ida e volta.

**Onde preencher depende de o ajuste ter documento.**

*Tem documento* — "esta nota foi lançada errada", "esta entrada não devia ter
crédito". Preencha na **linha da nota**, na aba `BASE TRATADA`, nas cinco
colunas de cabeçalho marrom:

| Coluna | O que informar |
|---|---|
| `ajuste_linha` | `002`, `003`, `006`, `007` — ou `ANOTAR` |
| `ajuste_valor` | quanto, **sempre positivo** |
| `ajuste_motivo` | por quê (obrigatório) |
| `ajuste_responsavel` | quem apurou |
| `ajuste_aprovador` | quem aprovou |

Estabelecimento e atividade não se digitam: a linha já diz os dois.

*Não tem documento* — uma parcela do Registro que não pertence a nota nenhuma.
Vai na aba **`AJUSTES`**, bloco `PARCELAS SEM DOCUMENTO`, com o estabelecimento
escrito. Em MS informe também a atividade, porque é ela que dimensiona o
benefício.

**O sentido vem da linha, não do sinal:**

| Informou | Efeito |
|---|---|
| `002` Outros Débitos | aumenta o que se deve |
| `003` Estornos de Créditos | aumenta o que se deve |
| `006` Outros Créditos | diminui o que se deve |
| `007` Estornos de Débitos | diminui o que se deve |

Para reduzir um estorno que a regra calculou, não lance negativo na `003`:
lance positivo na `006`, que é como o livro escreve isso.

**`ANOTAR` marca sem lançar.** Serve para "este ICMS é indevido, será tratado
por anuência": a apuração não muda, e o valor sai em *Marcado, não lançado*,
com o total, para ficar visível em vez de sumir.

**Ajuste pela metade é recusado** e vira pendência: valor sem linha, linha sem
motivo, lançamento sem aprovador. Ignorar seria perder uma decisão que alguém
tomou; completar por conta própria é o que a ferramenta não faz.

### Tirar o `AGUARDA AJUSTE`

Célula vazia diz duas coisas ao mesmo tempo — "não tem ajuste" e "ninguém olhou
ainda" —, e a ferramenta não escolhe uma. Por isso alguém assina, no bloco
`CONFERÊNCIA` da aba `AJUSTES`:

| estabelecimento | conferido por | conferido em | observação |
|---|---|---|---|
| HINOVE (FILIAL GUARÁ) | Fulano | 05/09/2026 | sem ajustes nesta competência |

É uma linha por estabelecimento, e a ferramenta já traz os nomes preenchidos.
Assinado, a marca some — **inclusive quando não houve ajuste nenhum**, que é
justamente a resposta que faltava.

A marca não trava o fechamento: ela avisa que o número ainda não é o final.

### O ano de uma vez só

A janela mostra a tabela do ano, mês a mês, com **saldo** e **a recolher**. O
mês que você acabou de apurar já vem preenchido; os outros você digita e clica
em **Salvar o ano**.

As duas colunas existem porque uma não sai da outra: com mais de um
estabelecimento, o que se recolhe é a soma do que cada um recolhe, e não o saldo
do grupo com o sinal trocado — filial credora não paga a conta de outra devedora
fora da centralização.

Fica gravado em `competencias/serie-<ano>.yaml`, que o git ignora: é dado
fiscal, não parâmetro.

### O saldo credor, de um mês para o outro

O Livro Fiscal só tem os documentos do mês. O crédito que sobrou do mês
anterior não está lá, mas está na conta — é a linha 009 do registro. Por isso
ele é **declarado** em `apurabot/parametros/saldos.yaml`:

```yaml
saldos_credores:
  - competencia: "2026-08"
    por_estabelecimento:
      11: 2215164.28          # HINOVE (FILIAL GUARÁ)
```

O código (`11`, acima) é o da empresa, o mesmo do Livro Fiscal. Estabelecimento
que não aparece na competência declarada abriu o mês sem saldo credor.

**De onde tirar o número:** da apuração do mês anterior. A tela, a planilha
(aba `APURAÇÃO POR FILIAL`) e o comando trazem o bloco **Saldo credor** com três
colunas — o que veio, o que o mês apurou e o que vai para a competência
seguinte. A última coluna é exatamente o que se cadastra:

```
  estabelecimento                    veio de 2026-06    apurado no mês  vai para 2026-08
  HINOVE (FILIAL GUARÁ)                   107.620,97      2.107.543,31      2.215.164,28
```

Se a competência não estiver declarada, a apuração roda assim mesmo, com todo
mundo abrindo o mês zerado — e o `REGISTRO` marca a linha 009 como
`AGUARDA AJUSTE`, para ninguém confundir "não tinha saldo" com "ninguém disse".

---

## 6. Pendência e alerta

**Pendência bloqueia o encerramento** e o comando sai com erro.

| Pendência | O que fazer |
|---|---|
| `SEM REGRA` | Cadastrar o produto em `apurabot/parametros/produtos.yaml` |
| Atividade indefinida | Cadastrar o CFOP em `regimes.yaml`, bloco `atividades` |

**Alerta não bloqueia** — lançamento que passou mas merece olhada, como carga
efetiva fora das homologadas. Sai no RESUMO.

O que não casa com regra vira pendência e para o fechamento. É de propósito: a
ferramenta não classifica por adivinhação.

---

## 7. Mudar uma regra

Toda regra está em `apurabot/parametros/`, em arquivos de texto com vigência.
Nenhum número tributário está dentro do código.

| Arquivo | Contém |
|---|---|
| `filiais.yaml` | Estabelecimentos, regimes e centralização |
| `regimes.yaml` | Estorno por UF, benefício fiscal, FADEFE, mapa de atividades |
| `cargas.yaml` | Régua de cargas e tabelas de fertilizante |
| `classificacao.yaml` | Como cada operação é classificada |
| `produtos.yaml` | Cadastro produto → categoria tributária |
| `saldos.yaml` | Saldo credor de abertura de cada competência |

Alterou, é só rodar de novo.

---

## 8. Erros

| Mensagem | Causa e solução |
|---|---|
| **Nenhum Python consegue rodar** | Ou não há Python 3.10+, ou a pasta veio incompleta. Rode `python verificar.py` para saber qual dos dois. |
| **`Falta a biblioteca ...`** | A pasta veio incompleta — as bibliotecas deveriam estar em `apurabot/src/apurabot/vendor`. Baixe o ZIP de novo e extraia **inteiro**. |
| **O navegador não abriu sozinho** | Copie o endereço `http://127.0.0.1:…` que aparece na janela preta e cole no navegador. |
| **A janela preta fecha na hora** | Abra o `cmd` na pasta e rode `python verificar.py` para ler o motivo. |
| **A página diz que perdeu contato** | A janela preta foi fechada. Abra o `Apurabot.bat` de novo. |
| **`python não é reconhecido`** | O Python não está no PATH. O `Apurabot.bat` também tenta `py`; se ele funcionar, use-o. |
| **`Acesso negado`** ao rodar `apurabot` | A política barrou um executável criado por `pip install -e`. Use o `Apurabot.bat` — ele não cria programa nenhum. |
| **`invalid choice: 'apurar'`** | Código desatualizado. Baixe o ZIP de novo. |
| **`Encerramento BLOQUEADO`** | Não é erro de instalação — é a ferramenta cobrando pendência. Ver passo 6. |
| **"não é defeito da ferramenta: é uma regra que ainda não foi cadastrada"** | Um estabelecimento, CFOP ou regime apareceu no livro e não está nos parâmetros. A mensagem diz qual arquivo e o que falta. Ver passo 7. |

---

## 9. O que não está pronto

| | |
|---|---|
| **CIAP** e **DIFAL** | Pausados |
| Regra de transferência de SP | Calculada, **não homologada** — o relatório avisa |
| Encadeamento das competências | O saldo credor a transportar é calculado e exibido; passá-lo para o mês seguinte é cadastro manual em `saldos.yaml` |

---

## 10. Testes

Para quem for mexer no código. O `pytest` é a única coisa que precisa ser
instalada, e só para isto:

```
python -m pip install --user pytest
cd apurabot
python -m pytest
```

Os de regressão precisam de um Livro Fiscal real e são pulados com explicação
quando não o encontram. Para rodá-los:

```
set APURABOT_FIXTURE_JULHO=C:\caminho\para\o\livro.xls
```

Depois, `cd ..` para voltar.
