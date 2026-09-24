"""A base na tela: consultar, corrigir, e a correção sobreviver à importação.

O que se prova aqui é o desenho de duas camadas — fotografia importada e
correção humana ao lado — e as três consequências de comparar em vez de marcar:
digitar o valor original desfaz o ajuste, reimportar não o apaga, e o arquivo
guarda só o que difere.
"""
from __future__ import annotations

from pendentes.conhecimento import ajustes as camada
from pendentes.conhecimento import base as conhecido
from pendentes.conhecimento import configuracao as tela
from pendentes.conhecimento.base import (AJUSTADO, FIRME, SUGESTAO,
                                         Conhecimento)


def _base_de_exemplo() -> Conhecimento:
    """Dois parceiros, um gestor e uma operação — anonimizados."""
    return Conhecimento(
        dominio="mercadorias",
        ultimo_relatorio_classificado=37,
        parceiros={
            "7001": {
                "nome": "BETA CONNECT LTDA",
                "guardiao": {
                    "proposto": "Almoxarifado Registro",
                    "evidencia": {"valor": "Joana M.", "notas": 65,
                                  "apoio": 23, "semanas": 21,
                                  "alternativas": {"Joana M.": 23,
                                                   "Balança": 11,
                                                   "Facilities": 6}},
                },
                "categoria": {
                    "proposto": "Indiretos",
                    "evidencia": {"valor": "Indiretos", "notas": 66,
                                  "apoio": 66, "semanas": 20,
                                  "alternativas": {"Indiretos": 66}},
                },
                "unidades": {
                    "HINOVE (REGISTRO)": {
                        "rotulo": "HINOVE (REGISTRO)",
                        "categoria": {
                            "proposto": "Diretos",
                            "evidencia": {"valor": "Diretos", "notas": 9,
                                          "apoio": 9, "semanas": 4,
                                          "alternativas": {"Diretos": 9}},
                        },
                    },
                },
            },
            "7002": {"nome": "GAMA INSUMOS SA"},
        },
        gestor_do_guardiao={
            "ALMOXARIFADO REGISTRO": {
                "rotulo": "Almoxarifado Registro",
                "proposto": "Joana M.",
                "evidencia": {"valor": "Joana M.", "notas": 4, "apoio": 4,
                              "semanas": 1, "alternativas": {"Joana M.": 4}},
            },
        },
        operacoes={
            "5102": {
                "|": {
                    "proposto": "Compra Uso Consumo",
                    "evidencia": {"valor": "Compra Uso Consumo", "notas": 30,
                                  "apoio": 30, "semanas": 8,
                                  "alternativas": {"Compra Uso Consumo": 30}},
                },
            },
        },
    )


def _montar(tmp_path):
    conhecido.gravar(_base_de_exemplo(), raiz=tmp_path)
    return tmp_path


# -- consultar --------------------------------------------------------------

def test_a_tela_mostra_uma_linha_por_regra_e_a_unidade_separada(tmp_path):
    raiz = _montar(tmp_path)
    linhas = tela.ler(raiz=raiz)[tela.PARCEIROS]

    assert [(l["codigo"], l["unidade"]) for l in linhas] == [
        ("7001", ""), ("7001", "HINOVE (REGISTRO)"), ("7002", "")]


def test_a_evidencia_vira_frase_com_as_alternativas(tmp_path):
    raiz = _montar(tmp_path)
    linha = tela.ler(raiz=raiz)[tela.PARCEIROS][0]

    assert linha["guardiao_evidencia"] == (
        "Joana M.: 23 de 65 notas, 21 semana(s) · também: Balança 11, "
        "Facilities 6")
    assert linha["categoria_evidencia"] == (
        "Indiretos: 66 de 66 notas, 20 semana(s)")


def test_sem_histórico_a_evidencia_diz_isso(tmp_path):
    raiz = _montar(tmp_path)
    linha = next(l for l in tela.ler(raiz=raiz)[tela.PARCEIROS]
                 if l["codigo"] == "7002")

    assert linha["guardiao_evidencia"] == "sem lastro no histórico"
    assert linha["guardiao"] == ""


