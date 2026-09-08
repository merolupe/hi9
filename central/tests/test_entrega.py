"""O que faz o conjunto ser entregável: rodar sem instalar nada.

Baixar a pasta e dar dois cliques tem que bastar — para a central e para
cada ferramenta dentro dela. Se alguém acrescentar uma dependência que precise
de instalação, estes testes quebram antes de a pessoa descobrir na máquina dela.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
import zipfile
from pathlib import Path

from conftest import NOTA

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


def test_verificar_aprova_este_python_sem_instalacao():
    """É o que o Hinove.bat pergunta antes de escolher o interpretador."""
    r = _sem_pacotes_instalados(
        "import runpy\n"
        "sys.argv = ['verificar.py']\n"
        "runpy.run_path('verificar.py', run_name='__main__')\n"
    )
    assert r.returncode == 0, r.stderr + r.stdout


def test_a_central_carrega_as_ferramentas_sem_nenhum_pacote_instalado():
    r = _sem_pacotes_instalados(
        "sys.path.insert(0, 'central/src')\n"
        "import central, apurabot, dixml, openpyxl\n"
        "assert 'vendor' in openpyxl.__file__, openpyxl.__file__\n"
        "print('ok')\n"
    )
    assert r.returncode == 0, r.stderr
    assert "ok" in r.stdout


def test_o_lote_vira_planilha_sem_instalacao(tmp_path):
    """A prova de ponta a ponta do DiXML, pelo mesmo arquivo que o .bat chama."""
    lote = tmp_path / "lote.zip"
    with zipfile.ZipFile(lote, "w") as zf:
        zf.writestr("nota.xml", NOTA)

    r = _sem_pacotes_instalados(
        "import runpy\n"
        f"sys.argv = ['rodar.py', 'dixml', {str(lote)!r}, '--saida', {str(tmp_path)!r}]\n"
        "runpy.run_path('rodar.py', run_name='__main__')\n"
    )
    assert r.returncode == 0, r.stderr
    gerados = list(tmp_path.glob("DiXML_*.xlsx"))
    assert len(gerados) == 1
    assert gerados[0].stat().st_size > 4_000


def test_a_janela_e_um_arquivo_dentro_do_pacote():
    """Se a página sair do pacote, a central abre em branco na máquina do usuário."""
    from central.servidor import PAGINA

    assert PAGINA.is_file()
    assert PAGINA.parent.name == "central"


def test_nenhuma_ferramenta_importa_outra():
    """Quem costura é a central. Ferramenta que conhece ferramenta vira novelo."""
    for pacote, vizinhos in (("apurabot", ("dixml", "central")),
                             ("dixml", ("apurabot", "central"))):
        for arquivo in (RAIZ / pacote / "src").rglob("*.py"):
            codigo = arquivo.read_text(encoding="utf-8")
            for vizinho in vizinhos:
                achado = re.search(
                    rf"^\s*(import\s+{vizinho}\b|from\s+{vizinho}[\s.])",
                    codigo, re.MULTILINE,
                )
                assert achado is None, f"{arquivo} importa {vizinho}"
