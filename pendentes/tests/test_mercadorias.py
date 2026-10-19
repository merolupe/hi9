"""O motor de mercadorias: limpeza, roteamento, conferência, herança e split.

Todo teste aqui exercita **comportamento**: o que entra em cada aba, o que a
regra escreve na célula, o que a tela passa a contar. Nenhum deles depende de
arquivo real — os documentos são montados em memória, a partir das mesmas
linhas sintéticas que o teste de ponta a ponta usa.

Os testes que dão nome ao arquivo são três, e são as três ordens que o VBA
documenta e que uma reimplementação ingênua inverteria:

* `test_a_limpeza_roda_antes_do_roteamento…` — um XML de terceiro com
  `Entrada` sobreviveria em `Entradas 3os` se a ordem fosse a outra;
* `test_o_roteamento_para_na_primeira_condicao_verdadeira` — a linha que
  satisfaz duas condições vai para a primeira, e só para ela;
* `test_b1_sobrescreve_a_classificacao_herdada` — é a única regra do módulo
  que sobrescreve, e ela só pode rodar depois da herança e antes do split.
"""
from __future__ import annotations

import pytest

from pendentes.cabecalho import Exigencia, mapear
from pendentes.estado import Classificacao, Livro
from pendentes.mercadorias import (
    classificacao, conferencia, limpeza, roteamento, vocabulario,
)
from pendentes.mercadorias import colunas as col
from pendentes.mercadorias import fontes
from pendentes.parametros import carregar_fabrica, mercadorias, roteamento as \
    roteamento_de
from conftest import (
    COLUNAS_CE, COLUNAS_XML, FAROL_VERDE, FAROL_VERMELHO, chave_de, linha_ce,
    linha_xml,
)

FABRICA = carregar_fabrica()
LITERAIS = mercadorias(FABRICA)
CONDICOES = roteamento.condicoes_de(roteamento_de(FABRICA))


# -- montagem em memória, sem passar por planilha ---------------------------

def _mapa(colunas):
    return mapear(colunas, [Exigencia(nome) for nome in colunas], "teste")


def documentos(*linhas):
    return fontes.ler_documentos(list(linhas), _mapa(COLUNAS_XML))


def conferir(*linhas):
    registros = fontes.ler_conferencia(list(linhas), _mapa(COLUNAS_CE))
    return conferencia.indexar(registros)


def limpar(*linhas):
    return limpeza.limpar(
        documentos(*linhas),
        tipo_nfe_de_transporte=LITERAIS["tipo_nfe_de_transporte"])


def anotar(docs, indice):
    conferencia.anotar(
        docs, indice,
        ausente_da_conferencia=LITERAIS["ausente_da_conferencia"],
        conferencia_fisica_confirmada=LITERAIS["conferencia_fisica_confirmada"],
        sem_pedido_vinculado=LITERAIS["sem_pedido_vinculado"])
    return docs


# =========================================================================
# A limpeza — A1, A2 e A3
# =========================================================================

def test_a1_descarta_o_xml_de_terceiro_e_diz_o_motivo():
    """`Nome Fantasia` vazia é XML de CNPJ que não é o da Hinove."""
    relato = limpar(
        linha_xml("1", chave_de(1)),
        linha_xml("2", chave_de(2), fantasia="   "),
    )
    assert [d.texto(col.X_NRO_NOTA) for d in relato.mantidos] == ["1"]
    assert relato.por_xml_de_terceiro == 1
    assert relato.descartados[0].motivo_do_descarte == \
        limpeza.MOTIVO_XML_DE_TERCEIRO


def test_a2_grava_sem_cadastro_e_poe_o_cnpj_no_lugar_do_nome():
    relato = limpar(linha_xml("1", chave_de(1), parceiro="",
                              cnpj="98765432000188"))
    documento = relato.mantidos[0]
    assert documento.texto(col.X_NOME_PARCEIRO) == "98765432000188"
    assert documento.texto(col.X_COD_PARCEIRO) == "Sem cadastro"
    assert relato.parceiros_sem_cadastro == 1


