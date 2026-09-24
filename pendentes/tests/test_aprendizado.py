"""A base aprende das semanas que voltaram classificadas.

O que se prova aqui é, antes de tudo, que **a mesma decisão não conta duas
vezes** — por mais vezes que o aprendizado rode, e por mais semanas que uma
nota pendente atravesse. Isso vem do desenho: aprende-se do livro, que tem uma
linha por nota, e só das semanas acima do corte da fotografia.
"""
from __future__ import annotations

from pendentes.conhecimento import aprendizado
from pendentes.conhecimento import base as conhecido
from pendentes.conhecimento.base import (AJUSTADO, FIRME, SUGESTAO,
                                         Conhecimento, Evidencia)
from pendentes.estado import Classificacao, Livro


def _livro(*registros: Classificacao) -> Livro:
    livro = Livro("mercadorias")
    for registro in registros:
        livro.registros[registro.chave] = registro
    return livro


def _nota(chave, semana, *, parceiro="7001", guardiao="", categoria="",
          operacao="", gestor="", cfop="5102", fantasia="") -> Classificacao:
    return Classificacao(
        chave=chave, semana=semana, codigo_do_parceiro=parceiro,
        cfop=cfop, fantasia=fantasia, guardiao=guardiao, categoria=categoria,
        tipo_de_operacao=operacao, gestor_de_apoio=gestor)


def _foto(**campos) -> Conhecimento:
    return Conhecimento(dominio="mercadorias",
                        ultimo_relatorio_classificado=37, **campos)


# -- o corte da semana ------------------------------------------------------

def test_so_aprende_das_semanas_depois_da_fotografia():
    livro = _livro(_nota("A", 36, guardiao="Facilities"),
                   _nota("B", 37, guardiao="Facilities"),
                   _nota("C", 38, guardiao="Facilities"),
                   _nota("D", 39, guardiao="Facilities"))

    relato = aprendizado.aprender(livro, desde_semana=37)

    assert relato.notas == 2
    assert relato.ate_semana == 39
    assert relato.parceiros["7001"]["guardiao"].notas == 2


def test_nota_sem_semana_nao_entra():
    """Livro antigo, gravado antes de o contexto existir: não se inventa semana."""
    livro = _livro(_nota("A", 0, guardiao="Facilities"))

    assert aprendizado.aprender(livro, desde_semana=0).vazio


def test_nota_sem_classificacao_nenhuma_nao_entra():
    livro = _livro(_nota("A", 38), _nota("B", 38, guardiao="Facilities"))

    assert aprendizado.aprender(livro, desde_semana=37).notas == 1


# -- a idempotência, que é o ponto ------------------------------------------

def test_aprender_duas_vezes_da_o_mesmo_numero():
    livro = _livro(*[_nota(str(i), 38 + i % 2, guardiao="Facilities")
                     for i in range(5)])

    primeira = aprendizado.aprender(livro, 37).parceiros["7001"]["guardiao"]
    segunda = aprendizado.aprender(livro, 37).parceiros["7001"]["guardiao"]

    assert primeira.como_evidencia() == segunda.como_evidencia()
    assert primeira.notas == 5


def test_a_nota_que_atravessa_semanas_conta_uma_vez():
    """É o defeito que o desenho evita: uma nota pendente aparece na planilha
    de várias semanas, e é **uma** linha no livro."""
    livro = _livro(_nota("A", 38, guardiao="Facilities"))
    # a semana 39 devolve a mesma nota, ainda pendente: a ingestão atualiza a
    # linha que já existe, e a semana passa a ser a mais recente
    livro.registros["A"].semana = 39

    relato = aprendizado.aprender(livro, 37)

    assert relato.notas == 1
    assert relato.parceiros["7001"]["guardiao"].notas == 1


def test_carregar_duas_vezes_da_a_mesma_evidencia(tmp_path):
    from pendentes import estado

    conhecido.gravar(_foto(), raiz=tmp_path)
    estado.gravar(_livro(*[_nota(str(i), 38 + i % 2, guardiao="Facilities")
                           for i in range(4)]), raiz=tmp_path)

    uma = conhecido.carregar(raiz=tmp_path).propor("7001", "guardiao")
    outra = conhecido.carregar(raiz=tmp_path).propor("7001", "guardiao")

    assert uma == outra
    assert uma.evidencia.notas == 4
    assert uma.confianca == FIRME


# -- somar sem sobrepor -----------------------------------------------------

