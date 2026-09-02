"""Camadas 5 a 8 — apuração de ICMS por estabelecimento.

Aplica o regime de cada filial sobre a base tratada e consolida crédito bruto,
crédito mantido, estorno e débito. Onde a UF exige — hoje MS —, o resultado sai
também segregado por atividade, porque é a segregação que dimensiona o
benefício fiscal.

Centralização de SP e DIFAL ficam para as entregas seguintes.
"""
from __future__ import annotations

import collections
import copy
from dataclasses import dataclass, field
from typing import Any

from . import ajustes as aj
from .base_tratada import BaseTratada
from .nucleo import atividade as ativ
from .nucleo import centralizacao as centr
from .nucleo.beneficio import ResultadoBeneficio
from .nucleo.beneficio import calcular as calcular_beneficio
from .nucleo.estorno import ResultadoEstorno, calcular
from .parametros import Parametros


def de_declarados(declarados: aj.Declarados) -> AjustesDaApuracao:
    """Converte o que a aba AJUSTES trouxe no que a apuração consome."""
    ajustes = AjustesDaApuracao()
    for parcela in declarados.parcelas:
        ajustes.somar(parcela)
    ajustes.conferencia = dict(declarados.conferencia)
    ajustes.recusados = list(declarados.erros)
    return ajustes


def ler_ajustes(caminho) -> AjustesDaApuracao:
    """Os ajustes da aba AJUSTES de um arquivo devolvido pelo time fiscal."""
    return de_declarados(aj.ler_aba(caminho))


def mes_vizinho(competencia: str, passo: int) -> str:
    """'2026-07' e -1 → '2026-06'. Devolve vazio se a competência não tem forma.

    Serve para dizer de onde veio e para onde vai o saldo credor, que é a única
    coisa na apuração que atravessa a virada do mês.
    """
    try:
        ano, mes = (int(parte) for parte in str(competencia).split("-", 1))
    except (TypeError, ValueError):
        return ""
    total = ano * 12 + (mes - 1) + passo
    return f"{total // 12:04d}-{total % 12 + 1:02d}"


