"""As chaves de identidade: chave de acesso, CNPJ e número de NFS-e.

Mercadorias tem uma chave natural — a `Chave Acesso`, 44 dígitos. Serviços
não tem nenhuma, e é por isso que o confronto de lá precisa de quatro chaves
construídas. Os três normalizadores ficam aqui, no núcleo, porque os dois
domínios e o livro de classificação usam os mesmos.

O que **não** está aqui: a cascata de confronto de serviços, que é regra de
domínio e vem na entrega seguinte.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .texto import so_digitos, texto_de

#: O CNPJ que o Portal de Compras usa como "sem parceiro". Não indexa nada.
CNPJ_ZERADO = "00000000000000"


def chave_de_acesso(valor: Any) -> str:
    """Os 44 dígitos da chave, sem pontuação, sem espaço, sem apóstrofo.

    **Hoje o confronto XML × Conferência de Entradas não passa por aqui**: o
    VBA compara as duas strings como vieram, e a integridade da chave é
    sustentada por formatar a coluna como Texto antes de escrever, não por
    normalizar. Normalizar os dois lados é o defeito 11 do porte e espera
    medição — o número de confrontos que passariam a casar é, ele próprio, um
    achado a levar ao time fiscal.

    A função existe e é usada desde já no **livro de classificação**, que é
    nosso: lá a chave é gravada normalizada, porque lá não há macro com que
    divergir.
    """
    return so_digitos(valor)


def cnpj(valor: Any) -> str:
    """CNPJ ou CPF sem pontuação. Vazio e zerado continuam distinguíveis."""
    return so_digitos(valor)


def cnpj_utilizavel(valor: Any) -> bool:
    """Falso para vazio e para `00000000000000`.

    O VBA simplesmente não indexa esses lançamentos — eles somem da análise
    sem contagem e sem aviso. Aqui a decisão é a mesma, mas o motor de
    serviços passa a **contar** quantos ficaram de fora, e a contagem vai para
    a tela.
    """
    digitos = cnpj(valor)
    return bool(digitos) and digitos != CNPJ_ZERADO


@dataclass(frozen=True)
class NumeroDeNota:
    """O número de NFS-e normalizado, e o que foi preciso fazer com ele."""

    valor: str
    cortou_prefixo_de_ano: bool = False
    removeu_zeros_a_esquerda: bool = False


def analisar_numero_de_nfse(valor: Any) -> NumeroDeNota:
    """A gramática do Portal Nacional, passo a passo — e o que ela cortou.

    O Portal Nacional emite número com o ano na frente (`202600012345`), e o
    Sankhya guarda o número sem ele. Sem este corte, nota nenhuma casa.

    Quatro passos, na ordem do VBA:

    1. só dígitos (de número, `Format "0"` antes, para não virar notação
       científica);
    2. se tem 13 dígitos ou mais e começa em `20`, **corta os 4 primeiros**;
    3. tira zeros à esquerda, preservando ao menos um dígito;
    4. string vazia vira `0`.

    O passo 2 é uma suposição declarada: *lançamento do Sankhya não tem número
    com 10 dígitos ou mais*. No dia em que tiver, o número é mutilado em
    silêncio. Por isso esta função devolve `cortou_prefixo_de_ano` — a tela do
    motor de serviços conta quantos sofreram o corte, para a suposição deixar
    de ser invisível.
    """
    if isinstance(valor, (int, float)) and not isinstance(valor, bool):
        # `Format$(v, "0")` do VBA: número vira inteiro, e nunca notação
        # científica — é o que impede `2,02600012345E+11` de virar chave.
        bruto = str(int(round(valor)))
    else:
        bruto = texto_de(valor)

    digitos = so_digitos(bruto)
    cortou = len(digitos) >= 13 and digitos[:2] == "20"
    if cortou:
        digitos = digitos[4:]

    sem_zeros = digitos
    while len(sem_zeros) > 1 and sem_zeros[0] == "0":
        sem_zeros = sem_zeros[1:]
    removeu = sem_zeros != digitos

    return NumeroDeNota(sem_zeros or "0", cortou, removeu)


def numero_de_nfse(valor: Any) -> str:
    """O número de NFS-e normalizado. Atalho para `analisar_numero_de_nfse`."""
    return analisar_numero_de_nfse(valor).valor