def test_a2_nao_mexe_em_quem_tem_cadastro():
    relato = limpar(linha_xml("1", chave_de(1), parceiro="FORNECEDOR X",
                              cod_parceiro="77"))
    assert relato.mantidos[0].texto(col.X_COD_PARCEIRO) == "77"
    assert relato.parceiros_sem_cadastro == 0


@pytest.mark.parametrize("escrito", [
    "NF-e Destinada a Transporte",
    "nf-e destinada a transporte",
    "  NF-e   Destinada a Transporte  ",
    "NF-E DESTINADA A TRANSPORTE",
])
def test_a3_descarta_a_nfe_de_transporte_com_variacao_de_caixa_e_espaco(escrito):
    """`vbTextCompare` sobre `NormalizarTexto`: caixa e espaço não importam."""
    relato = limpar(linha_xml("1", chave_de(1), tipo=escrito))
    assert relato.mantidos == []
    assert relato.por_nfe_de_transporte == 1
    assert relato.descartados[0].motivo_do_descarte == \
        limpeza.MOTIVO_NFE_DE_TRANSPORTE


def test_a3_nao_tolera_variacao_de_acento_porque_o_vba_nao_tolera():
    """O defeito 10 do porte, preservado: uniformizar exige medição antes."""
    relato = limpar(linha_xml("1", chave_de(1),
                              tipo="NF-e Destinada a Transporte "))
    assert relato.mantidos == []
    relato = limpar(linha_xml("1", chave_de(1),
                              tipo="NF-e Destinada a Trànsporte"))
    assert len(relato.mantidos) == 1


def test_a1_e_avaliada_antes_de_a3_e_a_linha_sai_uma_vez_so():
    """Fantasia vazia sai por A1, e `Tipo NF-e` nem chega a ser consultado."""
    relato = limpar(linha_xml("1", chave_de(1), fantasia="",
                              tipo="NF-e Destinada a Transporte"))
    assert relato.por_xml_de_terceiro == 1
    assert relato.por_nfe_de_transporte == 0
    assert len(relato.descartados) == 1


def test_a2_nao_conserta_linha_que_vai_sair():
    """A2 roda no ramo `Else` da exclusão. Consertar o que sai seria ruído."""
    relato = limpar(linha_xml("1", chave_de(1), fantasia="", parceiro=""))
    assert relato.parceiros_sem_cadastro == 0


def test_a_limpeza_roda_antes_do_roteamento_e_o_terceiro_nao_vaza_para_entradas():
    """A armadilha da ordem: XML de terceiro **de entrada**.

    Se a limpeza rodasse depois do roteamento, esta linha já teria ido para
    `Entradas 3os` e sobreviveria lá — exatamente o que o comentário da v8.0
    do VBA diz que não pode acontecer.
    """
    relato = limpar(linha_xml("1", chave_de(1), fantasia="",
                              entrada_saida="Entrada"))
    rotas = roteamento.rotear(relato.mantidos, CONDICOES)
    assert rotas.quantos_em("Entradas 3os") == 0
    assert len(relato.descartados) == 1

    # E o contraste: na ordem invertida, ela sobreviveria.
    sem_limpeza = documentos(linha_xml("1", chave_de(1), fantasia="",
                                       entrada_saida="Entrada"))
    assert roteamento.rotear(sem_limpeza, CONDICOES).quantos_em("Entradas 3os") == 1


# =========================================================================
# O roteamento
# =========================================================================

def test_as_quatro_condicoes_mandam_cada_uma_para_a_sua_aba():
    rotas = roteamento.rotear(documentos(
        linha_xml("1", chave_de(1), tomador="TRANSPORTADORA XPTO"),
        linha_xml("2", chave_de(2), manifestacao="Desconhecida"),
        linha_xml("3", chave_de(3), situacao="NF-e cancelada"),
        linha_xml("4", chave_de(4), entrada_saida="Entrada"),
        linha_xml("5", chave_de(5)),
    ), CONDICOES)
    assert rotas.quantos_em("CTe") == 1
    assert rotas.quantos_em("Manifestados") == 2
    assert rotas.quantos_em("Entradas 3os") == 1
    assert [d.texto(col.X_NRO_NOTA) for d in rotas.pendentes] == ["5"]


