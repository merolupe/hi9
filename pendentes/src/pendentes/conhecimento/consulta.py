"""A consulta das bases: o que a ferramenta sabe, sem abrir `.json`.

Duas bases alimentam as pendentes, e nenhuma se lia sem editor de texto:

| Base | Onde | O que tem |
|---|---|---|
| histórico do Portal de Compras | `conhecimento/portal_de_compras.json` | parceiro, pedido mais recente e filial por CNPJ (serviços) |
| base de mercadorias | `conhecimento/mercadorias.json` | guardião e categoria propostos por parceiro, gestor por guardião |

A tela é **só de consulta**: as duas bases são feitas por importação (o
Portal de Compras também cresce a cada semana), e editar uma linha à mão
quebraria o lastro que diz de onde ela veio. Para mudar, importa-se de novo.

Como o módulo de configuração, este descreve as seções em dicionários — quem
desenha é a Central.
"""
from __future__ import annotations

from typing import Any

from ..servicos import historico as portal
from ..servicos.enriquecimento import cnpj_formatado
from . import base as conhecido


def _campo(chave: str, rotulo: str, largura: int = 14,
           ajuda: str = "") -> dict[str, Any]:
    return {"chave": chave, "rotulo": rotulo, "largura": largura,
            "ajuda": ajuda, "tipo": "texto"}


def _secao(id_: str, titulo: str, explicacao: str, campos: list[dict],
           fixa: bool = False) -> dict[str, Any]:
    return {"id": id_, "titulo": titulo, "explicacao": explicacao,
            "campos": campos, "fixa": fixa, "somente_leitura": True}


def secoes() -> list[dict[str, Any]]:
    return [
        _secao("portal", "Histórico do Portal de Compras — situação",
               "O que as exportações do Portal de Compras já ensinaram. Cresce "
               "sozinho a cada execução do GerarServPend; a carga de um "
               "período longo entra arrastando o relatório aqui, sozinho.",
               [_campo("parceiros", "Parceiros", 10),
                _campo("pedidos", "Pedidos", 10),
                _campo("filiais", "Filiais", 8),
                _campo("periodo", "Período coberto", 26,
                       "Da negociação mais antiga à mais recente."),
                _campo("atualizado_em", "Atualizado em", 20),
                _campo("atualizado_por", "Por", 24)],
               fixa=True),
        _secao("portal_parceiros", "Histórico — parceiros",
               "Código e nome no Sankhya, por CNPJ. Parceiro sem movimento na "
               "semana sai com este código, em vez de 'Sem cadastro'.",
               [_campo("cnpj", "CNPJ/CPF", 20), _campo("codigo", "Código", 9),
                _campo("nome", "Nome no Sankhya", 44),
                _campo("visto_em", "Visto em", 12,
                       "Data de negociação do registro mais recente.")]),
        _secao("portal_pedidos", "Histórico — pedido de compra mais recente",
               "O pedido de maior Nro. Único de cada parceiro. É dele que saem "
               "comprador, requisitante, natureza e CR na Pendentes.",
               [_campo("cnpj", "CNPJ/CPF", 20),
                _campo("parceiro", "Parceiro", 36),
                _campo("numero_unico", "Nro. Único", 11),
                _campo("data", "Negociação", 12),
                _campo("comprador", "Comprador", 22),
                _campo("requisitante", "Requisitante", 22),
                _campo("natureza", "Natureza", 22),
                _campo("centro_de_resultado", "CR", 22),
                _campo("empresa", "Empresa", 8)]),
        _secao("portal_filiais", "Histórico — filiais",
               "O de-para de filial pelo CNPJ da empresa.",
               [_campo("cnpj", "CNPJ", 20), _campo("codigo", "Código", 8),
                _campo("nome", "Nome fantasia", 40)]),
        _secao("portal_fontes", "Histórico — o que já foi absorvido",
               "Cada relatório que entrou, com a impressão do arquivo.",
               [_campo("nome", "Arquivo", 34), _campo("como", "Como", 12),
                _campo("periodo", "Período", 24),
                _campo("registros", "Linhas", 8),
                _campo("absorvido_em", "Absorvido em", 20)]),
        _secao("mercadorias", "Base de mercadorias — situação",
               "A base de classificação de mercadorias, importada da lista "
               "curada (.csv) e das regras medidas (.json).",
               [_campo("parceiros", "Parceiros", 10),
                _campo("operacoes", "Operações por CFOP", 16),
                _campo("guardioes", "Guardiões observados", 18),
                _campo("importado_em", "Importada em", 20),
                _campo("importado_por", "Por", 20)],
               fixa=True),
        _secao("mercadorias_parceiros", "Base de mercadorias — parceiros",
               "O que a base propõe para cada parceiro. 'firme' preenche "
               "célula; 'sugestao' só preenche se a pré-categorização "
               "permitir. Regras por unidade não aparecem aqui.",
               [_campo("codigo", "Código", 9), _campo("nome", "Parceiro", 36),
                _campo("guardiao", "Guardião proposto", 20),
                _campo("grau_guardiao", "Grau", 10),
                _campo("categoria", "Categoria proposta", 16),
                _campo("grau_categoria", "Grau", 10),
                _campo("unidades", "Regras por unidade", 10)]),
        _secao("mercadorias_gestores", "Base de mercadorias — gestor por guardião",
               "O gestor vigente de cada guardião, que preenche 'Gestor de "
               "apoio'.",
               [_campo("guardiao", "Guardião", 24), _campo("gestor", "Gestor", 24),
                _campo("grau", "Grau", 10)]),
    ]


