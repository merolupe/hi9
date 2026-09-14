"""A foto semanal: nunca sobrescrita, e com a impressão digital das entradas."""
from __future__ import annotations

import json

from conftest import CHAVE
from pendentes import estado, snapshot


def livro_com_uma_classificacao() -> estado.Livro:
    livro = estado.Livro("mercadorias")
    livro.registros[CHAVE] = estado.Classificacao(CHAVE, guardiao="Suprimentos")
    return livro


def test_a_semana_grava_livro_entradas_e_resumo(tmp_path, arquivo_xml):
    pasta = snapshot.gravar(
        "mercadorias", 2026, 31,
        planilha=arquivo_xml,
        livro=livro_com_uma_classificacao(),
        entradas=[snapshot.impressao_de(arquivo_xml, "xml")],
        resumo={"titulo": "Semana 31 — 2 notas pendentes"},
        encerravel=False,
        raiz=tmp_path,
    )

    assert pasta.name == "2026-S31"
    assert (pasta / arquivo_xml.name).is_file()
    assert "Suprimentos" in (pasta / "classificacao.yaml").read_text(encoding="utf-8")

    entradas = json.loads((pasta / "entradas.json").read_text(encoding="utf-8"))
    assert entradas[0]["papel"] == "xml"
    assert len(entradas[0]["sha256"]) == 64

    resumo = json.loads((pasta / "resumo.json").read_text(encoding="utf-8"))
    assert resumo["encerravel"] is False
    assert resumo["semana"] == 31
    assert resumo["titulo"].startswith("Semana 31")


def test_a_pasta_da_semana_nunca_e_sobrescrita(tmp_path):
    primeira = snapshot.gravar("servicos", 2026, 31, raiz=tmp_path)
    segunda = snapshot.gravar("servicos", 2026, 31, raiz=tmp_path)
    terceira = snapshot.gravar("servicos", 2026, 31, raiz=tmp_path)

    assert [p.name for p in (primeira, segunda, terceira)] == \
        ["2026-S31", "2026-S31-2", "2026-S31-3"]
    assert len(snapshot.semanas_gravadas("servicos", tmp_path)) == 3


def test_a_execucao_seguinte_enxerga_o_que_ficou_aberto_na_anterior(tmp_path):
    """Sem botão de encerrar, é esta a trava: ninguém encerra sem saber."""
    snapshot.gravar("mercadorias", 2026, 30, encerravel=False,
                    resumo={"bloqueios": ["3 unidades não reconhecidas"]},
                    raiz=tmp_path)

    anterior = snapshot.ultima_semana("mercadorias", tmp_path)

    assert anterior["semana"] == 30
    assert anterior["encerravel"] is False
    assert anterior["bloqueios"] == ["3 unidades não reconhecidas"]


def test_sem_nenhuma_semana_gravada_nao_ha_anterior(tmp_path):
    assert snapshot.ultima_semana("mercadorias", tmp_path) is None


def test_arquivos_iguais_tem_a_mesma_impressao_digital(tmp_path, arquivo_xml):
    copia = tmp_path / "copia.xlsx"
    copia.write_bytes(arquivo_xml.read_bytes())

    original = snapshot.impressao_de(arquivo_xml, "xml")
    duplicata = snapshot.impressao_de(copia, "xml")

    assert original.sha256 == duplicata.sha256
    assert original.tamanho == duplicata.tamanho
    assert original.nome != duplicata.nome
