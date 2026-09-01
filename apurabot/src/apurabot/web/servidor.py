"""A janela do Apurabot — um servidor na própria máquina, aberto no navegador.

Por que assim, e não um executável:

A máquina do time fiscal é corporativa e sem elevação de administrador. Um
`.exe` novo e sem assinatura é barrado pela política de segurança — foi o que
aconteceu com o comando instalado por `pip`. Já o Python que está na máquina é
programa aprovado, e roda.

Então a interface gráfica não vem de um programa novo: vem do **navegador**, que
também já está aprovado. O Python abre um servidor em `127.0.0.1`, numa porta
que o próprio sistema operacional escolhe, e manda o navegador abrir a página.

O que isso garante:

* **nada é instalado** — nenhum binário novo, nenhum privilégio;
* **o dado não sai da máquina** — o servidor só aceita conexão de `127.0.0.1`,
  o arquivo enviado vive numa pasta temporária e é apagado no encerramento;
* **a janela é a interface** — arrastar o arquivo, ver o resultado, baixar a
  planilha. Sem caminho para digitar, sem pasta com nome fixo.

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
import webbrowser
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from ..apuracao import apurar
from ..base_tratada import tratar
from ..ingestao import LayoutInvalido
from ..erros import FALTA_DE_PARAMETRO, ONDE_CADASTRAR
from ..nucleo import registro as reg
from ..saida import escrever
from . import painel

PAGINA = Path(__file__).resolve().parent / "pagina.html"

#: Extensões que o leitor do Livro Fiscal reconhece.
EXTENSOES = (".xls", ".xlsx", ".xlsm")

#: Teto do arquivo enviado. O Livro de uma competência fica na casa das dezenas
#: de MB; acima disso é engano de arquivo, não Livro Fiscal.
LIMITE_BYTES = 200 * 1024 * 1024


class Sessao:
    """O estado de uma janela aberta: a chave, a pasta temporária, o resultado."""

    def __init__(self) -> None:
        self.chave = secrets.token_urlsafe(24)
        self.pasta = Path(tempfile.mkdtemp(prefix="apurabot-"))
        self.planilha: Path | None = None
        self.encerrar = threading.Event()

    def limpar(self) -> None:
        shutil.rmtree(self.pasta, ignore_errors=True)


def _erro_amigavel(erro: BaseException) -> str:
    if isinstance(erro, LayoutInvalido):
        return str(erro)
    if isinstance(erro, FileNotFoundError):
        return "Arquivo não encontrado."
    if isinstance(erro, FALTA_DE_PARAMETRO):
        return (
            f"{erro}\n\n"
            "Isto não é defeito da ferramenta: é uma regra que ainda não foi "
            f"cadastrada. {ONDE_CADASTRAR} Depois de cadastrar, é só arrastar "
            "o livro de novo."
        )
    return (
        f"{type(erro).__name__}: {erro}\n\n"
        "Se o arquivo é o Livro Fiscal correto, isto é defeito da ferramenta — "
        "guarde esta mensagem."
    )


class Manipulador(http.server.BaseHTTPRequestHandler):
    server_version = "Apurabot"
    sessao: Sessao                      # injetado pelo servidor

    # A janela do navegador é a interface; o terminal atrás dela fica limpo.
    def log_message(self, formato, *args) -> None:  # noqa: A002
        return

    # -- rotas -------------------------------------------------------------

    def do_GET(self) -> None:  # noqa: N802
        rota = urlparse(self.path)
        if rota.path == "/":
            if not self._autorizado(rota):
                return
            self._enviar(200, "text/html; charset=utf-8", PAGINA.read_bytes())
        elif rota.path == "/baixar":
            if not self._autorizado(rota):
                return
            self._baixar()
        elif rota.path == "/encerrar":
            if not self._autorizado(rota):
                return
            self._json(200, {"ok": True})
            self.sessao.encerrar.set()
        else:
            self._enviar(404, "text/plain; charset=utf-8", b"nao encontrado")

    def do_POST(self) -> None:  # noqa: N802
        rota = urlparse(self.path)
        if rota.path != "/apurar":
            self._enviar(404, "text/plain; charset=utf-8", b"nao encontrado")
            return
        if not self._autorizado(rota):
            return
        self._apurar(parse_qs(rota.query))

    # -- guarda ------------------------------------------------------------

    def _autorizado(self, rota) -> bool:
        """Confere a chave da sessão e a origem da conexão."""
        if self.client_address[0] not in ("127.0.0.1", "::1"):
            self._enviar(403, "text/plain; charset=utf-8", b"somente local")
            return False
        chave = (parse_qs(rota.query).get("chave") or [""])[0]
        if not secrets.compare_digest(chave, self.sessao.chave):
            self._enviar(403, "text/plain; charset=utf-8", b"chave invalida")
            return False
        return True

    # -- apuração ----------------------------------------------------------

    def _apurar(self, consulta: dict[str, list[str]]) -> None:
        nome = (consulta.get("nome") or ["livro.xls"])[0]
        sufixo = Path(nome).suffix.lower()
        if sufixo not in EXTENSOES:
            self._json(400, {"erro": (
                f"O arquivo {nome!r} não é uma planilha que o Apurabot leia. "
                f"Esperado {', '.join(EXTENSOES)}."
            )})
            return

        try:
            tamanho = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            tamanho = 0
        if tamanho <= 0:
            self._json(400, {"erro": "O arquivo chegou vazio."})
            return
        if tamanho > LIMITE_BYTES:
            self._json(400, {"erro": (
                f"O arquivo tem {tamanho / 1048576:.0f} MB, acima do limite de "
                f"{LIMITE_BYTES // 1048576} MB."
            )})
            return

        entrada = self.sessao.pasta / f"livro{sufixo}"
        with entrada.open("wb") as destino:
            restante = tamanho
            while restante > 0:
                pedaco = self.rfile.read(min(1024 * 256, restante))
                if not pedaco:
                    break
                destino.write(pedaco)
                restante -= len(pedaco)

        try:
            resposta = self._processar(entrada, nome)
        except Exception as erro:                     # noqa: BLE001
            self._json(400, {"erro": _erro_amigavel(erro)})
            return
        finally:
            entrada.unlink(missing_ok=True)

        self._json(200, resposta)

    def _processar(self, entrada: Path, nome_original: str) -> dict:
        base = tratar(entrada)
        apuracao = apurar(base)
        registros = reg.montar(apuracao, base.parametros)
        if len(registros) > 1:
            registros = registros + [reg.totalizador(registros, base.competencia)]

        planilha = self.sessao.pasta / f"Apuracao_{base.competencia}.xlsx"
        escrever(base, planilha, apuracao)
        self.sessao.planilha = planilha

        dados = painel.montar(base, apuracao, registros)
        dados["arquivo"] = nome_original
        dados["planilha"] = planilha.name
        return dados

    def _baixar(self) -> None:
        planilha = self.sessao.planilha
        if planilha is None or not planilha.is_file():
            self._enviar(404, "text/plain; charset=utf-8", b"nada gerado ainda")
            return
        corpo = planilha.read_bytes()
        self.send_response(200)
        self.send_header(
            "Content-Type",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        self.send_header(
            "Content-Disposition", f'attachment; filename="{planilha.name}"'
        )
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
        print("\nApurabot aberto no navegador.\n")
        print(f"  {endereco}\n")
        print("Se a janela não abrir sozinha, copie o endereço acima.")
        print("Para encerrar: feche esta janela preta ou tecle Ctrl+C.\n")

        if navegador:
            threading.Timer(0.5, webbrowser.open, args=(endereco,)).start()

        thread = threading.Thread(target=servidor.serve_forever, daemon=True)
        thread.start()
        try:
            sessao.encerrar.wait()
        except KeyboardInterrupt:
            pass
        finally:
            servidor.shutdown()
            sessao.limpar()
            print("Apurabot encerrado. Nada ficou na máquina.\n")
    return 0
