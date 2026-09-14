"""Notas pendentes de entrada — mercadorias e serviços.

**Duas ferramentas na tela, um projeto no disco.** As duas rotinas semanais do
time fiscal fazem a mesma coisa: cruzam um universo de documentos com um
registro de lançamento, dizem o que sobrou e preservam o julgamento humano de
uma semana para a outra. O que muda entre elas é a chave do cruzamento.

Por isso os dois domínios (`pendentes.mercadorias` e `pendentes.servicos`)
moram sobre um núcleo comum — este pacote — em vez de duplicarem cinco
conceitos, que é a situação de hoje no VBA.

**Esta entrega traz o núcleo e a documentação.** Os dois motores de domínio
ainda não existem: o que entrou e o que vem depois está em
`docs/pendentes/04-plano-de-entrega.md`.

| Módulo | O que resolve |
|---|---|
| `texto` | as duas normalizações que o VBA chamava pelo mesmo nome |
| `valores` | número, data e data-hora do Sankhya e do Portal Nacional |
| `farol` | o semáforo de emoji do Sankhya, com o vazio que **não** é "Não" |
| `planilha` | ler `.xls`, `.xlsx` e `.xlsm` numa matriz |
| `cabecalho` | achar a linha do cabeçalho e mapear coluna por nome |
| `papeis` | qual arquivo é qual, pelas âncoras do próprio cabeçalho |
| `tabelas` | tabelas em que a **ordem das linhas é a regra** |
| `parametros` | carga de fábrica versionada + base viva fora do git |
| `estado` | o livro de classificação: onde o julgamento humano passa a morar |
| `snapshot` | a foto semanal imutável, para o controle interno |
| `escrita` | a aba formatada, com o formato aplicado **antes** da escrita |
"""
from ._dependencias import preparar as _preparar

_preparar()

__version__ = "0.1.0"
