"""O que faz a ferramenta ser entregável: rodar sem instalar nada.

Baixar a pasta e dar dois cliques tem que bastar. Estes testes travam isso —
se alguém tirar as bibliotecas embarcadas ou reintroduzir um passo de
instalação, eles quebram antes de a pessoa descobrir na máquina dela.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

from apurabot._dependencias import EMBARCADAS, VENDOR

RAIZ = Path(__file__).resolve().parents[2]


def _sem_pacotes_instalados(codigo: str) -> subprocess.CompletedProcess:
    """Roda um trecho num Python que não enxerga site-packages nenhum.

    É a simulação da máquina do time fiscal, onde `pip install` não pegou.
    """
    limpeza = (
        "import sys\n"
        "sys.path = [p for p in sys.path\n"
        "            if 'site-packages' not in p and 'dist-packages' not in p]\n"
    )
    return subprocess.run(
        [sys.executable, "-S", "-c", limpeza + codigo],
        capture_output=True, text=True, cwd=RAIZ, timeout=300,
        env={**os.environ, "PYTHONNOUSERSITE": "1", "PYTHONPATH": ""},
    )


# -- as bibliotecas estão aqui ---------------------------------------------

def test_as_bibliotecas_viajam_junto_do_codigo():
    assert VENDOR.is_dir(), "a pasta vendor sumiu"
    for nome in EMBARCADAS:
        assert (VENDOR / nome).is_dir(), f"falta {nome} em vendor/"


def test_nada_embarcado_e_compilado():
    """Extensão em C amarraria a entrega a um sistema e a uma versão do Python.

    É o que faria a pasta parar de funcionar ao trocar de máquina — justamente
    o problema que embarcar as bibliotecas veio resolver.
    """
    compilados = [
        p.relative_to(VENDOR)
        for p in VENDOR.rglob("*")
        if p.suffix in (".so", ".pyd", ".dll", ".dylib")
    ]
    assert not compilados, f"vendor traz binário: {compilados}"


def test_a_procedencia_de_cada_biblioteca_esta_registrada():
    leiame = (VENDOR / "LEIA-ME.md").read_text(encoding="utf-8")
    for nome in EMBARCADAS:
        assert nome in leiame, f"{nome} não está documentada em vendor/LEIA-ME.md"
    for licenca in ("MIT", "BSD"):
        assert licenca in leiame


# -- e funcionam sem instalação --------------------------------------------

def test_o_apurabot_importa_sem_nenhum_pacote_instalado():
    r = _sem_pacotes_instalados(
        "sys.path.insert(0, 'apurabot/src')\n"
        "import apurabot, yaml, openpyxl, xlrd\n"
        "assert 'vendor' in yaml.__file__, yaml.__file__\n"
        "print('ok')\n"
    )
    assert r.returncode == 0, r.stderr
    assert "ok" in r.stdout


def test_verificar_aprova_este_python_sem_instalacao():
    """É o que o Apurabot.bat pergunta antes de escolher o interpretador."""
    r = _sem_pacotes_instalados(
        "import runpy\n"
        "sys.argv = ['verificar.py']\n"
        "runpy.run_path('verificar.py', run_name='__main__')\n"
    )
    assert r.returncode == 0, r.stderr + r.stdout


def test_o_livro_e_apurado_sem_instalacao(arquivo_julho, tmp_path):
    """A prova de ponta a ponta: da leitura do livro à planilha gravada."""
    r = _sem_pacotes_instalados(
        "import runpy\n"
        f"sys.argv = ['rodar.py', 'apurar', {str(arquivo_julho)!r},"
        f" '--saida', {str(tmp_path)!r}]\n"
        "runpy.run_path('rodar.py', run_name='__main__')\n"
    )
    assert r.returncode == 0, r.stderr
    gerados = list(tmp_path.glob("Apuracao_*.xlsx"))
    assert len(gerados) == 1
    assert gerados[0].stat().st_size > 100_000


# -- o lançador não pode voltar a adivinhar --------------------------------

def test_o_lancador_pergunta_ao_python_em_vez_de_escolher_pelo_nome():
    """Escolher `py -3` por vir primeiro na lista foi o defeito de antes."""
    bat = (RAIZ / "Apurabot.bat").read_text(encoding="cp1252")
    assert "verificar.py" in bat
    for candidato in ("python", "py -3"):
        assert f'"{candidato}"' in bat


def test_a_documentacao_nao_manda_mais_instalar_as_bibliotecas():
    """O passo do `pip` falhou duas vezes na máquina real. Ele saiu.

    Citar `pip install` ao explicar o histórico, ou ao instalar o `pytest` para
    quem mexe no código, continua valendo — o que não pode voltar é mandar o
    time fiscal instalar openpyxl, xlrd ou PyYAML.
    """
    for doc in ("docs/apurabot/07-como-rodar.md",
                "docs/apurabot/08-roteiro-de-teste.md",
                "README.md"):
        texto = (RAIZ / doc).read_text(encoding="utf-8")
        for biblioteca in ("openpyxl", "xlrd", "PyYAML"):
            assert f"install --user {biblioteca}" not in texto, doc
            assert f"install {biblioteca}" not in texto, doc


@pytest.mark.parametrize("arquivo", ["Apurabot.bat", "rodar.py", "verificar.py"])
def test_os_tres_arquivos_de_entrada_estao_na_raiz(arquivo):
    assert (RAIZ / arquivo).is_file()
