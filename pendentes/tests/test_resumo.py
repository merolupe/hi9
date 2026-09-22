"""O painel semanal: a conta, o desempate e o que ele se recusa a contar.

As planilhas são montadas aqui, com parceiro e guardião inventados — regra
nº 1. O que estes testes provam não é o número de uma semana real; é que o
painel conta o que o arquivo de origem conta, que ele não inventa categoria e
que ele não estraga a planilha em que entra.

A conferência contra o relatório de produção da semana 38 está registrada em
`docs/pendentes/07-resumo-executivo.md`: as três categorias, os dois TOP 5, o
corte por unidade e o ranking de guardiões saíram iguais, dígito a dígito.
"""
from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

import openpyxl
import pytest

from pendentes import parametros
from pendentes.mercadorias import colunas as merc
from pendentes.resumo import colunas as col
from pendentes.resumo import fontes, painel as agregacao
from pendentes.resumo.execucao import gerar
from pendentes.servicos import colunas as serv

SEMANA = 38
REFERENCIA = date(2026, 9, 21)

#: Cinco unidades cadastradas, com a ordem que a tabela exige.
UNIDADES = [
    {"ordem": 1, "trecho": "CORUMB", "unidade": "Corumbá"},
    {"ordem": 2, "trecho": "GUAR", "unidade": "Guará"},
    {"ordem": 3, "trecho": "MATRIZ", "unidade": "Matriz"},
]


def _linha_de_mercadoria(numero, categoria="Indiretos", guardiao="Suprimentos",
                         gestor="Anderson", parceiro="FORNECEDOR ALFA LTDA",
                         valor=1000.0, emissao=datetime(2026, 9, 1),
                         fantasia="HINOVE (FILIAL GUARÁ)") -> list:
    """Uma linha da aba `Pendentes`, preenchida pelo nome de cada coluna."""
    rotulos = [c.rotulo for c in merc.pendentes(SEMANA)]
    linha = ["" for _ in rotulos]
    valores = {
        merc.X_NRO_NOTA: numero, merc.C_CATEGORIA: categoria,
        merc.C_GUARDIAO: guardiao, merc.C_GESTOR: gestor,
        merc.X_NOME_PARCEIRO: parceiro, merc.X_VALOR: valor,
        merc.X_EMISSAO: emissao, merc.X_NOME_FANTASIA: fantasia,
    }
    for rotulo, valor_da_coluna in valores.items():
        linha[rotulos.index(rotulo)] = valor_da_coluna
    return linha


def _linha_de_servico(numero, guardiao="COMEX", gestor="Tavares",
                      parceiro="PRESTADOR BETA LTDA", valor=500.0,
                      emissao=datetime(2026, 8, 1),
                      filial="HINOVE (MATRIZ)") -> list:
    rotulos = [c.rotulo for c in serv.PENDENTES]
    linha = ["" for _ in rotulos]
    valores = {
        "Nro Nota": numero, "Guardiao": guardiao, "Gestor de apoio": gestor,
        "Parceiro": parceiro, "Valor NFSe (Valor Bruto)": valor,
        "Emissao": emissao, "Filial": filial,
    }
    for rotulo, valor_da_coluna in valores.items():
        linha[rotulos.index(rotulo)] = valor_da_coluna
    return linha


def relatorio(caminho: Path, mercadorias=(), servicos=(),
              outras: dict | None = None) -> Path:
    """Uma planilha da semana como as outras duas rotinas a entregam."""
    livro = openpyxl.Workbook()
    livro.remove(livro.active)
    if mercadorias is not None:
        aba = livro.create_sheet("Pendentes")
        aba.append([c.rotulo for c in merc.pendentes(SEMANA)])
        for linha in mercadorias:
            aba.append(linha)
    if servicos is not None:
        aba = livro.create_sheet("Servicos")
        aba.append([c.rotulo for c in serv.PENDENTES])
        for linha in servicos:
            aba.append(linha)
    for nome, linhas in (outras or {}).items():
        aba = livro.create_sheet(nome)
        for linha in linhas:
            aba.append(linha)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    livro.save(str(caminho))
    return caminho


