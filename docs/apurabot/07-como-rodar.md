# Apurabot — como rodar na sua máquina

Guia de instalação e uso. Do zero até a apuração do mês em `.xlsx`.

---

## 1. O que você precisa

**Python 3.10 ou mais novo.** Para conferir, abra o terminal e digite:

```
python --version
```

Se aparecer `Python 3.10` ou maior, está pronto. Se der erro ou aparecer versão
menor, baixe em [python.org/downloads](https://www.python.org/downloads/).

> **No Windows**, marque a caixa **"Add Python to PATH"** na primeira tela do
> instalador. Sem isso o comando não é reconhecido depois.

---

## 2. Instalar

Baixe o repositório e, na pasta dele, rode:

```
pip install -e apurabot
```

Isso instala o Apurabot e as três bibliotecas de que ele depende. Terminou sem
erro vermelho? Confira:

```
apurabot --help
```

Deve aparecer a lista de comandos.

> **Se `apurabot` não for reconhecido**, use `python -m apurabot.cli` no lugar de
> `apurabot` em todos os comandos deste guia. Funciona igual.

---

## 3. Onde colocar o Livro Fiscal

Em qualquer pasta. A recomendação é organizar por competência:

```
competencias/
  2026-07/
    entrada/
      Movimento Livros Fiscais.xls
    saida/
```

> **A pasta `competencias/` não vai para o Git.** Ela contém dado fiscal real, e
> o `.gitignore` do projeto a exclui de propósito. Isso é regra do projeto, não
> configuração — nenhum dado fiscal da empresa é versionado.

O Apurabot lê os dois formatos de extração do Sankhya: o
**Movimento Livros Fiscais**, que é o padrão, e a extração antiga da apuração.
Ele reconhece qual é sozinho.

---

## 4. Rodar

```
apurabot apurar "competencias/2026-07/entrada/Movimento Livros Fiscais.xls" --saida "competencias/2026-07/saida"
```

Aspas nos caminhos que tiverem espaço.

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
apurabot base-tratada <arquivo> --saida <pasta>
```

Para no tratamento e na classificação, sem apurar. Serve para conferir se o
Livro está limpo antes de fechar o mês.

---

## 5. O que sai

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

## 6. Pendências e alertas

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

## 7. Mudar uma regra tributária

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

## 8. O que ainda não está pronto

| | Situação |
|---|---|
| **CIAP** | Pausado |
| **DIFAL** | Pausado |
| **Ajustes manuais** | O relatório de ajustes ainda não é lido pela ferramenta |
| **Regra de transferência de SP** | Calculada, mas **não homologada** — o relatório avisa |
| **Interface gráfica** | Por enquanto só linha de comando |

---

## 9. Rodar os testes

Se quiser conferir que a instalação está sã:

```
pip install pytest
cd apurabot
python -m pytest
```

Os testes de unidade rodam sozinhos. Os de regressão precisam de um Livro Fiscal
real e são **pulados com explicação** quando não o encontram — dado fiscal não
vai para o repositório. Para rodá-los, aponte o arquivo:

```
set APURABOT_FIXTURE_JULHO=C:\caminho\para\o\livro.xls        (Windows)
export APURABOT_FIXTURE_JULHO=/caminho/para/o/livro.xls        (Linux e Mac)
```
