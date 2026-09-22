"""A janela da central — um servidor na própria máquina, aberto no navegador.

Por que assim, e não um programa instalado: a máquina do time fiscal é
corporativa e sem elevação de administrador. Um `.exe` novo e sem assinatura é
barrado pela política de segurança; o Python que já está na máquina é programa
aprovado, e o navegador também. Então a interface vem do navegador, servida por
`127.0.0.1` numa porta que o sistema escolhe. O argumento inteiro está em
`apurabot/src/apurabot/web/servidor.py`, onde ele foi decidido.

O que isso garante:

* **nada é instalado** — nenhum binário novo, nenhum privilégio;
* **o dado não sai da máquina** — só se aceita conexão de `127.0.0.1`, os
  arquivos enviados vivem numa pasta temporária e somem no encerramento;
* **a janela é a interface** — escolher a ferramenta, largar o arquivo, ver o
  resultado, baixar a planilha.

Como outra pessoa logada na mesma máquina também alcança `127.0.0.1`, cada
sessão nasce com uma chave aleatória na URL; requisição sem ela é recusada.
"""
from __future__ import annotations

import http.server
import json
import secrets
import shutil
import socketserver
import tempfile
import threading
import traceback
import webbrowser
from dataclasses import asdict
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from . import __version__, ferramentas, janelas

PAGINA = Path(__file__).resolve().parent / "pagina.html"

#: Teto de cada arquivo enviado. Um lote mensal de XML fica muito abaixo disso.
LIMITE_POR_ARQUIVO = 500 * 1024 * 1024

#: Teto do que uma execução aceita receber somado.
LIMITE_DA_EXECUCAO = 2 * 1024 * 1024 * 1024


class Sessao:
    """O estado de uma janela aberta: a chave, os arquivos, o que foi gerado."""

    def __init__(self) -> None:
        self.chave = secrets.token_urlsafe(24)
        self.pasta = Path(tempfile.mkdtemp(prefix="hinove-"))
        self.recebidos: dict[str, list[Path]] = {}
        self.gerado: Path | None = None
        self.janelas: dict[str, janelas.Janela] = {}
        self.encerrar = threading.Event()

    def recebidos_de(self, ferramenta: str) -> list[Path]:
        return self.recebidos.setdefault(ferramenta, [])

    def remover(self, ferramenta: str, indice: int) -> bool:
        recebidos = self.recebidos_de(ferramenta)
        if not 0 <= indice < len(recebidos):
            return False
        caminho = recebidos.pop(indice)
        shutil.rmtree(caminho.parent, ignore_errors=True)
        return True

    def esquecer(self, ferramenta: str) -> None:
        for caminho in self.recebidos.pop(ferramenta, []):
            shutil.rmtree(caminho.parent, ignore_errors=True)

    def limpar(self) -> None:
        for janela in self.janelas.values():
            janela.encerrar()
        shutil.rmtree(self.pasta, ignore_errors=True)


def _nome_seguro(nome: str) -> str:
    """Só o nome do arquivo, nunca um caminho.

    O nome viaja para dentro da planilha (o DiXML registra a origem de cada
    linha), então ele é preservado — mas nada de pasta, nada de `..`.
    """
    limpo = Path(nome.replace("\\", "/")).name.strip()
    return limpo if limpo and limpo not in (".", "..") else "arquivo"