def test_a_coluna_que_vale_comeca_igual_ao_proposto(tmp_path):
    raiz = _montar(tmp_path)
    linha = tela.ler(raiz=raiz)[tela.PARCEIROS][0]

    assert linha["guardiao_proposto"] == "Almoxarifado Registro"
    assert linha["guardiao"] == "Almoxarifado Registro"
    assert linha["trilha"] == ""


def test_o_nivel_do_cfop_aparece_por_extenso(tmp_path):
    raiz = _montar(tmp_path)
    linha = tela.ler(raiz=raiz)[tela.OPERACOES][0]

    assert linha["cfop"] == "5102"
    assert linha["nivel"] == "CFOP"
    assert linha["operacao"] == "Compra Uso Consumo"


# -- corrigir ---------------------------------------------------------------

def _gravar(raiz, secao, indice, campo, valor, por="Joana M."):
    """Lê a tela, muda uma célula e grava — como a pessoa faria."""
    dados = tela.ler(raiz=raiz)
    dados[secao][indice][campo] = valor
    return tela.gravar(dados, por, raiz=raiz)


def test_corrigir_o_guardiao_grava_so_o_que_difere(tmp_path):
    raiz = _montar(tmp_path)
    gravou, problemas = _gravar(raiz, tela.PARCEIROS, 0, "guardiao", "Manutenção Registro")

    assert gravou
    feitos = camada.carregar(raiz=raiz)
    assert feitos.quantos == 1
    assert feitos.do_parceiro("7001", "guardiao").valor == "Manutenção Registro"
    # a categoria, que não mudou, não virou ajuste
    assert not feitos.do_parceiro("7001", "categoria")
    assert any("1 correção" in p["mensagem"] for p in problemas)


def test_a_fotografia_nao_e_tocada(tmp_path):
    raiz = _montar(tmp_path)
    antes = conhecido.caminho_da_base(raiz=raiz).read_text(encoding="utf-8")

    _gravar(raiz, tela.PARCEIROS, 0, "guardiao", "Manutenção Registro")

    assert conhecido.caminho_da_base(raiz=raiz).read_text(
        encoding="utf-8") == antes


def test_a_correcao_vence_o_historico_na_consulta(tmp_path):
    raiz = _montar(tmp_path)
    _gravar(raiz, tela.PARCEIROS, 0, "guardiao", "Manutenção Registro")

    proposta = conhecido.carregar(raiz=raiz).propor("7001", "guardiao")

    assert proposta.valor == "Manutenção Registro"
    assert proposta.confianca == AJUSTADO
    assert proposta.ajustada
    assert proposta.pode_preencher
    # a evidência da fotografia continua ali, para quem quiser conferir
    assert proposta.evidencia.notas == 65


def test_a_correcao_preenche_onde_so_sugestao_preencheria(tmp_path):
    """`sugestao` aceita `ajustado` — é o grau mais forte, não um intermediário."""
    from pendentes.mercadorias.precategorizacao import GRAUS

    assert AJUSTADO in GRAUS[FIRME]
    assert AJUSTADO in GRAUS[SUGESTAO]


def test_digitar_de_volta_o_proposto_desfaz_o_ajuste(tmp_path):
    raiz = _montar(tmp_path)
    _gravar(raiz, tela.PARCEIROS, 0, "guardiao", "Manutenção Registro")
    assert camada.carregar(raiz=raiz).quantos == 1

    _gravar(raiz, tela.PARCEIROS, 0, "guardiao", "Almoxarifado Registro")

    feitos = camada.carregar(raiz=raiz)
    assert feitos.quantos == 0
    assert feitos.vazia
    assert conhecido.carregar(raiz=raiz).propor(
        "7001", "guardiao").confianca == SUGESTAO