@dataclass
class AjustesDaApuracao:
    """Lançamentos que não nascem de documento no Livro Fiscal.

    São as linhas 002, 003, 006, 007 e 009 do Registro de Apuração: outros
    débitos, estornos de créditos por ajuste, outros créditos, estornos de
    débitos e o saldo credor do período anterior. Nenhum deles pode ser deduzido
    do Livro — são decisões da apuração, aprovadas pelo time fiscal.

    Chegam por duas portas, que somam na mesma linha do Registro: as colunas
    `ajuste_*` da BASE TRATADA, quando o ajuste pertence a um documento, e a aba
    AJUSTES, quando não pertence a nenhum. Ver `ajustes.py`.
    """

    # {estabelecimento: {atividade: valor}}
    estorno_de_credito: dict[str, dict[str, float]] = field(default_factory=dict)
    outros_debitos: dict[str, dict[str, float]] = field(default_factory=dict)
    outros_creditos: dict[str, dict[str, float]] = field(default_factory=dict)
    estorno_de_debito: dict[str, dict[str, float]] = field(default_factory=dict)

    # {estabelecimento: valor} — não se reparte por atividade.
    saldo_credor_anterior: dict[str, float] = field(default_factory=dict)

    #: Todo lançamento aceito, na ordem em que foi lido. É a memória de quem
    #: mudou o Registro, por quê e com aprovação de quem.
    lancamentos: list[aj.Ajuste] = field(default_factory=list)
    #: Marcado sem lançar. Não muda o Registro — e não pode sumir por isso.
    anotacoes: list[aj.Ajuste] = field(default_factory=list)
    #: Quem assinou a conferência de cada estabelecimento.
    conferencia: dict[str, aj.Conferencia] = field(default_factory=dict)
    #: Ajuste informado pela metade, recusado com o motivo.
    recusados: list[str] = field(default_factory=list)

    def somar(self, ajuste: aj.Ajuste, atividade: str = "") -> None:
        """Lança um ajuste já validado na linha do Registro que ele escolheu.

        Anotação não entra em linha nenhuma: fica guardada para o relatório.
        """
        if ajuste.anotacao:
            self.anotacoes.append(ajuste)
            return
        if atividade:
            ajuste.atividade = atividade
        mapa = getattr(self, ajuste.campo).setdefault(ajuste.estabelecimento, {})
        mapa[ajuste.atividade] = mapa.get(ajuste.atividade, 0.0) + ajuste.valor
        self.lancamentos.append(ajuste)

    @property
    def marcado_nao_lancado(self) -> float:
        """Quanto está marcado como indevido e ainda não estornado."""
        return sum(a.valor for a in self.anotacoes)

    #: Campos que alimentam linhas do Registro de Apuração e por isso precisam
    #: ser declarados antes de o registro fechar.
    CAMPOS_DO_REGISTRO = (
        "outros_debitos", "estorno_de_credito", "outros_creditos",
        "estorno_de_debito",
    )

    def de(self, campo: str, estabelecimento: str, atividade: str) -> float:
        mapa = getattr(self, campo).get(estabelecimento) or {}
        return float(mapa.get(atividade) or 0.0)

    def total(self, campo: str, estabelecimento: str) -> float:
        """Soma de um ajuste em todas as atividades do estabelecimento."""
        mapa = getattr(self, campo).get(estabelecimento) or {}
        return float(sum(mapa.values()))

    def declarados(self, estabelecimento: str) -> bool:
        """Houve declaração de ajuste para este estabelecimento?

        Enquanto não houver, o registro sai com as linhas de ajuste zeradas e
        marcadas — nunca preenchidas por conta própria.

        A conferência assinada é a resposta limpa, e vale mesmo sem ajuste
        nenhum: célula vazia diz ao mesmo tempo "não tem" e "ninguém olhou", e
        a ferramenta não pode escolher uma. Um lançamento também conta — quem
        lançou, olhou.
        """
        if estabelecimento in self.conferencia:
            return True
        return any(
            estabelecimento in getattr(self, campo)
            for campo in self.CAMPOS_DO_REGISTRO
        ) or estabelecimento in self.saldo_credor_anterior


@dataclass
class LinhaApurada:
    """O que a apuração concluiu sobre uma linha do Livro Fiscal.

    Vive na memória da apuração, não na base tratada: a base trata a base, e o
    que a apuração decide sobre cada linha é resultado, não tratamento. É esta
    lista que alimenta a conferência por CFOP e produto.
    """

    tratada: Any
    resultado: ResultadoEstorno
    atividade: str = ""
    destino: str | None = None

    @property
    def credito_a_apropriar(self) -> float:
        return self.resultado.credito_mantido

    @property
    def credito_a_estornar(self) -> float:
        """Estorno somado ao crédito indevido — os dois saem da conta gráfica."""
        return self.resultado.estorno + self.resultado.credito_indevido

    @property
    def confere(self) -> bool:
        soma = self.credito_a_apropriar + self.credito_a_estornar
        return abs(soma - self.resultado.credito_bruto) < 0.005


