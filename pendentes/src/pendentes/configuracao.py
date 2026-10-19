"""A tela de parâmetros das notas pendentes: o que a Central mostra e grava.

Até aqui os parâmetros das pendentes só se alteravam editando
`dados/pendentes/parametros.yaml` à mão. Este módulo é a ponte entre a base
viva e a tela da Central, do mesmo jeito que o do Fiscalbot: descreve as
seções em dicionários e listas, sem conhecer navegador nem HTML. Quem desenha
é a Central — nenhuma ferramenta importa outra.

### O que entra na tela, e o que fica de fora

Entra o que o time muda sem desenvolvedor: unidades, filiais, guardiões,
categorias, exceções de serviços, os limiares do confronto, a semana, o
painel, a pré-categorização e os sinônimos de coluna.

Fica de fora o que é vocabulário do export do Sankhya e mecânica das regras
(roteamento, farol de emoji, papéis de arquivo, literais de mercadorias):
mexer nisso muda o resultado das regras, e a tela não teria como explicar o
efeito. Continua no arquivo, e o que a tela grava nunca o apaga — a gravação
**mescla** seção por seção.

### Com erro não grava

Uma tabela de unidades com ordem repetida ou um CNPJ de filial com 13
dígitos rodariam a semana inteira errada. Erro impede a gravação; aviso
grava e diz o que vai acontecer — como no Fiscalbot.
"""
from __future__ import annotations

import copy
from typing import Any, Iterable

from . import parametros
from .chaves import cnpj as so_cnpj
from .texto import aparar, chave_de_texto

#: Os três graus que a pré-categorização aceita, por coluna.
GRAUS = ("firme", "sugestao", "nao")

#: As colunas da pré-categorização: a chave na base e o rótulo da tela.
PRE_CATEGORIZACAO = (
    ("categoria", "Categoria"),
    ("guardiao", "Guardião"),
    ("gestor_de_apoio", "Gestor de apoio"),
    ("tipo_de_operacao", "Tipo de Operação"),
)

#: Como cada relatório aparece na seção de sinônimos.
FONTES = {
    "xml": "XML (mercadorias)",
    "conferencia_de_entradas": "Conferência de Entradas",
    "semana_anterior_mercadorias": "Semana anterior (mercadorias)",
    "asis": "ASIS (serviços)",
    "portal_de_compras": "Portal de Compras",
    "conferencia_de_servicos": "Conferência de Serviços",
    "semana_anterior_servicos": "Semana anterior (serviços)",
}


def _campo(chave: str, rotulo: str, largura: int = 14, ajuda: str = "",
           tipo: str = "texto") -> dict[str, Any]:
    return {"chave": chave, "rotulo": rotulo, "largura": largura,
            "ajuda": ajuda, "tipo": tipo}


