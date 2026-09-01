# Bibliotecas de terceiros embarcadas

Estas pastas **não são código do Apurabot**. São cópias inalteradas de
bibliotecas de código aberto, guardadas aqui para que a ferramenta rode sem
instalar nada.

## Por que embarcar

A máquina do time fiscal é corporativa e sem elevação de administrador. O
`pip install` já falhou ali de duas maneiras — barrado pela política de
segurança, e acertando um Python diferente do que a ferramenta abre. Nas duas
vezes a pessoa tinha feito tudo certo e mesmo assim não rodava.

As quatro bibliotecas são **Python puro**, sem extensão compilada, então
funcionam em qualquer Python 3.10 ou mais novo, em qualquer sistema. Copiá-las
para cá troca um passo que falha por um que não existe.

## O que está aqui

| Pasta | Versão | Licença | Origem |
|---|---|---|---|
| `openpyxl/` | 3.1.5 | MIT | <https://foss.heptapod.net/openpyxl/openpyxl> |
| `et_xmlfile/` | 2.0.0 | MIT | <https://foss.heptapod.net/openpyxl/et_xmlfile> |
| `xlrd/` | 2.0.1 | BSD-3-Clause | <https://github.com/python-excel/xlrd> |
| `yaml/` (PyYAML) | 6.0.1 | MIT | <https://github.com/yaml/pyyaml> |

Os metadados de distribuição de cada uma seguem junto, nas pastas
`*.dist-info/`, com a licença e a autoria originais. O `xlrd` traz o texto
completo em `xlrd-2.0.1.dist-info/LICENSE`.

De `PyYAML` vai só a parte em Python. A extensão em C (`_yaml`), que é opcional
e só acelera a leitura, ficou de fora justamente porque é compilada — e é ela
que tornaria o pacote dependente de sistema operacional e de versão do Python.
Os arquivos de parâmetro do Apurabot têm alguns quilobytes; a diferença de
velocidade não é perceptível.

## Como são carregadas

`apurabot/_dependencias.py` acrescenta esta pasta ao **fim** do `sys.path`.
O fim, e não o começo, é deliberado: se o administrador tiver instalado alguma
dessas bibliotecas na máquina, é a dele que vale. Esta cópia é a rede de
segurança.

## Ao atualizar

Substitua a pasta inteira pela nova versão, atualize a tabela acima e rode a
bateria de testes. Não edite nada aqui dentro: qualquer correção que o Apurabot
precise vai no código do Apurabot, nunca na cópia da biblioteca — uma alteração
local se perderia silenciosamente na próxima atualização.