@dataclass
class ApuracaoFilial:
    """Resultado de um estabelecimento, antes de centralização."""

    estabelecimento: str
    uf: str
    regime: str
    codigo: int | None = None
    #: Linha 009 do Registro — o crédito que veio do mês anterior. Não nasce do
    #: Livro Fiscal: vem declarado em `parametros/saldos.yaml`.
    saldo_credor_anterior: float = 0.0
    #: Diferencial de alíquota das entradas de uso, consumo e ativo. Vem
    #: calculado do Livro Fiscal, na coluna `Diferença ICMS`.
    difal: float = 0.0
    #: A parte do DIFAL que entra na conta gráfica. A linha TOTAL soma filiais
    #: de UFs diferentes, então o destino não é um só: guardar o valor já
    #: decidido é o que deixa o total somável.
    difal_na_conta: float = 0.0
    #: O DIFAL desta UF entra na conta gráfica, ou é guia avulsa?
    difal_na_conta_grafica: bool = False
    #: Efeito líquido dos ajustes declarados sobre a conta, no sinal do caixa:
    #: as linhas 006 e 007 somam, as 002 e 003 subtraem. Não inclui o débito
    #: recebido por centralização, que é consequência da apuração e não parte
    #: dela — ele aparece na linha 002 do Registro e no saldo do grupo.
    ajustes_da_conta: float = 0.0
    credito_bruto: float = 0.0
    credito_mantido: float = 0.0
    estorno: float = 0.0
    credito_indevido: float = 0.0
    debito: float = 0.0
    linhas: int = 0
    beneficio: ResultadoBeneficio | None = None
    segrega_por_atividade: bool = False
    apuradas: list[LinhaApurada] = field(default_factory=list)
    por_atividade: dict[str, ativ.TotaisAtividade] = field(default_factory=dict)
    por_carga: dict = field(default_factory=lambda: collections.defaultdict(
        lambda: {"credito_bruto": 0.0, "credito_mantido": 0.0, "estorno": 0.0,
                 "credito_indevido": 0.0}
    ))

    #: Só a linha TOTAL usa: ela soma filiais e não tem benefício próprio.
    presumido_consolidado: float = 0.0

    @property
    def credito_presumido(self) -> float:
        if self.beneficio is not None:
            return self.beneficio.credito_presumido
        return self.presumido_consolidado

    @property
    def fadefe(self) -> float:
        """Guia avulsa — informativo, fora da conta gráfica."""
        return self.beneficio.fadefe if self.beneficio else 0.0

    @property
    def difal_em_guia(self) -> float:
        """O DIFAL que sai por fora — informativo, como o FADEFE."""
        return self.difal - self.difal_na_conta

    @property
    def saldo(self) -> float:
        """Convenção de caixa: **positivo é credor, negativo é devedor.**

        Saldo credor é dinheiro a favor — crédito que se leva para o mês
        seguinte. Saldo devedor sai do caixa. Por isso o sinal é o do efeito
        financeiro, e não o da conta gráfica, onde o débito é que é positivo.

        As linhas 011 a 014 do Registro de Apuração não seguem esta convenção:
        lá devedor e credor têm linhas próprias, ambas positivas, como o livro
        manda. Ver `nucleo/registro.py`.

        A conta abre com o saldo credor do mês anterior — a linha 009 do
        registro —, porque a conta gráfica é contínua: o crédito que sobrou não
        se perde na virada do mês. E fecha com os ajustes declarados, que são
        decisão da apuração tanto quanto o estorno que a regra calcula.

        O DIFAL entra onde a UF o cobra na conta gráfica, e fica de fora onde
        ele é guia avulsa. Em SP ele entra **antes da centralização**: é da
        unidade que fez a entrada, e é o saldo dela, já com o DIFAL, que vai
        para o grupo.

        Sem o débito recebido por centralização: esse é consequência da
        apuração, não parte dela.
        """
        return (
            self.credito_mantido
            + self.credito_presumido
            + self.saldo_credor_anterior
            + self.ajustes_da_conta
            - self.debito
            - self.difal_na_conta
        )

    @property
    def a_recolher(self) -> float:
        """O que sai do caixa — zero quando o saldo é credor."""
        return max(-self.saldo, 0.0) + 0.0      # o + 0.0 mata o "-0,00"

    @property
    def credor(self) -> float:
        """O crédito que se transporta para o mês seguinte — a linha 014.

        É a abertura do mês que vem: este número é o que vai para
        `parametros/saldos.yaml` na competência seguinte.
        """
        return max(self.saldo, 0.0) + 0.0

    @property
    def saldo_do_periodo(self) -> float:
        """O que a competência produziu sozinha, sem a abertura.

        Serve para separar duas perguntas que o saldo final mistura: o mês foi
        credor ou devedor, e o estabelecimento tem ou não crédito acumulado.
        """
        return self.saldo - self.saldo_credor_anterior

    @property
    def confere(self) -> bool:
        soma = self.credito_mantido + self.estorno + self.credito_indevido
        return abs(soma - self.credito_bruto) < 0.005

    def atividade(self, nome: str) -> ativ.TotaisAtividade:
        """Totais de uma atividade; vazios se ela não teve movimento."""
        return self.por_atividade.get(nome) or ativ.TotaisAtividade(atividade=nome)

    @property
    def atividades_sem_regra(self) -> ativ.TotaisAtividade | None:
        return self.por_atividade.get(ativ.SEM_REGRA)


