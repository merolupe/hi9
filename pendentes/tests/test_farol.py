"""O farol de emoji — e o vazio que não é "Não"."""
from __future__ import annotations

from pendentes.farol import (FAROL_DE_PEDIDO, SEMAFORO_DE_SERVICOS,
                             farol_de_pedido, semaforo, tabela_de)

VERDE = '<div style="text-align:center"><span>&#128994;</span></div>'
VERMELHO = '<div style="text-align:center"><span>&#128308;</span></div>'
AMARELO = '<div style="text-align:center"><span>&#128993;</span></div>'
VAZIO = '<div style="text-align:center"><span>&#9711;</span></div>'


def test_o_farol_de_pedido_tem_tres_estados():
    assert farol_de_pedido(VERDE) == "Sim"
    assert farol_de_pedido(VERMELHO) == "Não"
    assert farol_de_pedido("") == ""


def test_celula_vazia_nao_e_nao():
    """Vazio significa nota SEM pedido vinculado — estado distinto de recusa."""
    assert farol_de_pedido("") == ""
    assert farol_de_pedido("") != "Não"


def test_o_farol_de_pedido_engole_qualquer_outra_coisa():
    """Mercadorias devolve vazio para o que não reconhece — fiel ao VBA."""
    assert farol_de_pedido("aguardando") == ""
    assert farol_de_pedido(AMARELO) == ""


def test_o_semaforo_de_servicos_tem_os_cinco_ramos():
    assert semaforo(VERDE) == "Sim"
    assert semaforo(VERMELHO) == "Nao"
    assert semaforo(AMARELO) == "Parcial"
    assert semaforo(VAZIO) == ""
    assert semaforo("<div></div>") == ""
    assert semaforo("  Pendente  ") == "Pendente"


def test_a_ordem_da_tabela_decide_quando_a_celula_tem_dois_codigos():
    misturado = f"{VERMELHO}{VERDE}"
    assert semaforo(misturado) == "Sim"          # 128994 vem primeiro na tabela


def test_a_tabela_pode_vir_do_parametro():
    """Trocar o ícone do semáforo troca o número — por isso é parâmetro."""
    nova = tabela_de([{"codigo": "9989", "rotulo": "Sim"}])
    assert semaforo("<span>&#9989;</span>", nova) == "Sim"
    assert semaforo(VERDE, nova) == ""           # o código antigo não vale mais


def test_as_tabelas_de_fabrica_tem_o_tamanho_que_o_vba_tinha():
    assert len(FAROL_DE_PEDIDO) == 2
    assert len(SEMAFORO_DE_SERVICOS) == 4