def secoes() -> list[dict[str, Any]]:
    """As seções da tela, na ordem em que aparecem."""
    return [
        {
            "id": "unidades",
            "titulo": "Unidades",
            "explicacao":
                "De que unidade é cada nota, pelo trecho que aparece no Nome "
                "Fantasia (mercadorias) ou na Filial (serviços). A ORDEM É A "
                "REGRA: vale a primeira linha cujo trecho aparece no nome — "
                "'MATRIZ-FILIAIS' tem de vir antes de 'MATRIZ'. Com a tabela "
                "preenchida, nome que não casa com nenhuma linha bloqueia o "
                "encerramento em mercadorias.",
            "campos": [
                _campo("ordem", "Ordem", 6, "1, 2, 3… — a primeira que casa vale.",
                       "numero"),
                _campo("trecho", "Trecho", 22,
                       "Pedaço do nome. Maiúscula e acento não contam."),
                _campo("unidade", "Unidade", 26, "O nome que sai no painel."),
            ],
            "fixa": False,
        },
        {
            "id": "filiais",
            "titulo": "Filiais (complemento do de-para)",
            "explicacao":
                "Serviços descobrem a filial pelo CNPJ do tomador, no Portal de "
                "Compras da semana e no histórico. Esta tabela só é consultada "
                "quando os dois não respondem — cadastre a filial que ficou "
                "sem movimento e travou a semana.",
            "campos": [
                _campo("cnpj", "CNPJ", 20, "Com ou sem pontuação."),
                _campo("codigo", "Código", 8, "Código da empresa no Sankhya."),
                _campo("nome", "Nome", 36, "Nome fantasia, como sai na planilha."),
            ],
            "fixa": False,
        },
        {
            "id": "guardioes",
            "titulo": "Guardiões válidos",
            "explicacao":
                "As áreas que podem aparecer em Guardião. Lista vazia aceita "
                "qualquer texto; preenchida, guardião fora dela bloqueia o "
                "encerramento em mercadorias.",
            "campos": [_campo("guardiao", "Guardião", 30, "Nome da área.")],
            "fixa": False,
        },
        {
            "id": "categorias",
            "titulo": "Categorias",
            "explicacao":
                "A categoria normalizada pelo trecho. A ORDEM É A REGRA: "
                "'indireto' antes de 'direto', senão toda categoria indireta "
                "vira direta.",
            "campos": [
                _campo("ordem", "Ordem", 6, "A primeira que casa vale.", "numero"),
                _campo("trecho", "Trecho", 18, "Pedaço do texto da categoria."),
                _campo("categoria", "Categoria", 18, "Como ela é contada."),
            ],
            "fixa": False,
        },
        {
            "id": "excecoes_servicos",
            "titulo": "Serviços que não são cobrados",
            "explicacao":
                "Parceiro e valor que o time decidiu não cobrar: a nota sai da "
                "Pendentes e vai para a aba 'Fora do relatorio', com o motivo.",
            "campos": [
                _campo("codigo_parceiro", "Cód. parceiro", 12,
                       "Código do parceiro no Sankhya."),
                _campo("nome", "Parceiro", 30, "Só para quem lê a tela."),
                _campo("valor", "Valor", 12, "Valor exato da nota.", "numero"),
                _campo("motivo", "Motivo", 36, "Opcional. Sai na planilha."),
            ],
            "fixa": False,
        },
        {
            "id": "confronto_servicos",
            "titulo": "Confronto de serviços",
            "explicacao":
                "Códigos do Sankhya e limiares do vínculo com o pedido. Um TOP "
                "novo de lançamento de serviço entra aqui.",
            "campos": [
                _campo("tops_de_lancamento", "TOPs de lançamento", 16,
                       "Separados por ponto e vírgula. Ex.: 2020;2111"),
                _campo("prefixo_de_pedido", "Prefixo de pedido", 10,
                       "Descrição de TOP que identifica pedido de compra."),
                _campo("cnpj_descartado", "CNPJ descartado", 16,
                       "CNPJ que o Portal usa como 'sem parceiro'."),
                _campo("tolerancia_da_razao", "Tolerância", 10,
                       "Quanto a razão pedido/nota pode fugir do inteiro.",
                       "numero"),
                _campo("multiplo_minimo", "Múltiplo mín.", 9,
                       "Pedido global: a partir de quantas notas.", "numero"),
                _campo("multiplo_maximo", "Múltiplo máx.", 9,
                       "Pedido global: até quantas notas.", "numero"),
                _campo("marca_de_cancelada", "Marca de cancelada", 14,
                       "O que se escreve em Guardião, Gestor e Retorno para "
                       "tirar a nota cancelada na prefeitura."),
            ],
            "fixa": True,
        },
        {
            "id": "semana",
            "titulo": "Semana",
            "explicacao":
                "Vazio: a semana é deduzida da data. Preencha só para corrigir "
                "a numeração antes de rodar.",
            "campos": [
                _campo("numero", "Nº da semana", 12, "Vazio = deduzida."),
                _campo("data_de_referencia", "Data de referência", 16,
                       "dd/mm/aaaa. Vazio = a data da execução."),
                _campo("limite_de_dias", "Limite de dias", 12,
                       "Acima disso, o tempo do TOP sai destacado.", "numero"),
            ],
            "fixa": True,
        },
        {
            "id": "resumo",
            "titulo": "Resumo Executivo",
            "explicacao": "O que cabe na tela do painel. Nada aqui muda número.",
            "campos": [
                _campo("linhas_do_top", "Linhas do TOP", 12,
                       "Quantas notas cada TOP mostra.", "numero"),
                _campo("guardioes_no_grafico", "Guardiões no gráfico", 16,
                       "Quantas barras o gráfico de guardião mostra.", "numero"),
                _campo("guardioes_fora_do_ranking", "Fora do ranking", 30,
                       "Guardiões que não entram no gráfico, separados por "
                       "ponto e vírgula."),
            ],
            "fixa": True,
        },
        {
            "id": "pre_categorizacao",
            "titulo": "Pré-categorização (mercadorias)",
            "explicacao":
                "O que a base de conhecimento preenche quando a célula está "
                "vazia: 'firme' (só com evidência firme), 'sugestao' (também "
                "as sugestões) ou 'nao'. Nada sobrescreve célula preenchida, e "
                "o que a base preenche sai marcado em âmbar.",
            "campos": [
                _campo(chave, rotulo, 16, "firme, sugestao ou nao")
                for chave, rotulo in PRE_CATEGORIZACAO
            ],
            "fixa": True,
        },
        {
            "id": "sinonimos",
            "titulo": "Nomes de coluna aceitos",
            "explicacao":
                "Quando um relatório trocar o nome de uma coluna, acrescente o "
                "nome novo em Sinônimos, separado por ponto e vírgula — não é "
                "preciso mexer em código. Só a coluna Sinônimos é editável: "
                "relatório e coluna identificam a linha.",
            "campos": [
                _campo("fonte", "Relatório", 26, "Qual relatório."),
                _campo("coluna", "Coluna", 30, "O nome que a ferramenta procura."),
                _campo("sinonimos", "Sinônimos", 40,
                       "Outros nomes aceitos, separados por ponto e vírgula."),
            ],
            "fixa": False,
        },
    ]


