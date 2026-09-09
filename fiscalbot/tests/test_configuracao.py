"""A tela de regras: o que ela confere antes de gravar, e o que ela preserva.

No Excel, regra mal escrita só aparecia quando o relatório rodava — e aparecia
como registro não mapeado, que é o sintoma errado para a causa.
"""
from __future__ import annotations

from conftest import base_com, regra

from fiscalbot import configuracao as cfg
from fiscalbot import validacao
from fiscalbot.base import de_dicionario, para_dicionario
from fiscalbot.modelo import Parceiro


# -- a base sobrevive à ida e volta ---------------------------------------

def test_a_base_volta_inteira_da_tela(base_de_fabrica):
    """A tela lê, a pessoa não mexe em nada, a tela grava: tem que dar igual."""
    lido = cfg.ler(base_de_fabrica)
    remontada = cfg.montar(lido)
    assert len(remontada.regras) == len(base_de_fabrica.regras)
    for antes, depois in zip(base_de_fabrica.regras, remontada.regras):
        assert antes == depois
    assert remontada.aliquotas == base_de_fabrica.aliquotas
    assert remontada.parametros.tabelas == base_de_fabrica.parametros.tabelas
    assert remontada.parametros.cst_exigem_icms_positivo == \
        base_de_fabrica.parametros.cst_exigem_icms_positivo


def test_o_arquivo_da_base_sobrevive_a_ida_e_volta(base_de_fabrica):
    de_volta = de_dicionario(para_dicionario(base_de_fabrica))
    assert de_volta.regras == base_de_fabrica.regras


def test_a_tela_declara_todas_as_secoes(base_de_fabrica):
    ids = [s["id"] for s in cfg.secoes(base_de_fabrica)]
    assert ids == ["regras", "parametros", "tabelas", "sinonimos",
                   "aliquotas", "parceiros_sn", "parceiros_cavaco"]
    for secao in cfg.secoes(base_de_fabrica):
        assert secao["explicacao"], f"{secao['id']} sem explicação na tela"
        for campo in secao["campos"]:
            assert campo["rotulo"]


def test_todo_campo_da_regra_tem_ajuda_na_tela():
    """A mini-linguagem não é óbvia para quem cadastra duas vezes por ano."""
    for campo in cfg.CAMPOS_DA_REGRA:
        assert campo["ajuda"], f"{campo['chave']} sem explicação"


# -- o que a conferência pega ---------------------------------------------

def test_a_carga_de_fabrica_esta_limpa(base_de_fabrica):
    assert validacao.conferir(base_de_fabrica) == [] or not validacao.tem_erro(
        validacao.conferir(base_de_fabrica))


def test_id_repetido_e_erro():
    base = base_com(regra("T01"), regra("T01", cfop="5102"))
    problemas = validacao.conferir(base)
    assert validacao.tem_erro(problemas)
    assert any("mesmo ID" in p.mensagem for p in problemas)


def test_duas_regras_que_casam_com_o_mesmo_registro_sao_erro():
    """É o que faria a auditoria marcar AMBIGUA no mês inteiro."""
    base = base_com(regra("T01", esp_cst="00"), regra("T02", esp_cst="20"))
    problemas = validacao.conferir(base)
    assert validacao.tem_erro(problemas)
    assert any("AMBIGUA" in p.mensagem for p in problemas)


def test_operador_inventado_e_erro():
    base = base_com(regra("T01", cond_produto="COMECACOM:701"))
    problemas = validacao.conferir(base)
    assert validacao.tem_erro(problemas)
    assert any("não conhece" in p.mensagem for p in problemas)


def test_tabela_citada_que_nao_existe_e_erro():
    base = base_com(regra("T01", cond_produto="TABELA:INVENTADA"))
    assert validacao.tem_erro(validacao.conferir(base))


def test_regra_ativa_sem_cfop_e_aviso_e_nao_impede_de_gravar():
    """Enquanto a regra está sendo escrita, ela pode estar incompleta."""
    base = base_com(regra("T01", cfop=()))
    problemas = validacao.conferir(base)
    assert not validacao.tem_erro(problemas)
    assert any("nunca vai casar" in p.mensagem for p in problemas)