def ajustes(**extras) -> dict:
    """A carga de fábrica com a semana fixada — nada de depender de hoje."""
    dados = parametros.carregar_fabrica()
    dados["semana"] = {"numero": SEMANA, "data_de_referencia": "21/09/2026"}
    dados["unidades"] = extras.pop("unidades", list(UNIDADES))
    dados["resumo"] = {**(dados.get("resumo") or {}), **extras}
    return dados


def executar(tmp_path, arquivos, **extras):
    return gerar(arquivos, tmp_path / "saida", dados=ajustes(**extras),
                 agora=datetime(2026, 9, 22, 9, 0))


@pytest.fixture()
def semana(tmp_path) -> Path:
    """Dez notas: sete de mercadoria em duas categorias, três de serviço."""
    return relatorio(
        tmp_path / f"Pendentes{SEMANA}.xlsx",
        mercadorias=[
            _linha_de_mercadoria("1001", valor=1000.0,
                                 emissao=datetime(2026, 9, 11)),
            _linha_de_mercadoria("1002", valor=2000.0,
                                 emissao=datetime(2026, 9, 1)),
            _linha_de_mercadoria("1003", categoria="Diretos",
                                 guardiao="Balança Guará", valor=5000.0,
                                 emissao=datetime(2026, 9, 19)),
            _linha_de_mercadoria("1004", categoria="Diretos",
                                 guardiao="Balança Guará", valor=3000.0,
                                 emissao=datetime(2026, 9, 17)),
            _linha_de_mercadoria("1005", valor=500.0,
                                 emissao=datetime(2026, 6, 9),
                                 fantasia="HINOVE (MATRIZ)"),
        ],
        servicos=[
            _linha_de_servico("9001", valor=700.0,
                              emissao=datetime(2026, 9, 6)),
            _linha_de_servico("9002", guardiao="RH DP", valor=100.0,
                              emissao=datetime(2026, 7, 21)),
        ],
    )


# -- a conta ----------------------------------------------------------------

def test_as_tres_categorias_saem_na_ordem_do_painel(tmp_path, semana):
    execucao = executar(tmp_path, [semana])
    assert [linha.categoria for linha in execucao.painel.categorias] == [
        "Diretos", "Indiretos", "Serviços"]


def test_cada_categoria_traz_quantidade_valor_e_media_de_dias(tmp_path, semana):
    execucao = executar(tmp_path, [semana])
    por_nome = {linha.categoria: linha for linha in execucao.painel.categorias}

    assert por_nome["Diretos"].quantidade == 2
    assert por_nome["Diretos"].valor == pytest.approx(8000.0)
    # 21/09 − 19/09 = 2 dias; 21/09 − 17/09 = 4 dias.
    assert por_nome["Diretos"].media_dias == pytest.approx(3.0)
    assert por_nome["Serviços"].quantidade == 2


def test_o_total_e_a_soma_das_tres_e_nao_uma_quarta_conta(tmp_path, semana):
    execucao = executar(tmp_path, [semana])
    categorias = execucao.painel.categorias
    assert execucao.painel.total.quantidade == sum(c.quantidade for c in categorias)
    assert execucao.painel.total.valor == pytest.approx(
        sum(c.valor for c in categorias))


def test_a_media_de_dias_conta_da_emissao_ate_a_data_de_referencia(tmp_path):
    arquivo = relatorio(tmp_path / "p.xlsx", mercadorias=[
        _linha_de_mercadoria("1", emissao=datetime(2026, 9, 11)),
        _linha_de_mercadoria("2", emissao=datetime(2026, 9, 1)),
    ], servicos=[])
    execucao = executar(tmp_path, [arquivo])
    indiretos = next(c for c in execucao.painel.categorias
                     if c.categoria == "Indiretos")
    assert indiretos.media_dias == pytest.approx(15.0)   # (10 + 20) / 2


def test_a_hora_da_emissao_nao_conta_como_um_dia_a_menos(tmp_path):
    """`INT()` no original: a emissão das 23h50 tem os mesmos dias da das 00h10."""
    arquivo = relatorio(tmp_path / "p.xlsx", mercadorias=[
        _linha_de_mercadoria("1", emissao=datetime(2026, 9, 11, 23, 50)),
    ], servicos=[])
    execucao = executar(tmp_path, [arquivo])
    assert execucao.painel.top_dias[0].dias(REFERENCIA) == 10