def test_o_roteamento_para_na_primeira_condicao_verdadeira():
    """A nota satisfaz a 1 **e** a 2. Vai para `CTe`, e só para `CTe`."""
    rotas = roteamento.rotear(documentos(
        linha_xml("1", chave_de(1), tomador="TRANSPORTADORA XPTO",
                  manifestacao="Desconhecida", situacao="NF-e cancelada",
                  entrada_saida="Entrada"),
    ), CONDICOES)
    assert rotas.quantos_em("CTe") == 1
    assert rotas.quantos_em("Manifestados") == 0
    assert rotas.quantos_em("Entradas 3os") == 0
    assert rotas.por_condicao == {1: 1}


def test_inverter_a_ordem_das_condicoes_muda_o_destino():
    """A ordem é a regra, e o teste prova a armadilha nos dois sentidos."""
    invertidas = roteamento.condicoes_de([
        {"ordem": 1, "coluna": col.X_SITUACAO_DA_MANIFESTACAO,
         "operador": "igual_a_algum", "valor": "desconhecida",
         "destino": "Manifestados"},
        {"ordem": 2, "coluna": col.X_TOMADOR_CTE,
         "operador": "preenchido_e_diferente", "valor": "Não se aplica",
         "destino": "CTe"},
    ])
    linhas = [linha_xml("1", chave_de(1), tomador="TRANSPORTADORA XPTO",
                        manifestacao="Desconhecida")]
    assert roteamento.rotear(documentos(*linhas),
                             invertidas).quantos_em("Manifestados") == 1
    assert roteamento.rotear(documentos(*linhas),
                             CONDICOES).quantos_em("CTe") == 1


def test_a_condicao_2_aceita_a_grafia_sem_acento_porque_o_vba_lista_as_duas():
    rotas = roteamento.rotear(documentos(
        linha_xml("1", chave_de(1), manifestacao="Operação não realizada"),
        linha_xml("2", chave_de(2), manifestacao="OPERACAO NAO REALIZADA"),
    ), CONDICOES)
    assert rotas.quantos_em("Manifestados") == 2


def test_as_condicoes_3_e_4_sao_exatas_e_sensiveis_a_caixa():
    """Preservado com o defeito: `"entrada"` minúsculo **não** roteia."""
    rotas = roteamento.rotear(documentos(
        linha_xml("1", chave_de(1), entrada_saida="entrada"),
        linha_xml("2", chave_de(2), situacao="NF-e Cancelada"),
    ), CONDICOES)
    assert rotas.quantos_em("Entradas 3os") == 0
    assert rotas.quantos_em("Manifestados") == 0
    assert len(rotas.pendentes) == 2


def test_o_tomador_com_espaco_a_esquerda_vai_para_cte():
    """A desigualdade da condição 1 não apara — e o VBA também não."""
    rotas = roteamento.rotear(documentos(
        linha_xml("1", chave_de(1), tomador=" Não se aplica"),
    ), CONDICOES)
    assert rotas.quantos_em("CTe") == 1


def test_roteamento_para_coluna_que_nao_existe_aborta_nomeando():
    with pytest.raises(roteamento.RoteamentoInvalido, match="Coluna Inventada"):
        roteamento.condicoes_de([{"ordem": 1, "coluna": "Coluna Inventada",
                                  "operador": "igual", "valor": "x",
                                  "destino": "CTe"}])


def test_roteamento_com_operador_desconhecido_aborta_nomeando():
    with pytest.raises(roteamento.RoteamentoInvalido, match="parecido_com"):
        roteamento.condicoes_de([{"ordem": 1, "coluna": col.X_TOMADOR_CTE,
                                  "operador": "parecido_com", "valor": "x",
                                  "destino": "CTe"}])


# =========================================================================
# A conferência de entradas
# =========================================================================

def test_o_farol_tem_tres_estados_e_o_vazio_nao_e_nao():
    indice = conferir(
        linha_ce(chave_de(1), farol=FAROL_VERDE),
        linha_ce(chave_de(2), farol=FAROL_VERMELHO),
        linha_ce(chave_de(3), farol="", pedido=""),
    )
    assert indice.de(chave_de(1)).pedido_confirmado == "Sim"
    assert indice.de(chave_de(2)).pedido_confirmado == "Não"
    assert indice.de(chave_de(3)).pedido_confirmado == ""


