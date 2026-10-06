"""Controle de créditos fiscais — Registros 1200 e 1210 da EFD ICMS/IPI.

Rio Brilhante recebe crédito de ICMS por transferência (NF-e da ADECOAGRO,
CFOP 1601, art. 68 do RICMS/MS). O crédito não é usado todo no mês em que
chega: forma um estoque, e a apuração usa dele o que o fiscal decidir — o uso
entra na linha 006 do Registro como "outros créditos". A EFD declara o estoque
como conta corrente:

    1200  COD_AJ_APUR | SLD_CRED | CRÉD_APR | CRÉD_RECEB | CRÉD_UTIL | SLD_CRED_FIM
    1210  TIPO_UTIL | NR_DOC | VL_CRED_UTIL | CHV_DOCe

    saldo inicial + apropriado + recebido − utilizado = saldo final

A ferramenta **não decide** quanto usar. Ela junta as pontas que já existem
em lugares diferentes — o saldo declarado em `saldos.yaml`, a nota no Livro
Fiscal e o ajuste declarado na linha 006 — e fecha a conta. Se o uso passar do
que o estoque tem, o 1200 sai marcado em vez de ficar negativo.

O que ela mostra é o limite: o disponível (saldo transportado + recebido) pode
ser usado até um percentual do saldo devedor do próprio mês — a linha 011 do
Registro, antes do uso. O total a utilizar é o menor dos dois, e uso declarado
acima do teto sai pendente.

Os parâmetros estão em `parametros/controle_de_creditos.yaml`.
"""
from __future__ import annotations

from dataclasses import dataclass, field

CENTAVO = 0.005


@dataclass
class NotaRecebida:
    """A NF-e que trouxe o crédito, como está no Livro Fiscal."""

    numero: str
    data: str
    chave: str
    parceiro: str
    valor: float


@dataclass
class MesTransmitido:
    """O 1200 de um mês já entregue na EFD, como está em `saldos.yaml`."""

    competencia: str
    saldo_inicial: float
    apropriado: float
    recebido: float
    utilizado: float

    @property
    def saldo_final(self) -> float:
        return round(self.saldo_inicial + self.apropriado
                     + self.recebido - self.utilizado, 2)