# -- os dois TOP N ----------------------------------------------------------

def test_o_top_de_dias_traz_as_mais_antigas_primeiro(tmp_path, semana):
    execucao = executar(tmp_path, [semana])
    dias = [nota.dias(REFERENCIA) for nota in execucao.painel.top_dias]
    assert dias == sorted(dias, reverse=True)
    assert dias[0] == (REFERENCIA - date(2026, 6, 9)).days


def test_o_top_de_valor_traz_as_maiores_primeiro(tmp_path, semana):
    execucao = executar(tmp_path, [semana])
    valores = [nota.valor for nota in execucao.painel.top_valor]
    assert valores == sorted(valores, reverse=True)
    assert valores[0] == pytest.approx(5000.0)


def test_o_top_para_no_numero_de_linhas_configurado(tmp_path, semana):
    execucao = executar(tmp_path, [semana], linhas_do_top=3)
    assert len(execucao.painel.top_dias) == 3
    assert len(execucao.painel.top_valor) == 3


def test_no_empate_vence_a_ultima_linha_como_no_arquivo_de_origem(tmp_path):
    """`V + LIN()/1000000` e `MAIOR()`: entre iguais, ganha quem está embaixo."""
    arquivo = relatorio(tmp_path / "p.xlsx", mercadorias=[
        _linha_de_mercadoria("1", parceiro="PRIMEIRA", valor=1000.0),
        _linha_de_mercadoria("2", parceiro="SEGUNDA", valor=1000.0),
    ], servicos=[])
    execucao = executar(tmp_path, [arquivo], linhas_do_top=1)
    assert execucao.painel.top_valor[0].parceiro == "SEGUNDA"


def test_nota_sem_emissao_fica_fora_da_media_e_dos_tops_e_e_contada(tmp_path):
    arquivo = relatorio(tmp_path / "p.xlsx", mercadorias=[
        _linha_de_mercadoria("1", emissao=datetime(2026, 9, 11)),
        _linha_de_mercadoria("2", emissao=""),
    ], servicos=[])
    execucao = executar(tmp_path, [arquivo])
    indiretos = next(c for c in execucao.painel.categorias
                     if c.categoria == "Indiretos")
    assert indiretos.quantidade == 2                     # continua contada
    assert indiretos.media_dias == pytest.approx(10.0)   # mas não na média
    assert len(execucao.painel.top_dias) == 1
    assert execucao.sem_emissao == 1
    assert any("sem data de emissão" in aviso for aviso in execucao.atencoes())


# -- unidade e guardião -----------------------------------------------------

def test_a_unidade_sai_da_tabela_cadastrada_pelo_trecho(tmp_path, semana):
    execucao = executar(tmp_path, [semana])
    por_nome = {corte.nome: corte for corte in execucao.painel.unidades}
    assert por_nome["Guará"].quantidade["Indiretos"] == 2
    assert por_nome["Guará"].quantidade["Diretos"] == 2
    # A nota 1005 é de Matriz, e os dois serviços também.
    assert por_nome["Matriz"].total_da_quantidade == 3


def test_unidade_cadastrada_sem_pendencia_aparece_zerada(tmp_path, semana):
    """Zero é uma resposta: a unidade existe e está limpa nesta semana."""
    execucao = executar(tmp_path, [semana])
    corumba = next(c for c in execucao.painel.unidades if c.nome == "Corumbá")
    assert corumba.total_da_quantidade == 0


def test_sem_tabela_de_unidades_o_bloco_fica_vazio_e_a_tela_diz(tmp_path, semana):
    execucao = executar(tmp_path, [semana], unidades=[])
    assert execucao.painel.unidades == []
    assert any("tabela de unidades está vazia" in aviso
               for aviso in execucao.atencoes())


def test_o_ranking_de_guardioes_vai_do_maior_para_o_menor(tmp_path, semana):
    execucao = executar(tmp_path, [semana])
    totais = [corte.total_da_quantidade for corte in execucao.painel.guardioes]
    assert totais == sorted(totais, reverse=True)


