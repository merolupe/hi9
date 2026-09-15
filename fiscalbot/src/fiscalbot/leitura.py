"""Achar o cabeçalho e as colunas — por nome, nunca por posição.

O relatório do Sankhya muda de layout: colunas entram, saem e trocam de lugar
entre uma extração e outra. Procurar a coluna pelo **nome** é o que faz a
ferramenta sobreviver a isso. Os nomes aceitos de cada campo ficam em
`parametros.sinonimos`, editáveis na tela — quando a extração mudar o nome de
uma coluna, se acrescenta o nome novo ali, sem tocar em código.

O cabeçalho também não fica numa linha fixa: as primeiras linhas trazem título,
data de emissão e usuário. A linha do cabeçalho é a mais preenchida das 15
primeiras.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Any

from .modelo import Parametros
from .planilha import LayoutInvalido

#: Nomes aceitos de cada campo quando a base não diz outra coisa. Vieram do
#: VBA, e são a rede para o caso de alguém esvaziar a lista na tela.
SINONIMOS_PADRAO: dict[str, tuple[str, ...]] = {
    "ES": ("Entrada/Saida", "Entrada / Saida", "E/S"),
    "CST": ("Cod. de tributacao", "Codigo de tributacao", "CST"),
    "ICMS": ("Vlr. do ICMS", "Valor do ICMS", "Vlr ICMS"),
    "CFOP": ("CFOP",),
    "UFO": ("UF de Origem", "UF Origem", "UF Orig"),
    "UFD": ("UF de Destino", "UF Destino", "UF Dest"),
    "PROD": ("Produto", "Cod Produto", "Codigo do Produto"),
    "ALIQ": ("Aliquota ICMS", "Aliq ICMS", "Aliquota"),
    "VCONT": ("Vlr. contabil", "Valor contabil", "Vlr contabil"),
    "ESP": ("Especie do documento", "Especie", "Esp documento"),
    "PARC": ("Empresa/Parceiro", "Parceiro", "Empresa Parceiro"),
    "PARCNOME": ("Descricao Parceiro/Empresa", "Descricao Parceiro Empresa",
                 "Parceiro/Empresa"),
    "ORIGEM": ("Origem",),
    "DESCPROD": ("Descricao (Produto)", "Descricao Produto", "Descricao do Produto"),
    "NUNOTA": ("Nro unico Nota", "Nro. unico Nota", "Numero unico Nota",
               "Nro Unico Nota"),
    "DESCTIPO": ("Descricao (Tipo de Operacao)", "Descricao Tipo de Operacao",
                 "Descricao do Tipo de Operacao"),
    "NOMEFANT": ("Nome Fantasia (Empresa)", "Nome Fantasia Empresa", "Nome Fantasia"),
    "DESCCFOP": ("Descricao da CFOP", "Descricao CFOP", "Desc CFOP"),
}

#: Sem estas o relatório não é auditável. O nome amigável é o da mensagem de erro.
OBRIGATORIAS = {
    "ES": "Entrada/Saida", "CST": "Cod. de tributacao", "ICMS": "Vlr. do ICMS",
    "CFOP": "CFOP", "UFO": "UF de Origem", "UFD": "UF de Destino",
    "PROD": "Produto", "ALIQ": "Aliquota ICMS", "VCONT": "Vlr. contabil",
    "ESP": "Especie do documento", "PARC": "Empresa/Parceiro",
    "PARCNOME": "Descricao Parceiro/Empresa",
}

#: As que ajudam mas não impedem: sem elas, a camada correspondente não roda.
OPCIONAIS = ("ORIGEM", "DESCPROD", "NUNOTA", "DESCTIPO", "NOMEFANT", "DESCCFOP")


def normalizar(texto: str) -> str:
    """Minúscula, sem acento e sem espaço duplo — para comparar nome de coluna."""
    sem_acento = "".join(
        c for c in unicodedata.normalize("NFKD", str(texto))
        if not unicodedata.combining(c)
    )
    return re.sub(r"\s+", " ", sem_acento.strip().lower())


def localizar_cabecalho(linhas: list[list[Any]]) -> int:
    """O índice da linha de cabeçalho: a mais preenchida das 15 primeiras.

    Antes dela vêm título, data de emissão e usuário — que ocupam poucas
    células. Menos de 5 células preenchidas não é cabeçalho de relatório.
    """
    melhor, melhor_n = -1, 0
    for i, linha in enumerate(linhas[:15]):
        n = sum(1 for v in linha[:70] if str(v).strip())
        if n > melhor_n:
            melhor, melhor_n = i, n
    return melhor if melhor_n >= 5 else -1


@dataclass(frozen=True)
class MapaDeColunas:
    """Em que coluna está cada campo. `-1` quando a coluna não existe."""

    posicoes: dict[str, int]

    def __getattr__(self, campo: str) -> int:
        try:
            return self.posicoes[campo.upper()]
        except KeyError as erro:
            raise AttributeError(campo) from erro

    def tem(self, campo: str) -> bool:
        return self.posicoes.get(campo.upper(), -1) >= 0


def sinonimos_de(campo: str, parametros: Parametros) -> tuple[str, ...]:
    da_base = parametros.sinonimos.get(campo.upper())
    if da_base:
        return da_base
    return SINONIMOS_PADRAO.get(campo.upper(), ())


def achar_coluna(cabecalho: list[Any], campo: str, parametros: Parametros) -> int:
    normalizado = [normalizar(v) for v in cabecalho]
    for nome in sinonimos_de(campo, parametros):
        alvo = normalizar(nome)
        if not alvo:
            continue
        for i, atual in enumerate(normalizado):
            if atual == alvo:
                return i
    return -1


def mapear(cabecalho: list[Any], parametros: Parametros) -> MapaDeColunas:
    """Localiza todas as colunas. Estoura quando falta uma obrigatória."""
    posicoes = {
        campo: achar_coluna(cabecalho, campo, parametros)
        for campo in list(OBRIGATORIAS) + list(OPCIONAIS)
    }
    faltando = [nome for campo, nome in OBRIGATORIAS.items() if posicoes[campo] < 0]
    if faltando:
        raise LayoutInvalido(
            "Coluna(s) obrigatória(s) não localizada(s) no relatório:\n\n  "
            + "\n  ".join(faltando)
            + "\n\nSe a extração mudou o nome da coluna, acrescente o nome novo "
              "em Sinônimos, na tela de configuração do Fiscalbot."
        )
    return MapaDeColunas(posicoes)


# -- extração de valor -----------------------------------------------------
# O relatório mistura número e texto na mesma coluna conforme a extração.
# Estas funções reproduzem, valor a valor, o que o VBA fazia.

def extrair_cst(valor: Any) -> str:
    """`41-Não tributada` vira `41`. São sempre os dois primeiros caracteres."""
    t = str(valor).strip()
    return t if len(t) < 2 else t[:2]


def extrair_cfop(valor: Any) -> str:
    """Vem numérico (`5552.0`); tem que virar `5552`, nunca `5552.0`."""
    if isinstance(valor, (int, float)) and not isinstance(valor, bool):
        return f"{int(valor)}" if float(valor) == int(valor) else str(valor)
    return str(valor).strip().replace(" ", "")


def extrair_produto(valor: Any) -> str:
    """Código de produto é código: `606000001.0` vira `606000001`."""
    if isinstance(valor, (int, float)) and not isinstance(valor, bool):
        if float(valor) == int(valor):
            return f"{int(valor)}"
        return str(valor).strip()
    t = str(valor).strip()
    return t[:-2] if t.endswith((".0", ",0")) else t


def parse_numero(valor: Any) -> tuple[float, bool]:
    """Devolve `(número, veio_preenchido)`.

    Célula vazia vira `0` com `veio_preenchido = False` — a diferença importa
    na carga efetiva, onde valor contábil ausente é advertência, não zero.
    """
    if valor is None or str(valor).strip() == "":
        return 0.0, False
    if isinstance(valor, (int, float)) and not isinstance(valor, bool):
        return float(valor), True
    texto = str(valor).strip().replace(".", "").replace(",", ".")
    try:
        return float(texto), True
    except ValueError:
        return 0.0, False
