"""A base de conhecimento na tela: consultável, filtrável e editável.

### O que a tela mostra

Uma linha por regra, com **três coisas lado a lado**: o que a importação
propôs, a evidência que sustenta aquilo, e o que vale hoje. Só a última é
editável — evidência não se digita, e proposta importada não se rasura.

### Como ela sabe o que foi corrigido

Não por um campo "alterado", que dependeria de o navegador lembrar. Ela
**compara**: na hora de gravar, valor igual ao da fotografia não é ajuste, e
valor diferente é. Três consequências, todas desejáveis:

* digitar de novo o valor original **desfaz** o ajuste, sem botão de desfazer;
* reimportar não ressuscita correção que a pessoa já tinha revertido;
* o arquivo de ajustes guarda só o que difere, e não 700 linhas iguais.

### Por que a evidência aparece em texto e não em número

Quem abre esta tela está decidindo se confia na base. `23 de 65 notas, 21
semanas` responde isso; `0.35` não. Onde o histórico discorda da proposta, as
alternativas vêm na mesma célula — é ali que a pessoa vê o motivo da dúvida.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from ..texto import aparar, chave_de_texto
from . import ajustes as camada
from . import base as conhecido
from .base import AJUSTADO, Conhecimento, Evidencia

#: Os três escopos da base, que são as três seções da tela.
PARCEIROS = "parceiros"
GESTORES = "gestores"
OPERACOES = "operacoes"


def _campo(chave: str, rotulo: str, largura: int, ajuda: str,
           tipo: str = "texto") -> dict[str, Any]:
    return {"chave": chave, "rotulo": rotulo, "largura": largura,
            "ajuda": ajuda, "tipo": tipo}


def secoes(dominio: str = "mercadorias",
           raiz: Path | None = None) -> list[dict[str, Any]]:
    """As três tabelas, com a coluna editável sempre por último.

    A primeira carrega o tamanho da base na explicação, e isso é lido do disco
    **aqui** — quando a tela abre —, e não quando a Central sobe: a base muda a
    cada importação e a cada gravação.
    """
    return [
        {
            "id": PARCEIROS,
            "titulo": "Guardião e categoria por parceiro",
            "explicacao":
                resumo(dominio, raiz) + " " +
                "O que a base propõe para cada fornecedor, e o que o histórico "
                "mostrou. Linha com unidade preenchida vale só naquela "
                "unidade e vence a linha geral do mesmo parceiro. Edite "
                "`Guardião` ou `Categoria` para corrigir: o valor corrigido "
                "passa a preencher a planilha mesmo onde o histórico discorda. "
                "Apagar a correção, ou digitar de volta o valor proposto, "
                "devolve a regra à importação.",
            "fixa": False,
            "campos": [
                _campo("codigo", "Código", 8, "Código do parceiro no Sankhya"),
                _campo("nome", "Parceiro", 30, "Razão social, como veio na base"),
                _campo("unidade", "Unidade", 20,
                       "Nome Fantasia. Vazio = regra geral do parceiro"),
                _campo("guardiao_proposto", "Guardião proposto", 20,
                       "O que a importação propôs", "leitura"),
                _campo("guardiao_evidencia", "Evidência do guardião", 34,
                       "O que o histórico mostrou, e o que mais apareceu",
                       "leitura"),
                _campo("categoria_proposta", "Categoria proposta", 14,
                       "O que a importação propôs", "leitura"),
                _campo("categoria_evidencia", "Evidência da categoria", 28,
                       "O que o histórico mostrou", "leitura"),
                _campo("guardiao", "Guardião (vale)", 20,
                       "Editável. Vazio volta ao proposto"),
                _campo("categoria", "Categoria (vale)", 14,
                       "Editável. Vazio volta ao proposto"),
                _campo("trilha", "Corrigido por", 24,
                       "Quem corrigiu e quando", "leitura"),
            ],
        },
        {
            "id": GESTORES,
            "titulo": "Gestor de apoio vigente de cada guardião",
            "explicacao":
                "Quem responde por cada área. É esta tabela que preenche "
                "`Gestor de apoio`, a partir do guardião que a linha tem. "
                "Troca de gestor se resolve aqui, numa linha — e não esperando "
                "a próxima importação.",
            "fixa": False,
            "campos": [
                _campo("guardiao", "Guardião", 24, "A área"),
                _campo("gestor_proposto", "Gestor proposto", 18,
                       "O que a importação propôs", "leitura"),
                _campo("gestor_evidencia", "Evidência", 30,
                       "Notas na última observação, e os empates", "leitura"),
                _campo("gestor", "Gestor (vale)", 18,
                       "Editável. Vazio volta ao proposto"),
                _campo("trilha", "Corrigido por", 24,
                       "Quem corrigiu e quando", "leitura"),
            ],
        },
        {
            "id": OPERACOES,
            "titulo": "Tipo de Operação por CFOP",
            "explicacao":
                "A regra mais específica vence: CFOP + parceiro + categoria, "
                "depois CFOP + parceiro, depois CFOP + categoria, depois o "
                "CFOP sozinho. Conjunto de CFOP casa por correspondência "
                "exata do conjunto — `5102+5405` não atende uma nota só de "
                "`5102`.",
            "fixa": False,
            "campos": [
                _campo("cfop", "CFOP", 14, "Conjunto normalizado, em ordem"),
                _campo("parceiro", "Parceiro", 8,
                       "Código, quando a regra é daquele parceiro"),
                _campo("categoria", "Categoria", 12,
                       "Quando a regra é daquela categoria"),
                _campo("nivel", "Nível", 26, "Qual das quatro regras é esta",
                       "leitura"),
                _campo("operacao_proposta", "Operação proposta", 26,
                       "O que a importação propôs", "leitura"),
                _campo("operacao_evidencia", "Evidência", 28,
                       "O que o histórico mostrou", "leitura"),
                _campo("operacao", "Operação (vale)", 26,
                       "Editável. Vazio volta ao proposto"),
                _campo("trilha", "Corrigido por", 24,
                       "Quem corrigiu e quando", "leitura"),
            ],
        },
    ]


# -- a evidência em português ----------------------------------------------

def texto_da_evidencia(evidencia: Evidencia, limite: int = 3) -> str:
    """`23 de 65 notas, 21 semanas · também: Fulano 11, Ciclano 6`.

    Sem nota, devolve o que é verdade: o histórico não viu.
    """
    if not evidencia.notas:
        return "sem lastro no histórico"
    partes = [f"{evidencia.valor or '—'}: {evidencia.apoio} de "
              f"{evidencia.notas} notas, {evidencia.semanas} semana(s)"]
    outras = [(nome, quantas)
              for nome, quantas in sorted(evidencia.alternativas.items(),
                                          key=lambda t: (-t[1], t[0]))
              if chave_de_texto(nome) != chave_de_texto(evidencia.valor)]
    if outras:
        mostradas = ", ".join(f"{nome} {quantas}"
                              for nome, quantas in outras[:limite])
        resto = len(outras) - limite
        partes.append(f"também: {mostradas}"
                      + (f" e +{resto}" if resto > 0 else ""))
    return " · ".join(partes)


def _trilha(ajuste: camada.Ajuste) -> str:
    if not ajuste:
        return ""
    quem = ajuste.por or "?"
    return f"{quem} em {ajuste.em}" if ajuste.em else quem


def _proposto(bruto: dict[str, Any] | None) -> str:
    return str((bruto or {}).get("proposto") or "")


def _evidencia(bruto: dict[str, Any] | None) -> Evidencia:
    return Evidencia.de((bruto or {}).get("evidencia"))


# -- ler ---------------------------------------------------------------------

def ler(dominio: str = "mercadorias", raiz: Path | None = None
        ) -> dict[str, list[dict[str, Any]]]:
    """As três tabelas, com a fotografia e os ajustes lado a lado.

    A fotografia é lida **crua** (`com_ajustes=False`): a tela precisa das duas
    versões para poder comparar na hora de gravar.
    """
    foto = conhecido.carregar(dominio, raiz, com_ajustes=False)
    feitos = camada.carregar(dominio, raiz)
    return {
        PARCEIROS: _linhas_de_parceiros(foto, feitos),
        GESTORES: _linhas_de_gestores(foto, feitos),
        OPERACOES: _linhas_de_operacoes(foto, feitos),
    }


def _linha_de_parceiro(codigo: str, nome: str, rotulo: str,
                       origem: dict[str, Any],
                       feitos: camada.Ajustes) -> dict[str, Any]:
    guardiao = feitos.do_parceiro(codigo, "guardiao", rotulo)
    categoria = feitos.do_parceiro(codigo, "categoria", rotulo)
    return {
        "codigo": codigo,
        "nome": nome,
        "unidade": rotulo,
        "guardiao_proposto": _proposto(origem.get("guardiao")),
        "guardiao_evidencia": texto_da_evidencia(_evidencia(origem.get("guardiao"))),
        "categoria_proposta": _proposto(origem.get("categoria")),
        "categoria_evidencia": texto_da_evidencia(
            _evidencia(origem.get("categoria"))),
        "guardiao": guardiao.valor or _proposto(origem.get("guardiao")),
        "categoria": categoria.valor or _proposto(origem.get("categoria")),
        "trilha": _trilha(guardiao) or _trilha(categoria),
    }


def _linhas_de_parceiros(foto: Conhecimento,
                         feitos: camada.Ajustes) -> list[dict[str, Any]]:
    linhas = []
    for codigo in sorted(foto.parceiros, key=_ordem_do_codigo):
        parceiro = foto.parceiros[codigo]
        nome = str(parceiro.get("nome") or "")
        linhas.append(_linha_de_parceiro(codigo, nome, "", parceiro, feitos))
        unidades = parceiro.get("unidades") or {}
        for chave in sorted(unidades):
            unidade = unidades[chave]
            linhas.append(_linha_de_parceiro(
                codigo, nome, str(unidade.get("rotulo") or chave), unidade,
                feitos))
    return linhas


def _linhas_de_gestores(foto: Conhecimento,
                        feitos: camada.Ajustes) -> list[dict[str, Any]]:
    linhas = []
    for chave in sorted(foto.gestor_do_guardiao):
        bruto = foto.gestor_do_guardiao[chave]
        ajuste = camada.Ajuste.de(feitos.gestores.get(chave))
        rotulo = str(bruto.get("rotulo") or chave)
        linhas.append({
            "guardiao": rotulo,
            "gestor_proposto": _proposto(bruto),
            "gestor_evidencia": texto_da_evidencia(_evidencia(bruto)),
            "gestor": ajuste.valor or _proposto(bruto),
            "trilha": _trilha(ajuste),
        })
    return linhas


def _linhas_de_operacoes(foto: Conhecimento,
                         feitos: camada.Ajustes) -> list[dict[str, Any]]:
    linhas = []
    for cfop in sorted(foto.operacoes):
        niveis = foto.operacoes[cfop]
        for nivel in sorted(niveis):
            bruto = niveis[nivel]
            parceiro, _, categoria = nivel.partition("|")
            ajuste = camada.Ajuste.de(
                (feitos.operacoes.get(cfop) or {}).get(nivel))
            linhas.append({
                "cfop": cfop,
                "parceiro": parceiro,
                "categoria": categoria,
                "nivel": conhecido._nivel_do_cfop(nivel),
                "operacao_proposta": _proposto(bruto),
                "operacao_evidencia": texto_da_evidencia(_evidencia(bruto)),
                "operacao": ajuste.valor or _proposto(bruto),
                "trilha": _trilha(ajuste),
            })
    return linhas


def _ordem_do_codigo(codigo: str) -> tuple[int, Any]:
    """Código numérico em ordem de número; o resto, em ordem de texto."""
    return (0, int(codigo)) if codigo.isdigit() else (1, codigo)


# -- gravar ------------------------------------------------------------------

#: Gravidades que a Central entende. `erro` não grava; `aviso` grava e conta.
ERRO = "erro"
AVISO = "aviso"


def _problema(gravidade: str, onde: str, mensagem: str) -> dict[str, str]:
    return {"gravidade": gravidade, "onde": onde, "mensagem": mensagem}


def gravar(dados: dict[str, Any], responsavel: str = "",
           dominio: str = "mercadorias", raiz: Path | None = None
           ) -> tuple[bool, list[dict[str, str]]]:
    """Guarda só o que difere da fotografia. Devolve `(gravou, problemas)`.

    A fotografia não é tocada — o que se grava é `<domínio>-ajustes.json`. Com
    erro não grava nada: uma correção pela metade classificaria a semana com um
    valor que ninguém escolheu.
    """
    foto = conhecido.carregar(dominio, raiz, com_ajustes=False)
    anteriores = camada.carregar(dominio, raiz)
    novos = camada.Ajustes(dominio=dominio)
    problemas: list[dict[str, str]] = []
    carimbo = camada.agora()
    quem = (responsavel or "").strip() or "?"

    _gravar_parceiros(dados.get(PARCEIROS) or [], foto, anteriores, novos,
                      problemas, quem, carimbo)
    _gravar_gestores(dados.get(GESTORES) or [], foto, anteriores, novos,
                     problemas, quem, carimbo)
    _gravar_operacoes(dados.get(OPERACOES) or [], foto, anteriores, novos,
                      problemas, quem, carimbo)

    if any(p["gravidade"] == ERRO for p in problemas):
        return False, problemas

    antes, depois = anteriores.quantos, novos.quantos
    camada.gravar(novos, raiz)
    problemas.append(_problema(
        AVISO, "Base de conhecimento",
        f"{depois} correção(ões) gravada(s), contra {antes} de antes. Elas "
        f"sobrevivem à próxima importação e vencem o que ela propuser."))
    return True, problemas


def _mesmo(a: str, b: str) -> bool:
    """Igual ao proposto é ausência de ajuste, não ajuste com o mesmo valor."""
    return chave_de_texto(a) == chave_de_texto(b)


def _herdar(anterior: camada.Ajuste, valor: str, quem: str,
            carimbo: str) -> camada.Ajuste:
    """Mantém a trilha de quem corrigiu antes, se o valor não mudou."""
    if anterior and _mesmo(anterior.valor, valor):
        return anterior
    return camada.Ajuste(valor=valor, por=quem, em=carimbo)


def _gravar_parceiros(linhas, foto, anteriores, novos, problemas, quem,
                      carimbo) -> None:
    vistas: set[tuple[str, str]] = set()
    for i, linha in enumerate(linhas, start=1):
        onde = f"Parceiros, linha {i}"
        codigo = aparar(linha.get("codigo"))
        if not codigo:
            if any(aparar(linha.get(c)) for c in ("nome", "guardiao",
                                                  "categoria")):
                problemas.append(_problema(
                    ERRO, onde, "linha sem código de parceiro"))
            continue
        rotulo = aparar(linha.get("unidade"))
        identidade = (codigo, chave_de_texto(rotulo))
        if identidade in vistas:
            problemas.append(_problema(
                ERRO, onde,
                f"o parceiro {codigo} aparece duas vezes"
                + (f" na unidade {rotulo}" if rotulo else " na regra geral")))
            continue
        vistas.add(identidade)

        origem = _origem_do_parceiro(foto, codigo, rotulo)
        for campo, chave in (("guardiao", "guardiao"),
                             ("categoria", "categoria")):
            valor = aparar(linha.get(chave))
            proposto = _proposto(origem.get(campo))
            if not valor or _mesmo(valor, proposto):
                continue
            novos.ajustar_parceiro(
                codigo, campo,
                _herdar(anteriores.do_parceiro(codigo, campo, rotulo), valor,
                        quem, carimbo),
                nome=aparar(linha.get("nome")), fantasia=rotulo)
            if not origem:
                problemas.append(_problema(
                    AVISO, onde,
                    f"o parceiro {codigo}"
                    + (f" na unidade {rotulo}" if rotulo else "")
                    + " não está na base importada — a correção passa a ser a "
                      "única regra dele"))


def _origem_do_parceiro(foto: Conhecimento, codigo: str,
                        rotulo: str) -> dict[str, Any]:
    """A regra da fotografia que aquela linha da tela representa.

    A unidade é procurada pela chave normalizada e, se não achar, pelo rótulo
    guardado ao lado. A segunda busca não é preciosismo: sem ela, uma base cuja
    chave e cujo rótulo tivessem divergido faria **toda** gravação inventar um
    ajuste com o valor que a própria fotografia propôs — em silêncio, e em
    todas as unidades de uma vez.
    """
    parceiro = foto.parceiros.get(codigo) or {}
    if not rotulo:
        return parceiro
    unidades = parceiro.get("unidades") or {}
    achada = unidades.get(chave_de_texto(rotulo))
    if achada is not None:
        return achada
    procurado = chave_de_texto(rotulo)
    for chave, unidade in unidades.items():
        if procurado in (chave_de_texto(chave),
                         chave_de_texto(unidade.get("rotulo"))):
            return unidade
    return {}


def _gravar_gestores(linhas, foto, anteriores, novos, problemas, quem,
                     carimbo) -> None:
    vistos: set[str] = set()
    for i, linha in enumerate(linhas, start=1):
        onde = f"Gestores, linha {i}"
        guardiao = aparar(linha.get("guardiao"))
        if not guardiao:
            if aparar(linha.get("gestor")):
                problemas.append(_problema(
                    ERRO, onde, "linha com gestor e sem guardião"))
            continue
        chave = chave_de_texto(guardiao)
        if chave in vistos:
            problemas.append(_problema(
                ERRO, onde, f"o guardião {guardiao} aparece duas vezes"))
            continue
        vistos.add(chave)
        valor = aparar(linha.get("gestor"))
        proposto = _proposto(foto.gestor_do_guardiao.get(chave))
        if not valor or _mesmo(valor, proposto):
            continue
        novos.ajustar_gestor(
            guardiao,
            _herdar(camada.Ajuste.de(anteriores.gestores.get(chave)), valor,
                    quem, carimbo))


def _gravar_operacoes(linhas, foto, anteriores, novos, problemas, quem,
                      carimbo) -> None:
    vistas: set[tuple[str, str]] = set()
    for i, linha in enumerate(linhas, start=1):
        onde = f"Operações, linha {i}"
        cfop = aparar(linha.get("cfop"))
        if not cfop:
            if aparar(linha.get("operacao")):
                problemas.append(_problema(
                    ERRO, onde, "linha com operação e sem CFOP"))
            continue
        nivel = f"{aparar(linha.get('parceiro'))}|{chave_de_texto(linha.get('categoria'))}"
        if (cfop, nivel) in vistas:
            problemas.append(_problema(
                ERRO, onde, f"a regra {cfop} / {nivel} aparece duas vezes"))
            continue
        vistas.add((cfop, nivel))
        valor = aparar(linha.get("operacao"))
        proposto = _proposto((foto.operacoes.get(cfop) or {}).get(nivel))
        if not valor or _mesmo(valor, proposto):
            continue
        novos.ajustar_operacao(
            cfop, nivel,
            _herdar(camada.Ajuste.de(
                (anteriores.operacoes.get(cfop) or {}).get(nivel)),
                valor, quem, carimbo))


def resumo(dominio: str = "mercadorias", raiz: Path | None = None) -> str:
    """A frase que a Central mostra no cabeçalho da tela."""
    foto = conhecido.carregar(dominio, raiz, com_ajustes=False)
    feitos = camada.carregar(dominio, raiz)
    if foto.vazia and feitos.vazia:
        return ("Base vazia: importe os dois arquivos de classificação na "
                "ferramenta Base de conhecimento.")
    unidades = sum(len(p.get("unidades") or {})
                   for p in foto.parceiros.values())
    regras = sum(len(n) for n in foto.operacoes.values())
    return (f"{len(foto.parceiros)} parceiro(s) — {unidades} com regra por "
            f"unidade —, {regras} regra(s) de operação em "
            f"{len(foto.operacoes)} CFOP e {len(foto.gestor_do_guardiao)} "
            f"gestor(es). Aprendeu até a semana "
            f"{foto.ultimo_relatorio_classificado or '—'}. "
            f"{feitos.quantos} correção(ões) feitas à mão.")