@dataclass
class Controle:
    """O 1200 de um código de ajuste, e o 1210 que o acompanha."""

    estabelecimento: str
    empresa: int
    cod_aj_apur: str
    descricao: str
    tipo_util: str
    competencia: str
    #: `None` quando `saldos.yaml` não declara a competência.
    saldo_inicial: float | None
    apropriado: float = 0.0
    notas: list[NotaRecebida] = field(default_factory=list)
    #: Os ajustes declarados na linha 006 com a observação padrão do uso.
    utilizacoes: list = field(default_factory=list)
    observacao_padrao_do_uso: str = ""
    #: O crédito recebido declarado em `saldos.yaml`, quando o Livro não o
    #: traz inteiro (a NF-e vem com desconto). `None` = vale o Livro.
    recebido_declarado: float | None = None
    #: Os meses do ano já transmitidos, antes da competência.
    historico: list[MesTransmitido] = field(default_factory=list)
    #: De onde veio o saldo inicial, quando não foi declarado para o mês.
    origem_do_saldo_inicial: str = ""
    #: O SLD_CRED_FIM do mês anterior transmitido, para conferir a abertura.
    saldo_final_anterior: float | None = None
    #: Linha 011 do Registro do estabelecimento, antes do uso do crédito.
    saldo_devedor: float | None = None
    #: Percentual do saldo devedor que limita o uso; `None` = sem teto vigente.
    percentual_do_teto: float | None = None

    @property
    def recebido_no_livro(self) -> float:
        return round(sum(n.valor for n in self.notas), 2)

    @property
    def recebido(self) -> float:
        if self.recebido_declarado is not None:
            return round(self.recebido_declarado, 2)
        return self.recebido_no_livro

    @property
    def disponivel(self) -> float:
        """Saldo transportado + apropriado + recebido: o que se pode usar."""
        return round((self.saldo_inicial or 0.0) + self.apropriado
                     + self.recebido, 2)

    @property
    def teto(self) -> float | None:
        if self.saldo_devedor is None or self.percentual_do_teto is None:
            return None
        return round(self.saldo_devedor * self.percentual_do_teto / 100, 2)

    @property
    def a_utilizar(self) -> float:
        """O máximo a usar no mês: o disponível, limitado ao teto."""
        if self.teto is None:
            return self.disponivel
        return max(min(self.disponivel, self.teto), 0.0)

    @property
    def utilizado(self) -> float:
        return round(sum(a.valor for a in self.utilizacoes), 2)

    @property
    def saldo_final(self) -> float:
        return round((self.saldo_inicial or 0.0) + self.apropriado
                     + self.recebido - self.utilizado, 2)

    @property
    def chave(self) -> str:
        """A chave que vai no 1210 — a da NF-e de recebimento do mês."""
        chaves = sorted({n.chave for n in self.notas if n.chave})
        return chaves[0] if len(chaves) == 1 else ""

    @property
    def pendencias(self) -> list[str]:
        """O que impede de transmitir o 1200 como está."""
        motivos = []
        if self.saldo_inicial is None:
            motivos.append(
                f"saldo inicial de {self.competencia} não declarado em "
                "parametros/saldos.yaml (bloco creditos_controlados) — o 1200 "
                "saiu abrindo em zero"
            )
        if self.saldo_final < -CENTAVO:
            motivos.append(
                "o utilizado passa do que o estoque tem: saldo final negativo — "
                "confira o ajuste da linha 006"
            )
        if self.teto is not None and self.utilizado > self.teto + CENTAVO:
            motivos.append(
                f"o utilizado ({_brl(self.utilizado)}) passa do teto de "
                f"{self.percentual_do_teto:g}% do saldo devedor "
                f"({_brl(self.teto)}) — confira o ajuste da linha 006"
            )
        if (self.saldo_inicial is not None and self.saldo_final_anterior is not None
                and abs(self.saldo_inicial - self.saldo_final_anterior) >= CENTAVO):
            motivos.append(
                f"o saldo inicial ({_brl(self.saldo_inicial)}) não é o saldo "
                f"final do 1200 transmitido no mês anterior "
                f"({_brl(self.saldo_final_anterior)})"
            )
        chaves = {n.chave for n in self.notas if n.chave}
        if self.utilizado and len(chaves) > 1:
            motivos.append(
                "mais de uma NF-e de recebimento no mês — escolha a chave que "
                "vai no 1210"
            )
        if self.utilizado and not chaves:
            motivos.append(
                "há crédito utilizado, mas nenhuma NF-e de recebimento com chave "
                "no Livro do mês — informe a chave do 1210 à mão"
            )
        return motivos

    # -- as linhas como vão para o arquivo da EFD ------------------------

    def linha_1200(self) -> str:
        campos = [self.saldo_inicial or 0.0, self.apropriado, self.recebido,
                  self.utilizado, self.saldo_final]
        return "|1200|" + self.cod_aj_apur + "|" + "|".join(
            _efd(v) for v in campos) + "|"

    def linha_1210(self) -> str | None:
        if not self.utilizado:
            return None
        return f"|1210|{self.tipo_util}||{_efd(self.utilizado)}|{self.chave}|"


def montar(apuracao, params, ajustes=None) -> list[Controle]:
    """Um `Controle` por código de ajuste vigente na competência."""
    from .nucleo import registro as reg

    ajustes = ajustes if ajustes is not None else apuracao.ajustes
    competencia = apuracao.base.competencia
    registros = None
    nomes = {
        int(f["codigo"]): " ".join(str(f["nome"]).split())
        for f in params.filiais.get("filiais") or []
        if f.get("codigo") is not None
    }

    controles = []
    for regra in (params.controle_de_creditos or {}).get("controles") or []:
        if not _vigente(regra, competencia):
            continue
        empresa = int(regra["empresa"])
        nome = nomes.get(empresa, f"empresa {empresa}")
        codigo = str(regra["cod_aj_apur"])
        recebimento = regra.get("recebimento") or {}
        uso = str((regra.get("utilizacao") or {}).get("observacao_padrao") or "")

        transmitidos = params.transmitidos_do_controle(empresa, codigo)
        anterior = transmitidos.get(_mes_anterior(competencia))
        controle = Controle(
            estabelecimento=nome, empresa=empresa, cod_aj_apur=codigo,
            descricao=" ".join(str(regra.get("descricao") or "").split()),
            tipo_util=str(regra.get("tipo_util") or ""),
            competencia=competencia,
            saldo_inicial=params.saldo_do_controle(competencia, empresa, codigo),
            observacao_padrao_do_uso=uso,
            recebido_declarado=params.recebido_do_controle(
                competencia, empresa, codigo),
            historico=[
                MesTransmitido(mes, v["sld_cred"], v["cred_apr"],
                               v["cred_receb"], v["cred_util"])
                for mes, v in sorted(transmitidos.items())
                if mes[:4] == competencia[:4] and mes < competencia
            ],
            percentual_do_teto=_percentual_do_teto(
                regra.get("utilizacao") or {}, competencia),
        )
        if anterior is not None:
            controle.saldo_final_anterior = MesTransmitido(
                _mes_anterior(competencia), anterior["sld_cred"],
                anterior["cred_apr"], anterior["cred_receb"],
                anterior["cred_util"]).saldo_final
            if controle.saldo_inicial is None:
                controle.saldo_inicial = controle.saldo_final_anterior
                controle.origem_do_saldo_inicial = (
                    "saldo final do 1200 transmitido no mês anterior")
        controle.notas = _notas(apuracao.base, nome, recebimento)
        controle.utilizacoes = [
            a for a in (ajustes.lancamentos if ajustes else [])
            if a.estabelecimento == nome and a.linha == 6
            and uso and str(a.observacao_padrao or "") == uso
        ]
        if controle.percentual_do_teto is not None:
            if registros is None:
                registros = {r.estabelecimento: r
                             for r in reg.montar(apuracao, params, ajustes)}
            controle.saldo_devedor = _saldo_devedor_antes_do_uso(
                registros.get(nome), controle.utilizado)
        controles.append(controle)
    return controles