def test_guardiao_fora_do_ranking_nao_entra_no_grafico(tmp_path, semana):
    execucao = executar(tmp_path, [semana],
                        guardioes_fora_do_ranking=["Balança Guará"])
    nomes = [corte.nome for corte in execucao.painel.guardioes]
    assert "Balança Guará" not in nomes
    # Mas as notas dele continuam na conta das categorias.
    diretos = next(c for c in execucao.painel.categorias
                   if c.categoria == "Diretos")
    assert diretos.quantidade == 2


def test_o_grafico_de_guardioes_para_no_limite_configurado(tmp_path, semana):
    execucao = executar(tmp_path, [semana], guardioes_no_grafico=2)
    # Quatro guardiões na semana; o gráfico mostra os dois maiores.
    assert len(execucao.painel.guardioes) == 4
    assert len(execucao.painel.guardioes_do_grafico) == 2


# -- o que o painel se recusa a contar --------------------------------------

def test_mercadoria_sem_categoria_fica_de_fora_e_bloqueia(tmp_path):
    arquivo = relatorio(tmp_path / "p.xlsx", mercadorias=[
        _linha_de_mercadoria("1"),
        _linha_de_mercadoria("2", categoria="", parceiro="SEM CATEGORIA LTDA"),
    ], servicos=[])
    execucao = executar(tmp_path, [arquivo])
    assert execucao.painel.total.quantidade == 1
    assert len(execucao.painel.sem_categoria) == 1
    assert not execucao.encerravel
    assert "SEM CATEGORIA LTDA" in execucao.bloqueios()[0]


def test_servico_nao_precisa_de_categoria_porque_a_frente_e_a_categoria(tmp_path):
    arquivo = relatorio(tmp_path / "p.xlsx", mercadorias=[],
                        servicos=[_linha_de_servico("9001")])
    execucao = executar(tmp_path, [arquivo])
    assert execucao.painel.sem_categoria == []
    servicos = next(c for c in execucao.painel.categorias
                    if c.categoria == "Serviços")
    assert servicos.quantidade == 1


def test_arquivo_sem_nenhuma_das_duas_abas_aborta_dizendo_o_que_esperava(tmp_path):
    arquivo = relatorio(tmp_path / "outro.xlsx", mercadorias=None,
                        servicos=None, outras={"Qualquer": [["a", "b"]]})
    with pytest.raises(fontes.SemRelatorio) as erro:
        executar(tmp_path, [arquivo])
    assert "já gerado e classificado" in str(erro.value)


# -- a planilha gravada -----------------------------------------------------

def test_o_painel_entra_na_planilha_sem_alterar_o_arquivo_de_entrada(
        tmp_path, semana):
    antes = semana.read_bytes()
    execucao = executar(tmp_path, [semana])
    assert semana.read_bytes() == antes
    assert execucao.planilha != semana

    livro = openpyxl.load_workbook(str(execucao.planilha))
    assert livro.sheetnames[0] == col.ABA_DO_PAINEL
    assert "Pendentes" in livro.sheetnames and "Servicos" in livro.sheetnames


def test_a_aba_auxiliar_nasce_oculta_e_os_tres_graficos_apontam_para_ela(
        tmp_path, semana):
    execucao = executar(tmp_path, [semana])
    livro = openpyxl.load_workbook(str(execucao.planilha))
    assert livro[col.ABA_AUXILIAR].sheet_state == "hidden"

    graficos = livro[col.ABA_DO_PAINEL]._charts
    assert len(graficos) == 3
    for grafico in graficos:
        for serie in grafico.series:
            # O nome da aba vai entre apóstrofos por causa do sublinhado.
            assert f"{col.ABA_AUXILIAR}'!" in serie.val.numRef.f


def test_sem_unidade_cadastrada_o_grafico_dela_nao_e_desenhado(tmp_path, semana):
    execucao = executar(tmp_path, [semana], unidades=[])
    livro = openpyxl.load_workbook(str(execucao.planilha))
    assert len(livro[col.ABA_DO_PAINEL]._charts) == 2