def test_a_evidencia_da_foto_e_a_aprendida_se_somam():
    foto = _foto(parceiros={"7001": {
        "nome": "BETA CONNECT LTDA",
        "guardiao": {"proposto": "Facilities",
                     "evidencia": {"valor": "Facilities", "notas": 20,
                                   "apoio": 20, "semanas": 10,
                                   "alternativas": {"Facilities": 20}}}}})
    livro = _livro(_nota("A", 38, guardiao="Facilities"),
                   _nota("B", 39, guardiao="Facilities"))

    aprendizado.aplicar(foto, aprendizado.aprender(livro, 37))
    proposta = foto.propor("7001", "guardiao")

    assert proposta.evidencia.notas == 22
    assert proposta.evidencia.semanas == 12
    assert proposta.confianca == FIRME


def test_as_semanas_novas_podem_derrubar_a_confianca_para_sugestao():
    """Somar é para isto: quando as semanas novas discordam, aparece."""
    foto = _foto(parceiros={"7001": {
        "guardiao": {"proposto": "Facilities",
                     "evidencia": {"valor": "Facilities", "notas": 5,
                                   "apoio": 5, "semanas": 3,
                                   "alternativas": {"Facilities": 5}}}}})
    livro = _livro(*[_nota(str(i), 38 + i, guardiao="Manutenção Guará")
                     for i in range(4)])

    aprendizado.aplicar(foto, aprendizado.aprender(livro, 37))
    proposta = foto.propor("7001", "guardiao")

    assert proposta.valor == "Facilities"     # a proposta curada não se toca
    assert proposta.confianca == SUGESTAO
    assert proposta.evidencia.alternativas == {"Manutenção Guará": 4,
                                              "Facilities": 5}


def test_somar_recalcula_quem_e_o_majoritario():
    a = Evidencia("Facilities", notas=5, apoio=5, semanas=3,
                  alternativas={"Facilities": 5})
    b = Evidencia("Manutenção", notas=9, apoio=9, semanas=4,
                  alternativas={"Manutenção": 9})

    somada = aprendizado.somar(a, b)

    assert somada.valor == "Manutenção"
    assert (somada.notas, somada.apoio, somada.semanas) == (14, 9, 7)


def test_somar_com_uma_metade_vazia_devolve_a_outra():
    cheia = Evidencia("Facilities", notas=3, apoio=3, semanas=2)

    assert aprendizado.somar(cheia, Evidencia()) == cheia
    assert aprendizado.somar(Evidencia(), cheia) == cheia


# -- criar proposta onde não havia nenhuma ----------------------------------

def test_regra_sem_proposta_ganha_uma_quando_o_livro_repete_sem_divergir():
    """3 notas em 2 semanas, 100% do mesmo valor — o limiar da fotografia."""
    foto = _foto(parceiros={"7002": {"nome": "GAMA INSUMOS SA"}})
    livro = _livro(_nota("A", 38, parceiro="7002", guardiao="Facilities"),
                   _nota("B", 38, parceiro="7002", guardiao="Facilities"),
                   _nota("C", 39, parceiro="7002", guardiao="Facilities"))

    aprendizado.aplicar(foto, aprendizado.aprender(livro, 37))
    proposta = foto.propor("7002", "guardiao")

    assert proposta.valor == "Facilities"
    assert proposta.confianca == FIRME
    assert proposta.pode_preencher


def test_duas_notas_nao_bastam_para_criar_proposta():
    foto = _foto(parceiros={"7002": {}})
    livro = _livro(_nota("A", 38, parceiro="7002", guardiao="Facilities"),
                   _nota("B", 39, parceiro="7002", guardiao="Facilities"))

    aprendizado.aplicar(foto, aprendizado.aprender(livro, 37))

    assert not foto.propor("7002", "guardiao")


def test_tres_notas_na_mesma_semana_nao_bastam():
    foto = _foto(parceiros={"7002": {}})
    livro = _livro(*[_nota(c, 38, parceiro="7002", guardiao="Facilities")
                     for c in "ABC"])

    aprendizado.aplicar(foto, aprendizado.aprender(livro, 37))

    assert not foto.propor("7002", "guardiao")


def test_livro_que_diverge_nao_cria_proposta():
    foto = _foto(parceiros={"7002": {}})
    livro = _livro(_nota("A", 38, parceiro="7002", guardiao="Facilities"),
                   _nota("B", 38, parceiro="7002", guardiao="Facilities"),
                   _nota("C", 39, parceiro="7002", guardiao="Manutenção"),
                   _nota("D", 39, parceiro="7002", guardiao="Facilities"))

    aprendizado.aplicar(foto, aprendizado.aprender(livro, 37))
    proposta = foto.propor("7002", "guardiao")

    assert not proposta
    # mas a evidência fica registrada, para a tela mostrar
    contagem = aprendizado.aprender(livro, 37).parceiros["7002"]["guardiao"]
    assert contagem.como_evidencia().alternativas == {"Facilities": 3,
                                                     "Manutenção": 1}