def _saldo_devedor_antes_do_uso(registro, utilizado: float) -> float | None:
    """A linha 011 do Registro como seria sem o crédito usado no mês.

    O uso entra na linha 006 e já abate o saldo devedor; o teto se mede antes
    dele, senão cada real usado encolheria o próprio limite.
    """
    if registro is None:
        return None
    debitos = registro.linha(4).valor
    creditos = registro.linha(10).valor - utilizado
    return round(max(debitos - creditos, 0.0), 2)


def _percentual_do_teto(utilizacao: dict, competencia: str) -> float | None:
    for versao in utilizacao.get("teto_por_vigencia") or []:
        if _vigente(versao, competencia):
            return float(versao["percentual_do_saldo_devedor"])
    return None


def _mes_anterior(competencia: str) -> str:
    ano, mes = int(competencia[:4]), int(competencia[5:7])
    return f"{ano - 1}-12" if mes == 1 else f"{ano}-{mes - 1:02d}"


def _brl(valor: float) -> str:
    texto = f"{valor:,.2f}"
    return "R$ " + texto.replace(",", "_").replace(".", ",").replace("_", ".")


def _notas(base, estabelecimento: str, recebimento: dict) -> list[NotaRecebida]:
    """As notas de recebimento do crédito, uma por NF-e.

    Uma NF-e pode vir em mais de uma linha (itens); o valor se soma por chave.
    """
    cfops = {int(c) for c in recebimento.get("cfop") or []}
    campo = str(recebimento.get("campo_do_valor") or "valor_contabil")
    por_nota: dict[tuple, NotaRecebida] = {}
    for tratada in base.linhas:
        origem = tratada.origem
        dados = origem.dados
        if origem.cfop_int not in cfops or origem.cancelado:
            continue
        if " ".join(str(dados.get("estabelecimento") or "").split()) != estabelecimento:
            continue
        chave = "".join(ch for ch in str(dados.get("chave_nfe") or "") if ch.isdigit())
        numero = _texto(dados.get("numero_nota"))
        nota = por_nota.get((chave, numero))
        if nota is None:
            nota = por_nota[(chave, numero)] = NotaRecebida(
                numero=numero, data=_data(dados.get("data_documento")),
                chave=chave, parceiro=_texto(dados.get("parceiro")), valor=0.0,
            )
        nota.valor += _numero(dados.get(campo))
    return list(por_nota.values())


def _vigente(regra: dict, competencia: str) -> bool:
    inicio = str(regra.get("vigencia_inicio") or "")[:7]
    fim = str(regra.get("vigencia_fim") or "")[:7]
    return not (inicio and competencia < inicio) and not (fim and competencia > fim)


def _efd(valor: float) -> str:
    """Número no formato da EFD: vírgula decimal, sem milhar, zero sem casas."""
    valor = round(valor, 2)
    if abs(valor) < CENTAVO:
        return "0"
    texto = f"{valor:.2f}".replace(".", ",")
    return texto[:-3] if texto.endswith(",00") else texto


def _texto(valor) -> str:
    if valor is None:
        return ""
    if isinstance(valor, float) and valor.is_integer():
        return str(int(valor))
    return str(valor).strip()


def _data(valor) -> str:
    if hasattr(valor, "strftime"):
        return valor.strftime("%d/%m/%Y")
    return _texto(valor)


def _numero(valor) -> float:
    try:
        return float(valor or 0.0)
    except (TypeError, ValueError):
        return 0.0