# -- da base para a tela ---------------------------------------------------

def _numero(valor: Any) -> Any:
    """`2.0` sai `2`: a tela mostra o número como a pessoa o escreveria."""
    if isinstance(valor, float) and valor.is_integer():
        return int(valor)
    return "" if valor is None else valor


def _junta(valores: Iterable[Any]) -> str:
    return ";".join(str(v).strip() for v in valores or () if str(v).strip())


def ler(dados: dict[str, Any] | None = None) -> dict[str, list[dict]]:
    dados = dados if dados is not None else parametros.carregar()
    confronto = dict(dados.get("confronto_servicos") or {})
    semana = dict(dados.get("semana") or {})
    resumo = dict(dados.get("resumo") or {})
    pre = dict(dados.get("pre_categorizacao") or {})
    padrao_pre = {"categoria": "sugestao", "guardiao": "sugestao",
                  "gestor_de_apoio": "sugestao", "tipo_de_operacao": "firme"}
    return {
        "unidades": [
            {"ordem": _numero(l.get("ordem")), "trecho": l.get("trecho", ""),
             "unidade": l.get("unidade", "")}
            for l in dados.get("unidades") or []
        ],
        "filiais": [
            {"cnpj": l.get("cnpj", ""), "codigo": l.get("codigo", ""),
             "nome": l.get("nome", "")}
            for l in dados.get("filiais") or []
        ],
        "guardioes": [{"guardiao": g} for g in dados.get("guardioes") or []],
        "categorias": [
            {"ordem": _numero(l.get("ordem")), "trecho": l.get("trecho", ""),
             "categoria": l.get("categoria", "")}
            for l in dados.get("categorias") or []
        ],
        "excecoes_servicos": [
            {"codigo_parceiro": l.get("codigo_parceiro") or l.get("parceiro", ""),
             "nome": l.get("nome", ""), "valor": _numero(l.get("valor")),
             "motivo": l.get("motivo", "")}
            for l in dados.get("excecoes_servicos") or []
        ],
        "confronto_servicos": [{
            "tops_de_lancamento": _junta(confronto.get("tops_de_lancamento")),
            "prefixo_de_pedido": confronto.get("prefixo_de_pedido", ""),
            "cnpj_descartado": confronto.get("cnpj_descartado", ""),
            "tolerancia_da_razao": _numero(confronto.get("tolerancia_da_razao")),
            "multiplo_minimo": _numero(confronto.get("multiplo_minimo")),
            "multiplo_maximo": _numero(confronto.get("multiplo_maximo")),
            "marca_de_cancelada": confronto.get("marca_de_cancelada", ""),
        }],
        "semana": [{
            "numero": semana.get("numero", ""),
            "data_de_referencia": semana.get("data_de_referencia", ""),
            "limite_de_dias": _numero(semana.get("limite_de_dias")),
        }],
        "resumo": [{
            "linhas_do_top": _numero(resumo.get("linhas_do_top")),
            "guardioes_no_grafico": _numero(resumo.get("guardioes_no_grafico")),
            "guardioes_fora_do_ranking":
                _junta(resumo.get("guardioes_fora_do_ranking")),
        }],
        "pre_categorizacao": [{
            chave: pre.get(chave) or padrao_pre[chave]
            for chave, _ in PRE_CATEGORIZACAO
        }],
        "sinonimos": [
            {"fonte": FONTES.get(fonte, fonte), "coluna": c.get("nome", ""),
             "sinonimos": _junta(c.get("sinonimos"))}
            for fonte, colunas in (dados.get("colunas") or {}).items()
            for c in colunas or []
        ],
    }