def test_apagar_a_celula_devolve_a_regra_a_importacao(tmp_path):
    raiz = _montar(tmp_path)
    _gravar(raiz, tela.PARCEIROS, 0, "guardiao", "Manutenção Registro")

    _gravar(raiz, tela.PARCEIROS, 0, "guardiao", "")

    assert camada.carregar(raiz=raiz).vazia
    assert conhecido.carregar(raiz=raiz).propor(
        "7001", "guardiao").valor == "Almoxarifado Registro"


def test_a_trilha_diz_quem_corrigiu_e_quando(tmp_path):
    raiz = _montar(tmp_path)
    _gravar(raiz, tela.PARCEIROS, 0, "guardiao", "Manutenção Registro")

    linha = tela.ler(raiz=raiz)[tela.PARCEIROS][0]

    assert linha["trilha"].startswith("Joana M. em 20")


def test_a_trilha_do_primeiro_autor_sobrevive_a_uma_gravacao_que_nao_mudou(tmp_path):
    """Salvar a tela de novo não reescreve o carimbo de quem decidiu."""
    raiz = _montar(tmp_path)
    _gravar(raiz, tela.PARCEIROS, 0, "guardiao", "Manutenção Registro")
    trilha = camada.carregar(raiz=raiz).do_parceiro("7001", "guardiao")

    tela.gravar(tela.ler(raiz=raiz), "Outra Pessoa", raiz=raiz)

    depois = camada.carregar(raiz=raiz).do_parceiro("7001", "guardiao")
    assert depois.por == trilha.por == "Joana M."
    assert depois.em == trilha.em


# -- a unidade, e o parceiro que não existe na fotografia -------------------

def test_a_correcao_por_unidade_vence_a_geral_do_mesmo_parceiro(tmp_path):
    raiz = _montar(tmp_path)
    _gravar(raiz, tela.PARCEIROS, 1, "categoria", "Indiretos")

    conhecimento = conhecido.carregar(raiz=raiz)
    na_unidade = conhecimento.propor("7001", "categoria", "HINOVE (REGISTRO)")
    geral = conhecimento.propor("7001", "categoria", "OUTRA UNIDADE")

    assert (na_unidade.valor, na_unidade.confianca) == ("Indiretos", AJUSTADO)
    assert (geral.valor, geral.confianca) == ("Indiretos", FIRME)


def test_corrigir_parceiro_que_a_importacao_nao_trouxe_avisa_e_grava(tmp_path):
    raiz = _montar(tmp_path)
    dados = tela.ler(raiz=raiz)
    dados[tela.PARCEIROS].append({
        "codigo": "7003", "nome": "DELTA PECAS LTDA", "unidade": "",
        "guardiao": "Manutenção Guará", "categoria": "Indiretos"})

    gravou, problemas = tela.gravar(dados, "Joana M.", raiz=raiz)

    assert gravou
    assert any("7003" in p["mensagem"] and p["gravidade"] == tela.AVISO
               for p in problemas)
    assert conhecido.carregar(raiz=raiz).propor(
        "7003", "guardiao").valor == "Manutenção Guará"


def test_o_gestor_corrigido_na_tela_e_o_que_vale(tmp_path):
    raiz = _montar(tmp_path)
    _gravar(raiz, tela.GESTORES, 0, "gestor", "Carlos R.")

    proposta = conhecido.carregar(raiz=raiz).gestor_de("Almoxarifado Registro")

    assert (proposta.valor, proposta.confianca) == ("Carlos R.", AJUSTADO)


def test_a_operacao_corrigida_na_tela_e_a_que_vale(tmp_path):
    raiz = _montar(tmp_path)
    _gravar(raiz, tela.OPERACOES, 0, "operacao", "Compra Uso e Consumo")

    proposta = conhecido.carregar(raiz=raiz).propor_operacao("5102")

    assert (proposta.valor, proposta.confianca) == ("Compra Uso e Consumo",
                                                    AJUSTADO)


# -- o que a tela recusa ----------------------------------------------------

