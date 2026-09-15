"""A foto semanal imutável — a evidência que o controle interno cobra.

A política interna pede que *snapshots semanais imutáveis coexistam com a base
viva*. O livro de classificação é a base viva: ele muda toda semana, e é essa
a graça dele. O snapshot é a outra metade — a resposta para "qual era a
posição em 08/09, e com base em quê?", sem depender de alguém ter guardado o
anexo do e-mail.

Cada execução grava uma pasta em
`dados/pendentes/semanas/<domínio>/<AAAA>-S<NN>/`:

| Arquivo | O que é |
|---|---|
| a planilha entregue | byte a byte, como foi baixada |
| `classificacao.yaml` | o livro **como estava no momento da geração** |
| `entradas.json` | nome, tamanho e SHA-256 de cada arquivo de entrada, com o papel |
| `resumo.json` | as fichas e listas da tela, e se a semana ficou encerrável |

**A pasta nunca é sobrescrita.** Rodar a mesma semana de novo grava
`<AAAA>-S<NN>-2`, depois `-3`, e a mais alta é a vigente. Apagar evidência por
iniciativa da ferramenta seria pior do que ocupar disco, então não há expurgo
automático (pendência 10).

### Por que isto vale mais que vigência, aqui

A regra nº 3 do `CLAUDE.md` pede vigência em toda regra, e a tela de
configuração já abriu exceção a ela — decisão registrada em
`docs/central/01-arquitetura.md`. Nesta ferramenta a exceção é mais confortável
ainda de defender: nada aqui é regra tributária, e o snapshot entrega o que a
vigência entregaria. Vigência responde "qual regra valia em julho"; o snapshot
responde "o que exatamente saiu em 08/09, e com base em quê". Para uma rotina
semanal de controle interno, a segunda pergunta é a que importa.
"""
from __future__ import annotations

import hashlib
import json
import shutil
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

import yaml

from .estado import Livro, para_dicionario


@dataclass(frozen=True)
class EntradaDaSemana:
    """Um arquivo que entrou na execução, e o que ele era."""

    nome: str
    papel: str
    tamanho: int
    sha256: str


def _raiz() -> Path:
    for pasta in Path(__file__).resolve().parents:
        if (pasta / "vendor" / "openpyxl").is_dir():
            return pasta
    return Path(__file__).resolve().parents[3]         # pragma: no cover


def pasta_das_semanas(dominio: str, raiz: Path | None = None) -> Path:
    base = Path(raiz) if raiz else _raiz() / "dados"
    return base / "pendentes" / "semanas" / dominio


def impressao_de(caminho: Path, papel: str = "") -> EntradaDaSemana:
    """Nome, tamanho e SHA-256 de um arquivo de entrada.

    O hash é o que permite dizer, meses depois, que a semana foi gerada a
    partir **daquele** relatório, e não de outro com o mesmo nome.
    """
    caminho = Path(caminho)
    digestor = hashlib.sha256()
    with caminho.open("rb") as arquivo:
        for pedaco in iter(lambda: arquivo.read(1 << 20), b""):
            digestor.update(pedaco)
    return EntradaDaSemana(caminho.name, papel, caminho.stat().st_size,
                           digestor.hexdigest())


def _proxima_pasta(base: Path, rotulo: str) -> Path:
    """`2026-S31`, e se já existir, `2026-S31-2`, `-3`, …"""
    candidata = base / rotulo
    sufixo = 1
    while candidata.exists():
        sufixo += 1
        candidata = base / f"{rotulo}-{sufixo}"
    return candidata


def rotulo_da_semana(ano: int, semana: int) -> str:
    return f"{ano:04d}-S{semana:02d}"


def gravar(dominio: str, ano: int, semana: int, *,
           planilha: Path | None = None,
           livro: Livro | None = None,
           entradas: Iterable[EntradaDaSemana] = (),
           resumo: dict[str, Any] | None = None,
           encerravel: bool = True,
           raiz: Path | None = None) -> Path:
    """Grava a foto da semana numa pasta nova. Devolve a pasta criada."""
    base = pasta_das_semanas(dominio, raiz)
    base.mkdir(parents=True, exist_ok=True)
    pasta = _proxima_pasta(base, rotulo_da_semana(ano, semana))
    pasta.mkdir(parents=True)

    if planilha is not None and Path(planilha).is_file():
        shutil.copy2(planilha, pasta / Path(planilha).name)

    if livro is not None:
        (pasta / "classificacao.yaml").write_text(
            yaml.safe_dump(para_dicionario(livro), allow_unicode=True,
                           sort_keys=False),
            encoding="utf-8",
        )

    (pasta / "entradas.json").write_text(
        json.dumps([asdict(e) for e in entradas], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    conteudo = dict(resumo or {})
    conteudo.update({
        "dominio": dominio,
        "ano": ano,
        "semana": semana,
        "encerravel": bool(encerravel),
        "gerado_em": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    })
    (pasta / "resumo.json").write_text(
        json.dumps(conteudo, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )
    return pasta


def semanas_gravadas(dominio: str, raiz: Path | None = None) -> list[Path]:
    """As pastas de semana já gravadas, da mais antiga para a mais nova."""
    base = pasta_das_semanas(dominio, raiz)
    if not base.is_dir():
        return []
    return sorted((p for p in base.iterdir() if p.is_dir()), key=lambda p: p.name)


def ultima_semana(dominio: str, raiz: Path | None = None) -> dict[str, Any] | None:
    """O `resumo.json` da última execução gravada, ou `None` se não há nenhuma.

    É o que permite a execução seguinte dizer o que ficou aberto na anterior —
    "a semana 30 foi encerrada com 4 unidades não reconhecidas". Sem botão de
    encerrar, é essa a trava possível: ninguém encerra sem saber.
    """
    gravadas = semanas_gravadas(dominio, raiz)
    for pasta in reversed(gravadas):
        arquivo = pasta / "resumo.json"
        if arquivo.is_file():
            return json.loads(arquivo.read_text(encoding="utf-8"))
    return None
