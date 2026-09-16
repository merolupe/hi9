"""A ordem como dado visível, e os dois endereços do parâmetro."""
from __future__ import annotations

from pendentes import parametros
from pendentes.tabelas import por_ordem, primeira_que_casa

#: A tabela de unidades como ela precisa ser cadastrada — e é este `ordem` que
#: carrega a armadilha que hoje vive enterrada na sequência de `ElseIf`.
UNIDADES = [
    {"ordem": 2, "trecho": "RIO BRILHANTE", "unidade": "Rio Brilhante"},
    {"ordem": 4, "trecho": "CORUMB", "unidade": "Corumbá"},
    {"ordem": 1, "trecho": "MATRIZ", "unidade": "Matriz"},
    {"ordem": 5, "trecho": "GUAR", "unidade": "Guará"},
    {"ordem": 3, "trecho": "REGISTRO", "unidade": "Registro"},
]


def test_por_ordem_devolve_as_linhas_na_ordem_cadastrada():
    assert [linha["trecho"] for linha in por_ordem(UNIDADES)] == \
        ["MATRIZ", "RIO BRILHANTE", "REGISTRO", "CORUMB", "GUAR"]


def test_linha_sem_ordem_vai_para_o_fim_preservando_o_cadastro():
    """Empate nunca é resolvido por acaso."""
    misturada = [{"trecho": "NOVA"}, {"ordem": 1, "trecho": "MATRIZ"},
                 {"trecho": "OUTRA"}]
    assert [linha["trecho"] for linha in por_ordem(misturada)] == \
        ["MATRIZ", "NOVA", "OUTRA"]


def test_corumba_vem_antes_de_guara_e_e_isso_que_decide():
    """A armadilha, provada nos dois sentidos.

    Com `CORUMB` antes de `GUAR`, a fantasia de Corumbá vira Corumbá. Com a
    ordem invertida — que é o que um cadastro desavisado faria — ela vira
    Guará, sem erro e sem aviso. É por isso que a ordem virou coluna.
    """
    fantasia = "HINOVE CORUMBA GUARDA MOVEIS"

    certa = primeira_que_casa(fantasia, UNIDADES)
    assert certa["unidade"] == "Corumbá"

    invertida = [dict(linha) for linha in UNIDADES]
    for linha in invertida:
        if linha["trecho"] == "CORUMB":
            linha["ordem"] = 6
    assert primeira_que_casa(fantasia, invertida)["unidade"] == "Guará"


def test_fantasia_que_nao_casa_com_nenhum_trecho_devolve_nada():
    """Quem decide o que fazer com isso é o domínio: o fallback devolve o
    texto original, e a unidade não reconhecida bloqueia o encerramento."""
    assert primeira_que_casa("HINOVE CAMPO GRANDE", UNIDADES) is None
    assert primeira_que_casa("", UNIDADES) is None


# -- a carga de fábrica ----------------------------------------------------

def test_a_fabrica_carrega_e_traz_os_parametros_do_confronto():
    fabrica = parametros.carregar_fabrica()
    confronto = fabrica["confronto_servicos"]
    assert confronto["tops_de_lancamento"] == ["2020", "2111"]
    assert confronto["tolerancia_da_razao"] == 0.005
    assert (confronto["multiplo_minimo"], confronto["multiplo_maximo"]) == (2, 12)
    assert confronto["cnpj_descartado"] == "00000000000000"


def test_a_fabrica_nao_traz_nenhum_dado_da_empresa():
    """Regra nº 1: unidade, filial e guardião trazem nome e CNPJ reais."""
    fabrica = parametros.carregar_fabrica()
    assert fabrica["unidades"] == []
    assert fabrica["filiais"] == []
    assert fabrica["guardioes"] == []


def test_a_fabrica_declara_as_colunas_de_cada_relatorio():
    fabrica = parametros.carregar_fabrica()
    assert len(parametros.colunas_de(fabrica, "xml")) == 27
    assert len(parametros.colunas_de(fabrica, "conferencia_de_entradas")) == 7
    assert len(parametros.colunas_de(fabrica, "asis")) == 24
    assert len(parametros.colunas_de(fabrica, "portal_de_compras")) == 16
    assert len(parametros.colunas_de(fabrica, "conferencia_de_servicos")) == 8


def test_as_27_colunas_do_xml_sao_igualmente_obrigatorias():
    """O VBA declara 16 "principais" e 11 "complementares" e valida as 27."""
    exigencias = parametros.colunas_de(parametros.carregar_fabrica(), "xml")
    assert all(e.obrigatoria for e in exigencias)


def test_o_roteamento_vem_com_as_quatro_condicoes_na_ordem():
    roteamento = parametros.roteamento(parametros.carregar_fabrica())
    assert [linha["destino"] for linha in por_ordem(roteamento)] == \
        ["CTe", "Manifestados", "Manifestados", "Entradas 3os"]


def test_a_base_viva_nasce_da_fabrica_e_depois_manda(tmp_path):
    base = tmp_path / "parametros.yaml"
    assert parametros.carregar(base)["categorias"] == ["Diretos", "Indiretos"]

    parametros.gravar({"categorias": ["Diretos", "Indiretos", "Ativo"]},
                      "luan", base)

    assert parametros.carregar(base)["categorias"] == \
        ["Diretos", "Indiretos", "Ativo"]


def test_gravar_mescla_a_fatia_que_a_tela_mandou(tmp_path):
    """Cada tela edita um pedaço; mandar o arquivo inteiro apagaria a outra."""
    base = tmp_path / "parametros.yaml"
    parametros.gravar({"unidades": [{"ordem": 1, "trecho": "MATRIZ",
                                     "unidade": "Matriz"}]}, "luan", base)
    parametros.gravar({"guardioes": ["Suprimentos"]}, "ana", base)

    dados = parametros.carregar(base)
    assert dados["unidades"][0]["unidade"] == "Matriz"
    assert dados["guardioes"] == ["Suprimentos"]


def test_a_base_carimba_quem_gravou_e_quando(tmp_path):
    base = tmp_path / "parametros.yaml"
    parametros.gravar({"guardioes": ["Fiscal"]}, "luan", base)
    dados = parametros.carregar(base)
    assert dados["atualizado_por"] == "luan"
    assert dados["atualizado_em"]


def test_secao_nova_da_fabrica_chega_a_uma_base_antiga(tmp_path):
    base = tmp_path / "parametros.yaml"
    base.write_text("categorias: [Diretos]\n", encoding="utf-8")
    dados = parametros.carregar(base)
    assert dados["categorias"] == ["Diretos"]          # a base manda
    assert dados["confronto_servicos"]["prefixo_de_pedido"] == "PC"