def test_chave_com_varias_linhas_no_ce_vence_a_primeira_e_conta():
    indice = conferir(
        linha_ce(chave_de(1), pedido="7788"),
        linha_ce(chave_de(1), pedido="7788"),
        linha_ce(chave_de(1), pedido="7788"),
    )
    assert len(indice) == 1
    assert indice.de(chave_de(1)).numero_do_pedido == "7788"
    assert indice.chaves_duplicadas == [chave_de(1)]
    assert indice.chaves_divergentes == []


def test_linhas_duplicadas_que_divergem_no_pedido_ficam_bloqueantes():
    indice = conferir(
        linha_ce(chave_de(1), pedido="7788"),
        linha_ce(chave_de(1), pedido="9999"),
    )
    assert indice.chaves_divergentes == [chave_de(1)]


def test_linhas_duplicadas_que_divergem_no_farol_ficam_bloqueantes():
    indice = conferir(
        linha_ce(chave_de(1), farol=FAROL_VERDE),
        linha_ce(chave_de(1), farol=FAROL_VERMELHO),
    )
    assert indice.chaves_divergentes == [chave_de(1)]


def test_a_nota_fora_do_ce_recebe_o_nao_minusculo_nas_tres_colunas():
    """Preservado nº 19: é este literal que impede B1 de disparar."""
    docs = anotar(documentos(linha_xml("1", chave_de(9))), conferir())
    assert conferencia.valor_da_coluna(docs[0], col.P_CONF_FISICA) == "não"
    assert conferencia.valor_da_coluna(docs[0], col.P_CONF_FISCAL) == "não"
    assert conferencia.valor_da_coluna(docs[0], col.P_INCONGRUENCIA) == "não"
    assert conferencia.valor_da_coluna(docs[0], col.P_NRO_DO_PEDIDO) == ""
    assert conferencia.valor_da_coluna(docs[0], col.P_DATA_CONF_FISICA) == ""
    assert docs[0].no_ce is False


def test_a_data_da_conferencia_vira_data_de_verdade():
    docs = anotar(documentos(linha_xml("1", chave_de(1))),
                  conferir(linha_ce(chave_de(1), data="05/07/2026")))
    valor = conferencia.valor_da_coluna(docs[0], col.P_DATA_CONF_FISICA)
    assert not isinstance(valor, str)
    assert (valor.day, valor.month, valor.year) == (5, 7, 2026)


def test_data_de_conferencia_ilegivel_vira_vazio_como_o_coagirdata():
    docs = anotar(documentos(linha_xml("1", chave_de(1))),
                  conferir(linha_ce(chave_de(1), data="não conferida")))
    assert conferencia.valor_da_coluna(docs[0], col.P_DATA_CONF_FISICA) == ""


def test_lancados_sai_por_igualdade_exata_de_conf_fiscal():
    docs = anotar(documentos(
        linha_xml("1", chave_de(1)),
        linha_xml("2", chave_de(2)),
        linha_xml("3", chave_de(3)),
    ), conferir(
        linha_ce(chave_de(1), fiscal="Sim"),
        linha_ce(chave_de(2), fiscal="SIM"),
        linha_ce(chave_de(3), fiscal="não"),
    ))
    lancados, restantes = roteamento.segregar_lancados(
        docs, LITERAIS["conf_fiscal_lancada"])
    assert [d.texto(col.X_NRO_NOTA) for d in lancados] == ["1"]
    assert [d.texto(col.X_NRO_NOTA) for d in restantes] == ["2", "3"]


# =========================================================================
# A herança, B1 e B2
# =========================================================================

def _livro_com(chave, **campos) -> Livro:
    livro = Livro("mercadorias")
    livro.registros[chave] = Classificacao(chave=chave, **campos)
    return livro