@dataclass
class Apuracao:
    filiais: dict[str, ApuracaoFilial]
    base: BaseTratada
    centralizacao: list[centr.ResultadoCentralizacao] = field(default_factory=list)
    #: A competência tem saldo credor de abertura declarado?
    #: Competência não declarada não é competência que abre em zero: enquanto
    #: ninguém disser o que veio do mês anterior, a linha 009 sai marcada.
    saldos_declarados: bool = False
    #: Os ajustes que de fato valeram: os que chegaram de fora somados aos que
    #: vieram escritos nas linhas do Livro. É esta a versão que o Registro usa.
    ajustes: AjustesDaApuracao = field(default_factory=lambda: AjustesDaApuracao())
    #: Parcela da aba AJUSTES sem atividade, onde a UF exige a segregação.
    ajustes_sem_atividade: list[aj.Ajuste] = field(default_factory=list)

    @property
    def competencia(self) -> str:
        return self.base.competencia

    @property
    def competencia_anterior(self) -> str:
        """De onde veio o saldo credor de abertura."""
        return mes_vizinho(self.competencia, -1)

    @property
    def competencia_seguinte(self) -> str:
        """Para onde vai o saldo credor a transportar."""
        return mes_vizinho(self.competencia, +1)

    @property
    def total(self) -> ApuracaoFilial:
        t = ApuracaoFilial(estabelecimento="TOTAL", uf="", regime="")
        for f in self.filiais.values():
            t.credito_bruto += f.credito_bruto
            t.credito_mantido += f.credito_mantido
            t.estorno += f.estorno
            t.credito_indevido += f.credito_indevido
            t.debito += f.debito
            t.linhas += f.linhas
            t.saldo_credor_anterior += f.saldo_credor_anterior
            t.ajustes_da_conta += f.ajustes_da_conta
            t.difal += f.difal
            t.difal_na_conta += f.difal_na_conta
            t.presumido_consolidado += f.credito_presumido
        return t

    @property
    def credito_presumido(self) -> float:
        return sum(f.credito_presumido for f in self.filiais.values())

    @property
    def fadefe(self) -> float:
        return sum(f.fadefe for f in self.filiais.values())

    @property
    def difal(self) -> float:
        return sum(f.difal for f in self.filiais.values())

    @property
    def difal_em_guia(self) -> float:
        """O DIFAL que se recolhe por fora da conta gráfica."""
        return sum(f.difal_em_guia for f in self.filiais.values())

    @property
    def inconsistentes(self) -> list[ApuracaoFilial]:
        """Filiais em que crédito mantido + estorno ≠ crédito bruto."""
        return [f for f in self.filiais.values() if not f.confere]

    @property
    def saldos(self) -> dict[str, float]:
        """Saldo individual de cada estabelecimento, antes da centralização."""
        return {f.estabelecimento: f.saldo for f in self.filiais.values()}

    @property
    def instrucoes_de_centralizacao(self) -> list[str]:
        """Transferências a emitir depois do encerramento da competência."""
        return [i for c in self.centralizacao for i in c.instrucoes]

    def debito_por_centralizacao(self, estabelecimento: str) -> float:
        """Débito que o estabelecimento assume por centralizar — linha 002."""
        return centr.debito_recebido_por(self.centralizacao, estabelecimento)

    @property
    def bloqueios_de_ajuste(self) -> list[str]:
        """Ajustes que não dá para aceitar como estão.

        Ignorar um ajuste pela metade seria perder uma decisão que alguém
        tomou; completá-lo por conta própria é o que a regra 4 proíbe. Então
        ele bloqueia até ser corrigido ou apagado.
        """
        motivos = list(self.ajustes.recusados)
        for ajuste in self.ajustes_sem_atividade:
            motivos.append(
                f"{ajuste.onde}: {ajuste.estabelecimento} segrega por atividade "
                "— informe a atividade da parcela (industrial, comercial…)"
            )
        for ajuste in self.ajustes.lancamentos + self.ajustes.anotacoes:
            if ajuste.estabelecimento not in self.filiais:
                motivos.append(
                    f"{ajuste.onde}: {ajuste.estabelecimento!r} não apurou nada "
                    "nesta competência — confira o nome do estabelecimento"
                )
        return motivos

    @property
    def sem_regra_de_atividade(self) -> list[ApuracaoFilial]:
        """Filiais com linha que não casou com nenhuma atividade.

        Bloqueia o encerramento: sem a atividade não há como dimensionar o
        benefício, e classificar por adivinhação é o que a regra 4 proíbe.
        """
        return [f for f in self.filiais.values() if f.atividades_sem_regra]