def test_cfop_vazio_no_meio_da_lista_e_avisado():
    """O motor confere só até o primeiro vazio — herança do VBA."""
    base = base_com(regra("T01", cfop=("1602", "", "2602")))
    assert any("vazio no meio" in p.mensagem for p in validacao.conferir(base))


def test_base_sem_regra_ativa_e_erro():
    assert validacao.tem_erro(validacao.conferir(base_com(regra("T01", ativa=False))))


def test_lista_de_parceiros_vazia_e_aviso_com_o_motivo():
    problemas = validacao.conferir(base_com(regra("T01")))
    aviso = next(p for p in problemas if p.onde == "Parceiros")
    assert aviso.gravidade == validacao.AVISO
    assert "dado da empresa" in aviso.mensagem


# -- gravar --------------------------------------------------------------

def test_gravar_recusa_base_com_erro_e_nao_toca_no_arquivo(tmp_path, monkeypatch):
    from fiscalbot import base as bases

    destino = tmp_path / "base.yaml"
    monkeypatch.setattr(bases, "caminho_da_base", lambda: destino)
    monkeypatch.setattr(cfg.bases, "caminho_da_base", lambda: destino)

    gravou, problemas = cfg.gravar({
        "regras": [{"id": "T01", "cfop": "5101"}, {"id": "T01", "cfop": "5102"}],
        "parametros": [{"tolerancia_carga": "0,05",
                        "cst_exigem_icms_positivo": "00;20"}],
    })
    assert gravou is False
    assert any(p["gravidade"] == "erro" for p in problemas)
    assert not destino.exists(), "não pode gravar base inconsistente"


def test_gravar_aceita_virgula_como_separador_decimal(tmp_path, monkeypatch):
    from fiscalbot import base as bases

    destino = tmp_path / "base.yaml"
    monkeypatch.setattr(bases, "caminho_da_base", lambda: destino)
    monkeypatch.setattr(cfg.bases, "caminho_da_base", lambda: destino)

    gravou, _ = cfg.gravar({
        "regras": [{"id": "T01", "cfop": "5101", "operacao": "Teste",
                    "ativa": True}],
        "parametros": [{"tolerancia_carga": "0,08",
                        "cst_exigem_icms_positivo": "00;20"}],
        "parceiros_sn": [{"codigo": "1", "descricao": "X"}],
    })
    assert gravou is True
    assert bases.carregar(destino).parametros.tolerancia_carga == 0.08


def test_gravar_carimba_quem_alterou(tmp_path, monkeypatch):
    """É o que substitui, dentro do aplicativo, o histórico que o git daria."""
    from fiscalbot import base as bases

    destino = tmp_path / "base.yaml"
    monkeypatch.setattr(bases, "caminho_da_base", lambda: destino)
    monkeypatch.setattr(cfg.bases, "caminho_da_base", lambda: destino)

    cfg.gravar({
        "regras": [{"id": "T01", "cfop": "5101", "ativa": True}],
        "parametros": [{"tolerancia_carga": "0.05",
                        "cst_exigem_icms_positivo": "00"}],
        "parceiros_sn": [{"codigo": "1"}],
    }, responsavel="lupe")
    gravada = bases.carregar(destino)
    assert gravada.atualizado_por == "lupe"
    assert gravada.atualizado_em


def test_a_carga_de_fabrica_nao_leva_dado_da_empresa(base_de_fabrica):
    """Regra tributária vai para o git; parceiro real, nunca."""
    assert base_de_fabrica.parceiros_simples_nacional == []
    assert base_de_fabrica.parceiros_cavaco == []
    publicavel = para_dicionario(base_de_fabrica, com_parceiros=False)
    assert "parceiros" not in publicavel


def test_parceiro_cadastrado_na_tela_fica_so_na_base_viva(tmp_path, monkeypatch):
    from fiscalbot import base as bases

    destino = tmp_path / "base.yaml"
    viva = bases.carregar_fabrica()
    viva.parceiros_simples_nacional = [Parceiro("6428", "TRANSPORTADORA X")]
    bases.gravar(viva, destino)
    assert "6428" in destino.read_text(encoding="utf-8")
    assert "6428" not in bases.FABRICA.read_text(encoding="utf-8")
