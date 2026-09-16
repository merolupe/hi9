"""As normalizações de texto — e a reconciliação do nome duplicado.

Os dois módulos VBA têm uma função chamada `NormalizarTexto`, e **elas fazem
coisas diferentes**:

| Onde | O que faz | Preserva caixa? | Preserva acento? |
|---|---|---|---|
| `GerarPendentes` (mercadorias) | colapsa espaços e apara as pontas | sim | sim |
| `RelatorioServicosPendentes` (serviços) | maiúsculas, tira acento, colapsa espaços | não | não |

Ler o nome não diz qual das duas está sendo chamada, e o mesmo nome em dois
módulos que passaram a conviver é um acidente esperando acontecer. Aqui elas
viram duas funções com dois nomes, e cada ponto de chamada passa a dizer qual
delas quer:

* `aparar` — a de mercadorias. É para **exibir**: o valor continua o que era,
  só sem espaço sobrando. É o que a regra nº 4 pede quando o fallback devolve
  o texto original "para que nenhum registro desapareça silenciosamente".
* `chave_de_texto` — a de serviços. É para **comparar**: nome de coluna, nome
  de aba, rótulo de guardião. É ela que faz `Guardião` casar com `Guardiao` no
  arquivo da semana anterior.

Regra da casa: nunca comparar com `aparar`, nunca gravar com `chave_de_texto`.
"""
from __future__ import annotations

import unicodedata
from datetime import date, datetime
from typing import Any

#: Os 24 caracteres que a tabela do VBA (`RemoverAcentos`) mapeia. Ficam aqui
#: como registro do que o original cobria — a implementação usa `unicodedata`,
#: que cobre estes e mais os minúsculos, que no VBA nunca chegavam à tabela
#: porque o `UCase` rodava antes.
ACENTOS_DO_VBA = "ÁÀÂÃÄÉÈÊËÍÌÎÏÓÒÔÕÖÚÙÛÜÇÑ"


def texto_de(valor: Any) -> str:
    """O valor da célula como texto, do jeito que o VBA o veria.

    Número inteiro não ganha `.0` — `5552.0` é o CFOP `5552`, e um código com
    casa decimal a mais deixa de casar com qualquer outra base. Data vira
    `dd/mm/aaaa`, que é como ela aparece na planilha.
    """
    if valor is None:
        return ""
    if isinstance(valor, bool):
        return str(valor)
    if isinstance(valor, float):
        return str(int(valor)) if valor.is_integer() else str(valor)
    if isinstance(valor, datetime):
        return valor.strftime("%d/%m/%Y %H:%M:%S") if (
            valor.hour or valor.minute or valor.second
        ) else valor.strftime("%d/%m/%Y")
    if isinstance(valor, date):
        return valor.strftime("%d/%m/%Y")
    return str(valor)


def _colapsar(s: str) -> str:
    """Espaços repetidos viram um só, e as pontas somem.

    Fiel ao VBA: só o espaço comum é colapsado. Tabulação e quebra de linha
    ficam onde estão — para elas existe `limpar_quebras`.
    """
    return " ".join(parte for parte in s.strip(" ").split(" ") if parte)


def aparar(valor: Any) -> str:
    """Colapsa espaços e apara as pontas. **Preserva caixa e acento.**

    É a `NormalizarTexto` de mercadorias.
    """
    return _colapsar(texto_de(valor))


def sem_acento(valor: Any) -> str:
    """`Guardião` vira `Guardiao`. Nada mais muda."""
    decomposto = unicodedata.normalize("NFKD", texto_de(valor))
    return "".join(c for c in decomposto if not unicodedata.combining(c))


def chave_de_texto(valor: Any) -> str:
    """Maiúsculas, sem acento, sem espaço sobrando. **Para comparar.**

    É a `NormalizarTexto` de serviços, e é a única comparação de texto que o
    projeto usa — nome de coluna, nome de aba, rótulo de papel e de guardião.
    """
    return _colapsar(sem_acento(texto_de(valor)).upper())


def so_digitos(valor: Any) -> str:
    """Só o que for de `0` a `9`.

    CNPJ, chave de acesso e número de nota chegam pontuados de um lado e não
    do outro; é isto que faz os dois lados comparáveis.
    """
    return "".join(c for c in texto_de(valor) if "0" <= c <= "9")


def limpar_quebras(valor: Any) -> str:
    """Tira quebra de linha e o `_x000D_` que o XML do ASIS deixa para trás.

    A `Discriminação` da nota de serviço vem com quebras dentro da célula, e o
    retorno de carro escapado (`_x000D_`) atravessa a exportação como texto
    literal. Nos dois casos o destino é uma linha só.
    """
    texto = texto_de(valor)
    for quebra in ("_x000D_", "\r\n", "\r", "\n", "\t"):
        texto = texto.replace(quebra, " ")
    return _colapsar(texto)
