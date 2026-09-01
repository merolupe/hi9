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
| **RESUMO** | Procedência do arquivo, volume, equalização e categorias |
| **REGISTRO** | Espelho do Registro de Apuração: entradas e saídas por CFOP, resumo em 14 linhas, um bloco por estabelecimento e o totalizador do grupo |
| **APURAÇÃO EFETIVA** | Crédito, estorno e apropriação por CFOP → chave da regra → produto, com a operação, o % estornado e o CHECK |
| **APURAÇÃO POR FILIAL** | Crédito, estorno, débito e saldo por estabelecimento; segregação por atividade, memória do benefício e FADEFE |
| **TRANSFERÊNCIAS** | O que transferir para a centralizadora depois de fechar a competência |
| **PENDÊNCIAS** | O que bloqueia o encerramento |
| **POR ESTABELECIMENTO E CARGA** | O recorte por carga efetiva |
| **BASE TRATADA** | Uma linha por linha do Livro, com a regra aplicada em cada uma |

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
| Relatório de ajustes | Ainda não é lido pela ferramenta |
| Regra de transferência de SP | Calculada, **não homologada** — o relatório avisa |

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
