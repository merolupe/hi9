"""Os ajustes a lançar no Sankhya — o Registro desmontado em lançamentos.

No Sankhya as linhas 002, 003, 006, 007 e 012 do Registro de Apuração não se
digitam como total. Cada parcela é um lançamento em "Ajuste de Apuração", com o
Tipo apuração (a linha), o valor e uma Observação padrão — o código que carrega
o texto legal. É esse o relatório que o Sankhya devolve ("Ajuste de Apuração":
Nome Fantasia, Tipo apuração, Valor, Observação padrão, Observação).

A aba AJUSTES MANUAIS da planilha só mostra o que alguém declarou. Mas a maior parte do
que se lança é o que a própria apuração calculou — estorno, crédito indevido,
DIFAL, as duas pontas da centralização e o benefício. Este módulo junta as duas
coisas numa lista só, um lançamento por linha, na forma do relatório do Sankhya:
é o roteiro para lançar um a um e conferir depois.

O código de cada parcela calculada vem de `parametros/lancamentos_sankhya.yaml`,
com vigência. Parcela sem código cadastrado sai sem código e marcada — nunca
com um código parecido (regra 4 do repositório).

A soma dos lançamentos de cada linha tem que dar o valor da linha no Registro.
Se não der, a lista sai com a divergência, em vez de esconder o que faltou.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .nucleo import registro as reg

#: Linha do Registro → "Tipo apuração" do Sankhya. É a definição do próprio
#: Registro de Apuração, não regra com vigência.
TIPO_APURACAO = {
    2: "Outros débitos",
    3: "Estorno de créditos",
    6: "Outros créditos",
    7: "Estorno de débitos",
    12: "Deduções do imposto apurado",
}

#: O que cada parcela calculada é, em palavras, para a coluna "de onde vem".
ORIGEM = {
    "estorno": "calculado — estorno da regra do regime sobre o Livro",
    "credito_indevido": "calculado — crédito indevido (CFOP 2152)",
    "difal": "calculado — DIFAL do Livro (coluna Diferença ICMS)",
    "centralizacao_recebe_debito": "calculado — centralização, saldo devedor recebido",
    "centralizacao_transfere_debito": "calculado — centralização, saldo devedor transferido",
    "centralizacao_recebe_credito": "calculado — centralização, saldo credor recebido",
    "centralizacao_transfere_credito": "calculado — centralização, saldo credor transferido",
    "beneficio": "calculado — benefício fiscal (linha 012)",
}

CENTAVO = 0.005


@dataclass
class Lancamento:
    """Um lançamento de "Ajuste de Apuração" no Sankhya."""

    estabelecimento: str
    linha: int
    valor: float
    #: A parcela calculada (chave de `ORIGEM`) ou "declarado".
    parcela: str
    observacao_padrao: str = ""
    #: O texto que a observação padrão carrega, do catálogo do parâmetro.
    texto: str = ""
    #: O que não cabe no texto padrão: o motivo do ajuste declarado.
    complemento: str = ""
    origem: str = ""

    @property
    def tipo(self) -> str:
        return TIPO_APURACAO[self.linha]

    @property
    def sem_codigo(self) -> bool:
        return not self.observacao_padrao


@dataclass
class Divergencia:
    """Linha do Registro que os lançamentos não reproduzem."""

    estabelecimento: str
    linha: int
    lancado: float
    registro: float

    @property
    def diferenca(self) -> float:
        return self.lancado - self.registro


@dataclass
class Roteiro:
    """Os lançamentos da competência e a conferência contra o Registro."""

    competencia: str
    lancamentos: list[Lancamento] = field(default_factory=list)
    #: (estabelecimento, linha, soma dos lançamentos, valor do Registro).
    conferencia: list[tuple[str, int, float, float]] = field(default_factory=list)
    #: Estabelecimentos cujo Registro ainda espera a conferência dos ajustes.
    aguardando: list[str] = field(default_factory=list)

    @property
    def divergencias(self) -> list[Divergencia]:
        return [
            Divergencia(nome, linha, lancado, alvo)
            for nome, linha, lancado, alvo in self.conferencia
            if abs(lancado - alvo) >= CENTAVO
        ]

    @property
    def sem_codigo(self) -> list[Lancamento]:
        return [x for x in self.lancamentos if x.sem_codigo]


# --------------------------------------------------------------------------
# Montagem
# --------------------------------------------------------------------------

def montar(apuracao, params, registros: list[reg.Registro] | None = None,
           ajustes=None) -> Roteiro:
    """Um lançamento por parcela, estabelecimento a estabelecimento.

    `registros` e `ajustes` são os mesmos que a aba REGISTRO DE APURAÇÃO usou — passar os
    dois garante que a conferência compara com o Registro que saiu na planilha.
    """
    ajustes = ajustes if ajustes is not None else apuracao.ajustes
    if registros is None:
        registros = reg.montar(apuracao, params, ajustes)
    competencia = apuracao.base.competencia
    catalogo = _catalogo(params)
    cadastro = {
        " ".join(str(f["nome"]).split()): f
        for f in params.filiais.get("filiais") or []
    }

    roteiro = Roteiro(competencia=competencia)
    for registro in registros:
        if registro.gerencial:
            continue
        nome = registro.estabelecimento
        filial = apuracao.filiais.get(nome)
        if filial is None:
            continue
        beneficio = str((cadastro.get(nome) or {}).get("beneficio_fiscal") or "")
        centralizacao = apuracao.centralizacao_no_registro(nome)

        calculados = [
            ("difal", 2, filial.difal_na_conta),
            ("centralizacao_recebe_debito", 2, centralizacao.recebe_debito),
            ("centralizacao_transfere_credito", 2, centralizacao.transfere_credito),
            ("estorno", 3, filial.estorno),
            ("credito_indevido", 3, filial.credito_indevido),
            ("centralizacao_recebe_credito", 6, centralizacao.recebe_credito),
            ("centralizacao_transfere_debito", 6, centralizacao.transfere_debito),
            ("beneficio", 12, registro.linha(12).valor),
        ]
        daqui: list[Lancamento] = []
        for parcela, linha, valor in calculados:
            if abs(valor) < CENTAVO:
                continue
            codigo = _codigo_da_parcela(params, parcela, filial, beneficio,
                                        competencia)
            daqui.append(Lancamento(
                estabelecimento=nome, linha=linha, valor=round(valor, 2),
                parcela=parcela, observacao_padrao=codigo,
                texto=catalogo.get(codigo, ""), origem=ORIGEM[parcela],
            ))

        for ajuste in (ajustes.lancamentos if ajustes else []):
            if ajuste.estabelecimento != nome:
                continue
            codigo = str(ajuste.observacao_padrao or "")
            daqui.append(Lancamento(
                estabelecimento=nome, linha=ajuste.linha,
                valor=round(ajuste.valor, 2), parcela="declarado",
                observacao_padrao=codigo, texto=catalogo.get(codigo, ""),
                complemento=ajuste.motivo,
                origem=f"declarado — {ajuste.onde}" if ajuste.onde else "declarado",
            ))

        daqui.sort(key=lambda x: x.linha)
        roteiro.lancamentos.extend(daqui)

        for linha in TIPO_APURACAO:
            lancado = sum(x.valor for x in daqui if x.linha == linha)
            alvo = registro.linha(linha).valor
            if abs(lancado) >= CENTAVO or abs(alvo) >= CENTAVO:
                roteiro.conferencia.append((nome, linha, lancado, alvo))
        if registro.aguarda_ajustes:
            roteiro.aguardando.append(nome)

    return roteiro


def _catalogo(params) -> dict[str, str]:
    """Código da observação padrão → texto, como o Sankhya mostra."""
    bruto = (params.lancamentos_sankhya or {}).get("observacoes_padrao") or {}
    return {
        str(codigo): " ".join(str((item or {}).get("texto") or "").split())
        for codigo, item in bruto.items()
    }


def _codigo_da_parcela(params, parcela: str, filial, beneficio: str,
                       competencia: str) -> str:
    """A observação padrão da parcela, ou vazio se nenhuma regra casar.

    Uma regra casa quando a parcela é a mesma, cada filtro que ela declara
    (`regime`, `uf`, `beneficio`) bate com o estabelecimento e a competência
    está dentro da vigência.
    """
    for regra in (params.lancamentos_sankhya or {}).get("calculados") or []:
        if regra.get("parcela") != parcela:
            continue
        if "regime" in regra and regra["regime"] != filial.regime:
            continue
        if "uf" in regra and str(regra["uf"]).upper() != str(filial.uf).upper():
            continue
        if "beneficio" in regra and regra["beneficio"] != beneficio:
            continue
        if not _vigente(regra, competencia):
            continue
        return str(regra.get("observacao_padrao") or "")
    return ""


def _vigente(regra: dict, competencia: str) -> bool:
    """A competência (AAAA-MM) está dentro de `vigencia_inicio`/`vigencia_fim`?"""
    inicio = str(regra.get("vigencia_inicio") or "")[:7]
    fim = str(regra.get("vigencia_fim") or "")[:7]
    if inicio and competencia < inicio:
        return False
    if fim and competencia > fim:
        return False
    return True
