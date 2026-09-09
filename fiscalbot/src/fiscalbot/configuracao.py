"""O que a tela da Central mostra e grava.

Este módulo é a ponte entre a base de regras e a interface. Ele descreve as
seções em estruturas simples — dicionários e listas —, sem conhecer navegador
nem HTML: quem desenha é a Central. É o que mantém a regra do repositório de
que nenhuma ferramenta importa outra.

Cada seção é uma tabela editável. A explicação de cada campo aparece na tela,
porque a mini-linguagem das condições não é óbvia para quem cadastra uma regra
duas vezes por ano.
"""
from __future__ import annotations

from typing import Any

from . import base as bases
from .modelo import BaseDeRegras, Parametros, Parceiro, Regra
from .validacao import conferir, tem_erro

#: A ordem em que as UFs aparecem na matriz de alíquotas.
UFS = ("AC", "AL", "AM", "AP", "BA", "CE", "DF", "ES", "GO", "MA", "MT", "MS",
       "MG", "PA", "PB", "PR", "PE", "PI", "RJ", "RN", "RS", "RO", "RR", "SC",
       "SP", "SE", "TO")


def _campo(chave: str, rotulo: str, largura: int = 14, ajuda: str = "",
           tipo: str = "texto") -> dict[str, Any]:
    return {"chave": chave, "rotulo": rotulo, "largura": largura,
            "ajuda": ajuda, "tipo": tipo}


CAMPOS_DA_REGRA = [
    _campo("id", "ID", 7, "Identificador curto e único. Ex.: E01, S12, RS03."),
    _campo("operacao", "Operação", 26,
           "O nome que aparece na planilha auditada."),
    _campo("ativa", "Ativa", 6, "Regra inativa não entra na auditoria.", "booleano"),
    _campo("es", "E/S", 8, "Entrada ou Saída. Compara só a primeira letra."),
    _campo("especie", "Espécie", 8, "NF ou CT. Vazio vale para as duas."),
    _campo("cfop", "CFOP", 16,
           "Um ou mais, separados por ponto e vírgula: 1602;2602. "
           "Regra ativa sem CFOP nunca casa."),
    _campo("cond_produto", "Cond. produto", 20,
           "Código exato, INICIA:7010, NAOINICIA:7010, TABELA:FRETE ou "
           "TABELAEXCETO:FRETE:700000001,700000002"),
    _campo("cond_par_uf", "Cond. UF", 20,
           "SPxSP;MTxMT, INTRA, INTER, UFORIG:BA;PR, NAOUFORIG:SC ou "
           "NAOPARUF:SPxSP"),
    _campo("cond_parceiro", "Cond. parceiro", 18,
           "INICIA:econet ou NAOINICIA:econet — pelo nome do parceiro."),
    _campo("esp_cst", "CST esperado", 14,
           "60, EM:00,20 ou NAOEM:41,50. Atenção: aqui a lista separa por "
           "vírgula."),
    _campo("esp_icms", "ICMS esperado", 14,
           "0, >0 ou CARGA (quando quem confere o ICMS é a carga efetiva)."),
    _campo("esp_aliq", "Alíquota", 12,
           "7;12 ou TABELAUF, que busca na matriz origem × destino."),
    _campo("esp_carga", "Carga %", 9,
           "Carga efetiva alvo, em porcentagem. Ex.: 4 ou 12."),
    _campo("esp_outros", "Outros", 24,
           "PARCEIRO<20, PARCEIROINICIA:HINOVE, SEMPRE:texto ou "
           "SECST:20:texto"),
    _campo("base_legal", "Base legal", 22,
           "Não entra no motor. É a fonte da regra, para quem for revisar."),
    _campo("ultima_revisao", "Últ. revisão", 12,
           "Não entra no motor. Quando a regra foi conferida pela última vez."),
]


