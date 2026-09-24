"""A carga de fábrica versionada e a base viva que fica fora do git.

Mesma arquitetura do Fiscalbot, pelo mesmo motivo. Dois endereços:

| Onde | O que tem | Versionado? |
|---|---|---|
| `pendentes/parametros_de_fabrica.yaml` | valores de partida, **sem dado da empresa** | sim |
| `dados/pendentes/parametros.yaml` | a base viva, editada pela tela | não |

Na primeira abertura a base é semeada da fábrica. Dali em diante quem manda é
a base: atualizar a fábrica não mexe em quem já está rodando.

**O que nunca entra na fábrica:** unidade, filial e guardião. São nome e CNPJ
reais — dado da empresa, regra nº 1. Numa máquina nova nascem vazios e são
cadastrados na tela, exatamente como as listas de parceiros do Fiscalbot.

A regra nº 2 do `CLAUDE.md` fala de **regra tributária**, e nada aqui é regra
tributária: não há alíquota, não há base, não há crédito. O que vale é o
princípio por trás dela — *o que o time fiscal muda sem precisar de
desenvolvedor não pode morar em `.py`* —, que é mais exigente, não menos.
"""
from __future__ import annotations

import os
from datetime import date, datetime
from pathlib import Path
from typing import Any

import yaml

from . import cabecalho as cab
from . import papeis as pap
from .farol import tabela_de

#: A carga de fábrica, versionada, ao lado do projeto.
FABRICA = Path(__file__).resolve().parents[2] / "parametros_de_fabrica.yaml"

#: As seções que a tela edita em fatias — `gravar` mescla, nunca substitui.
SECOES = ("confronto_servicos", "excecoes_servicos", "mercadorias",
          "pre_categorizacao", "resumo", "semana", "farol", "roteamento",
          "categorias", "unidades", "filiais", "guardioes", "papeis",
          "colunas")


def _raiz() -> Path:
    for pasta in Path(__file__).resolve().parents:
        if (pasta / "vendor" / "openpyxl").is_dir():
            return pasta
    return Path(__file__).resolve().parents[3]


def caminho_da_base() -> Path:
    """A base viva do aplicativo. Fora do git, como `dados/fiscalbot/`."""
    return _raiz() / "dados" / "pendentes" / "parametros.yaml"


# -- carregar e gravar -----------------------------------------------------

def carregar_fabrica(caminho: Path | None = None) -> dict[str, Any]:
    caminho = Path(caminho) if caminho else FABRICA
    if not caminho.is_file():                            # pragma: no cover
        return {}
    return yaml.safe_load(caminho.read_text(encoding="utf-8")) or {}


def carregar(caminho: Path | None = None) -> dict[str, Any]:
    """A base viva. Semeia da carga de fábrica na primeira vez."""
    caminho = Path(caminho) if caminho else caminho_da_base()
    if caminho.is_file():
        dados = yaml.safe_load(caminho.read_text(encoding="utf-8")) or {}
        # A base de uma versão antiga pode não ter uma seção nova. Ela vem da
        # fábrica, e o que a base já tem continua valendo.
        de_fabrica = carregar_fabrica()
        for secao, valor in de_fabrica.items():
            dados.setdefault(secao, valor)
        return dados
    return carregar_fabrica()