def test_a_heranca_preenche_as_cinco_colunas_a_partir_do_livro():
    livro = _livro_com(chave_de(1), tipo_de_operacao="Compra direta",
                       guardiao="Suprimentos", gestor_de_apoio="Maria",
                       categoria="Diretos",
                       retornos={29: "aguardando fornecedor"})
    docs = documentos(linha_xml("1", chave_de(1)))
    relato = classificacao.herdar(docs, livro)

    assert docs[0].categorizacao == ["Compra direta", "Suprimentos", "Maria",
                                     "Diretos", "aguardando fornecedor"]
    assert (relato.herdadas, relato.sem_classificacao) == (1, 0)


def test_a_nota_sem_registro_no_livro_entra_sem_classificacao():
    docs = documentos(linha_xml("1", chave_de(1)))
    relato = classificacao.herdar(docs, Livro("mercadorias"))
    assert docs[0].categorizacao == ["", "", "", "", ""]
    assert relato.sem_classificacao == 1


def test_o_retorno_que_volta_e_o_da_semana_mais_recente_do_livro():
    livro = _livro_com(chave_de(1), retornos={28: "antigo", 30: "recente"})
    docs = documentos(linha_xml("1", chave_de(1)))
    classificacao.herdar(docs, livro)
    assert docs[0].categorizacao[4] == "recente"


def test_b1_sobrescreve_a_classificacao_herdada():
    """A única regra do módulo que sobrescreve — e por isso roda depois."""
    livro = _livro_com(chave_de(1), guardiao="Suprimentos",
                       gestor_de_apoio="Maria")
    docs = anotar(documentos(linha_xml("1", chave_de(1))),
                  conferir(linha_ce(chave_de(1), fisica="Sim",
                                    incongruencia="")))
    classificacao.herdar(docs, livro)
    assert docs[0].categorizacao[1] == "Suprimentos"

    quantas = classificacao.reclassificar_para_fiscal(
        docs,
        conferencia_fisica_confirmada=LITERAIS["conferencia_fisica_confirmada"],
        guardiao=LITERAIS["guardiao_da_reclassificacao"])

    assert quantas == 1
    assert docs[0].categorizacao[1] == "Fiscal"
    assert docs[0].categorizacao[2] == ""


@pytest.mark.parametrize("incongruencia", ["", "0", "0,00", "000"])
def test_b1_dispara_com_incongruencia_vazia_ou_zerada(incongruencia):
    docs = anotar(documentos(linha_xml("1", chave_de(1))),
                  conferir(linha_ce(chave_de(1), fisica="Sim",
                                    incongruencia=incongruencia)))
    classificacao.herdar(docs, Livro("mercadorias"))
    assert classificacao.reclassificar_para_fiscal(
        docs, conferencia_fisica_confirmada="Sim", guardiao="Fiscal") == 1


def test_b1_nao_dispara_para_nota_que_nem_estava_no_ce():
    """O literal `"não"` impede, e a condição explícita também. Os dois."""
    docs = anotar(documentos(linha_xml("1", chave_de(1))), conferir())
    classificacao.herdar(docs, Livro("mercadorias"))
    assert classificacao.reclassificar_para_fiscal(
        docs, conferencia_fisica_confirmada="Sim", guardiao="Fiscal") == 0
    assert docs[0].categorizacao[1] == ""


def test_b1_nao_dispara_quando_ha_incongruencia_escrita():
    docs = anotar(documentos(linha_xml("1", chave_de(1))),
                  conferir(linha_ce(chave_de(1), fisica="Sim",
                                    incongruencia="divergência de peso")))
    classificacao.herdar(docs, Livro("mercadorias"))
    assert classificacao.reclassificar_para_fiscal(
        docs, conferencia_fisica_confirmada="Sim", guardiao="Fiscal") == 0


def test_b2_move_e_nao_copia():
    docs = documentos(
        linha_xml("1", chave_de(1)),
        linha_xml("2", chave_de(2)),
        linha_xml("3", chave_de(3)),
    )
    for documento, guardiao in zip(docs, ("Fiscal", " faturamento ",
                                          "Suprimentos")):
        documento.categorizacao = ["", guardiao, "", "", ""]

    fis_fat, principal = classificacao.dividir_fis_fat(
        docs, LITERAIS["guardioes_da_fis_fat"])

    assert [d.texto(col.X_NRO_NOTA) for d in fis_fat] == ["1", "2"]
    assert [d.texto(col.X_NRO_NOTA) for d in principal] == ["3"]
    assert len(fis_fat) + len(principal) == len(docs)


