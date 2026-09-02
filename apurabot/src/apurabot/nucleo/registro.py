"""Camada 10 — Registro de Apuração do ICMS.

Espelho do livro que o ERP emite em PDF, uma folha por estabelecimento: as
entradas e as saídas por CFOP, com os valores fiscais separados entre operações
com e sem crédito (ou débito) do imposto, e o resumo em quatorze linhas que
fecha o imposto do período.

Duas naturezas convivem aqui, e é importante não confundi-las:

**Entradas e saídas são soma pura do Livro Fiscal.** Não há regra tributária
nesse bloco — é reclassificação e totalização do que já está escriturado. Por
isso ele fecha com o registro do ERP sem depender de nenhum parâmetro.

**O resumo é apuração.** É onde o estorno, o benefício fiscal e a centralização
se encontram. E é onde aparecem as linhas que não nascem de documento — 002,
003 por ajuste, 006, 007 e 009 —, que só podem vir declaradas pelo time fiscal.
Enquanto não vierem, saem zeradas e marcadas: o registro diz o que falta em vez
de fingir um total.

A linha 009 é a exceção que já tem endereço: o saldo credor do período anterior
é declarado por competência em `parametros/saldos.yaml` e chega aqui pronto,
aplicado pela apuração. As demais ainda esperam o relatório de ajustes.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from ..parametros import Parametros

# O primeiro dígito do CFOP diz a procedência (entradas) ou o destino (saídas).
# É a definição do próprio sistema de CFOP, não uma regra com vigência.
GRUPOS_ENTRADA = {1: "do Estado", 2: "de outros Estados", 3: "do Exterior"}
GRUPOS_SAIDA = {5: "para o Estado", 6: "para outros Estados", 7: "para o Exterior"}

ENTRADAS = "ENTRADAS"
SAIDAS = "SAÍDAS"
SEM_CFOP = "(lançamento sem CFOP)"


@dataclass
class ValoresFiscais:
    """As cinco colunas do livro, para um CFOP ou para um subtotal."""

    valor_contabil: float = 0.0
    base_calculo: float = 0.0
    imposto: float = 0.0
    isentas: float = 0.0
    outras: float = 0.0

    def somar(self, outro: "ValoresFiscais") -> None:
        self.valor_contabil += outro.valor_contabil
        self.base_calculo += outro.base_calculo
        self.imposto += outro.imposto
        self.isentas += outro.isentas
        self.outras += outro.outras

    def as_tuple(self) -> tuple[float, float, float, float, float]:
        return (self.valor_contabil, self.base_calculo, self.imposto,
                self.isentas, self.outras)


@dataclass
class LinhaCfop:
    cfop: int | None
    descricao: str
    grupo: str
    valores: ValoresFiscais = field(default_factory=ValoresFiscais)


@dataclass
class Bloco:
    """Um lado do livro — entradas ou saídas."""

    lado: str
    linhas: list[LinhaCfop] = field(default_factory=list)

    def subtotal(self, grupo: str) -> ValoresFiscais:
        v = ValoresFiscais()
        for linha in self.linhas:
            if linha.grupo == grupo:
                v.somar(linha.valores)
        return v

    @property
    def total(self) -> ValoresFiscais:
        v = ValoresFiscais()
        for linha in self.linhas:
            v.somar(linha.valores)
        return v

    def grupos(self) -> list[str]:
        ordem = GRUPOS_ENTRADA if self.lado == ENTRADAS else GRUPOS_SAIDA
        return list(ordem.values())


@dataclass
class LinhaResumo:
    """Uma das quatorze linhas do resumo da apuração."""

    codigo: int
    rotulo: str
    valor: float = 0.0
    discriminacao: list[tuple[str, float]] = field(default_factory=list)
    #: A linha depende de ajuste declarado e ele ainda não veio.
    aguarda_ajuste: bool = False


@dataclass
class Registro:
    estabelecimento: str
    uf: str
    cnpj: str
    inscricao_estadual: str
    competencia: str
    entradas: Bloco
    saidas: Bloco
    resumo: list[LinhaResumo] = field(default_factory=list)
    #: Rótulo alternativo — o totalizador não é documento de nenhuma filial.
    gerencial: bool = False

    def linha(self, codigo: int) -> LinhaResumo:
        for item in self.resumo:
            if item.codigo == codigo:
                return item
        raise KeyError(f"o resumo não tem a linha {codigo:03d}")

    @property
    def aguarda_ajustes(self) -> bool:
        return any(item.aguarda_ajuste for item in self.resumo)

    @property
    def confere_com_a_apuracao(self) -> bool:
        """O imposto creditado do livro é o crédito bruto da apuração.

        É a trava entre os dois blocos: se a soma por CFOP não bate com o que a
        apuração creditou, um dos dois leu o livro errado.
        """
        return abs(self.entradas.total.imposto - self.linha(5).valor) < 0.005


# --------------------------------------------------------------------------
# Montagem
# --------------------------------------------------------------------------

def montar(apuracao, params: Parametros, ajustes=None) -> list[Registro]:
    """Um registro por estabelecimento, na ordem em que a apuração os lista.

    Sem `ajustes`, valem os que a apuração concluiu — os que chegaram de fora
    mais os que vinham escritos nas linhas do Livro. Passar outros sobrepõe os
    dois, e serve para experimentar um cenário sem reapurar.
    """
    ajustes = ajustes if ajustes is not None else getattr(apuracao, "ajustes", None)
    cadastro = {
        " ".join(str(f["nome"]).split()): f
        for f in params.filiais.get("filiais") or []
    }
    por_estabelecimento = _blocos(apuracao.base)

    registros = []
    for filial in sorted(
        apuracao.filiais.values(), key=lambda f: (f.uf, f.estabelecimento)
    ):
        ficha = cadastro.get(filial.estabelecimento) or {}
        entradas, saidas = por_estabelecimento.get(
            filial.estabelecimento, (Bloco(ENTRADAS), Bloco(SAIDAS))
        )
        registros.append(
            Registro(
                estabelecimento=filial.estabelecimento,
                uf=filial.uf,
                cnpj=str(ficha.get("cnpj") or ""),
                inscricao_estadual=str(ficha.get("inscricao_estadual") or ""),
                competencia=apuracao.base.competencia,
                entradas=entradas,
                saidas=saidas,
                resumo=_resumo(filial, apuracao, ajustes),
            )
        )
    return registros


def totalizador(registros: list[Registro], competencia: str) -> Registro:
    """Soma dos estabelecimentos.

    Não é documento fiscal: consolida UFs diferentes, cada uma com a sua própria
    conta gráfica. Serve para enxergar o resultado do grupo de uma vez só — que
    é justamente o que o registro por filial não mostra.
    """
    entradas, saidas = Bloco(ENTRADAS), Bloco(SAIDAS)
    for lado, bloco in ((ENTRADAS, entradas), (SAIDAS, saidas)):
        acumulado: dict[tuple, LinhaCfop] = {}
        for registro in registros:
            origem = registro.entradas if lado == ENTRADAS else registro.saidas
            for linha in origem.linhas:
                alvo = acumulado.get((linha.cfop, linha.grupo))
                if alvo is None:
                    alvo = acumulado[(linha.cfop, linha.grupo)] = LinhaCfop(
                        cfop=linha.cfop, descricao=linha.descricao, grupo=linha.grupo
                    )
                alvo.valores.somar(linha.valores)
        bloco.linhas = _ordenar(list(acumulado.values()))

    resumo = []
    for modelo in (registros[0].resumo if registros else []):
        item = LinhaResumo(codigo=modelo.codigo, rotulo=modelo.rotulo)
        for registro in registros:
            outra = registro.linha(modelo.codigo)
            item.valor += outra.valor
            item.aguarda_ajuste = item.aguarda_ajuste or outra.aguarda_ajuste
        resumo.append(item)

    return Registro(
        estabelecimento="TOTALIZADOR — todos os estabelecimentos",
        uf="", cnpj="", inscricao_estadual="",
        competencia=competencia,
        entradas=entradas, saidas=saidas, resumo=resumo, gerencial=True,
    )


def _blocos(base) -> dict[str, tuple[Bloco, Bloco]]:
    """Agrupa o Livro Fiscal inteiro por estabelecimento, lado e CFOP."""
    montagem: dict[str, dict[str, dict[tuple, LinhaCfop]]] = {}

    for tratada in base.linhas:
        dados = tratada.origem.dados
        estabelecimento = " ".join(str(dados.get("estabelecimento") or "").split())
        cfop = tratada.origem.cfop_int
        prefixo = cfop // 1000 if cfop else None

        if prefixo in GRUPOS_ENTRADA:
            lado, grupo = ENTRADAS, GRUPOS_ENTRADA[prefixo]
        elif prefixo in GRUPOS_SAIDA:
            lado, grupo = SAIDAS, GRUPOS_SAIDA[prefixo]
        else:
            # Lançamento sem CFOP — o ERP também o exibe, com valor zerado.
            entrada = str(dados.get("entrada_saida") or "") != "Saída"
            lado, grupo = (ENTRADAS if entrada else SAIDAS), SEM_CFOP
            cfop = None

        por_lado = montagem.setdefault(estabelecimento, {ENTRADAS: {}, SAIDAS: {}})
        chave = (cfop, grupo)
        linha = por_lado[lado].get(chave)
        if linha is None:
            linha = por_lado[lado][chave] = LinhaCfop(
                cfop=cfop,
                descricao=str(dados.get("cfop_descricao") or "").strip(),
                grupo=grupo,
            )
        linha.valores.somar(
            ValoresFiscais(
                valor_contabil=_numero(dados.get("valor_contabil")),
                base_calculo=_numero(dados.get("base_icms")),
                imposto=_numero(dados.get("valor_icms")),
                isentas=_numero(dados.get("isentas_icms")),
                outras=_numero(dados.get("outras_icms")),
            )
        )

    resultado = {}
    for estabelecimento, por_lado in montagem.items():
        resultado[estabelecimento] = (
            Bloco(ENTRADAS, _ordenar(list(por_lado[ENTRADAS].values()))),
            Bloco(SAIDAS, _ordenar(list(por_lado[SAIDAS].values()))),
        )
    return resultado


def _ordenar(linhas: list[LinhaCfop]) -> list[LinhaCfop]:
    """Por CFOP crescente; o lançamento sem CFOP vai para o fim."""
    return sorted(linhas, key=lambda linha: (linha.cfop is None, linha.cfop or 0))


def _numero(valor) -> float:
    try:
        return float(valor or 0.0)
    except (TypeError, ValueError):
        return 0.0


def _resumo(filial, apuracao, ajustes) -> list[LinhaResumo]:
    """As quatorze linhas, na ordem e com os rótulos do livro."""
    nome = filial.estabelecimento
    declarados = bool(ajustes and ajustes.declarados(nome))

    def ajuste(campo: str) -> float:
        return ajustes.total(campo, nome) if ajustes else 0.0

    recebido = apuracao.debito_por_centralizacao(nome)

    l001 = LinhaResumo(1, "por Saídas/Prestações com Débito do Imposto", filial.debito)

    l002 = LinhaResumo(2, "Outros Débitos", ajuste("outros_debitos") + recebido)
    if recebido:
        l002.discriminacao.append(
            ("Recebimento de saldo devedor — estabelecimento centralizador", recebido)
        )
    if ajuste("outros_debitos"):
        l002.discriminacao.append(("Outros débitos declarados", ajuste("outros_debitos")))
    l002.aguarda_ajuste = not declarados and not recebido

    # O crédito indevido é crédito tomado que a regra manda devolver: no livro
    # ele mora na mesma linha do estorno.
    do_livro = filial.estorno + filial.credito_indevido
    l003 = LinhaResumo(3, "Estornos de Créditos", do_livro + ajuste("estorno_de_credito"))
    l003.discriminacao.append(("Estorno apurado sobre o Livro Fiscal", do_livro))
    if ajuste("estorno_de_credito"):
        l003.discriminacao.append(
            ("Estorno de créditos por ajuste de apuração", ajuste("estorno_de_credito"))
        )
    l003.aguarda_ajuste = not declarados

    l004 = LinhaResumo(4, "Sub Total", l001.valor + l002.valor + l003.valor)

    l005 = LinhaResumo(
        5, "por Entradas/Aquisições com Crédito do Imposto", filial.credito_bruto
    )
    l006 = LinhaResumo(6, "Outros Créditos", ajuste("outros_creditos"))
    l006.aguarda_ajuste = not declarados
    l007 = LinhaResumo(7, "Estornos de Débitos", ajuste("estorno_de_debito"))
    l007.aguarda_ajuste = not declarados

    l008 = LinhaResumo(8, "Sub Total", l005.valor + l006.valor + l007.valor)

    # A abertura da conta gráfica já foi resolvida pela apuração — parâmetro da
    # competência ou ajuste aprovado, nesta ordem. Aqui ela só é transcrita.
    l009 = LinhaResumo(
        9, "Saldo Credor do Período Anterior", filial.saldo_credor_anterior
    )
    l009.aguarda_ajuste = not apuracao.saldos_declarados and not (
        ajustes and nome in ajustes.saldo_credor_anterior
    )

    l010 = LinhaResumo(10, "Total", l008.valor + l009.valor)

    devedor = max(l004.valor - l010.valor, 0.0)
    l011 = LinhaResumo(11, "SALDO DEVEDOR (Débito menos Crédito)", devedor)

    l012 = LinhaResumo(12, "DEDUÇÕES", min(filial.credito_presumido, devedor))
    if filial.beneficio:
        l012.discriminacao.append((filial.beneficio.documento, l012.valor))

    l013 = LinhaResumo(13, "IMPOSTO A RECOLHER", max(l011.valor - l012.valor, 0.0))
    l014 = LinhaResumo(
        14, "SALDO CREDOR (Crédito menos Débito) a Transportar p/ o Período Seguinte",
        max(l010.valor - l004.valor, 0.0),
    )

    return [l001, l002, l003, l004, l005, l006, l007,
            l008, l009, l010, l011, l012, l013, l014]
