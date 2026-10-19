"""Onde moram os dados do time — **fora** da pasta do código.

Cada versão nova chega como um ZIP extraído numa pasta nova. Enquanto os dados
moravam dentro da pasta do código (`dados/` e `competencias/`), cada versão
nova começava vazia, e alguém precisava carregar livro de classificação,
parâmetros, bases e apurações de uma pasta para a outra.

Agora os dados moram numa pasta fixa por usuário, e o código fica descartável:

    Documentos\\Hinove\\
        dados\\          livro, parâmetros, bases de conhecimento, regras
        competencias\\   série do Apurabot, padrões-ouro

A mesma árvore de antes, só que fora do código.

### Quem decide, e como as ferramentas ficam sabendo

A Central, e só ela — regra nº 7: nenhuma ferramenta importa outra. Ela
resolve a pasta, migra o que houver, e publica o caminho na variável de
ambiente `HINOVE_DADOS`. Cada ferramenta só lê a variável; sem ela, usa a
pasta do código, como sempre usou. É por isso que os testes e quem chama uma
ferramenta direto, sem a Central, continuam funcionando igual.

Quem quiser os dados em outro lugar (uma pasta de rede, por exemplo) define
`HINOVE_DADOS` antes de abrir a Central: a variável já definida é respeitada.

### A migração

Na primeira abertura de uma versão com esta mudança: se a pasta fixa ainda não
tem `dados` (ou `competencias`) e a pasta do código tem, o conteúdo é
**copiado** — nunca movido. O original fica onde está, e a tela diz o que foi
copiado. Depois disso quem manda é a pasta fixa; uma pasta `dados` que
reapareça na pasta do código é ignorada, e a tela avisa.

Se a cópia falhar, a Central **não** troca de pasta: continua na do código e
diz por quê. Trocar para uma pasta vazia seria abrir sem o trabalho do time.
"""
from __future__ import annotations

import os
import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path

from ._dependencias import RAIZ

#: A variável que as ferramentas leem. Aponta para a pasta que contém
#: `dados/` e `competencias/`.
VARIAVEL = "HINOVE_DADOS"

#: O que é dado do time, e por isso sai da pasta do código.
PASTAS = ("dados", "competencias")

NOME_DA_PASTA = "Hinove"

LEIA_ME = """\
Dados das ferramentas fiscais da Hinove (Central Fiscal)
========================================================

Esta pasta guarda o que o time produziu e cadastrou: livro de classificação,
parâmetros, bases de conhecimento, histórico do Portal de Compras, regras do
Fiscalbot e a série do Apurabot.

Ela fica FORA da pasta do código de propósito: uma versão nova da Central,
baixada em outra pasta, encontra tudo aqui sem ninguém copiar nada.

  dados\\          o que as ferramentas gravam e cadastram
  competencias\\   série do Apurabot e padrões-ouro

Não apague esta pasta. Para fazer backup, copie-a inteira.
Contém dado real da empresa: não compartilhe fora do time.
"""


@dataclass
class Preparo:
    """Onde os dados ficaram, e o que a abertura teve de fazer."""

    pasta: Path
    externa: bool = True
    copiadas: list[str] = field(default_factory=list)
    ignoradas: list[str] = field(default_factory=list)
    erro: str = ""

    def mensagens(self) -> list[str]:
        if self.erro:
            return [f"Não consegui preparar a pasta de dados: {self.erro}",
                    f"Continuo usando a pasta do código: {self.pasta}"]
        linhas = [f"Dados em: {self.pasta}"]
        for nome in self.copiadas:
            linhas.append(f"'{nome}' copiada da pasta do código para cá "
                          f"(a original ficou onde estava).")
        for nome in self.ignoradas:
            linhas.append(f"A pasta do código também tem '{nome}', e ela foi "
                          f"ignorada: quem vale é a de cima.")
        return linhas


def pasta_de_documentos() -> Path:
    """A pasta Documentos do usuário — inclusive redirecionada pelo OneDrive.

    No Windows corporativo o "Documentos" costuma morar dentro do OneDrive, e
    `~/Documents` aponta para uma pasta que ninguém abre. O caminho de verdade
    está no registro do usuário, que o Windows mantém atualizado.
    """
    if sys.platform.startswith("win"):
        try:
            import winreg

            with winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER,
                    r"Software\Microsoft\Windows\CurrentVersion\Explorer"
                    r"\User Shell Folders") as chave:
                valor, _ = winreg.QueryValueEx(chave, "Personal")
            caminho = Path(os.path.expandvars(valor))
            if caminho.is_dir():
                return caminho
        except OSError:
            pass
    return Path.home() / "Documents"


def pasta_padrao() -> Path:
    return pasta_de_documentos() / NOME_DA_PASTA


def _tem_conteudo(pasta: Path) -> bool:
    return pasta.is_dir() and any(pasta.iterdir())


def preparar(codigo: Path = RAIZ, destino: Path | None = None) -> Preparo:
    """Resolve a pasta de dados, migra o que houver e publica `HINOVE_DADOS`."""
    if destino is None:
        definida = os.environ.get(VARIAVEL, "").strip()
        destino = Path(definida) if definida else pasta_padrao()
    destino = Path(destino)

    if destino.resolve() == Path(codigo).resolve():
        # Apontada para a própria pasta do código: nada a migrar.
        os.environ[VARIAVEL] = str(destino)
        return Preparo(destino, externa=False)

    preparo = Preparo(destino)
    try:
        destino.mkdir(parents=True, exist_ok=True)
        for nome in PASTAS:
            origem, alvo = Path(codigo) / nome, destino / nome
            if not _tem_conteudo(origem):
                continue
            if alvo.exists():
                preparo.ignoradas.append(nome)
                continue
            # Copia com outro nome e só no fim renomeia: uma cópia que falhe
            # no meio não pode deixar um `dados` pela metade, que na abertura
            # seguinte seria tomado pelo de verdade.
            provisoria = destino / f".{nome}-copiando"
            shutil.rmtree(provisoria, ignore_errors=True)
            shutil.copytree(origem, provisoria)
            provisoria.rename(alvo)
            preparo.copiadas.append(nome)
        leia_me = destino / "LEIA-ME.txt"
        if not leia_me.exists():
            leia_me.write_text(LEIA_ME, encoding="utf-8")
    except OSError as erro:
        os.environ.pop(VARIAVEL, None)
        return Preparo(Path(codigo), externa=False, erro=str(erro))

    os.environ[VARIAVEL] = str(destino)
    return preparo
