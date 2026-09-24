"""O que a base aprende sozinha, das semanas que voltaram classificadas.

### O problema, e por que ele não é resolvido guardando o que já foi lido

A base importada é uma fotografia de um ano de relatórios, e vai até uma
semana — hoje a 37. Da 38 em diante o time continua classificando, e essas
decisões precisam entrar na base. A tentação é ler a planilha devolvida e somar
evidência. **Não dá:** uma nota pendente aparece na planilha de várias semanas
seguidas, e somar a cada execução contaria a mesma decisão humana cinco, seis,
dez vezes. A evidência inflaria sem que ninguém tivesse decidido nada de novo.

Guardar a lista do que já foi absorvido resolveria, ao preço de uma lista de
dezenas de milhares de chaves dentro da base — e de um jeito de errar novo: a
lista e a evidência podem sair de sincronia.

### O que se faz em vez disso

Aprende-se do **livro**, não da planilha. O livro já é indexado pela nota e
guarda uma linha por nota, para sempre, com a classificação mais recente que
uma pessoa deu. Recalcular a evidência a partir dele é **idempotente por
construção**: rodar duas vezes dá o mesmo número, porque a nota é uma linha
tanto na primeira vez quanto na segunda.

E para não contar de novo o que a fotografia já contou, aprende-se **só das
semanas depois de `ultimo_relatorio_classificado`**. As duas metades não se
sobrepõem, então somá-las é legítimo — e nenhuma delas precisa saber da outra.

### O que ele pode criar, e o que não pode

Ele **soma evidência** a uma regra que existe, e pode **criar** a proposta de
uma regra que não tinha nenhuma — quando o livro mostra o mesmo valor em três
notas de duas semanas, sem uma divergência. É o mesmo limiar que a fotografia
usa, aplicado aos mesmos dados: decisões humanas. Não é adivinhação (regra
nº 4); é a leitura de um histórico que agora tem dono.

O que ele **não** faz é derrubar proposta que já existe. Onde o livro novo
discorda da lista curada, a discordância aparece como divergência de evidência
— a proposta cai para `sugestao` com as alternativas ao lado — e quem decide é
a pessoa, na tela. Uma máquina que trocasse a proposta sozinha estaria
decidindo classificação, e não é o que ela faz.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Iterable

from ..estado import Classificacao, Livro
from ..texto import aparar, chave_de_texto
from .base import (NOTAS_PARA_FIRMAR, SEMANAS_PARA_FIRMAR, Conhecimento,
                   Evidencia, chave_de_operacao)

#: Qual campo do livro alimenta qual campo da base.
CAMPOS = {"guardiao": "guardiao", "categoria": "categoria"}


@dataclass
class Contagem:
    """As decisões observadas para uma regra, antes de virarem evidência.

    `normalizar` é o que decide o que conta como o mesmo valor, e muda por
    escopo: guardião e categoria comparam por `chave_de_texto`, `Tipo de
    Operação` por `chave_de_operacao` — nela o conectivo não é divergência, e
    contar `Compra Uso e Consumo` contra `Compra Uso Consumo` faria a base
    discordar de si mesma.
    """

    normalizar: Callable[[Any], str] = chave_de_texto
    por_valor: dict[str, int] = field(default_factory=dict)
    semanas: set[int] = field(default_factory=set)
    #: A grafia mais frequente de cada valor normalizado — a base guarda o que
    #: as pessoas escrevem, e a comparação é que normaliza.
    grafias: dict[str, dict[str, int]] = field(default_factory=dict)

    def somar(self, valor: str, semana: int) -> None:
        chave = self.normalizar(valor)
        self.por_valor[chave] = self.por_valor.get(chave, 0) + 1
        if semana:
            self.semanas.add(semana)
        grafias = self.grafias.setdefault(chave, {})
        grafias[valor] = grafias.get(valor, 0) + 1

    @property
    def notas(self) -> int:
        return sum(self.por_valor.values())

    def grafia(self, chave: str) -> str:
        grafias = self.grafias.get(chave) or {}
        return max(grafias.items(), key=lambda t: (t[1], t[0]))[0] if grafias else ""

    def como_evidencia(self) -> Evidencia:
        """O valor majoritário, e o resto como alternativa. Empate não firma.

        No empate a escolha é a grafia em ordem alfabética — ela não vira
        proposta de todo jeito, porque `apoio` fica abaixo de `notas` e o
        cruzamento em `base._confianca` recusa firmar.
        """
        if not self.por_valor:
            return Evidencia()
        maior = max(self.por_valor.values())
        vencedora = sorted(c for c, n in self.por_valor.items() if n == maior)[0]
        return Evidencia(
            valor=self.grafia(vencedora),
            notas=self.notas,
            apoio=self.por_valor[vencedora],
            semanas=len(self.semanas),
            alternativas={self.grafia(c): n
                          for c, n in sorted(self.por_valor.items(),
                                             key=lambda t: (-t[1], t[0]))},
        )


@dataclass
class Aprendido:
    """O que as semanas novas mostraram, e quanto delas foi lido."""

    desde_semana: int = 0
    ate_semana: int = 0
    notas: int = 0
    #: `código` → {campo: Contagem}, e `código|fantasia` para o nível da unidade
    parceiros: dict[str, dict[str, Contagem]] = field(default_factory=dict)
    unidades: dict[str, dict[str, Contagem]] = field(default_factory=dict)
    #: `CFOP normalizado` → {nível: Contagem}
    operacoes: dict[str, dict[str, Contagem]] = field(default_factory=dict)
    #: `guardião normalizado` → Contagem do gestor de apoio
    gestores: dict[str, Contagem] = field(default_factory=dict)
    #: Os rótulos originais, para a base guardar o que as pessoas escrevem.
    rotulos: dict[str, str] = field(default_factory=dict)

    @property
    def vazio(self) -> bool:
        return not self.notas

    def resumo(self) -> str:
        if self.vazio:
            return ("Nada novo: o livro não tem nota classificada depois da "
                    f"semana {self.desde_semana}.")
        return (f"{self.notas} nota(s) classificada(s) entre as semanas "
                f"{self.desde_semana + 1} e {self.ate_semana} · "
                f"{len(self.parceiros)} parceiro(s), {len(self.unidades)} "
                f"regra(s) por unidade, {len(self.operacoes)} CFOP e "
                f"{len(self.gestores)} gestor(es).")


def aprender(livro: Livro, desde_semana: int = 0) -> Aprendido:
    """Refaz a contagem a partir do livro, só das semanas acima de `desde_semana`.

    Idempotente: o livro tem uma linha por nota, então a mesma decisão nunca é
    contada duas vezes, por mais vezes que isto rode.
    """
    relato = Aprendido(desde_semana=desde_semana)
    for registro in _classificadas(livro, desde_semana):
        relato.notas += 1
        relato.ate_semana = max(relato.ate_semana, registro.semana)
        codigo = aparar(registro.codigo_do_parceiro)
        fantasia = aparar(registro.fantasia)

        if codigo:
            _contar_parceiro(relato, codigo, fantasia, registro)
        _contar_operacao(relato, codigo, registro)
        _contar_gestor(relato, registro)
    return relato


def _classificadas(livro: Livro, desde: int) -> Iterable[Classificacao]:
    """Nota com semana acima do corte e com alguma classificação de gente."""
    for registro in livro.registros.values():
        if registro.semana <= desde:
            continue
        if any(aparar(getattr(registro, campo)) for campo in
               ("guardiao", "categoria", "tipo_de_operacao")):
            yield registro


def _contar_parceiro(relato: Aprendido, codigo: str, fantasia: str,
                     registro: Classificacao) -> None:
    geral = relato.parceiros.setdefault(codigo, {})
    na_unidade = (relato.unidades.setdefault(f"{codigo}|{chave_de_texto(fantasia)}", {})
                  if fantasia else None)
    if fantasia:
        relato.rotulos[f"{codigo}|{chave_de_texto(fantasia)}"] = fantasia
    for campo, no_livro in CAMPOS.items():
        valor = aparar(getattr(registro, no_livro))
        if not valor:
            continue
        geral.setdefault(campo, Contagem()).somar(valor, registro.semana)
        if na_unidade is not None:
            na_unidade.setdefault(campo, Contagem()).somar(valor, registro.semana)


def _contar_operacao(relato: Aprendido, codigo: str,
                     registro: Classificacao) -> None:
    from .importacao import cfop_normalizado

    cfop = cfop_normalizado(registro.cfop)
    operacao = aparar(registro.tipo_de_operacao)
    if not cfop or not operacao:
        return
    categoria = chave_de_texto(registro.categoria)
    niveis = relato.operacoes.setdefault(cfop, {})
    # Os quatro níveis da consulta, todos alimentados: quem pergunta escolhe o
    # mais específico que existir, e não saberia montar o geral a partir dele.
    for nivel in (f"{codigo}|{categoria}", f"{codigo}|", f"|{categoria}", "|"):
        niveis.setdefault(
            nivel, Contagem(normalizar=chave_de_operacao)
        ).somar(operacao, registro.semana)


def _contar_gestor(relato: Aprendido, registro: Classificacao) -> None:
    guardiao = aparar(registro.guardiao)
    gestor = aparar(registro.gestor_de_apoio)
    if not guardiao or not gestor:
        return
    chave = chave_de_texto(guardiao)
    relato.rotulos.setdefault(chave, guardiao)
    relato.gestores.setdefault(chave, Contagem()).somar(gestor, registro.semana)


# -- juntar as duas metades --------------------------------------------------

def somar(anterior: Evidencia, nova: Evidencia) -> Evidencia:
    """Soma duas evidências que **não se sobrepõem**.

    A da fotografia vai até `ultimo_relatorio_classificado`; a aprendida começa
    depois dele. Por isso as notas se somam sem risco de contar a mesma duas
    vezes, e as semanas também — são conjuntos disjuntos de semanas.

    O valor majoritário é recalculado sobre o total: é o ponto de somar. Uma
    proposta que o histórico antigo sustentava com folga pode passar a divergir
    quando as semanas novas discordarem dela — e é exatamente isso que tem de
    aparecer na tela.
    """
    if not nova.notas:
        return anterior
    if not anterior.notas:
        return nova

    juntas: dict[str, tuple[str, int]] = {}
    for evidencia in (anterior, nova):
        fontes = dict(evidencia.alternativas) or {evidencia.valor: evidencia.apoio}
        for rotulo, quantas in fontes.items():
            chave = chave_de_texto(rotulo)
            grafia, total = juntas.get(chave, (rotulo, 0))
            juntas[chave] = (grafia or rotulo, total + quantas)

    maior = max(n for _, n in juntas.values())
    chave = sorted(c for c, (_, n) in juntas.items() if n == maior)[0]
    return Evidencia(
        valor=juntas[chave][0],
        notas=anterior.notas + nova.notas,
        apoio=maior,
        semanas=anterior.semanas + nova.semanas,
        alternativas={grafia: n for grafia, n in sorted(
            juntas.values(), key=lambda t: (-t[1], t[0]))},
    )


def _firma(evidencia: Evidencia) -> bool:
    """O mesmo limiar da fotografia: 3 notas, 2 semanas, sem divergência."""
    return (evidencia.notas >= NOTAS_PARA_FIRMAR
            and evidencia.semanas >= SEMANAS_PARA_FIRMAR
            and evidencia.apoio == evidencia.notas)


def _firma_gestor(evidencia: Evidencia) -> bool:
    """Gestor não se mede por repetição: o que impede é o **empate**.

    É a mesma assimetria que `Conhecimento.gestor_de` já aplica na consulta, e
    a razão dela é a regra da fonte: *o gestor com mais notas na última
    observação daquele guardião*. Exigir três notas aqui faria a tabela de
    gestores nunca aprender uma troca de gestor.
    """
    if not evidencia.notas:
        return False
    return not any(
        quantas >= evidencia.apoio
        and chave_de_texto(outro) != chave_de_texto(evidencia.valor)
        for outro, quantas in evidencia.alternativas.items())


def _fundir(bloco: dict[str, Any], contagem: Contagem,
            firma: Callable[[Evidencia], bool] = _firma) -> dict[str, Any]:
    """Põe o aprendido dentro de um bloco `{proposto, evidencia}` da base."""
    nova = somar(Evidencia.de(bloco.get("evidencia")), contagem.como_evidencia())
    fundido = {**bloco, "evidencia": nova.como_dicionario()}
    if not str(bloco.get("proposto") or "").strip() and firma(nova):
        # Regra sem proposta que o livro repetiu sem divergir: a base passa a
        # ter o que dizer sobre ela. Onde já havia proposta, ela não se toca —
        # trocar proposta sozinha seria decidir classificação.
        fundido["proposto"] = nova.valor
    return fundido


def aplicar(conhecimento: Conhecimento, aprendido: Aprendido) -> Conhecimento:
    """Funde o aprendido na base, em memória. O disco não é tocado."""
    if aprendido.vazio:
        return conhecimento

    for codigo, campos in aprendido.parceiros.items():
        parceiro = conhecimento.parceiros.setdefault(codigo, {})
        for campo, contagem in campos.items():
            parceiro[campo] = _fundir(parceiro.get(campo) or {}, contagem)

    for identidade, campos in aprendido.unidades.items():
        codigo, _, chave = identidade.partition("|")
        parceiro = conhecimento.parceiros.setdefault(codigo, {})
        unidades = parceiro.setdefault("unidades", {})
        unidade = unidades.setdefault(
            chave, {"rotulo": aprendido.rotulos.get(identidade, "")})
        for campo, contagem in campos.items():
            unidade[campo] = _fundir(unidade.get(campo) or {}, contagem)

    for cfop, niveis in aprendido.operacoes.items():
        alvo = conhecimento.operacoes.setdefault(cfop, {})
        for nivel, contagem in niveis.items():
            alvo[nivel] = _fundir(alvo.get(nivel) or {}, contagem)

    for chave, contagem in aprendido.gestores.items():
        bruto = conhecimento.gestor_do_guardiao.setdefault(
            chave, {"rotulo": aprendido.rotulos.get(chave, "")})
        conhecimento.gestor_do_guardiao[chave] = _fundir(
            bruto, contagem, firma=_firma_gestor)

    observados = {chave_de_texto(g): g for g in conhecimento.guardioes_observados}
    for contagem in aprendido.parceiros.values():
        evidencia = (contagem.get("guardiao") or Contagem()).como_evidencia()
        for rotulo in evidencia.alternativas:
            observados.setdefault(chave_de_texto(rotulo), rotulo)
    conhecimento.guardioes_observados = sorted(
        v for v in observados.values() if v)
    conhecimento.aprendido_ate = aprendido.ate_semana
    conhecimento.notas_aprendidas = aprendido.notas
    return conhecimento
