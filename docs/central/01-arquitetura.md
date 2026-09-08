# Central Fiscal — arquitetura e contrato de ferramenta

> Documento técnico. Público: analista desenvolvedor + Gerência Fiscal/Tributária.

---

## 1. O problema, em uma frase

As automações do setor nasceram uma a uma, cada uma com o seu jeito de ser
aberta — script solto, popup do tkinter, planilha com macro. Quem usa precisa
saber qual arquivo abrir, de qual pasta, com qual Python. **A central troca isso
por uma tela só**: escolhe-se a ferramenta, ela pede o que precisa e devolve o
resultado.

## 2. Como as ferramentas entram no repositório

A ordem foi decidida assim: **nem tudo de uma vez, nem a interface primeiro.**

Despejar as cinco ferramentas antes de existir interface produziria cinco
formatos diferentes para a interface depois ter que acomodar — ou reescrever.
Fazer a interface primeiro seria desenhar um menu para ferramentas cuja forma
ainda não se conhece.

O caminho é o do meio, e tem três passos:

1. **Definir o encaixe** — o que uma ferramenta declara para aparecer na tela
   (a seção 4 deste documento, e o código em `central/src/central/ferramentas.py`).
2. **Importar a mais simples primeiro**, como teste do encaixe. Foi o DiXML:
   entrada de arquivo, saída de planilha, sem regra tributária e sem estado.
3. **As demais, uma a uma**, cada uma já nascendo dentro da central.

Ao importar, a regra é **trazer como está**: versionado, documentado e rodando
pela central. Reescrever no mesmo movimento transformaria "centralizar" em
"reescrever tudo", que é como este tipo de projeto trava. O que se reescreve é
só o que impede a ferramenta de rodar sem instalação — no DiXML foram duas
coisas, listadas em [`../dixml/01-o-que-faz.md`](../dixml/01-o-que-faz.md).

## 3. Decisão central: a interface é o navegador

Mesma decisão que o Apurabot tomou, pelo mesmo motivo — está inteira em
`apurabot/src/apurabot/web/servidor.py`. Em resumo:

A máquina do time fiscal é corporativa e sem elevação de administrador. Um
`.exe` novo e sem assinatura é barrado pela política de segurança; o `pip
install` já falhou ali duas vezes. O Python que está na máquina é programa
aprovado, e o navegador também. Então a central não é um programa novo: é o
Python abrindo um servidor em `127.0.0.1`, numa porta que o sistema escolhe,
e mandando o navegador abrir a página.

| O que se garante | Como |
|---|---|
| Nada é instalado | Nenhum binário novo, nenhum privilégio de administrador |
| O dado não sai da máquina | Só se aceita conexão de `127.0.0.1`; o arquivo enviado vive numa pasta temporária e some no encerramento |
| Outra sessão na mesma máquina não alcança | Cada janela nasce com uma chave aleatória no endereço; requisição sem ela é recusada |
| Não depende de TI nem de rede | Não há servidor, não há banco, não há porta aberta para fora |

## 4. O contrato de ferramenta

Para aparecer na tela, uma ferramenta declara três coisas em
`central/src/central/ferramentas.py`:

**Quem é** — `id`, `nome`, `resumo` de uma linha, `icone` e `estado`.

**O que pede** — uma `Entrada`: o rótulo que aparece na área de largar, quais
extensões aceita e se aceita mais de um arquivo.

**O que devolve** — um `Resultado`: um título, as `Ficha`s (os números em
destaque), as `Lista`s (o que precisa ser visto item a item — o que ficou de
fora, o que falhou) e, quando houver, o caminho da planilha para baixar.

```python
Ferramenta(
    id="dixml",
    nome="DiXML",
    resumo="Lote de XML de nota em planilha, para conferir qualquer campo.",
    icone="🧾",
    estado=DISPONIVEL,
    entrada=Entrada(rotulo="Arraste aqui os pacotes de XML",
                    apoio="um ou mais arquivos <code>.zip</code>",
                    extensoes=(".zip",), varios=True),
    verbo="Lendo os XMLs…",
    executar=_rodar_dixml,          # (arquivos, pasta_de_saída) -> Resultado
)
```