def test_rodar_duas_vezes_troca_o_painel_em_vez_de_empilhar(tmp_path, semana):
    primeira = executar(tmp_path, [semana]).planilha
    segunda = executar(tmp_path, [primeira]).planilha
    livro = openpyxl.load_workbook(str(segunda))
    assert livro.sheetnames.count(col.ABA_DO_PAINEL) == 1
    assert livro.sheetnames.count(col.ABA_AUXILIAR) == 1
    assert len(livro[col.ABA_DO_PAINEL]._charts) == 3


def test_as_outras_abas_atravessam_a_gravacao_como_estavam(tmp_path):
    arquivo = relatorio(
        tmp_path / f"Pendentes{SEMANA}.xlsx",
        mercadorias=[_linha_de_mercadoria("1")],
        servicos=[_linha_de_servico("9001")],
        outras={"Lançados": [["Nro Nota", "Valor"], ["7777", 12.5]]})
    execucao = executar(tmp_path, [arquivo])
    livro = openpyxl.load_workbook(str(execucao.planilha))
    assert [c.value for c in livro["Lançados"][2]] == ["7777", 12.5]


def test_a_celula_de_dias_acima_do_limite_sai_destacada(tmp_path, semana):
    execucao = executar(tmp_path, [semana], destacar_acima_de_dias=10)
    aba = openpyxl.load_workbook(str(execucao.planilha))[col.ABA_DO_PAINEL]
    linha = col.LINHA_DO_TOP_DIAS + 2
    coluna = col.COLUNA_DA_DIREITA + 6
    assert aba.cell(linha, coluna).value > 10
    assert aba.cell(linha, coluna).fill.fgColor.rgb == "FFFFC7CE"


def test_as_duas_frentes_podem_chegar_em_arquivos_separados(tmp_path):
    mercadorias = relatorio(tmp_path / "Pendentes38.xlsx",
                            mercadorias=[_linha_de_mercadoria("1")],
                            servicos=None)
    servicos = relatorio(tmp_path / "Servicos38.xlsx", mercadorias=None,
                         servicos=[_linha_de_servico("9001")])
    execucao = executar(tmp_path, [mercadorias, servicos])
    assert execucao.mercadorias == 1 and execucao.servicos == 1
    assert len(execucao.abas_lidas) == 2
    # A planilha que leva o painel é a que tem mais abas de pendência — com
    # empate, a primeira arrastada.
    assert execucao.planilha.name == "Pendentes38.xlsx"


def test_a_data_de_referencia_cadastrada_manda_no_lugar_de_hoje(tmp_path, semana):
    execucao = executar(tmp_path, [semana])
    assert execucao.referencia == REFERENCIA
    aba = openpyxl.load_workbook(str(execucao.planilha))[col.ABA_DO_PAINEL]
    celula = aba.cell(col.LINHA_DO_TITULO, col.COLUNA_DOS_AJUSTES + 1)
    assert celula.value.date() == REFERENCIA


def test_a_ordem_de_leitura_e_mercadorias_antes_de_servicos(tmp_path, semana):
    """Não é detalhe: é ela que decide o desempate dos dois TOP N."""
    execucao = executar(tmp_path, [semana])
    leitura = fontes.ler_relatorios([semana], lambda _: "")
    origens = [p.origem for p in leitura.pendencias]
    assert origens == sorted(origens, key=lambda o: o != "mercadorias")
    assert execucao.mercadorias == 5 and execucao.servicos == 2


def test_montar_nao_depende_de_planilha_nenhuma(tmp_path):
    """A conta é testável sem arquivo — é o que separa `painel` de `escrita`."""
    notas = [
        fontes.Pendencia("Diretos", "Balança", "Gestor", "ALFA", 10.0,
                         date(2026, 9, 1), "Guará", "mercadorias", 0),
        fontes.Pendencia("Serviços", "COMEX", "Gestor", "BETA", 5.0,
                         date(2026, 9, 11), "Matriz", "servicos", 1),
    ]
    quadro = agregacao.montar(notas, referencia=REFERENCIA, unidades=UNIDADES)
    assert quadro.total.quantidade == 2
    assert quadro.total.valor == pytest.approx(15.0)
    assert quadro.top_dias[0].parceiro == "ALFA"