def test_a_fis_fat_perde_gestor_e_categoria_e_mantem_o_retorno():
    documento = documentos(linha_xml("1", chave_de(1)))[0]
    documento.categorizacao = ["Compra direta", "Fiscal", "Maria", "Diretos",
                               "aguardando"]
    linha = documento.linha_fis_fat()
    assert linha[:3] == ["Compra direta", "Fiscal", "aguardando"]
    assert len(linha) == 36


# =========================================================================
# O vocabulário — o que a ferramenta não consegue dizer o que é
# =========================================================================

UNIDADES = [
    {"ordem": 1, "trecho": "MATRIZ", "unidade": "Matriz"},
    {"ordem": 2, "trecho": "RIO BRILHANTE", "unidade": "Rio Brilhante"},
    {"ordem": 3, "trecho": "REGISTRO", "unidade": "Registro"},
    {"ordem": 4, "trecho": "CORUMB", "unidade": "Corumbá"},
    {"ordem": 5, "trecho": "GUAR", "unidade": "Guará"},
]


def test_corumba_vem_antes_de_guara_e_e_isso_que_decide():
    """A armadilha da ordem, provada nos dois sentidos."""
    fantasia = "HINOVE CORUMBA GUARDA SUL"
    assert vocabulario.unidade_de(fantasia, UNIDADES).valor == "Corumbá"

    invertidas = [dict(linha, ordem=6 - linha["ordem"]) for linha in UNIDADES]
    assert vocabulario.unidade_de(fantasia, invertidas).valor == "Guará"


def test_a_unidade_que_nao_casa_devolve_o_texto_original_e_nao_e_reconhecida():
    achada = vocabulario.unidade_de("HINOVE (CAMPO GRANDE)", UNIDADES)
    assert achada.valor == "HINOVE (CAMPO GRANDE)"
    assert achada.reconhecido is False


def test_a_fantasia_vazia_e_reconhecida_e_nao_bloqueia():
    achada = vocabulario.unidade_de("", UNIDADES)
    assert (achada.valor, achada.reconhecido) == (vocabulario.SEM_UNIDADE, True)


def test_a_tabela_vazia_desliga_a_validacao_de_unidade():
    """Numa máquina nova a tabela nasce vazia: validar reprovaria todo mundo."""
    assert vocabulario.unidade_de("QUALQUER COISA", []).reconhecido is True


def test_indireto_e_testado_antes_de_direto():
    categorias = [linha for linha in FABRICA["categorias"]]
    assert vocabulario.categoria_de("indiretos", categorias).valor == "Indiretos"
    assert vocabulario.categoria_de("Direto", categorias).valor == "Diretos"


def test_a_categoria_vazia_vira_nao_classificado_e_nao_bloqueia():
    achada = vocabulario.categoria_de("", FABRICA["categorias"])
    assert (achada.valor, achada.reconhecido) == (vocabulario.NAO_CLASSIFICADO,
                                                  True)


def test_a_categoria_fora_da_lista_nao_e_reconhecida_e_e_contada():
    relato = vocabulario.conferir(
        [("HINOVE MATRIZ", "Ativo imobilizado", "Suprimentos")] * 4,
        unidades=UNIDADES, categorias=FABRICA["categorias"], guardioes=[])
    assert relato.categorias == {"Ativo imobilizado": 4}
    assert "4 nota" in relato.bloqueios()[0]


def test_a_categoria_escrita_com_ponto_continua_sendo_reconhecida():
    """`Indireto.` casa por subcadeia, como no VBA — e portanto não bloqueia.

    O teste existe porque o exemplo de tela do desenho do porte usava
    justamente `"Indireto."` como categoria não reconhecida. O `.bas` diz
    outra coisa: `InStr(s, "indireto") > 0` é um teste de **subcadeia**, e
    `Indireto.` passa. Onde os dois divergem, o VBA vence.
    """
    achada = vocabulario.categoria_de("Indireto.", FABRICA["categorias"])
    assert (achada.valor, achada.reconhecido) == ("Indiretos", True)