def test_linha_sem_codigo_de_parceiro_e_erro_e_nada_grava(tmp_path):
    raiz = _montar(tmp_path)
    dados = tela.ler(raiz=raiz)
    dados[tela.PARCEIROS][0]["guardiao"] = "Manutenção Registro"
    dados[tela.PARCEIROS].append({"codigo": "", "nome": "SEM CODIGO",
                                  "guardiao": "Facilities"})

    gravou, problemas = tela.gravar(dados, "Joana M.", raiz=raiz)

    assert not gravou
    assert any(p["gravidade"] == tela.ERRO for p in problemas)
    assert camada.carregar(raiz=raiz).vazia


def test_parceiro_repetido_na_mesma_unidade_e_erro(tmp_path):
    raiz = _montar(tmp_path)
    dados = tela.ler(raiz=raiz)
    dados[tela.PARCEIROS].append({"codigo": "7001", "nome": "BETA CONNECT LTDA",
                                  "unidade": "", "guardiao": "Facilities"})

    gravou, problemas = tela.gravar(dados, "Joana M.", raiz=raiz)

    assert not gravou
    assert any("duas vezes" in p["mensagem"] for p in problemas)


def test_guardiao_em_branco_com_gestor_escrito_e_erro(tmp_path):
    raiz = _montar(tmp_path)
    dados = tela.ler(raiz=raiz)
    dados[tela.GESTORES].append({"guardiao": "", "gestor": "Alguém"})

    gravou, _ = tela.gravar(dados, "Joana M.", raiz=raiz)

    assert not gravou


# -- a reimportação ---------------------------------------------------------

def test_reimportar_troca_a_fotografia_e_mantem_a_correcao(tmp_path):
    """O ponto do desenho todo."""
    raiz = _montar(tmp_path)
    _gravar(raiz, tela.PARCEIROS, 0, "guardiao", "Manutenção Registro")

    # uma fotografia nova, que propõe outra coisa para o mesmo parceiro
    nova = _base_de_exemplo()
    nova.parceiros["7001"]["guardiao"]["proposto"] = "Facilities"
    nova.ultimo_relatorio_classificado = 40
    conhecido.gravar(nova, raiz=raiz)

    conhecimento = conhecido.carregar(raiz=raiz)

    assert conhecimento.ultimo_relatorio_classificado == 40
    proposta = conhecimento.propor("7001", "guardiao")
    assert proposta.valor == "Manutenção Registro"
    assert proposta.confianca == AJUSTADO
    # e a tela continua mostrando o que a importação nova propôs
    linha = tela.ler(raiz=raiz)[tela.PARCEIROS][0]
    assert linha["guardiao_proposto"] == "Facilities"
    assert linha["guardiao"] == "Manutenção Registro"


def test_a_base_crua_nao_leva_ajuste_dentro(tmp_path):
    raiz = _montar(tmp_path)
    _gravar(raiz, tela.PARCEIROS, 0, "guardiao", "Manutenção Registro")

    crua = conhecido.carregar(raiz=raiz, com_ajustes=False)

    assert crua.propor("7001", "guardiao").valor == "Almoxarifado Registro"
    assert camada.CHAVE not in crua.parceiros["7001"]["guardiao"]


def test_sem_base_nem_ajuste_a_tela_abre_vazia_e_diz_o_que_fazer(tmp_path):
    dados = tela.ler(raiz=tmp_path)

    assert dados == {tela.PARCEIROS: [], tela.GESTORES: [],
                     tela.OPERACOES: []}
    assert "importe" in tela.resumo(raiz=tmp_path).casefold()


def test_unidade_com_rotulo_que_nao_casa_com_a_chave_nao_inventa_ajuste(tmp_path):
    """Sem a segunda busca, gravar a tela sem mexer em nada criaria um ajuste
    com o valor que a própria fotografia propôs — em silêncio."""
    base = _base_de_exemplo()
    unidades = base.parceiros["7001"]["unidades"]
    unidades["CHAVE ANTIGA"] = unidades.pop("HINOVE (REGISTRO)")
    conhecido.gravar(base, raiz=tmp_path)

    gravou, _ = tela.gravar(tela.ler(raiz=tmp_path), "Joana M.", raiz=tmp_path)

    assert gravou
    assert camada.carregar(raiz=tmp_path).vazia
