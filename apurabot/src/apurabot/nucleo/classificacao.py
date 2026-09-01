"""Camada 4 — classificação da operação.

Regras avaliadas em ordem; a primeira que casar vence. O que não casar em
nenhuma recebe `SEM REGRA` e bloqueia o encerramento da competência — nunca
se classifica por adivinhação.
"""
from __future__ import annotations

from dataclasses import dataclass

from ..ingestao import LinhaLivro
from ..parametros import Parametros

SEM_REGRA = "SEM REGRA"


@dataclass(frozen=True)
class ResultadoClassificacao:
    categoria: str
    regra: str
    tratamento: str | None = None      # ex.: estorna_100_credito_entrada

    @property
    def e_pendencia(self) -> bool:
        return self.categoria == SEM_REGRA


def classificar(linha: LinhaLivro, params: Parametros) -> ResultadoClassificacao:
    """Determina a categoria tributária de uma linha do Livro Fiscal."""
    for etapa in (
        _lancamento_sem_contabil,
        _excecao_por_cfop,
        _frete,
        _mercadoria,
    ):
        resultado = etapa(linha, params)
        if resultado is not None:
            return resultado

    return ResultadoClassificacao(
        categoria=SEM_REGRA,
        regra=(
            f"CFOP {linha.cfop_int}, produto {linha.produto_codigo}, espécie "
            f"{linha.dados.get('especie')} não casou com nenhuma regra"
        ),
    )


def casa_lancamento_sem_contabil(linha: LinhaLivro, item: dict) -> str | None:
    """Este item de `lancamentos_sem_contabil` reconhece esta linha?

    Devolve o motivo do casamento, ou None. Três chaves, e basta uma:

    `produto`             o código do produto do lançamento;
    `cfop`                a lista de CFOP;
    `sem_valor_contabil`  a **forma** do lançamento — sem valor contábil, com
                          base e com ICMS. É como o complemento de ICMS chega
                          quando é lançado contra o código do produto real, e
                          não contra um código próprio.

    A forma só reconhece o que hoje já seria pendência: um lançamento com valor
    contábil nunca casa por ela. Sem isso, a chave alargaria a regra para
    linhas normais do mesmo CFOP.
    """
    produto = item.get("produto")
    if produto is not None and linha.produto_codigo == str(produto):
        return f"produto {produto}"
    cfops = set(item.get("cfop") or [])
    if cfops and linha.cfop_int in cfops:
        return f"CFOP {linha.cfop_int}"
    if item.get("sem_valor_contabil") and _tem_a_forma_de_lancamento_sem_contabil(linha):
        return "lançado sem valor contábil, só com base e ICMS"
    return None


def _tem_a_forma_de_lancamento_sem_contabil(linha: LinhaLivro) -> bool:
    def numero(campo: str) -> float:
        try:
            return float(linha.dados.get(campo) or 0.0)
        except (TypeError, ValueError):
            return 0.0

    return (
        not numero("valor_contabil")
        and numero("base_icms") > 0
        and numero("valor_icms") != 0
    )


def _lancamento_sem_contabil(linha, params) -> ResultadoClassificacao | None:
    for item in params.classificacao.get("lancamentos_sem_contabil") or []:
        motivo = casa_lancamento_sem_contabil(linha, item)
        if motivo:
            return ResultadoClassificacao(
                categoria=item["categoria"],
                regra=f"lançamento sem contábil — {item.get('descricao', '')}",
            )
    return None


def _excecao_por_cfop(linha, params) -> ResultadoClassificacao | None:
    for excecao in params.classificacao.get("excecoes_cfop") or []:
        if linha.cfop_int in set(excecao.get("cfop") or []):
            return ResultadoClassificacao(
                categoria=excecao["categoria"],
                tratamento=excecao.get("regra"),
                regra=(
                    f"CFOP {linha.cfop_int} — "
                    f"{excecao.get('descricao') or excecao['categoria']}"
                ),
            )
    return None