def _inteiro(valor: Any) -> Any:
    if isinstance(valor, float) and valor.is_integer():
        return int(valor)
    return valor if valor is not None else ""


def _ler_portal(memoria: portal.Historico) -> dict[str, list[dict]]:
    datas = [str(p.get("visto_em") or "") for p in memoria.parceiros.values()]
    datas += [str(p.get("data") or "") for p in memoria.pedidos.values()]
    datas = sorted(d for d in datas if d)
    nomes = {cnpj: p.get("nome", "") for cnpj, p in memoria.parceiros.items()}
    codigos = {cnpj: p.get("codigo", "") for cnpj, p in memoria.parceiros.items()}
    return {
        "portal": [{
            "parceiros": len(memoria.parceiros),
            "pedidos": len(memoria.pedidos),
            "filiais": len(memoria.filiais),
            "periodo": f"{datas[0]} a {datas[-1]}" if datas else "vazio",
            "atualizado_em": memoria.atualizado_em,
            "atualizado_por": memoria.atualizado_por,
        }],
        "portal_parceiros": [
            {"cnpj": cnpj_formatado(cnpj), "codigo": p.get("codigo", ""),
             "nome": p.get("nome", ""), "visto_em": p.get("visto_em", "")}
            for cnpj, p in sorted(memoria.parceiros.items(),
                                  key=lambda t: str(t[1].get("nome", "")))
        ],
        "portal_pedidos": [
            {"cnpj": cnpj_formatado(cnpj),
             "parceiro": " — ".join(x for x in (codigos.get(cnpj, ""),
                                                nomes.get(cnpj, "")) if x),
             "numero_unico": _inteiro(p.get("numero_unico")),
             "data": p.get("data", ""), "comprador": p.get("comprador", ""),
             "requisitante": p.get("requisitante", ""),
             "natureza": p.get("natureza", ""),
             "centro_de_resultado": p.get("centro_de_resultado", ""),
             "empresa": p.get("empresa", "")}
            for cnpj, p in sorted(memoria.pedidos.items(),
                                  key=lambda t: -float(t[1].get("numero_unico")
                                                       or 0))
        ],
        "portal_filiais": [
            {"cnpj": cnpj_formatado(cnpj), "codigo": f.get("codigo", ""),
             "nome": f.get("nome", "")}
            for cnpj, f in sorted(memoria.filiais.items(),
                                  key=lambda t: str(t[1].get("nome", "")))
        ],
        "portal_fontes": [
            {"nome": f.get("nome", ""), "como": f.get("como", ""),
             "periodo": " a ".join(x for x in f.get("periodo") or [] if x),
             "registros": f.get("registros", ""),
             "absorvido_em": f.get("absorvido_em", "")}
            for f in reversed(memoria.fontes)
        ],
    }


def _proposta(parceiro: dict[str, Any], campo: str) -> tuple[str, str]:
    bruto = parceiro.get(campo) or {}
    valor = str(bruto.get("proposto") or "")
    grau, _ = conhecido._confianca(valor,
                                   conhecido.Evidencia.de(bruto.get("evidencia")))
    return valor, grau


def _ler_mercadorias(base: conhecido.Conhecimento) -> dict[str, list[dict]]:
    parceiros = []
    for codigo, p in sorted(base.parceiros.items(),
                            key=lambda t: str(t[1].get("nome", ""))):
        guardiao, grau_g = _proposta(p, "guardiao")
        categoria, grau_c = _proposta(p, "categoria")
        parceiros.append({
            "codigo": codigo, "nome": p.get("nome", ""),
            "guardiao": guardiao, "grau_guardiao": grau_g,
            "categoria": categoria, "grau_categoria": grau_c,
            "unidades": len(p.get("unidades") or {}) or "",
        })
    gestores = []
    for chave, bruto in sorted(base.gestor_do_guardiao.items()):
        proposta = base.gestor_de(bruto.get("rotulo") or chave)
        gestores.append({"guardiao": bruto.get("rotulo") or chave,
                         "gestor": proposta.valor, "grau": proposta.confianca})
    return {
        "mercadorias": [{
            "parceiros": len(base.parceiros),
            "operacoes": sum(len(n) for n in base.operacoes.values()),
            "guardioes": len(base.guardioes_observados),
            "importado_em": base.importado_em or "nunca importada",
            "importado_por": base.importado_por,
        }],
        "mercadorias_parceiros": parceiros,
        "mercadorias_gestores": gestores,
    }


def ler() -> dict[str, list[dict]]:
    return {**_ler_portal(portal.carregar()),
            **_ler_mercadorias(conhecido.carregar())}
