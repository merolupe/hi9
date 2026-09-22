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

Para aparecer na tela, uma ferramenta declara até cinco coisas em
`central/src/central/ferramentas.py`:

**Quem é** — `id`, `nome`, `resumo` de uma linha, `icone` e `estado`.

**O que pede** — uma `Entrada`: o rótulo que aparece na área de largar, quais
extensões aceita e se aceita mais de um arquivo.

**O que devolve** — um `Resultado`: um título, as `Ficha`s (os números em
destaque), as `Lista`s (o que precisa ser visto item a item — o que ficou de
fora, o que falhou) e, quando houver, o caminho da planilha para baixar.

**O que se configura nela** — uma `Configuracao`, quando a ferramenta guarda
estado entre uma execução e outra. É a parte mais nova do contrato, e nasceu
com o Fiscalbot: as regras tributárias dele são cadastradas numa tela, não em
planilha nem em arquivo no git. A ferramenta declara `Secao`s — cada uma uma
tabela editável, com seus `Campo`s — e duas funções: `ler`, que devolve o que
está gravado, e `gravar`, que confere e responde `(gravou, problemas)`. Com
erro não grava; com aviso grava e conta o que vai acontecer.

**Como conferir o que chegou** — `conferir`, opcional, para quem pede mais de
um relatório e reconhece cada um pelo cabeçalho (GerarServPend e
GerarPendentes). Recebe os caminhos já enviados e devolve uma `Conferencia`:
os `Documento`s esperados — cada um `ok`, `falta`, `opcional` ou `repetido`,
com os arquivos que o preencheram — e os arquivos que não são nenhum deles.
Com isso a tela deixa de rodar no instante em que o arquivo cai: ela mostra a
lista dos relatórios, marca cada um conforme chega, deixa anexar **aos poucos**
e tirar um arquivo errado, e só acende "Gerar planilha" quando nada falta.
Quem não declara (`DiXML`, `Fiscalbot`) continua rodando ao largar o arquivo.

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

A configuração segue a mesma disciplina: o Fiscalbot descreve as seções dele
em dicionários simples (`fiscalbot/configuracao.py`), e é a central que os
converte nos tipos dela e desenha a tela. Se fosse o contrário, a ferramenta
precisaria importar a central.

### Onde a configuração de uma ferramenta mora

**Fora do git.** A base de uma ferramenta fica em `dados/<ferramenta>/`, pasta
ignorada como `competencias/`. A razão é dupla: parte do conteúdo é dado da
empresa (as listas de parceiros do Fiscalbot trazem nome de fornecedor real), e
o time fiscal precisa alterar regra sem passar por commit.

O que fica versionado é a **carga de fábrica** — `<projeto>/regras_de_fabrica.yaml`
—, que traz só a parte tributária, sem dado de empresa. Ela existe para a
ferramenta abrir funcionando numa máquina nova; na primeira abertura a base é
semeada a partir dela, e dali em diante quem manda é a base.

Isso **abre exceção às regras nº 2 e nº 3 do `CLAUDE.md`** — regra tributária
versionada, com vigência. Foi decisão do time: a tela substitui a planilha, e a
trilha de alteração passa a viver dentro do aplicativo, que carimba quem gravou
e quando. Vale para ferramenta com tela de configuração; o Apurabot continua
com os parâmetros dele versionados em `apurabot/parametros/`.

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
├─ fiscalbot/            auditoria do Livro Fiscal
├─ pendentes/            notas pendentes de entrada: mercadorias e serviços
├─ dados/                base de regras das ferramentas — ignorada pelo git
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
| "Gerar" com relatório obrigatório faltando, repetido ou ilegível — os anexos ficam, para completar sem reenviar | `servidor.py` (`_executar`) |
| A saída da própria ferramenta tomada por relatório de origem — a `Sem Correspondencia ASIS` traz as colunas do Portal de Compras, a `CTe` traz as do XML | `pendentes/papeis.py` (`abas_da_saida`) |
| `.zip` que se expande além de 2 GB descompactados | `dixml/pacote.py` |
| `.zip` aninhado além de 8 níveis | `dixml/pacote.py` |

O nome do arquivo é preservado (só o nome, nunca o caminho) porque ele viaja
para dentro da planilha: é por ele que se acha a origem de uma linha meses
depois.

## 8. O que falta

- **Resumo Executivo — importado, em teste.** A terceira entrada de
  `pendentes/`, e a única do catálogo que recebe a **saída** de outras
  ferramentas em vez de um export do ERP: ela lê a planilha da semana, já
  classificada, e devolve o painel das duas frentes dentro dela. Conferida
  contra o relatório de produção da semana 38, bloco a bloco. O que falta é a
  aba `Resumo`, que é a série entre semanas.
- **GerarServPend — importado, em teste.** O projeto `pendentes/` traz o
  núcleo comum das duas rotinas (reconhecimento de arquivo por âncora de
  cabeçalho, coluna por nome, as normalizações, o livro de classificação, o
  snapshot semanal e a escrita formatada) e o **motor de serviços**: a cascata
  de quatro procedimentos de confronto, o vínculo com a Conferência de
  Serviços e a população inversa. A entrada do catálogo está `DISPONIVEL` e
  roda dentro da janela. **A divergência zero contra a macro ainda não está
  provada** — faltam os arquivos reais de uma semana e a saída que a macro
  gerou a partir deles.
- **GerarPendentes — importado, em teste.** O motor de mercadorias entrou:
  a limpeza (A1, A2 e A3) com a aba `Descartados`, o roteamento das quatro
  condições parametrizadas, o lookup da Conferência de Entradas com o farol de
  três estados, a herança pelo livro, a reclassificação para Fiscal e o split
  da `PENDENTES FIS-FAT`. A entrada do catálogo está `DISPONIVEL` e roda
  dentro da janela. **O Resumo Executivo não entrou**: ele saiu do porte por
  decisão do Compliance Tributário de 15/09/2026 e vira um resumo das duas
  frentes, com três categorias — ver
  [`../pendentes/06-proximas-rodadas.md`](../pendentes/06-proximas-rodadas.md).
  A divergência zero contra a macro também aqui **não está provada**, e o que
  trava o quê está em
  [`../pendentes/04-plano-de-entrega.md`](../pendentes/04-plano-de-entrega.md).
- **As duas ferramentas de pendentes entraram sem tela de configuração.** Os
  parâmetros são lidos da carga de fábrica e da base viva, e os motores os
  honram; o que falta é a tela que os edita. Enquanto ela não vem, a tabela de
  unidades e a lista de guardiões só se cadastram editando
  `dados/pendentes/parametros.yaml` à mão — e, **vazias, elas não validam
  nada**, que é o comportamento de hoje.
- Quando a segunda ferramenta com tela própria chegar, hospedar as telas na
  central em vez de abrir janela ao lado (seção 5).
- O Faturabot está em desenvolvimento e entra pelo mesmo contrato.