def secoes(base: BaseDeRegras | None = None) -> list[dict[str, Any]]:
    """As seções da tela. A matriz de alíquotas depende das UFs em uso."""
    base = base if base is not None else bases.carregar()
    ufs = sorted({uf for linha in base.aliquotas.values() for uf in linha} | set(UFS))
    return [
        {
            "id": "regras",
            "titulo": "Regras de enquadramento",
            "explicacao":
                "Cada linha identifica uma operação e diz o que se espera dela. "
                "Espera-se que exatamente uma regra case com cada registro — "
                "duas casando fazem a auditoria marcar AMBIGUA.",
            "campos": CAMPOS_DA_REGRA,
            "fixa": False,
        },
        {
            "id": "parametros",
            "titulo": "Parâmetros do motor",
            "explicacao":
                "Valem para a auditoria inteira, fora das regras.",
            "campos": [
                _campo("tolerancia_carga", "Tolerância da carga (pp)", 20,
                       "Quanto a carga efetiva pode variar para mais e para "
                       "menos, em pontos percentuais. Padrão 0,05.", "numero"),
                _campo("cst_exigem_icms_positivo", "CST que exigem ICMS > 0", 26,
                       "Separados por ponto e vírgula. Todos os demais CST "
                       "passam a exigir ICMS igual a zero (Camada 0)."),
            ],
            "fixa": True,
        },
        {
            "id": "tabelas",
            "titulo": "Tabelas de produto",
            "explicacao":
                "Listas nomeadas usadas por TABELA: e TABELAEXCETO: nas regras. "
                "A tabela CFOP_IND diz em quais CFOP a camada de produto de "
                "industrialização é conferida.",
            "campos": [
                _campo("nome", "Nome", 14, "Como a regra cita a tabela."),
                _campo("produtos", "Códigos", 60,
                       "Separados por ponto e vírgula."),
            ],
            "fixa": False,
        },
        {
            "id": "sinonimos",
            "titulo": "Nomes de coluna aceitos",
            "explicacao":
                "O layout do relatório muda entre extrações. Quando uma coluna "
                "trocar de nome, acrescente o nome novo aqui — não é preciso "
                "mexer em código.",
            "campos": [
                _campo("campo", "Campo", 12, "O campo interno: CST, CFOP, ICMS…"),
                _campo("nomes", "Nomes aceitos", 60,
                       "Separados por ponto e vírgula, na ordem de preferência."),
            ],
            "fixa": False,
        },
        {
            "id": "aliquotas",
            "titulo": "Matriz de alíquotas",
            "explicacao":
                "Alíquota esperada por UF de origem × UF de destino. É o que o "
                "operador TABELAUF consulta.",
            "campos": [_campo("origem", "Origem", 8, "UF de origem.")]
                      + [_campo(uf, uf, 6, f"Destino {uf}.", "numero") for uf in ufs],
            "fixa": False,
        },
        {
            "id": "parceiros_sn",
            "titulo": "Parceiros do Simples Nacional",
            "explicacao":
                "CT-e destes parceiros espera CST 90, sobrepondo qualquer regra. "
                "Esta lista tem dado da empresa e por isso não vem no "
                "repositório — é cadastrada aqui e fica só nesta máquina.",
            "campos": [
                _campo("codigo", "Código", 10, "Coluna Empresa/Parceiro do relatório."),
                _campo("descricao", "Parceiro", 40, "Só para quem lê a tela."),
            ],
            "fixa": False,
        },
        {
            "id": "parceiros_cavaco",
            "titulo": "Parceiros de cavaco",
            "explicacao":
                "Compra de matéria-prima (CFOP 1101/2101) destes parceiros tem "
                "enquadramento próprio: intra CST 51 com ICMS zero, inter CST 00 "
                "com alíquota 7 ou 12. Também é dado da empresa.",
            "campos": [
                _campo("codigo", "Código", 10, "Coluna Empresa/Parceiro do relatório."),
                _campo("descricao", "Parceiro", 40, "Só para quem lê a tela."),
            ],
            "fixa": False,
        },
    ]


# -- da base para a tela ---------------------------------------------------

def ler(base: BaseDeRegras | None = None) -> dict[str, Any]:
    base = base if base is not None else bases.carregar()
    ufs = [c["chave"] for c in secoes(base)[4]["campos"][1:]]
    return {
        "regras": [
            {
                "id": r.id, "operacao": r.operacao, "ativa": r.ativa, "es": r.es,
                "especie": r.especie, "cfop": ";".join(r.cfop),
                "cond_produto": r.cond_produto, "cond_par_uf": r.cond_par_uf,
                "cond_parceiro": r.cond_parceiro, "esp_cst": r.esp_cst,
                "esp_icms": r.esp_icms, "esp_aliq": r.esp_aliq,
                "esp_carga": r.esp_carga, "esp_outros": r.esp_outros,
                "base_legal": r.base_legal, "ultima_revisao": r.ultima_revisao,
            }
            for r in base.regras
        ],
        "parametros": [{
            "tolerancia_carga": base.parametros.tolerancia_carga,
            "cst_exigem_icms_positivo":
                ";".join(base.parametros.cst_exigem_icms_positivo),
        }],
        "tabelas": [
            {"nome": nome, "produtos": ";".join(valores)}
            for nome, valores in sorted(base.parametros.tabelas.items())
        ],
        "sinonimos": [
            {"campo": campo, "nomes": ";".join(valores)}
            for campo, valores in sorted(base.parametros.sinonimos.items())
        ],
        "aliquotas": [
            {"origem": origem, **{uf: linha.get(uf, "") for uf in ufs}}
            for origem, linha in sorted(base.aliquotas.items())
        ],
        "parceiros_sn": [
            {"codigo": p.codigo, "descricao": p.descricao}
            for p in base.parceiros_simples_nacional
        ],
        "parceiros_cavaco": [
            {"codigo": p.codigo, "descricao": p.descricao}
            for p in base.parceiros_cavaco
        ],
    }