def apurar(
    base: BaseTratada,
    parametros: Parametros | None = None,
    ajustes: AjustesDaApuracao | None = None,
) -> Apuracao:
    params = parametros or base.parametros
    # Cópia: a apuração acrescenta os ajustes escritos nas linhas do Livro, e
    # quem chamou não pode ver o próprio objeto crescer a cada rodada.
    ajustes = copy.deepcopy(ajustes) if ajustes is not None else AjustesDaApuracao()

    cadastro = {
        " ".join(str(f["nome"]).split()).casefold(): f
        for f in params.filiais.get("filiais") or []
    }

    filiais: dict[str, ApuracaoFilial] = {}
    for tratada in base.linhas:
        resultado: ResultadoEstorno = calcular(tratada, params)
        if not (resultado.credito_bruto or resultado.debito):
            continue

        chave = " ".join(str(tratada.origem.dados["estabelecimento"]).split())
        filial = filiais.get(chave)
        if filial is None:
            ficha = cadastro.get(chave.casefold()) or {}
            uf = ficha.get("uf", "")
            filial = filiais[chave] = ApuracaoFilial(
                estabelecimento=chave,
                uf=uf,
                regime=resultado.regime,
                codigo=int(ficha["codigo"]) if ficha.get("codigo") is not None else None,
                segrega_por_atividade=ativ.mapa_da_uf(uf, params) is not None,
            )
        filial.credito_bruto += resultado.credito_bruto
        filial.credito_mantido += resultado.credito_mantido
        filial.estorno += resultado.estorno
        filial.credito_indevido += resultado.credito_indevido
        filial.debito += resultado.debito
        filial.linhas += 1

        apurada = LinhaApurada(tratada=tratada, resultado=resultado)
        filial.apuradas.append(apurada)

        if filial.segrega_por_atividade:
            classificada = _somar_na_atividade(filial, tratada, resultado, params)
            if classificada is not None:
                apurada.atividade = classificada.atividade
                apurada.destino = classificada.destino


        if resultado.credito_bruto:
            carga = tratada.carga.carga if tratada.carga.carga is not None else "CIAP"
            alvo = filial.por_carga[carga]
            alvo["credito_bruto"] += resultado.credito_bruto
            alvo["credito_mantido"] += resultado.credito_mantido
            alvo["estorno"] += resultado.estorno
            alvo["credito_indevido"] += resultado.credito_indevido

    # Camada 7 — benefício fiscal. Vem depois do estorno e depois da segregação,
    # porque incide sobre o saldo devedor da atividade industrial.
    for chave, filial in filiais.items():
        nome_beneficio = (cadastro.get(chave.casefold()) or {}).get("beneficio_fiscal")
        if not nome_beneficio:
            continue
        filial.beneficio = calcular_beneficio(
            filial.atividade(ativ.INDUSTRIAL),
            nome_beneficio,
            params,
            ajuste_de_credito=ajustes.de(
                "estorno_de_credito", chave, ativ.INDUSTRIAL
            ),
        )

    _difal(base, filiais, params, cadastro)

    # Os ajustes escritos nas linhas do Livro. Fora do laço de movimento de
    # propósito: uma linha pode não ter ICMS nenhum e ainda assim merecer
    # ajuste — "esta nota devia ter tido débito e não teve" é disso que trata a
    # linha 002 do Registro.
    _ajustes_das_linhas(base, filiais, params, ajustes)

    # Abertura da conta gráfica — a linha 009. Vem antes da centralização
    # porque muda o saldo que cada estabelecimento leva para o grupo.
    abertura = _abertura(base, params, ajustes, filiais)

    # Os ajustes declarados, pelo mesmo motivo: o estabelecimento leva ao grupo
    # o saldo que de fato tem.
    for chave, filial in filiais.items():
        filial.ajustes_da_conta = (
            ajustes.total("outros_creditos", chave)
            + ajustes.total("estorno_de_debito", chave)
            - ajustes.total("outros_debitos", chave)
            - ajustes.total("estorno_de_credito", chave)
        )

    apuracao = Apuracao(
        filiais=filiais, base=base, saldos_declarados=abertura, ajustes=ajustes,
        ajustes_sem_atividade=_sem_atividade(ajustes, filiais),
    )

    # Camada 9 — centralização. Vem por último porque opera sobre o saldo já
    # apurado de cada estabelecimento.
    apuracao.centralizacao = centr.calcular(apuracao.saldos, params)
    return apuracao


