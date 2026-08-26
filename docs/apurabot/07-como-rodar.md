# Apurabot — como rodar na sua máquina

Guia de instalação e uso. Do zero até a apuração do mês em `.xlsx`.

---

## 1. Abrir o terminal

Quase tudo aqui é digitado numa janela preta chamada **terminal** (ou *prompt de
comando*). Se você nunca abriu uma:

**Windows** — segure a tecla `Windows` e aperte `R`, digite `cmd` e dê Enter.

**Mac** — aperte `Command` + `barra de espaço`, digite `Terminal` e dê Enter.

Você digita um comando, aperta Enter, e espera ele terminar. É isso.

---

## 2. Instalar o Python

O Apurabot é escrito em Python, então o Python precisa estar na máquina.

No terminal, digite:

```
python --version
```

**Apareceu `Python 3.10` ou maior?** Pode pular para o passo 3.

**Deu erro, ou apareceu uma versão menor?** Baixe em
[python.org/downloads](https://www.python.org/downloads/) e instale.

> ### No Windows, marque "Add Python to PATH"
>
> É uma caixinha na **primeira tela** do instalador, embaixo. Sem ela o Windows
> não encontra o Python depois, e todos os comandos deste guia falham.
>
> Se você já instalou sem marcar, rode o instalador de novo, escolha
> **Modify** e marque a opção.

> **Abriu a Microsoft Store em vez de responder?** É o atalho falso que o
> Windows instala de fábrica. Instale o Python pelo site mesmo, e o problema
> some.

Feche e abra o terminal de novo, e confira outra vez com `python --version`.

---

## 3. Baixar o Apurabot

O código está no GitHub, em **`merolupe/hi9`**. Há dois jeitos.

### Jeito A — baixar o `.zip` (não precisa instalar nada)

1. Abra <https://github.com/merolupe/hi9> no navegador, logado na sua conta.
2. Clique no botão verde **`Code`** e depois em **`Download ZIP`**.
3. O arquivo cai em Downloads. Clique com o botão direito nele e escolha
   **Extrair tudo**.
4. Escolha uma pasta fácil de achar. A sugestão é a raiz do disco:
   `C:\hi9` no Windows, ou a sua pasta pessoal no Mac.

Você vai terminar com uma pasta chamada `hi9-main` (ou `hi9`), e dentro dela
outras pastas: `apurabot`, `docs`, e alguns arquivos soltos.

> **Deixe essa pasta onde está.** A instalação aponta para ela; se você mover ou
> apagar depois, o comando para de funcionar.

### Jeito B — `git clone` (se você já usa Git)

```
git clone https://github.com/merolupe/hi9.git
```

---

## 4. Preparar para rodar

O Apurabot **não precisa ser instalado**. Ele roda direto da pasta que você
baixou, pelo Python que já está na máquina. Isso é de propósito: em máquina
corporativa, instalar programa costuma esbarrar em permissão de administrador ou
na política de segurança.

### 4.1. Levar o terminal até a pasta

**No Windows, o jeito mais fácil:**

1. Abra a pasta no Explorador de Arquivos.
2. Clique na **barra de endereço** lá em cima (onde aparece o caminho).
3. Apague o que está escrito, digite `cmd` e dê Enter.

Abre um terminal **já dentro da pasta certa**.

**No Mac, ou se preferir digitar:** digite `cd`, um espaço, e **arraste a pasta**
para dentro da janela do terminal — ele preenche o caminho sozinho. Dê Enter.

**Confirme que chegou:**

```
dir          (Windows)
ls           (Mac e Linux)
```

Tem que aparecer uma pasta chamada **`apurabot`** e um arquivo **`rodar.py`** na
lista. Se não aparecerem, você está na pasta errada.

### 4.2. Instalar as três bibliotecas

O Apurabot usa três bibliotecas de terceiros para ler e escrever planilhas.
O `--user` instala na sua conta, **sem precisar de administrador**:

```
pip install --user openpyxl "xlrd==2.0.1" PyYAML
```

> Se o `pip` não for reconhecido, use `python -m pip` no lugar dele:
> `python -m pip install --user openpyxl "xlrd==2.0.1" PyYAML`

### 4.3. Conferir

```
python rodar.py --help
```

Deve aparecer a lista de comandos: `apurar` e `base-tratada`. Se apareceu, está
pronto — pule para o passo 5.

---

## 5. Onde colocar o Livro Fiscal

Em qualquer pasta. A recomendação é criar uma pasta `competencias` **dentro da
pasta do Apurabot**, organizada por mês:

```
hi9/
  apurabot/
  docs/
  competencias/
    2026-07/
      entrada/     ← o Livro Fiscal que saiu do Sankhya vai aqui
      saida/       ← a apuração vai aparecer aqui
```

Crie as pastas normalmente pelo Explorador de Arquivos, e copie o Livro Fiscal
para dentro de `entrada`.

> **A pasta `competencias/` não vai para o Git.** Ela contém dado fiscal real, e
> o `.gitignore` do projeto a exclui de propósito. Isso é regra do projeto, não
> configuração — nenhum dado fiscal da empresa é versionado.

O Apurabot lê os dois formatos de extração do Sankhya: o
**Movimento Livros Fiscais**, que é o padrão, e a extração antiga da apuração.
Ele reconhece qual é sozinho.

---

## 6. Rodar

Com o terminal na pasta do Apurabot (passo 4), o comando é:

```
python rodar.py apurar "competencias/2026-07/entrada/Movimento Livros Fiscais.xls" --saida "competencias/2026-07/saida"
```

Troque `2026-07` pelo mês que você está apurando, e o nome do arquivo pelo nome
real dele.

> ### As aspas não são enfeite
>
> Caminho com espaço no meio **precisa** de aspas. Sem elas o terminal entende
> `Movimento`, `Livros` e `Fiscais.xls` como três coisas separadas e dá erro.
> Na dúvida, use aspas sempre.

> ### Não quer digitar o caminho? Copie
>
> **Windows:** segure `Shift`, clique com o botão direito no arquivo e escolha
> **"Copiar como caminho"**. Ele copia já com as aspas — é só colar no terminal
> com `Ctrl` + `V`.
>
> **Mac:** clique com o botão direito no arquivo, segure a tecla `Option`, e a
> opção vira **"Copiar ... como nome do caminho"**.

O que aparece na tela:

```
Apurabot — apuração de ICMS
Competência................... 2026-07
Linhas no Livro Fiscal........ 6.555
Linhas relevantes para ICMS... 2.345
Alertas....................... 30

Apuração por estabelecimento
  estabelecimento              UF      crédito       débito        saldo
  ...

Segregação por atividade
  ...

Benefício fiscal — HINOVE (RIO BRILHANTE)
  ...

Centralização
  ...

Encerramento liberado
Nenhuma pendência.

Gerado: competencias/2026-07/saida/Apuracao_2026-07.xlsx
```

### O outro comando

```
python rodar.py base-tratada <arquivo> --saida <pasta>
```

Para no tratamento e na classificação, sem apurar. Serve para conferir se o
Livro está limpo antes de fechar o mês.

---

## 7. O que sai

Um `.xlsx` com cinco abas:

| Aba | O que tem |
|---|---|
| **RESUMO** | Procedência do arquivo, volume, situação da equalização e categorias |
| **APURAÇÃO POR FILIAL** | Crédito, estorno, débito e saldo por estabelecimento — mais a segregação por atividade, a memória do benefício fiscal, o FADEFE e a centralização |
| **BASE TRATADA** | Uma linha por linha do Livro, com a regra que foi aplicada em cada uma |
| **PENDÊNCIAS** | O que bloqueia o encerramento da competência |
| **POR ESTABELECIMENTO E CARGA** | O recorte que confere com a tabela dinâmica da apuração manual |

A aba **BASE TRATADA** é a que responde "por que este número deu isso": cada
linha carrega a carga efetiva calculada, a categoria, o regime e a regra
aplicada, em texto.

---

## 8. Pendências e alertas

Não são a mesma coisa.

**Pendência bloqueia o encerramento.** A ferramenta termina com aviso e o
comando devolve erro. Os tipos:

| Pendência | O que significa | O que fazer |
|---|---|---|
| `SEM REGRA` | Um produto ou operação não casou com nenhuma regra | Cadastrar o produto em `apurabot/parametros/produtos.yaml` |
| Atividade indefinida | Um CFOP de MS não está no mapa de atividades | Cadastrar em `apurabot/parametros/regimes.yaml`, bloco `atividades` |
| Transferência sem NF-e | Há saldo a transferir na centralização e nenhuma NF-e escriturada | Emitir e escriturar, ou conferir se o CFOP usado está no parâmetro |

**Alerta não bloqueia.** É lançamento que passou, mas merece olhada — carga
efetiva fora das homologadas, por exemplo. Aparece na aba RESUMO.

> A ferramenta **nunca classifica por adivinhação**. O que não casa com regra
> vira pendência e para o fechamento. É de propósito: melhor travar e perguntar
> do que fechar um número errado.

---

## 9. Mudar uma regra tributária

Toda regra vive em `apurabot/parametros/`, em arquivos de texto. **Nenhum número
tributário está dentro do código.**

| Arquivo | O que contém |
|---|---|
| `filiais.yaml` | Estabelecimentos, regimes e as regras de centralização |
| `regimes.yaml` | Estorno por UF, benefício fiscal, FADEFE e o mapa de atividades |
| `cargas.yaml` | Régua de cargas efetivas e as tabelas de fertilizante |
| `classificacao.yaml` | Como cada operação é classificada |
| `produtos.yaml` | Cadastro produto → categoria tributária |

Alterou um deles, é só rodar de novo — não precisa reinstalar nada.

Cada regra tem **vigência**, para que a apuração de um mês antigo continue
reproduzível depois de mudança na legislação.

---

## 10. O que ainda não está pronto

| | Situação |
|---|---|
| **CIAP** | Pausado |
| **DIFAL** | Pausado |
| **Ajustes manuais** | O relatório de ajustes ainda não é lido pela ferramenta |
| **Regra de transferência de SP** | Calculada, mas **não homologada** — o relatório avisa |
| **Interface gráfica** | Por enquanto só linha de comando |

---

## 11. Rodar os testes

Se quiser conferir que a instalação está sã:

```
pip install --user pytest
cd apurabot
python -m pytest
```

Terminou? Volte para a pasta de cima com `cd ..`, senão os comandos do passo 6
não vão achar a pasta `competencias`.

Os testes de unidade rodam sozinhos. Os de regressão precisam de um Livro Fiscal
real e são **pulados com explicação** quando não o encontram — dado fiscal não
vai para o repositório. Para rodá-los, aponte o arquivo:

```
set APURABOT_FIXTURE_JULHO=C:\caminho\para\o\livro.xls        (Windows)
export APURABOT_FIXTURE_JULHO=/caminho/para/o/livro.xls        (Linux e Mac)
```

---

## 12. Quando dá erro

### "Acesso negado."

Aparece ao rodar `apurabot`, depois de um `pip install -e apurabot`.

**O que é:** o Windows *achou* o programa e se recusou a executá-lo. É diferente
de *"não é reconhecido"*, que significa não encontrado. A instalação cria um
executável novo (`apurabot.exe`) numa pasta da sua conta, e em máquina
corporativa isso costuma ser barrado — pela política de segurança, que não
permite executável em pasta de usuário, ou pelo antivírus, que bloqueia binário
recém-criado e sem assinatura.

**O que fazer:** não use o executável. Use o `rodar.py`, como está no passo 4:

```
python rodar.py apurar "caminho\do\livro.xls" --saida "pasta\de\saida"
```

Aqui quem roda é o `python.exe`, que já está aprovado na máquina. Nenhum
executável novo é criado, e não há nada para a política bloquear. É por isso que
o guia não pede instalação.

> Se quiser limpar o que ficou pela metade: `pip uninstall apurabot`. Não é
> obrigatório — o `rodar.py` funciona de qualquer jeito.

### "pip não é reconhecido"

Use `python -m pip` no lugar de `pip`, em qualquer comando:

```
python -m pip install --user openpyxl "xlrd==2.0.1" PyYAML
```

### "Acesso negado" ou "Permission denied" no próprio `pip`

Falta o `--user`. Sem ele o pip tenta escrever na pasta do Python do sistema, que
exige administrador:

```
pip install --user openpyxl "xlrd==2.0.1" PyYAML
```

### "Falta a biblioteca ..."

O `rodar.py` avisa qual falta e repete o comando de instalação. É o passo 4.2 que
não rodou, ou rodou num Python diferente do que você está usando agora.

### "python não é reconhecido"

O Python não está instalado, ou foi instalado sem marcar **"Add Python to PATH"**
— ver passo 2. No Windows, tente também `py` no lugar de `python`:

```
py rodar.py --help
```

### "não é possível criar a pasta" ao gravar a saída

A pasta de `--saida` não existe, ou você não tem permissão de escrever nela.
Crie a pasta antes pelo Explorador de Arquivos, e prefira uma pasta dentro de
**Documentos** a uma na raiz do disco.

### O comando roda, mas termina com "Encerramento BLOQUEADO"

**Não é erro de instalação — é a ferramenta funcionando.** Alguma linha do Livro
não casou com regra, ou falta uma NF-e de transferência. A tela lista o motivo, e
a aba PENDÊNCIAS do arquivo gerado traz o detalhe. Ver o passo 8.

