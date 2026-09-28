"""Os dados do time moram fora da pasta do código.

Uma versão nova é um ZIP extraído noutra pasta; o que o time produziu não pode
ficar para trás na pasta velha.
"""
from __future__ import annotations

import os

import pytest

from central import dados


@pytest.fixture(autouse=True)
def _sem_variavel(monkeypatch):
    """Cada teste começa sem `HINOVE_DADOS`, e a variável não vaza para o resto."""
    monkeypatch.delenv(dados.VARIAVEL, raising=False)


def _versao_antiga(pasta):
    """Uma pasta de código de antes da mudança, com dados dentro."""
    livro = pasta / "dados" / "pendentes" / "classificacao" / "servicos.yaml"
    livro.parent.mkdir(parents=True)
    livro.write_text("registros: []\n", encoding="utf-8")
    serie = pasta / "competencias" / "serie-2026.yaml"
    serie.parent.mkdir(parents=True)
    serie.write_text("meses: []\n", encoding="utf-8")
    return pasta


def test_a_primeira_abertura_copia_os_dados_e_deixa_o_original(tmp_path):
    codigo = _versao_antiga(tmp_path / "hi9-antigo")
    destino = tmp_path / "Documentos" / "Hinove"

    preparo = dados.preparar(codigo, destino)

    assert preparo.copiadas == ["dados", "competencias"]
    assert (destino / "dados/pendentes/classificacao/servicos.yaml").is_file()
    assert (destino / "competencias/serie-2026.yaml").is_file()
    assert (codigo / "dados/pendentes/classificacao/servicos.yaml").is_file()
    assert os.environ[dados.VARIAVEL] == str(destino)
    assert (destino / "LEIA-ME.txt").is_file()


def test_a_versao_nova_encontra_tudo_sem_copiar_nada(tmp_path):
    destino = tmp_path / "Documentos" / "Hinove"
    dados.preparar(_versao_antiga(tmp_path / "hi9-antigo"), destino)

    nova = tmp_path / "hi9-novo"
    nova.mkdir()
    preparo = dados.preparar(nova, destino)

    assert preparo.copiadas == [] and preparo.ignoradas == []
    assert (destino / "dados/pendentes/classificacao/servicos.yaml").is_file()


def test_depois_da_migracao_a_pasta_do_codigo_nao_manda_mais(tmp_path):
    destino = tmp_path / "Documentos" / "Hinove"
    codigo = _versao_antiga(tmp_path / "hi9")
    dados.preparar(codigo, destino)
    (destino / "dados/pendentes/classificacao/servicos.yaml").write_text(
        "registros: [novo]\n", encoding="utf-8")

    preparo = dados.preparar(codigo, destino)

    assert preparo.ignoradas == ["dados", "competencias"]
    assert "novo" in (destino / "dados/pendentes/classificacao/servicos.yaml"
                      ).read_text(encoding="utf-8")
    assert any("ignorada" in linha for linha in preparo.mensagens())


def test_a_variavel_ja_definida_e_respeitada(tmp_path, monkeypatch):
    rede = tmp_path / "rede" / "fiscal"
    monkeypatch.setenv(dados.VARIAVEL, str(rede))
    preparo = dados.preparar(_versao_antiga(tmp_path / "hi9"))
    assert preparo.pasta == rede
    assert (rede / "dados").is_dir()


def test_sem_variavel_o_padrao_e_a_pasta_documentos(tmp_path, monkeypatch):
    monkeypatch.setattr(dados, "pasta_de_documentos", lambda: tmp_path / "Docs")
    assert dados.preparar(tmp_path / "hi9").pasta == tmp_path / "Docs" / "Hinove"


def test_se_a_copia_falha_a_central_fica_na_pasta_do_codigo(tmp_path,
                                                            monkeypatch):
    """Trocar para uma pasta vazia seria abrir sem o trabalho do time."""
    codigo = _versao_antiga(tmp_path / "hi9")

    def falha(*_, **__):
        raise PermissionError("acesso negado")

    monkeypatch.setattr(dados.shutil, "copytree", falha)
    preparo = dados.preparar(codigo, tmp_path / "Documentos" / "Hinove")

    assert preparo.erro and preparo.pasta == codigo
    assert dados.VARIAVEL not in os.environ
    assert not (tmp_path / "Documentos/Hinove/dados").exists()


def test_as_ferramentas_leem_a_pasta_publicada(tmp_path, monkeypatch):
    """Cada uma lê a variável; nenhuma importa a Central."""
    from apurabot import serie
    from fiscalbot import base as fiscalbot_base
    from pendentes import estado, parametros, snapshot
    from pendentes.conhecimento import base as conhecimento
    from pendentes.servicos import historico

    monkeypatch.setenv(dados.VARIAVEL, str(tmp_path))
    assert estado.caminho_do_livro("servicos").is_relative_to(tmp_path / "dados")
    assert parametros.caminho_da_base().is_relative_to(tmp_path / "dados")
    assert snapshot.pasta_das_semanas("servicos").is_relative_to(tmp_path / "dados")
    assert conhecimento.caminho_da_base().is_relative_to(tmp_path / "dados")
    assert historico.caminho().is_relative_to(tmp_path / "dados")
    assert fiscalbot_base.caminho_da_base().is_relative_to(tmp_path / "dados")
    assert serie.caminho(2026).parent == tmp_path / "competencias"
