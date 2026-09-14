"""Ferramenta que tem tela própria: a central sobe a janela dela e leva junto.

O Apurabot já tinha uma janela inteira — conferência, registro por
estabelecimento, série do ano — antes de a central existir. Reescrevê-la aqui
seria refazer o que funciona e está homologado contra a apuração real.

Então a central não a reescreve: ela **sobe o servidor do Apurabot** numa porta
própria e manda o navegador para lá. O Apurabot não sabe que a central existe,
e continua abrindo sozinho por `Apurabot.bat`, como sempre.

É provisório por escolha, não por descuido: quando a segunda ferramenta com
tela própria aparecer, o certo passa a ser a central hospedar as duas telas.
Enquanto é uma só, isto custa vinte linhas e não mexe no que está de pé.
"""
from __future__ import annotations

import threading
from dataclasses import dataclass
from typing import Any


@dataclass
class Janela:
    """Uma janela de ferramenta rodando ao lado da central."""

    endereco: str
    _servidor: Any

    def encerrar(self) -> None:
        self._servidor.shutdown()
        self._servidor.server_close()


def abrir_apurabot() -> Janela:
    from apurabot.web import servidor as apurabot

    sessao = apurabot.Sessao()
    manipulador = type(
        "ManipuladorDaCentral", (apurabot.Manipulador,), {"sessao": sessao}
    )
    servidor = apurabot.Servidor(("127.0.0.1", 0), manipulador)
    threading.Thread(target=servidor.serve_forever, daemon=True).start()

    def _ao_encerrar() -> None:
        # O botão "Encerrar" da janela do Apurabot avisa por este evento.
        sessao.encerrar.wait()
        servidor.shutdown()
        sessao.limpar()

    threading.Thread(target=_ao_encerrar, daemon=True).start()

    porta = servidor.server_address[1]
    return Janela(f"http://127.0.0.1:{porta}/?chave={sessao.chave}", servidor)


#: Quem sabe abrir tela própria, por id de ferramenta.
ABERTURAS = {"apurabot": abrir_apurabot}