# -- da tela para a base ---------------------------------------------------

def _texto(linha: dict[str, Any], chave: str) -> str:
    return str(linha.get(chave, "") or "").strip()


def _lista(texto: str) -> tuple[str, ...]:
    return tuple(p.strip() for p in texto.split(";") if p.strip())


def montar(dados: dict[str, Any]) -> BaseDeRegras:
    """Transforma o que a tela mandou numa base, sem gravar nada."""
    parametros_linha = (dados.get("parametros") or [{}])[0]
    try:
        tolerancia = float(str(parametros_linha.get("tolerancia_carga", 0.05)
                               ).replace(",", "."))
    except (TypeError, ValueError):
        tolerancia = -1.0                       # a validação recusa

    return BaseDeRegras(
        regras=[
            Regra(
                id=_texto(l, "id"), operacao=_texto(l, "operacao"),
                ativa=bool(l.get("ativa", True)), es=_texto(l, "es"),
                especie=_texto(l, "especie"),
                cfop=tuple(c.strip() for c in _texto(l, "cfop").split(";")),
                cond_produto=_texto(l, "cond_produto"),
                cond_par_uf=_texto(l, "cond_par_uf"),
                cond_parceiro=_texto(l, "cond_parceiro"),
                esp_cst=_texto(l, "esp_cst"), esp_icms=_texto(l, "esp_icms"),
                esp_aliq=_texto(l, "esp_aliq"), esp_carga=_texto(l, "esp_carga"),
                esp_outros=_texto(l, "esp_outros"),
                base_legal=_texto(l, "base_legal"),
                ultima_revisao=_texto(l, "ultima_revisao"),
            )
            for l in (dados.get("regras") or [])
            if any(str(v).strip() for v in l.values())
        ],
        parametros=Parametros(
            tolerancia_carga=tolerancia,
            cst_exigem_icms_positivo=_lista(
                _texto(parametros_linha, "cst_exigem_icms_positivo")),
            tabelas={
                _texto(l, "nome").upper(): _lista(_texto(l, "produtos"))
                for l in (dados.get("tabelas") or []) if _texto(l, "nome")
            },
            sinonimos={
                _texto(l, "campo").upper(): _lista(_texto(l, "nomes"))
                for l in (dados.get("sinonimos") or []) if _texto(l, "campo")
            },
        ),
        aliquotas={
            _texto(l, "origem").upper(): {
                uf.upper(): float(str(valor).replace(",", "."))
                for uf, valor in l.items()
                if uf != "origem" and str(valor).strip() not in ("", "None")
            }
            for l in (dados.get("aliquotas") or []) if _texto(l, "origem")
        },
        parceiros_simples_nacional=[
            Parceiro(_texto(l, "codigo"), _texto(l, "descricao"))
            for l in (dados.get("parceiros_sn") or []) if _texto(l, "codigo")
        ],
        parceiros_cavaco=[
            Parceiro(_texto(l, "codigo"), _texto(l, "descricao"))
            for l in (dados.get("parceiros_cavaco") or []) if _texto(l, "codigo")
        ],
    )


def gravar(dados: dict[str, Any], responsavel: str = "") -> tuple[bool, list[dict]]:
    """Confere e grava. Devolve `(gravou, problemas)`.

    Com erro, não grava: uma base inconsistente auditaria o mês inteiro errado.
    Só aviso, grava e conta o que vai acontecer.
    """
    try:
        nova = montar(dados)
    except (TypeError, ValueError) as erro:
        return False, [{"gravidade": "erro", "onde": "Base",
                        "mensagem": f"não entendi o que a tela mandou: {erro}"}]

    problemas = conferir(nova)
    achados = [{"gravidade": p.gravidade, "onde": p.onde, "mensagem": p.mensagem}
               for p in problemas]
    if tem_erro(problemas):
        return False, achados
    bases.gravar(nova, responsavel=responsavel or None)
    return True, achados