class Manipulador(http.server.BaseHTTPRequestHandler):
    server_version = "CentralFiscalHinove"
    sessao: Sessao                      # injetado pelo servidor

    # A janela do navegador é a interface; o terminal atrás dela fica limpo.
    def log_message(self, formato, *args) -> None:  # noqa: A002
        return

    # -- rotas -------------------------------------------------------------

    def do_GET(self) -> None:  # noqa: N802
        rota = urlparse(self.path)
        if not self._autorizado(rota):
            return
        consulta = parse_qs(rota.query)
        if rota.path == "/":
            self._enviar(200, "text/html; charset=utf-8", PAGINA.read_bytes())
        elif rota.path == "/ferramentas":
            self._json(200, {
                "versao": __version__,
                "ferramentas": ferramentas.catalogo(),
            })
        elif rota.path == "/abrir":
            self._abrir_janela(consulta)
        elif rota.path == "/configuracao":
            self._ler_configuracao(consulta)
        elif rota.path == "/conferir":
            self._conferir(consulta)
        elif rota.path == "/remover":
            self._remover(consulta)
        elif rota.path == "/limpar":
            self.sessao.esquecer((consulta.get("ferramenta") or [""])[0])
            self._json(200, {"ok": True})
        elif rota.path == "/baixar":
            self._baixar()
        elif rota.path == "/encerrar":
            self._json(200, {"ok": True})
            self.sessao.encerrar.set()
        else:
            self._enviar(404, "text/plain; charset=utf-8", b"nao encontrado")

    def do_POST(self) -> None:  # noqa: N802
        rota = urlparse(self.path)
        if not self._autorizado(rota):
            return
        consulta = parse_qs(rota.query)
        if rota.path == "/enviar":
            self._receber(consulta)
        elif rota.path == "/executar":
            self._executar(consulta)
        elif rota.path == "/configuracao":
            self._gravar_configuracao(consulta)
        else:
            self._enviar(404, "text/plain; charset=utf-8", b"nao encontrado")

    # -- guarda ------------------------------------------------------------

    def _autorizado(self, rota) -> bool:
        """Confere a origem da conexão e a chave da sessão."""
        if self.client_address[0] not in ("127.0.0.1", "::1"):
            self._enviar(403, "text/plain; charset=utf-8", b"somente local")
            return False
        chave = (parse_qs(rota.query).get("chave") or [""])[0]
        if not secrets.compare_digest(chave, self.sessao.chave):
            self._enviar(403, "text/plain; charset=utf-8", b"chave invalida")
            return False
        return True

    def _ferramenta(self, consulta: dict) -> ferramentas.Ferramenta | None:
        achada = ferramentas.achar((consulta.get("ferramenta") or [""])[0])
        if achada is None:
            self._json(404, {"erro": "Ferramenta desconhecida."})
        return achada

    # -- tela própria ------------------------------------------------------

    def _abrir_janela(self, consulta: dict) -> None:
        ferramenta = self._ferramenta(consulta)
        if ferramenta is None:
            return
        abertura = janelas.ABERTURAS.get(ferramenta.id)
        if abertura is None:
            self._json(400, {"erro": f"{ferramenta.nome} não abre janela própria."})
            return
        janela = self.sessao.janelas.get(ferramenta.id)
        if janela is None:
            try:
                janela = abertura()
            except Exception as erro:                 # noqa: BLE001
                self._json(400, {"erro": (
                    f"Não consegui abrir o {ferramenta.nome}: {erro}"
                )})
                return
            self.sessao.janelas[ferramenta.id] = janela
        self._json(200, {"endereco": janela.endereco})

    # -- configuração da ferramenta ----------------------------------------

    def _ler_configuracao(self, consulta: dict) -> None:
        ferramenta = self._ferramenta(consulta)
        if ferramenta is None:
            return
        if ferramenta.configuracao is None:
            self._json(400, {"erro": f"{ferramenta.nome} não tem o que configurar."})
            return
        try:
            secoes = ferramenta.configuracao.secoes()
            dados = ferramenta.configuracao.ler()
        except Exception as erro:                 # noqa: BLE001
            self._json(400, {"erro": self._explicar(erro, ferramenta)})
            return
        self._json(200, {
            "resumo": ferramenta.configuracao.resumo,
            "secoes": [
                {
                    "id": s.id, "titulo": s.titulo, "explicacao": s.explicacao,
                    "fixa": s.fixa,
                    "campos": [asdict(c) for c in s.campos],
                }
                for s in secoes
            ],
            "dados": dados,
        })

    def _gravar_configuracao(self, consulta: dict) -> None:
        ferramenta = self._ferramenta(consulta)
        if ferramenta is None:
            return
        if ferramenta.configuracao is None:
            self._json(400, {"erro": f"{ferramenta.nome} não tem o que configurar."})
            return
        try:
            tamanho = int(self.headers.get("Content-Length") or 0)
            corpo = json.loads(self.rfile.read(tamanho) or b"{}")
        except (ValueError, json.JSONDecodeError):
            self._json(400, {"erro": "não entendi o que a tela mandou."})
            return

        quem = str(corpo.get("responsavel") or "").strip()
        try:
            gravou, problemas = ferramenta.configuracao.gravar(
                corpo.get("dados") or {}, quem)
        except Exception as erro:                 # noqa: BLE001
            self._json(400, {"erro": self._explicar(erro, ferramenta)})
            return
        self._json(200, {"gravou": gravou, "problemas": problemas})

    # -- receber arquivo ---------------------------------------------------

    def _receber(self, consulta: dict) -> None:
        ferramenta = self._ferramenta(consulta)
        if ferramenta is None:
            return
        if ferramenta.entrada is None:
            self._json(400, {"erro": f"{ferramenta.nome} não recebe arquivo."})
            return

        nome = _nome_seguro((consulta.get("nome") or ["arquivo"])[0])
        extensao = Path(nome).suffix.lower()
        if extensao not in ferramenta.entrada.extensoes:
            esperadas = ", ".join(ferramenta.entrada.extensoes)
            self._json(400, {"erro": (
                f"O arquivo {nome!r} não é do tipo que o {ferramenta.nome} lê. "
                f"Esperado {esperadas}."
            )})
            return

        try:
            tamanho = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            tamanho = 0
        if tamanho <= 0:
            self._json(400, {"erro": f"O arquivo {nome!r} chegou vazio."})
            return
        if tamanho > LIMITE_POR_ARQUIVO:
            self._json(400, {"erro": (
                f"{nome} tem {tamanho / 1048576:.0f} MB, acima do limite de "
                f"{LIMITE_POR_ARQUIVO // 1048576} MB por arquivo."
            )})
            return

        recebidos = self.sessao.recebidos_de(ferramenta.id)
        ja_recebido = sum(c.stat().st_size for c in recebidos if c.is_file())
        if ja_recebido + tamanho > LIMITE_DA_EXECUCAO:
            self._json(400, {"erro": (
                "Os arquivos somados passam de "
                f"{LIMITE_DA_EXECUCAO // 1048576} MB. Rode em duas levas."
            )})
            return

        # Cada arquivo na sua própria subpasta: dois pacotes podem ter o mesmo
        # nome, e o nome precisa ser preservado — ele vai para dentro da saída.
        # Subpasta de nome único, e não numerada: arquivo pode ser removido
        # antes de rodar, e o próximo não pode cair na pasta de outro.
        base = self.sessao.pasta / ferramenta.id
        base.mkdir(parents=True, exist_ok=True)
        pasta = Path(tempfile.mkdtemp(prefix="anexo-", dir=base))
        destino = pasta / nome
        with destino.open("wb") as arquivo:
            restante = tamanho
            while restante > 0:
                pedaco = self.rfile.read(min(1024 * 256, restante))
                if not pedaco:
                    break
                arquivo.write(pedaco)
                restante -= len(pedaco)

        recebidos.append(destino)
        self._json(200, {
            "ok": True,
            "arquivos": [c.name for c in recebidos],
        })

    # -- conferir o que já foi anexado --------------------------------------

    def _quadro(self, ferramenta) -> dict:
        """A conferência dos anexos, como a página a desenha."""
        conferencia = ferramenta.conferir(self.sessao.recebidos_de(ferramenta.id))
        return {
            "documentos": [
                {"id": d.id, "rotulo": d.rotulo, "obrigatorio": d.obrigatorio,
                 "estado": d.estado, "anexos": [asdict(a) for a in d.anexos]}
                for d in conferencia.documentos
            ],
            "soltos": [asdict(a) for a in conferencia.soltos],
            "pendencias": conferencia.pendencias,
            "pronta": conferencia.pronta,
        }

    def _conferir(self, consulta: dict) -> None:
        ferramenta = self._ferramenta(consulta)
        if ferramenta is None:
            return
        if ferramenta.conferir is None:
            self._json(400, {"erro": f"{ferramenta.nome} não confere anexos."})
            return
        try:
            self._json(200, self._quadro(ferramenta))
        except Exception as erro:                     # noqa: BLE001
            self._json(400, {"erro": self._explicar(erro, ferramenta)})

    def _remover(self, consulta: dict) -> None:
        ferramenta = self._ferramenta(consulta)
        if ferramenta is None:
            return
        try:
            indice = int((consulta.get("indice") or ["-1"])[0])
        except ValueError:
            indice = -1
        if not self.sessao.remover(ferramenta.id, indice):
            self._json(400, {"erro": "Esse arquivo já não está na lista."})
            return
        self._json(200, {"ok": True})

    # -- executar ----------------------------------------------------------

    def _executar(self, consulta: dict) -> None:
        ferramenta = self._ferramenta(consulta)
        if ferramenta is None:
            return
        if ferramenta.executar is None:
            self._json(400, {"erro": f"{ferramenta.nome} ainda não roda por aqui."})
            return

        recebidos = self.sessao.recebidos_de(ferramenta.id)
        if not recebidos:
            self._json(400, {"erro": "Nenhum arquivo foi enviado."})
            return

        # Com conferência, o que falta é dito antes de rodar — e os anexos
        # ficam: a pessoa acrescenta o que faltou sem reenviar o resto.
        if ferramenta.conferir is not None:
            try:
                pendencias = ferramenta.conferir(recebidos).pendencias
            except Exception as erro:                 # noqa: BLE001
                self._json(400, {"erro": self._explicar(erro, ferramenta)})
                return
            if pendencias:
                self._json(400, {"erro": "Ainda não dá para gerar:\n\n  "
                                          + "\n  ".join(pendencias)})
                return

        saida = self.sessao.pasta / ferramenta.id / "saida"
        try:
            resultado = ferramenta.executar(recebidos, saida)
        except Exception as erro:                     # noqa: BLE001
            if ferramenta.conferir is None:
                self.sessao.esquecer(ferramenta.id)
            self._json(400, {"erro": self._explicar(erro, ferramenta)})
            return
        self.sessao.esquecer(ferramenta.id)

        self.sessao.gerado = resultado.planilha
        self._json(200, {
            "titulo": resultado.titulo,
            "fichas": [asdict(f) for f in resultado.fichas],
            "listas": [asdict(lista) for lista in resultado.listas],
            "planilha": resultado.planilha.name if resultado.planilha else None,
        })

    def _explicar(self, erro: BaseException, ferramenta) -> str:
        """A mensagem que a pessoa lê quando algo falha."""
        conhecidos = ("PacoteGrandeDemais", "LayoutInvalido")
        if type(erro).__name__ in conhecidos:
            return str(erro)
        if isinstance(erro, FileNotFoundError):
            return "Arquivo não encontrado."
        traceback.print_exc()
        return (
            f"{type(erro).__name__}: {erro}\n\n"
            f"Se os arquivos são os certos, isto é defeito do {ferramenta.nome} "
            "— guarde esta mensagem."
        )

    # -- baixar ------------------------------------------------------------

    def _baixar(self) -> None:
        gerado = self.sessao.gerado
        if gerado is None or not gerado.is_file():
            self._enviar(404, "text/plain; charset=utf-8", b"nada gerado ainda")
            return
        corpo = gerado.read_bytes()
        self.send_response(200)
        self.send_header(
            "Content-Type",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        self.send_header("Content-Disposition", f'attachment; filename="{gerado.name}"')
        self.send_header("Content-Length", str(len(corpo)))
        self.end_headers()
        self.wfile.write(corpo)

    # -- resposta ----------------------------------------------------------

    def _enviar(self, codigo: int, tipo: str, corpo: bytes) -> None:
        self.send_response(codigo)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(corpo)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(corpo)

    def _json(self, codigo: int, dados: dict) -> None:
        corpo = json.dumps(dados, ensure_ascii=False).encode("utf-8")
        self._enviar(codigo, "application/json; charset=utf-8", corpo)


class Servidor(socketserver.ThreadingTCPServer):
    """Escuta só em 127.0.0.1, numa porta que o sistema escolhe."""

    daemon_threads = True
    allow_reuse_address = True


def abrir(porta: int = 0, navegador: bool = True) -> int:
    """Sobe a janela e só volta quando ela for encerrada."""
    sessao = Sessao()
    manipulador = type("ManipuladorDaSessao", (Manipulador,), {"sessao": sessao})

    with Servidor(("127.0.0.1", porta), manipulador) as servidor:
        endereco = f"http://127.0.0.1:{servidor.server_address[1]}/?chave={sessao.chave}"
        print("\nCentral de Ferramentas Fiscais aberta no navegador.\n")
        print(f"  {endereco}\n")
        print("Se a janela não abrir sozinha, copie o endereço acima.")
        print("Para encerrar: feche esta janela preta ou tecle Ctrl+C.\n")

        if navegador:
            threading.Timer(0.5, webbrowser.open, args=(endereco,)).start()

        threading.Thread(target=servidor.serve_forever, daemon=True).start()
        try:
            sessao.encerrar.wait()
        except KeyboardInterrupt:
            pass
        finally:
            servidor.shutdown()
            sessao.limpar()
            print("Central encerrada. Nada ficou na máquina.\n")
    return 0
