"""`Sem Correspondencia ASIS` — o que o ASIS deixou de capturar.

A pergunta que as outras três abas não respondem: **o ASIS está vendo tudo?**

Esta aba é a população inversa. Ela lista os lançamentos de serviço do Sankhya
que nenhuma das quatro chaves conseguiu casar com uma nota do ASIS, e para
cada um pergunta se aquele prestador aparece no ASIS **antes** e **depois** da
data de negociação do lançamento. Um fornecedor que aparece dos dois lados,
mas não naquele documento, sugere lacuna pontual de captura; um que não
aparece nunca sugere que o ASIS não cobre aquele município.

### O bloco de análise vem antes das colunas de origem

Sete colunas de análise, e só então o relatório do Portal de Compras inteiro,
reordenado. A ordem não é estética: o relatório chega a 268 colunas, e um
bloco de análise no fim da linha seria invisível para quem abre a planilha.

As colunas de origem saem em três blocos: as cinco pré-definidas (na ordem da
`Lancadas`), depois as que têm `CIDADE` no nome, depois todas as demais na
ordem original do arquivo. Coluna sem cabeçalho não entra.

### Três honestidades sobre os números

* **A comparação antes/depois é estrita.** Emissão do ASIS na mesma data do
  `Dt. Neg.` não conta nem como antes nem como depois. O dossiê duvidava; o
  código decidiu, e mudar isso moveria as contagens da execução de referência.
* **`Dt. Neg.` ausente não é avaliada.** As colunas 1 e 3 recebem
  `Dt. Neg. ausente` e as 2 e 4 ficam vazias — a ferramenta diz que não sabe,
  em vez de responder "Não".
* **`Diferenca` compara universos diferentes.** A contagem do lado das
  Entradas só inclui lançamentos TOP de serviço; a do lado do ASIS inclui
  **todas** as notas daquele CNPJ, canceladas e já lançadas inclusive. É
  métrica aproximada, o time já a lê assim, e preservá-la é preservar o
  significado da coluna.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Sequence

from ..escrita import Coluna
from ..texto import chave_de_texto, texto_de
from .enriquecimento import Cadastro
from .fontes import NotaDeServico, Registro
from . import colunas as col

#: O que as colunas 1 e 3 dizem quando o lançamento não tem data de negociação.
DATA_AUSENTE = "Dt. Neg. ausente"


@dataclass
class PresencaNoAsis:
    """Quantas notas e quais datas de emissão o ASIS tem de cada prestador.

    O universo é o ASIS **completo**, canceladas inclusive. É decisão do
    código, e ela é coerente com a pergunta: aqui se mede o que o ASIS
    capturou, não o que está pendente.
    """

    quantidade: dict[str, int] = field(default_factory=dict)
    emissoes: dict[str, list[Any]] = field(default_factory=dict)

    def quantas(self, cnpj: str) -> int:
        return self.quantidade.get(cnpj, 0)


def medir_presenca(notas: Sequence[NotaDeServico]) -> PresencaNoAsis:
    """Percorre o ASIS inteiro e monta a contagem e as datas por prestador."""
    presenca = PresencaNoAsis()
    for nota in notas:
        cnpj = nota.cnpj_do_prestador
        if not cnpj:
            continue
        presenca.quantidade[cnpj] = presenca.quantidade.get(cnpj, 0) + 1
        if nota.emissao_e_data and nota.emissao:
            presenca.emissoes.setdefault(cnpj, []).append(nota.emissao)
    return presenca


def ordem_das_colunas(cabecalho: Sequence[Any],
                      predefinidas: Sequence[int]) -> list[int]:
    """As posições das colunas de origem, nos três blocos, sem repetir nenhuma."""
    ultima = -1
    for i, nome in enumerate(cabecalho):
        if texto_de(nome).strip():
            ultima = i
    largura = ultima + 1

    ordem: list[int] = []
    usada = [False] * largura
    for posicao in predefinidas:
        if 0 <= posicao < largura and not usada[posicao]:
            ordem.append(posicao)
            usada[posicao] = True
    for i in range(largura):
        if not usada[i] and col.TRECHO_DE_CIDADE in chave_de_texto(cabecalho[i]):
            ordem.append(i)
            usada[i] = True
    for i in range(largura):
        if not usada[i] and texto_de(cabecalho[i]).strip():
            ordem.append(i)
            usada[i] = True
    return ordem


def colunas_da_aba(cabecalho: Sequence[Any], ordem: Sequence[int]) -> list[Coluna]:
    """As 7 de análise mais as de origem, com o formato de cada uma.

    Só duas colunas de origem ganham formato: a primeira (`Nro. Nota`, texto,
    para o número não virar notação científica) e a quarta (`Vlr. Nota`,
    valor). É o que o VBA formata, e as posições são as mesmas porque o bloco
    pré-definido é fixo.
    """
    saida = list(col.ANALISE_DA_INVERSA)
    for i, posicao in enumerate(ordem):
        rotulo = texto_de(cabecalho[posicao])
        formato = "geral"
        if i == 0:
            formato = "texto"
        elif i == 3:
            formato = "valor"
        saida.append(Coluna(rotulo, formato))
    return saida


def _antes_e_depois(emissoes: Sequence[Any], negociacao: Any
                    ) -> tuple[bool, Any, bool, Any]:
    """A emissão mais próxima antes e a mais próxima depois. **Estrito.**"""
    anterior = posterior = None
    for emissao in emissoes:
        if emissao < negociacao:
            if anterior is None or emissao > anterior:
                anterior = emissao
        elif emissao > negociacao:
            if posterior is None or emissao < posterior:
                posterior = emissao
    return (anterior is not None, anterior or "",
            posterior is not None, posterior or "")


def _dia(valor: Any) -> Any:
    data = getattr(valor, "date", None)
    if callable(data):
        return data()
    return valor if hasattr(valor, "year") else None


def analisar(lancamento: Registro, cadastro: Cadastro,
             presenca: PresencaNoAsis) -> list[Any]:
    """As sete colunas de análise de um lançamento sem correspondência."""
    cnpj = lancamento.cnpj_do_parceiro
    negociacao = _dia(lancamento.data_de_negociacao)

    if negociacao is None:
        antes, anterior, depois, posterior = DATA_AUSENTE, "", DATA_AUSENTE, ""
    else:
        tem_antes, anterior, tem_depois, posterior = _antes_e_depois(
            [d for d in (_dia(e) for e in presenca.emissoes.get(cnpj, ()))
             if d is not None],
            negociacao,
        )
        antes = "Sim" if tem_antes else "Nao"
        depois = "Sim" if tem_depois else "Nao"

    entradas = cadastro.quantos_lancamentos(cnpj)
    no_asis = presenca.quantas(cnpj)
    return [antes, anterior, depois, posterior,
            entradas, no_asis, entradas - no_asis]


def montar(lancamentos: Sequence[Registro], consumidos: Sequence[bool],
           cabecalho_do_portal: Sequence[Any], cadastro: Cadastro,
           presenca: PresencaNoAsis) -> tuple[list[Coluna], list[list[Any]]]:
    """A aba inteira: as colunas e as linhas dos lançamentos não consumidos."""
    predefinidas = []
    normalizado = [chave_de_texto(n) for n in cabecalho_do_portal]
    for nome in col.PREDEFINIDAS_DA_INVERSA:
        alvo = chave_de_texto(nome)
        predefinidas.append(normalizado.index(alvo) if alvo in normalizado else -1)

    ordem = ordem_das_colunas(cabecalho_do_portal,
                              [p for p in predefinidas if p >= 0])
    colunas = colunas_da_aba(cabecalho_do_portal, ordem)

    linhas = []
    for posicao, lancamento in enumerate(lancamentos):
        if consumidos[posicao]:
            continue
        analise = analisar(lancamento, cadastro, presenca)
        origem = [lancamento.linha[p] if p < len(lancamento.linha) else ""
                  for p in ordem]
        linhas.append(analise + origem)
    return colunas, linhas