def _frete(linha, params) -> ResultadoClassificacao | None:
    fretes = params.classificacao["fretes"]
    identificacao = fretes["identificacao"]
    especie = str(linha.dados.get("especie") or "").strip()
    modelo = str(linha.dados.get("modelo") or "")
    e_frete = especie == identificacao["especie_documento"] or modelo.startswith(
        str(identificacao["modelo_documento"])
    )
    if not e_frete:
        return None

    descricao = str(linha.dados.get("produto_descricao") or "").casefold()
    for finalidade in fretes["finalidades"]:
        if finalidade["contem"].casefold() in descricao:
            return ResultadoClassificacao(
                categoria=finalidade["categoria"],
                regra=f"CT-e com finalidade {finalidade['contem']!r}",
            )

    for categoria, cfops in (fretes.get("fallback_cfop") or {}).items():
        if linha.cfop_int in set(cfops):
            return ResultadoClassificacao(
                categoria=categoria,
                regra=(
                    f"CT-e sem finalidade reconhecida na descrição; classificado "
                    f"pelo CFOP {linha.cfop_int}"
                ),
            )

    return ResultadoClassificacao(
        categoria=SEM_REGRA,
        regra=(
            f"CT-e com descrição {linha.dados.get('produto_descricao')!r} e CFOP "
            f"{linha.cfop_int} não casou com nenhuma finalidade de frete"
        ),
    )


def _mercadoria(linha, params) -> ResultadoClassificacao | None:
    classif = params.classificacao
    codigo = linha.produto_codigo
    if not codigo:
        return None

    # 1. Cadastro de produtos — a exceção manda sobre o padrão do prefixo.
    do_cadastro = _cadastro(linha, params, codigo)
    if do_cadastro is not None:
        return do_cadastro

    # 2. Padrão pelo prefixo do código do produto.
    #
    # O prefixo vem ANTES do CFOP de propósito. O CFOP de compra diz para que
    # a mercadoria foi adquirida; a regra de estorno pergunta o que ela É.
    # Uma embalagem comprada com CFOP 1101 (compra para industrialização)
    # continua sendo embalagem e continua estornando.
    padrao = (classif.get("prefixo_produto") or {}).get(codigo[0])
    if padrao:
        return ResultadoClassificacao(
            categoria=padrao,
            regra=f"produto {codigo} — prefixo {codigo[0]} indica {padrao}",
        )

    # 3. Sem prefixo conhecido, o CFOP decide a natureza.
    if linha.cfop_int in set(classif.get("cfop_revenda") or []):
        return ResultadoClassificacao(
            categoria="revenda", regra=f"CFOP {linha.cfop_int} — compra para revenda"
        )
    if linha.cfop_int in set(classif.get("cfop_industrializacao") or []):
        return ResultadoClassificacao(
            categoria="materia_prima",
            regra=f"CFOP {linha.cfop_int} — compra para industrialização",
        )

    return None


def _cadastro(linha, params, codigo) -> ResultadoClassificacao | None:
    """Procura o produto no cadastro, considerando o fornecedor quando ele importa.

    A entrada do cadastro pode ser um mapa (a categoria vale para o produto,
    venha de quem vier) ou uma lista de alternativas. Na lista, a alternativa com
    `fornecedor` só casa com aquele fornecedor, e a sem `fornecedor` é o padrão
    do produto — as específicas são avaliadas primeiro.

    Isso existe porque o enquadramento é do par produto + fornecedor: a mesma
    matéria-prima pode ser `materia_prima` de um fabricante de fertilizante e
    `produto_quimico` de uma indústria química sem registro no MAPA para
    vendê-la enquadrada. Ver docs/apurabot/04-matriz-de-regras-icms.md, item 2.1.
    """
    if not codigo.isdigit():
        return None
    entrada = (params.produtos.get("produtos") or {}).get(int(codigo))
    if not entrada:
        return None

    alternativas = entrada if isinstance(entrada, list) else [entrada]
    fornecedor = _texto(linha.dados.get("parceiro"))
    especificas = [a for a in alternativas if a.get("fornecedor")]
    padroes = [a for a in alternativas if not a.get("fornecedor")]

    for item in especificas:
        if _texto(item["fornecedor"]) in fornecedor:
            return ResultadoClassificacao(
                categoria=item["categoria"],
                regra=(
                    f"produto {codigo} no cadastro, fornecedor "
                    f"{item['fornecedor']!r} — {item.get('descricao', '')}"
                ),
            )
    for item in padroes:
        return ResultadoClassificacao(
            categoria=item["categoria"],
            regra=f"produto {codigo} no cadastro — {item.get('descricao', '')}",
        )

    # Produto cadastrado só com regras por fornecedor, e nenhuma casou. Não se
    # adivinha: a linha vira pendência.
    return ResultadoClassificacao(
        categoria=SEM_REGRA,
        regra=(
            f"produto {codigo} tem cadastro por fornecedor, e o fornecedor "
            f"{linha.dados.get('parceiro')!r} não está entre eles"
        ),
    )


def _texto(valor) -> str:
    return " ".join(str(valor or "").split()).casefold()