def test_a_proposta_que_ja_existe_nunca_e_trocada():
    """Trocar proposta sozinha seria decidir classificação (regra nº 4)."""
    foto = _foto(parceiros={"7001": {"guardiao": {"proposto": "Facilities"}}})
    livro = _livro(*[_nota(c, 38 + i, guardiao="Manutenção Guará")
                     for i, c in enumerate("ABCDE")])

    aprendizado.aplicar(foto, aprendizado.aprender(livro, 37))

    assert foto.propor("7001", "guardiao").valor == "Facilities"


# -- os outros três escopos -------------------------------------------------

def test_a_unidade_aprende_separada_do_geral():
    foto = _foto(parceiros={"7001": {}})
    livro = _livro(
        _nota("A", 38, guardiao="Balança Guará", fantasia="HINOVE (GUARA)"),
        _nota("B", 38, guardiao="Balança Guará", fantasia="HINOVE (GUARA)"),
        _nota("C", 39, guardiao="Balança Guará", fantasia="HINOVE (GUARA)"))

    aprendizado.aplicar(foto, aprendizado.aprender(livro, 37))

    na_unidade = foto.propor("7001", "guardiao", "HINOVE (GUARA)")
    assert (na_unidade.valor, na_unidade.nivel) == ("Balança Guará",
                                                    "parceiro + unidade")


def test_a_operacao_aprende_nos_quatro_niveis():
    foto = _foto()
    livro = _livro(*[_nota(c, 38 + i, operacao="Compra MP", categoria="Diretos")
                     for i, c in enumerate("ABC")])

    aprendizado.aplicar(foto, aprendizado.aprender(livro, 37))

    assert foto.propor_operacao("5102").valor == "Compra MP"
    assert foto.propor_operacao("5102", "7001").nivel == "CFOP + parceiro"
    assert foto.propor_operacao("5102", "7001", "Diretos").nivel == (
        "CFOP + parceiro + categoria")


def test_o_gestor_aprende_do_par_guardiao_gestor():
    foto = _foto()
    livro = _livro(_nota("A", 38, guardiao="Facilities", gestor="Joana M."),
                   _nota("B", 39, guardiao="Facilities", gestor="Joana M."))

    aprendizado.aplicar(foto, aprendizado.aprender(livro, 37))
    proposta = foto.gestor_de("Facilities")

    assert (proposta.valor, proposta.confianca) == ("Joana M.", FIRME)


def test_guardiao_novo_entra_na_lista_dos_observados():
    foto = _foto(guardioes_observados=["Facilities"])
    livro = _livro(_nota("A", 38, guardiao="PCP Registro"))

    aprendizado.aplicar(foto, aprendizado.aprender(livro, 37))

    assert foto.guardioes_observados == ["Facilities", "PCP Registro"]


# -- a grafia ---------------------------------------------------------------

def test_a_base_guarda_a_grafia_mais_frequente_e_compara_normalizado():
    foto = _foto()
    livro = _livro(
        _nota("A", 38, operacao="Compra Uso e Consumo"),
        _nota("B", 38, operacao="Compra Uso e Consumo"),
        _nota("C", 39, operacao="Compra Uso Consumo"))

    aprendizado.aplicar(foto, aprendizado.aprender(livro, 37))
    proposta = foto.propor_operacao("5102")

    assert proposta.valor == "Compra Uso e Consumo"
    assert proposta.confianca == FIRME        # o conectivo não é divergência


# -- a ordem das três camadas ----------------------------------------------

def test_a_correcao_da_tela_vence_o_que_o_livro_ensinou(tmp_path):
    from pendentes import estado
    from pendentes.conhecimento import configuracao as tela

    conhecido.gravar(_foto(parceiros={"7001": {"nome": "BETA CONNECT LTDA"}}),
                     raiz=tmp_path)
    estado.gravar(_livro(*[_nota(c, 38 + i, guardiao="Facilities")
                           for i, c in enumerate("ABC")]), raiz=tmp_path)
    # o livro já basta para firmar
    assert conhecido.carregar(raiz=tmp_path).propor(
        "7001", "guardiao").confianca == FIRME

    dados = tela.ler(raiz=tmp_path)
    linha = next(l for l in dados[tela.PARCEIROS] if l["codigo"] == "7001")
    linha["guardiao"] = "Manutenção Registro"
    assert tela.gravar(dados, "Joana M.", raiz=tmp_path)[0]

    proposta = conhecido.carregar(raiz=tmp_path).propor("7001", "guardiao")
    assert (proposta.valor, proposta.confianca) == ("Manutenção Registro",
                                                    AJUSTADO)