# -- da tela para a base ---------------------------------------------------

class _Relato:
    def __init__(self) -> None:
        self.problemas: list[dict[str, str]] = []

    def erro(self, onde: str, mensagem: str) -> None:
        self.problemas.append({"gravidade": "erro", "onde": onde,
                               "mensagem": mensagem})

    def aviso(self, onde: str, mensagem: str) -> None:
        self.problemas.append({"gravidade": "aviso", "onde": onde,
                               "mensagem": mensagem})

    @property
    def tem_erro(self) -> bool:
        return any(p["gravidade"] == "erro" for p in self.problemas)


def _texto(linha: dict[str, Any], chave: str) -> str:
    return aparar(linha.get(chave, "") if linha.get(chave) is not None else "")


def _vazia(linha: dict[str, Any]) -> bool:
    return not any(str(v).strip() for v in linha.values() if v is not None)


def _num(texto: Any, relato: _Relato, onde: str, rotulo: str, *,
         inteiro: bool = False, minimo: float | None = None) -> Any:
    bruto = str(texto if texto is not None else "").strip().replace(",", ".")
    try:
        valor = float(bruto)
    except ValueError:
        relato.erro(onde, f"'{rotulo}' precisa ser um número (veio '{texto}').")
        return None
    if inteiro:
        if not valor.is_integer():
            relato.erro(onde, f"'{rotulo}' precisa ser um número inteiro.")
            return None
        valor = int(valor)
    if minimo is not None and valor < minimo:
        relato.erro(onde, f"'{rotulo}' não pode ser menor que {minimo:g}.")
        return None
    return valor


def _tabela_ordenada(linhas: list[dict], campo_valor: str, rotulo: str,
                     relato: _Relato) -> list[dict]:
    """Unidades e categorias: ordem numérica única, trecho preenchido.

    E um aviso que só a ordem explica: um trecho que **contém** um trecho
    anterior nunca casa, porque o anterior pega tudo antes dele —
    `MATRIZ-FILIAIS` depois de `MATRIZ` é a linha que nunca vale.
    """
    saida, ordens = [], set()
    for linha in linhas:
        if _vazia(linha):
            continue
        trecho, valor = _texto(linha, "trecho"), _texto(linha, campo_valor)
        onde = f"{rotulo} '{trecho or valor}'"
        ordem = _num(linha.get("ordem"), relato, onde, "Ordem", inteiro=True,
                     minimo=1)
        if not trecho:
            relato.erro(onde, "falta o trecho.")
        if not valor:
            relato.erro(onde, f"falta o nome da {rotulo.lower()}.")
        if ordem is not None and ordem in ordens:
            relato.erro(onde, f"a ordem {ordem} está repetida — a ordem decide "
                              f"qual linha vale, e não pode empatar.")
        if ordem is not None:
            ordens.add(ordem)
        saida.append({"ordem": ordem if ordem is not None else 0,
                      "trecho": trecho, campo_valor: valor})
    saida.sort(key=lambda l: l["ordem"])
    for i, primeira in enumerate(saida):
        for depois in saida[i + 1:]:
            a, b = chave_de_texto(primeira["trecho"]), chave_de_texto(depois["trecho"])
            if a and b and a in b:
                relato.aviso(
                    f"{rotulo} '{depois['trecho']}'",
                    f"nunca vai casar: '{primeira['trecho']}' vem antes "
                    f"(ordem {primeira['ordem']}) e está contido nele. "
                    f"Ponha '{depois['trecho']}' antes.")
    return saida