def test_sem_lista_de_guardioes_qualquer_texto_entra():
    relato = vocabulario.conferir(
        [("HINOVE MATRIZ", "Diretos", "Time do Zé")],
        unidades=UNIDADES, categorias=FABRICA["categorias"], guardioes=[])
    assert relato.nada_a_dizer


def test_com_a_lista_cadastrada_o_guardiao_de_fora_bloqueia():
    relato = vocabulario.conferir(
        [("HINOVE MATRIZ", "Diretos", "Time do Zé"),
         ("HINOVE MATRIZ", "Diretos", ""),
         ("HINOVE MATRIZ", "Diretos", "suprimentos")],
        unidades=UNIDADES, categorias=FABRICA["categorias"],
        guardioes=["Suprimentos", "Fiscal"])
    assert relato.sem_guardiao == 2
    assert "sem guardião válido" in relato.bloqueios()[0]


# =========================================================================
# Os invariantes estruturais da seção 11.1
# =========================================================================

def test_as_larguras_de_cada_aba_sao_as_da_secao_11_1():
    assert len(col.XML) == 27
    assert len(col.NOMES_DO_CE) == 7
    assert len(col.pendentes(31)) == 39
    assert len(col.fis_fat(31)) == 36
    assert len(col.AUXILIARES) == 27
    assert len(col.LANCADOS) == 33
    assert len(col.DESCARTADOS) == 28
    assert len(col.CONFERENCIA) == 6
    assert len(col.categorizacao(31)) == 5


def test_o_bloco_de_conferencia_vem_logo_depois_da_chave_de_acesso():
    rotulos = [c.rotulo for c in col.pendentes(31)]
    inicio = rotulos.index(col.X_CHAVE) + 1
    assert rotulos[inicio:inicio + 6] == [c.rotulo for c in col.CONFERENCIA]


def test_o_bloco_de_categorizacao_ocupa_as_cinco_primeiras_posicoes():
    rotulos = [c.rotulo for c in col.pendentes(31)]
    assert rotulos[:5] == [col.C_TIPO_DE_OPERACAO, col.C_GUARDIAO,
                           col.C_GESTOR, col.C_CATEGORIA, "Retorno semana 30"]


def test_a_ordem_das_39_colunas_e_a_do_relatorio_em_producao():
    """A ordem da seção A7, com `Pedido vinculado` na nona posição.

    As 38 do `.bas` v14 mais a coluna que o relatório real da semana 37 traz
    logo depois de `Dh. Emissão` — o pedido de compra que o CE informa, à
    frente da linha em vez de na coluna 19.
    """
    assert [c.rotulo for c in col.pendentes(31)] == [
        "Tipo de Operação", "Guardião", "Gestor de apoio", "Categoria",
        "Retorno semana 30", "Nro Nota", "Cód. Parceiro",
        "Nome Parceiro (Parceiro)", "Dh. Emissão", "Pedido vinculado",
        "CFOP's XML",
        "Valor da Nota", "Nome Fantasia", "Chave Acesso", "Conf fisica",
        "Dt. Conf. Física", "Conf fiscal", "Incongruência", "Nro. do Pedido",
        "Pedido confirmado?", "Dt. Vencimento", "Situação da manifestação",
        "Situação NF-e", "Tipo NF-e", "Último Evento DF-e",
        "Descrição Nat. Operação", "Entrada/Saida NF-e", "Tomador CT-e",
        "Dias Emissão Doc", "Dh. Importação", "Status", "Nome (Usuário)",
        "Papel no CT-e", "Código da Empresa", "Cnpj Parceiro", "Código",
        "Possui o XML", "Importado pelo DF-e", "Série Doc",
    ]


def test_o_rotulo_do_retorno_carrega_a_semana_anterior():
    assert col.rotulo_do_retorno(31) == "Retorno semana 30"