A função de execução recebe os caminhos dos arquivos e a pasta onde gravar, e
devolve o `Resultado`. **Só isso.** A ferramenta não sabe que existe navegador,
não monta HTML e não conhece as outras. Quem costura é a central — e há um
teste que trava isso (`test_nenhuma_ferramenta_importa_outra`).

### Os três estados

| Estado | O que significa | Na tela |
|---|---|---|
| `DISPONIVEL` | Roda dentro da janela da central | Botão ativo |
| `JANELA_PROPRIA` | Tem tela própria; a central abre a janela dela | Botão ativo, etiqueta "janela própria" |
| `A_IMPORTAR` | Já existe e é usada, mas ainda não veio para o repositório | Botão apagado, com o nome e o que faz |

O terceiro estado é deliberado: a ferramenta que ainda falta **aparece na tela**,
apagada. O time enxerga o que está por vir, em vez de descobrir que falta na
hora em que for precisar.

## 5. Por que o Apurabot abre em janela própria

O Apurabot já tinha uma janela inteira — conferência, registro por
estabelecimento, série do ano — homologada contra a apuração real, antes de a
central existir. Reescrevê-la dentro da central seria refazer o que funciona.

Então a central sobe o servidor do Apurabot numa porta própria e manda o
navegador para lá (`central/src/central/janelas.py`, vinte linhas). O Apurabot
não sabe que a central existe e continua abrindo sozinho por `Apurabot.bat`.

É provisório por escolha: **quando a segunda ferramenta com tela própria
aparecer**, o certo passa a ser a central hospedar as duas telas, e aí o
trabalho se paga. Com uma só, não se paga.

## 6. Layout do repositório

```
hi9/
├─ Hinove.bat            dois cliques: abre a Central
├─ Apurabot.bat          atalho direto para a apuração, sem passar pelo menu
├─ rodar.py              a porta de entrada de tudo, pelo terminal
├─ verificar.py          "este Python consegue rodar?" — é o que o .bat pergunta
├─ vendor/               bibliotecas embarcadas, compartilhadas (ver LEIA-ME.md)
├─ central/src/central/  o menu, o contrato e o servidor
├─ apurabot/             apuração de ICMS
├─ dixml/                lote de XML para planilha
└─ docs/                 esta documentação
```

`vendor/` fica na raiz porque não é de ninguém em particular: as ferramentas
carregam as mesmas cópias. Cada pacote tem um `_dependencias.py` que acha a
pasta subindo a partir do próprio arquivo.

A central é a única parte do repositório que conhece o repositório inteiro —
é o trabalho dela. Ela põe `<projeto>/src` de cada ferramenta no `sys.path`;
nenhuma ferramenta importa outra.

## 7. O que a janela recusa

A ferramenta passou a receber arquivo pela janela, então o que entra por ali é
conferido:

| Trava | Onde |
|---|---|
| Extensão diferente da declarada pela ferramenta | `servidor.py` |
| Arquivo vazio, ou acima de 500 MB | `servidor.py` |
| Soma dos arquivos acima de 2 GB | `servidor.py` |
| Nome de arquivo que tente sair da pasta temporária | `_nome_seguro` |
| `.zip` que se expande além de 2 GB descompactados | `dixml/pacote.py` |
| `.zip` aninhado além de 8 níveis | `dixml/pacote.py` |

O nome do arquivo é preservado (só o nome, nunca o caminho) porque ele viaja
para dentro da planilha: é por ele que se acha a origem de uma linha meses
depois.

## 8. O que falta

- Trazer Fiscalbot, GerarPendentes e GerarServPend, uma a uma.
- Quando a segunda ferramenta com tela própria chegar, hospedar as telas na
  central em vez de abrir janela ao lado (seção 5).
- O Faturabot está em desenvolvimento e entra pelo mesmo contrato.