def gravar(parcial: dict[str, Any], responsavel: str | None = None,
           caminho: Path | None = None) -> Path:
    """Mescla o que a tela mandou na base, e carimba quem gravou e quando.

    **Mescla, nunca substitui.** Cada tela edita uma fatia — a de mercadorias
    não conhece os TOPs de serviço, e mandar o arquivo inteiro de volta faria
    uma tela apagar o que a outra cadastrou.

    O carimbo é o que substitui, dentro do aplicativo, o histórico que o git
    daria: sem ele ninguém sabe de onde veio um parâmetro que mudou.
    """
    caminho = Path(caminho) if caminho else caminho_da_base()
    dados = carregar(caminho)
    for secao, valor in parcial.items():
        dados[secao] = valor
    dados["atualizado_em"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    dados["atualizado_por"] = (
        responsavel or os.environ.get("USERNAME") or os.environ.get("USER") or "?"
    )
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(
        yaml.safe_dump(dados, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    return caminho


# -- as vistas que o resto do projeto consome ------------------------------

def secao(dados: dict[str, Any], nome: str, padrao: Any = None) -> Any:
    valor = dados.get(nome)
    return padrao if valor is None else valor


def colunas_de(dados: dict[str, Any], fonte: str) -> tuple[cab.Exigencia, ...]:
    """As exigências de coluna de um relatório, com sinônimos e obrigatoriedade."""
    return cab.exigencias_de((dados.get("colunas") or {}).get(fonte) or [])


def papeis_de(dados: dict[str, Any], dominio: str = "") -> tuple[pap.Papel, ...]:
    """Os papéis de arquivo esperados, do domínio pedido."""
    return pap.papeis_de(dados.get("papeis") or [], dominio)


def farol_de(dados: dict[str, Any], qual: str):
    """A tabela de códigos de emoji: `pedido` ou `semaforo`."""
    return tabela_de((dados.get("farol") or {}).get(qual) or [])


def unidades(dados: dict[str, Any]) -> list[dict]:
    """A tabela de palavras-chave de unidade, na ordem em que foi cadastrada.

    Quem for aplicá-la passa por `tabelas.por_ordem` — a ordem é a regra,
    porque `CORUMB` tem de ser testado antes de `GUAR`.
    """
    return list(dados.get("unidades") or [])


def roteamento(dados: dict[str, Any]) -> list[dict]:
    """As condições de roteamento de mercadorias, como cadastradas."""
    return list(dados.get("roteamento") or [])


def categorias(dados: dict[str, Any]) -> list[dict]:
    """A tabela de categorias, na ordem em que foi cadastrada.

    Tabela vazia desliga a validação, que é o comportamento de hoje — e a
    ordem é a regra: `indireto` antes de `direto`, senão "Indiretos" casa com
    o trecho "direto" e a categoria indireta vira direta sem aviso.
    """
    return list(dados.get("categorias") or [])


def guardioes(dados: dict[str, Any]) -> list[str]:
    """As áreas guardiãs válidas. Nasce **vazia**, e vazia não valida nada.

    É dado da empresa (nome de área), então não vem da fábrica. Enquanto a
    lista não for cadastrada, qualquer texto entra em `Guardião` — que é o
    comportamento de hoje. Ver a decisão pendente nº 6.
    """
    return [str(g).strip() for g in (dados.get("guardioes") or []) if str(g).strip()]


def mercadorias(dados: dict[str, Any]) -> dict[str, Any]:
    """Os literais que as regras de mercadorias comparam e gravam.

    Nenhum deles é regra tributária, e nenhum é dado da empresa: são o
    vocabulário do export do Sankhya (`NF-e Destinada a Transporte`, `Sim`) e
    o das regras B1 e B2 (`Fiscal`, `Faturamento`). Mudam quando o relatório
    muda de redação — hoje isso quebra em silêncio, e é o defeito 10 do porte.

    O `ausente_da_conferencia` merece nota: é o `"não"` **minúsculo** que o VBA
    grava em `Conf fisica`, `Conf fiscal` e `Incongruência` quando a nota não
    está na Conferência de Entradas. Trocá-lo por vazio faria `zero_ou_vazio`
    devolver `True` e a regra B1 reclassificaria para Fiscal notas que nem
    foram conferidas. Ver o preservado nº 19 do registro do porte.

    Os três de B1.5 são os dois rótulos do farol de pedido e o guardião que a
    regra grava. Os rótulos **têm de casar com a tabela `farol.pedido`** — é o
    que ela escreve na coluna, e trocar o ícone do semáforo no Sankhya troca o
    código, não o rótulo. `Suprimentos` entra pelo mesmo critério que `Fiscal`
    e `Faturamento`: é nome de função, o vocabulário da regra, e não o
    organograma desta empresa — que continua nascendo vazio (regra nº 1).
    """
    bruto = dict(dados.get("mercadorias") or {})
    return {
        "tipo_nfe_de_transporte": str(
            bruto.get("tipo_nfe_de_transporte") or "NF-e Destinada a Transporte"),
        "ausente_da_conferencia": str(bruto.get("ausente_da_conferencia") or "não"),
        "conferencia_fisica_confirmada": str(
            bruto.get("conferencia_fisica_confirmada") or "Sim"),
        "conf_fiscal_lancada": str(bruto.get("conf_fiscal_lancada") or "Sim"),
        "sem_pedido_vinculado": str(
            bruto.get("sem_pedido_vinculado") or "NA Conf Física"),
        "guardiao_da_reclassificacao": str(
            bruto.get("guardiao_da_reclassificacao") or "Fiscal"),
        "guardioes_da_fis_fat": tuple(
            str(g).strip() for g in (bruto.get("guardioes_da_fis_fat")
                                     or ("Fiscal", "Faturamento"))),
        "pedido_confirmado": str(bruto.get("pedido_confirmado") or "Sim"),
        "pedido_nao_confirmado": str(
            bruto.get("pedido_nao_confirmado") or "Não"),
        "guardiao_do_pedido": str(
            bruto.get("guardiao_do_pedido") or "Suprimentos"),
    }


def resumo(dados: dict[str, Any]) -> dict[str, Any]:
    """Os ajustes do painel semanal, com o padrão medido no arquivo de origem.

    Nenhum é regra tributária e nenhum muda número: mudam **o que cabe na
    tela**. Quantas notas cada TOP mostra, quantas barras o gráfico de
    guardião aguenta e a partir de quantos dias uma nota é destacada são
    decisões de quem lê o painel toda segunda-feira, não de quem programa.

    `guardioes_fora_do_ranking` nasce vazia pelo mesmo motivo que a lista de
    guardiões: nome de área é dado da empresa (regra nº 1). No arquivo da
    semana 38 ela tem três entradas — dois marcadores de que a classificação
    não fechou e uma área que o time decidiu não rankear.
    """
    bruto = dict(dados.get("resumo") or {})
    return {
        "linhas_do_top": int(bruto.get("linhas_do_top") or 5),
        "guardioes_no_grafico": int(bruto.get("guardioes_no_grafico") or 8),
        "destacar_acima_de_dias": int(bruto.get("destacar_acima_de_dias") or 10),
        "guardioes_fora_do_ranking": tuple(
            str(g).strip()
            for g in (bruto.get("guardioes_fora_do_ranking") or ())
            if str(g).strip()),
    }


def pre_categorizacao(dados: dict[str, Any]) -> dict[str, str]:
    """Qual coluna a base de conhecimento preenche, e com que exigência.

    Um valor por coluna: `firme` (só o que a lista curada e o histórico
    afirmam juntos, com lastro), `sugestao` (também o que tem proposta sem
    lastro) ou `nao` (não preenche).

    `[FATO]` A carga de fábrica liga as duas colunas em `sugestao`, por
    decisão do Compliance Tributário de 22/09/2026, tomada depois da medição
    contra a semana 38 — que mostra categoria acertando 44 de 44 com
    evidência firme e guardião acertando 77% no grau de sugestão. Não é
    parâmetro tributário nem dado da empresa: é o quanto de risco de revisão
    manual o time aceita, e por isso vem da fábrica e é editável na tela.

    `Gestor de apoio` entrou em 24/09/2026, também em `sugestao`. O padrão
    está aqui, e não só na fábrica, porque a fábrica não chega a quem já
    roda: a base viva que já tem a seção `pre_categorizacao` não ganha a
    chave nova, e é o padrão do código que liga o gestor para todo mundo.

    A trava que não é parâmetro: **nada sobrescreve célula preenchida**, e
    toda célula preenchida pela base sai marcada.
    """
    bruto = dict(dados.get("pre_categorizacao") or {})
    from .mercadorias import colunas as col

    return {
        col.C_CATEGORIA: str(bruto.get("categoria") or "sugestao"),
        col.C_GUARDIAO: str(bruto.get("guardiao") or "sugestao"),
        col.C_GESTOR: str(bruto.get("gestor_de_apoio") or "sugestao"),
        col.C_TIPO_DE_OPERACAO: str(bruto.get("tipo_de_operacao") or "firme"),
    }


def confronto_de_servicos(dados: dict[str, Any]) -> dict[str, Any]:
    """Os limiares do confronto de serviços, com o padrão da fábrica.

    Nenhum deles é regra tributária — são código de configuração do ERP e
    calibragem de heurística. O critério que os tira do `.py` é o outro, o que
    o Fiscalbot explicitou: *o que o time fiscal muda sem precisar de
    desenvolvedor não pode morar em código*. Um TOP novo é criado por quem
    administra o Sankhya.
    """
    bruto = dict(dados.get("confronto_servicos") or {})
    return {
        "tops_de_lancamento": tuple(
            str(t).strip() for t in bruto.get("tops_de_lancamento") or ()),
        "prefixo_de_pedido": str(bruto.get("prefixo_de_pedido") or "PC"),
        "cnpj_descartado": str(bruto.get("cnpj_descartado") or ""),
        "tolerancia_da_razao": float(bruto.get("tolerancia_da_razao") or 0.005),
        "multiplo_minimo": int(bruto.get("multiplo_minimo") or 2),
        "multiplo_maximo": int(bruto.get("multiplo_maximo") or 12),
        "marca_de_cancelada": str(bruto.get("marca_de_cancelada") or "cancelada"),
    }


def excecoes_de_servicos(dados: dict[str, Any]) -> tuple:
    """Os parceiros e valores que o time decidiu não cobrar. Nasce vazia.

    É cadastro, não regra derivável: alguém decidiu que aquela nota daquele
    parceiro não vira pendência. Traz código e nome de parceiro real, então é
    dado da empresa — regra nº 1 — e mora só na base viva.
    """
    from .servicos.exclusao import excecoes_de

    return excecoes_de(dados.get("excecoes_servicos") or [])


def filiais(dados: dict[str, Any]) -> list[dict]:
    """O complemento estático do de-para de filiais. Nasce vazio.

    É dado da empresa — CNPJ e nome de filial —, então mora só na base viva.
    Numa máquina nova a lista está vazia e o de-para é 100% dinâmico, que é o
    comportamento de hoje.
    """
    return list(dados.get("filiais") or [])


def semana_de(dados: dict[str, Any], hoje: date | None = None) -> tuple[int, int]:
    """O ano e o número da semana desta execução.

    O VBA pergunta o número num `InputBox`. Não há campo de texto na tela de
    execução da Central, e **deduzir em silêncio seria adivinhação** — por
    isso a semana deduzida é sempre exibida como ficha e é corrigível na tela
    de configuração antes da execução seguinte.

    A regra: o número cadastrado manda; sem ele, vale a semana ISO da data de
    referência; sem data de referência, a de hoje.
    """
    secao_da_semana = dict(dados.get("semana") or {})
    referencia = secao_da_semana.get("data_de_referencia")
    quando = None
    if referencia:
        from .valores import data_br

        convertida = data_br(referencia)
        if not isinstance(convertida, str):
            quando = convertida
    if quando is None:
        quando = hoje or date.today()
    if isinstance(quando, datetime):
        quando = quando.date()

    ano, semana_iso, _ = quando.isocalendar()
    numero = str(secao_da_semana.get("numero") or "").strip()
    if numero.isdigit():
        return ano, int(numero)
    return ano, semana_iso