def _difal(
    base: BaseTratada,
    filiais: dict[str, ApuracaoFilial],
    params: Parametros,
    cadastro: dict[str, Any],
) -> None:
    """Soma o diferencial de alíquota e decide o destino dele.

    **Fora do laço de movimento, de propósito.** A entrada de uso e consumo
    escritura ICMS zero — não há crédito a tomar —, então ela não tem nem
    crédito nem débito e o laço da apuração a descarta. O DIFAL dela está na
    coluna `Diferença ICMS`, calculada pelo ERP a partir do ICMS destacado no
    XML, e some junto se for lido lá dentro.

    O DIFAL não é decisão da apuração: chega pronto do Livro. O que a UF decide
    é o destino — conta gráfica ou guia avulsa. Ver `regimes.yaml`, bloco
    `difal`.
    """
    for tratada in base.linhas:
        valor = float(tratada.origem.dados.get("diferenca_icms") or 0.0)
        if not valor:
            continue
        chave = " ".join(str(tratada.origem.dados.get("estabelecimento") or "").split())
        filial = filiais.get(chave)
        if filial is None:
            # Estabelecimento que só teve DIFAL no mês ainda assim tem apuração:
            # o Registro dele existe, com a linha 002 preenchida.
            ficha = cadastro.get(chave.casefold()) or {}
            uf = ficha.get("uf", "")
            filial = filiais[chave] = ApuracaoFilial(
                estabelecimento=chave,
                uf=uf,
                regime=str(ficha.get("regime") or ""),
                codigo=int(ficha["codigo"]) if ficha.get("codigo") is not None else None,
                segrega_por_atividade=ativ.mapa_da_uf(uf, params) is not None,
            )
        filial.difal += valor

    for filial in filiais.values():
        filial.difal_na_conta_grafica = bool(
            params.difal_da_uf(filial.uf).get("na_conta_grafica", False)
        )
        filial.difal_na_conta = filial.difal if filial.difal_na_conta_grafica else 0.0