def test_as_colunas_criticas_sao_texto_e_as_de_data_sao_data():
    """44 dígitos em coluna numérica viram `3,52604E+43` — e o PROCX cai."""
    formato = {c.rotulo: c.formato for c in col.pendentes(31)}
    for rotulo in ("Nro Nota", "Chave Acesso", "Cnpj Parceiro", "Código",
                   "Nome Parceiro (Parceiro)", "Nro. do Pedido"):
        assert formato[rotulo] == "texto", rotulo
    for rotulo in ("Dh. Emissão", "Dt. Vencimento", "Dh. Importação",
                   "Dt. Conf. Física"):
        assert formato[rotulo] == "data", rotulo
    assert formato["Valor da Nota"] == "valor"
    # A coluna que ninguém sabe se é data ou contagem de dias: formato de
    # data, valor como veio. Ver a pendência nº 2.
    assert formato["Dias Emissão Doc"] == "data_ou_contagem"


def test_sao_sete_abas_duas_visiveis_e_cinco_ocultas():
    assert len(col.ABAS) == 7
    assert [nome for nome, visivel in col.ABAS if visivel] == [
        "Pendentes", "PENDENTES FIS-FAT"]
    assert len([nome for nome, visivel in col.ABAS if not visivel]) == 5


# =========================================================================
# `Pedido vinculado` — a nona coluna, medida no relatório da semana 37
# =========================================================================

def test_nota_conferida_traz_o_pedido_do_ce_como_numero():
    """Como número, e não como texto: é assim que ele sai hoje."""
    docs = anotar(documentos(linha_xml("1001", chave=chave_de(1))),
                  conferir(linha_ce(chave_de(1), fisica="Sim", pedido="713535")))
    assert docs[0].pedido_vinculado == 713535
    assert isinstance(docs[0].pedido_vinculado, int)


def test_nota_sem_conferencia_fisica_diz_que_nao_se_aplica():
    """53 das 97 linhas da semana 37: conferência vazia, rótulo no lugar."""
    docs = anotar(documentos(linha_xml("1001", chave=chave_de(1))),
                  conferir(linha_ce(chave_de(1), fisica="", pedido="")))
    assert docs[0].pedido_vinculado == "NA Conf Física"


def test_nota_fora_do_ce_tambem_diz_que_nao_se_aplica():
    """As outras 3: a nota nem está no CE, e recebe o `não` minúsculo."""
    docs = anotar(documentos(linha_xml("1001", chave=chave_de(1))),
                  conferir(linha_ce(chave_de(2))))
    assert docs[0].pedido_vinculado == "NA Conf Física"


def test_conferida_e_sem_pedido_fica_vazia_em_vez_de_ganhar_rotulo():
    """Caso que não apareceu na semana 37 — e por isso não se afirma nada.

    O rótulo diz "não se aplica por falta de conferência física". Usá-lo aqui
    afirmaria o que não se sabe: a nota foi conferida, e o pedido é que falta.
    """
    docs = anotar(documentos(linha_xml("1001", chave=chave_de(1))),
                  conferir(linha_ce(chave_de(1), fisica="Sim", pedido="")))
    assert docs[0].pedido_vinculado == ""


def test_pedido_que_nao_e_numero_chega_como_veio():
    docs = anotar(documentos(linha_xml("1001", chave=chave_de(1))),
                  conferir(linha_ce(chave_de(1), fisica="Sim", pedido="PC-42")))
    assert docs[0].pedido_vinculado == "PC-42"


def test_o_pedido_vinculado_entra_na_pendentes_e_nao_na_fis_fat():
    """A `PENDENTES FIS-FAT` do relatório real tem 36 colunas, sem ela."""
    assert col.P_PEDIDO_VINCULADO in [c.rotulo for c in col.pendentes(31)]
    assert col.P_PEDIDO_VINCULADO not in [c.rotulo for c in col.fis_fat(31)]
    assert col.P_PEDIDO_VINCULADO not in [c.rotulo for c in col.LANCADOS]
    assert col.P_PEDIDO_VINCULADO not in [c.rotulo for c in col.AUXILIARES]


def test_o_pedido_vinculado_vem_logo_depois_da_emissao():
    rotulos = [c.rotulo for c in col.pendentes(31)]
    assert rotulos[rotulos.index(col.X_EMISSAO) + 1] == col.P_PEDIDO_VINCULADO