def _unidades_sem_linha(unidades: list[dict], relato: _Relato) -> None:
    """As filiais que o histórico do Portal de Compras conhece e nenhuma
    linha reconhece — com a tabela preenchida, elas bloqueariam a semana."""
    if not unidades:
        return
    from .mercadorias.vocabulario import unidade_de
    from .servicos import historico

    nomes = sorted({str(f.get("nome") or "")
                    for f in historico.carregar().filiais.values()} - {""})
    soltas = [n for n in nomes if not unidade_de(n, unidades).reconhecido]
    if soltas:
        relato.aviso("Unidades",
                     f"{len(soltas)} filial(is) do histórico do Portal de "
                     f"Compras não casam com nenhuma linha: "
                     f"{'; '.join(soltas[:5])}")


def montar(tela: dict[str, Any], atual: dict[str, Any]
           ) -> tuple[dict[str, Any], list[dict[str, str]]]:
    """O que a tela mandou vira as seções da base, com os problemas achados."""
    relato = _Relato()
    parcial: dict[str, Any] = {}

    parcial["unidades"] = _tabela_ordenada(
        tela.get("unidades") or [], "unidade", "Unidade", relato)
    _unidades_sem_linha(parcial["unidades"], relato)
    parcial["categorias"] = _tabela_ordenada(
        tela.get("categorias") or [], "categoria", "Categoria", relato)

    filiais = []
    for linha in tela.get("filiais") or []:
        if _vazia(linha):
            continue
        digitos = so_cnpj(linha.get("cnpj"))
        if len(digitos) != 14:
            relato.erro(f"Filial '{_texto(linha, 'nome') or linha.get('cnpj')}'",
                        f"o CNPJ precisa ter 14 dígitos (tem {len(digitos)}).")
        filiais.append({"cnpj": digitos, "codigo": _texto(linha, "codigo"),
                        "nome": _texto(linha, "nome")})
    parcial["filiais"] = filiais

    parcial["guardioes"] = [
        _texto(l, "guardiao") for l in tela.get("guardioes") or []
        if _texto(l, "guardiao")]

    excecoes = []
    for linha in tela.get("excecoes_servicos") or []:
        if _vazia(linha):
            continue
        codigo = _texto(linha, "codigo_parceiro")
        onde = f"Exceção '{codigo or _texto(linha, 'nome')}'"
        if not codigo:
            relato.erro(onde, "falta o código do parceiro.")
        valor = _num(linha.get("valor"), relato, onde, "Valor", minimo=0)
        excecoes.append({"codigo_parceiro": codigo, "nome": _texto(linha, "nome"),
                         "valor": valor, "motivo": _texto(linha, "motivo")})
    parcial["excecoes_servicos"] = excecoes

    onde = "Confronto de serviços"
    linha = (tela.get("confronto_servicos") or [{}])[0]
    confronto = dict(atual.get("confronto_servicos") or {})
    tops = [t.strip() for t in str(linha.get("tops_de_lancamento") or "").split(";")
            if t.strip()]
    if not tops:
        relato.erro(onde, "sem TOP de lançamento nenhum, nenhuma nota casa.")
    confronto.update({
        "tops_de_lancamento": tops,
        "prefixo_de_pedido": _texto(linha, "prefixo_de_pedido"),
        "cnpj_descartado": so_cnpj(linha.get("cnpj_descartado")),
        "tolerancia_da_razao": _num(linha.get("tolerancia_da_razao"), relato,
                                    onde, "Tolerância", minimo=0),
        "multiplo_minimo": _num(linha.get("multiplo_minimo"), relato, onde,
                                "Múltiplo mín.", inteiro=True, minimo=1),
        "multiplo_maximo": _num(linha.get("multiplo_maximo"), relato, onde,
                                "Múltiplo máx.", inteiro=True, minimo=1),
        "marca_de_cancelada": _texto(linha, "marca_de_cancelada"),
    })
    if not confronto["prefixo_de_pedido"]:
        relato.erro(onde, "falta o prefixo de pedido.")
    if not confronto["marca_de_cancelada"]:
        relato.erro(onde, "falta a marca de cancelada.")
    minimo, maximo = confronto["multiplo_minimo"], confronto["multiplo_maximo"]
    if isinstance(minimo, int) and isinstance(maximo, int) and minimo > maximo:
        relato.erro(onde, "o múltiplo mínimo é maior que o máximo.")
    parcial["confronto_servicos"] = confronto

    onde = "Semana"
    linha = (tela.get("semana") or [{}])[0]
    semana = dict(atual.get("semana") or {})
    numero = _texto(linha, "numero")
    if numero and not (numero.isdigit() and 1 <= int(numero) <= 53):
        relato.erro(onde, f"o número da semana vai de 1 a 53 (veio '{numero}').")
    referencia = _texto(linha, "data_de_referencia")
    if referencia:
        from .valores import data_br

        if isinstance(data_br(referencia), str):
            relato.erro(onde, f"não entendi a data '{referencia}' — use "
                              f"dd/mm/aaaa.")
    if numero:
        relato.aviso(onde, f"a semana está fixada em {numero}: lembre de "
                           f"esvaziar antes da semana seguinte.")
    semana.update({
        "numero": numero, "data_de_referencia": referencia,
        "limite_de_dias": _num(linha.get("limite_de_dias"), relato, onde,
                               "Limite de dias", inteiro=True, minimo=0),
    })
    parcial["semana"] = semana

    onde = "Resumo Executivo"
    linha = (tela.get("resumo") or [{}])[0]
    resumo = dict(atual.get("resumo") or {})
    resumo.update({
        "linhas_do_top": _num(linha.get("linhas_do_top"), relato, onde,
                              "Linhas do TOP", inteiro=True, minimo=1),
        "guardioes_no_grafico": _num(linha.get("guardioes_no_grafico"), relato,
                                     onde, "Guardiões no gráfico",
                                     inteiro=True, minimo=1),
        "guardioes_fora_do_ranking": [
            g.strip() for g in str(linha.get("guardioes_fora_do_ranking") or ""
                                   ).split(";") if g.strip()],
    })
    parcial["resumo"] = resumo

    onde = "Pré-categorização"
    linha = (tela.get("pre_categorizacao") or [{}])[0]
    pre = dict(atual.get("pre_categorizacao") or {})
    for chave, rotulo in PRE_CATEGORIZACAO:
        valor = chave_de_texto(linha.get(chave)).lower()
        if valor not in GRAUS:
            relato.erro(onde, f"'{rotulo}' aceita firme, sugestao ou nao "
                              f"(veio '{linha.get(chave)}').")
        pre[chave] = valor
    parcial["pre_categorizacao"] = pre

    colunas = copy.deepcopy(atual.get("colunas") or {})
    por_rotulo = {rotulo: fonte for fonte, rotulo in FONTES.items()}
    for linha in tela.get("sinonimos") or []:
        if _vazia(linha):
            continue
        fonte = por_rotulo.get(_texto(linha, "fonte"), _texto(linha, "fonte"))
        coluna = _texto(linha, "coluna")
        alvo = next((c for c in colunas.get(fonte) or []
                     if chave_de_texto(c.get("nome")) == chave_de_texto(coluna)),
                    None)
        if alvo is None:
            relato.erro(f"Sinônimo '{coluna}'",
                        f"o relatório '{_texto(linha, 'fonte')}' não tem a "
                        f"coluna '{coluna}'. Só os sinônimos são editáveis — "
                        f"relatório e coluna não mudam pela tela.")
            continue
        alvo["sinonimos"] = [s.strip() for s in
                             str(linha.get("sinonimos") or "").split(";")
                             if s.strip()]
    parcial["colunas"] = colunas

    return parcial, relato.problemas


def gravar(tela: dict[str, Any], responsavel: str = "") -> tuple[bool, list[dict]]:
    """Confere e grava. Devolve `(gravou, problemas)`. Com erro, não grava."""
    atual = parametros.carregar()
    parcial, problemas = montar(tela, atual)
    if any(p["gravidade"] == "erro" for p in problemas):
        return False, problemas
    parametros.gravar(parcial, responsavel=responsavel or None)
    return True, problemas