def _ajustes_das_linhas(
    base: BaseTratada,
    filiais: dict[str, ApuracaoFilial],
    params: Parametros,
    ajustes: AjustesDaApuracao,
) -> None:
    """Recolhe o que foi escrito nas colunas `ajuste_*` da BASE TRATADA.

    Nem o estabelecimento nem a atividade precisam ser digitados: a linha já
    diz os dois. A atividade sai do CFOP pela mesma classificação que a
    apuração usa — o ajuste de uma linha industrial é industrial.
    """
    for tratada in base.linhas:
        ajuste = tratada.ajuste
        if ajuste is None:
            continue
        filial = filiais.get(ajuste.estabelecimento)
        atividade = ""
        if filial is not None and filial.segrega_por_atividade:
            mapa = ativ.mapa_da_uf(filial.uf, params)
            if mapa is not None:
                atividade = ativ.classificar(tratada.origem, mapa).atividade
        ajustes.somar(ajuste, atividade=atividade)


def _sem_atividade(
    ajustes: AjustesDaApuracao, filiais: dict[str, ApuracaoFilial]
) -> list[aj.Ajuste]:
    """Parcelas sem documento que não disseram a atividade onde ela importa.

    Onde a UF segrega — hoje MS —, é a atividade que dimensiona o benefício.
    Uma parcela lançada sem ela mudaria o incentivo sem que ninguém tivesse
    decidido. Nas demais UFs a atividade não existe, e não faz falta.
    """
    return [
        ajuste
        for ajuste in ajustes.lancamentos
        if not ajuste.atividade
        and (filial := filiais.get(ajuste.estabelecimento)) is not None
        and filial.segrega_por_atividade
    ]


def _abertura(
    base: BaseTratada,
    params: Parametros,
    ajustes: AjustesDaApuracao,
    filiais: dict[str, ApuracaoFilial],
) -> bool:
    """Aplica o saldo credor do mês anterior e diz se ele foi declarado.

    O Livro Fiscal traz os documentos da competência e nada mais — o crédito
    que sobrou do mês passado só pode vir declarado. A fonte é
    `parametros/saldos.yaml`, indexada pelo código da empresa; um ajuste
    aprovado para a rodada, quando existe, prevalece sobre ela.
    """
    declarados = params.saldos_credores(base.competencia)
    for chave, filial in filiais.items():
        do_parametro = (
            float((declarados or {}).get(filial.codigo, 0.0))
            if filial.codigo is not None
            else 0.0
        )
        do_ajuste = ajustes.saldo_credor_anterior.get(chave)
        filial.saldo_credor_anterior = (
            float(do_ajuste) if do_ajuste is not None else do_parametro
        )
    return declarados is not None


def _somar_na_atividade(
    filial: ApuracaoFilial,
    tratada,
    resultado: ResultadoEstorno,
    params: Parametros,
) -> ativ.ResultadoAtividade | None:
    mapa = ativ.mapa_da_uf(filial.uf, params)
    if mapa is None:
        return None
    classificada = ativ.classificar(tratada.origem, mapa)
    alvo = filial.por_atividade.get(classificada.atividade)
    if alvo is None:
        alvo = filial.por_atividade[classificada.atividade] = ativ.TotaisAtividade(
            atividade=classificada.atividade
        )
    alvo.credito_bruto += resultado.credito_bruto
    alvo.credito_mantido += resultado.credito_mantido
    alvo.estorno += resultado.estorno
    alvo.credito_indevido += resultado.credito_indevido
    alvo.debito += resultado.debito
    alvo.linhas += 1
    if resultado.debito and classificada.destino:
        alvo.debito_por_destino[classificada.destino] = (
            alvo.debito_por_destino.get(classificada.destino, 0.0) + resultado.debito
        )
    return classificada