def test_a_tela_mostra_o_que_o_livro_ensinou(tmp_path):
    """A tela mostra o que a base diz **por si**: fotografia mais aprendizado.

    Se ela mostrasse só a fotografia, o que o livro ensinou seria invisível — e
    a pessoa não teria como saber por que a ferramenta começou a preencher uma
    coluna que antes ficava vazia.
    """
    from pendentes import estado
    from pendentes.conhecimento import configuracao as tela

    conhecido.gravar(_foto(parceiros={"7001": {"nome": "BETA CONNECT LTDA"}}),
                     raiz=tmp_path)
    estado.gravar(_livro(*[_nota(c, 38 + i, guardiao="Facilities")
                           for i, c in enumerate("ABC")]), raiz=tmp_path)

    linha = next(l for l in tela.ler(raiz=tmp_path)[tela.PARCEIROS]
                 if l["codigo"] == "7001")

    assert linha["guardiao_proposto"] == "Facilities"
    assert linha["guardiao_evidencia"] == (
        "Facilities: 3 de 3 notas, 3 semana(s)")
    assert linha["trilha"] == ""


def test_gravar_a_tela_sem_mexer_nao_transforma_aprendizado_em_ajuste(tmp_path):
    """A tela compara contra o que mostrou — e o que ela mostra já inclui o
    aprendizado. Se comparasse contra a fotografia crua, toda gravação viraria
    o aprendizado inteiro em correção humana, em silêncio."""
    from pendentes import estado
    from pendentes.conhecimento import ajustes as camada
    from pendentes.conhecimento import configuracao as tela

    conhecido.gravar(_foto(parceiros={"7001": {"nome": "BETA CONNECT LTDA"}}),
                     raiz=tmp_path)
    estado.gravar(_livro(*[_nota(c, 38 + i, guardiao="Facilities")
                           for i, c in enumerate("ABC")]), raiz=tmp_path)

    gravou, _ = tela.gravar(tela.ler(raiz=tmp_path), "Joana M.", raiz=tmp_path)

    assert gravou
    assert camada.carregar(raiz=tmp_path).vazia


def test_so_a_fotografia_se_pede_sem_o_aprendizado(tmp_path):
    from pendentes import estado

    conhecido.gravar(_foto(parceiros={"7001": {}}), raiz=tmp_path)
    estado.gravar(_livro(*[_nota(c, 38 + i, guardiao="Facilities")
                           for i, c in enumerate("ABC")]), raiz=tmp_path)

    crua = conhecido.carregar(raiz=tmp_path, com_aprendizado=False)

    assert not crua.propor("7001", "guardiao")
    assert conhecido.carregar(raiz=tmp_path).propor(
        "7001", "guardiao").valor == "Facilities"


def test_sem_livro_a_base_continua_valendo_pela_fotografia(tmp_path):
    conhecido.gravar(_foto(parceiros={"7001": {
        "guardiao": {"proposto": "Facilities"}}}), raiz=tmp_path)

    assert conhecido.carregar(raiz=tmp_path).propor(
        "7001", "guardiao").valor == "Facilities"


def test_o_relato_diz_o_que_aprendeu():
    livro = _livro(_nota("A", 38, guardiao="Facilities"),
                   _nota("B", 40, guardiao="Facilities"))

    texto = aprendizado.aprender(livro, 37).resumo()

    assert "2 nota(s)" in texto and "semanas 38 e 40" in texto


def test_o_relato_de_nada_novo_diz_isso():
    texto = aprendizado.aprender(_livro(), 37).resumo()

    assert "Nada novo" in texto and "semana 37" in texto


def test_a_tela_diz_quanto_veio_de_cada_camada(tmp_path):
    from pendentes import estado
    from pendentes.conhecimento import configuracao as tela

    conhecido.gravar(_foto(parceiros={"7001": {}}), raiz=tmp_path)
    estado.gravar(_livro(*[_nota(c, 38 + i, guardiao="Facilities")
                           for i, c in enumerate("ABC")]), raiz=tmp_path)

    texto = tela.resumo(raiz=tmp_path)

    assert "importação trouxe até a semana 37" in texto
    assert "3 nota(s) classificada(s) até a semana 40" in texto
    assert "0 correção(ões)" in texto


def test_a_tela_nao_fala_de_aprendizado_quando_nao_houve(tmp_path):
    conhecido.gravar(_foto(parceiros={"7001": {}}), raiz=tmp_path)

    assert "aprendeu sozinha" not in tela_resumo(tmp_path)


def tela_resumo(raiz):
    from pendentes.conhecimento import configuracao as tela

    return tela.resumo(raiz=raiz)
