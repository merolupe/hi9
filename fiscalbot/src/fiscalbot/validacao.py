"""Confere a base de regras antes de gravar.

No Excel, uma regra mal escrita só aparecia quando o relatório rodava — e
aparecia como registro não mapeado, que é o sintoma errado para a causa. A
tela da Central confere na hora de salvar.

Há duas gravidades. **Erro** impede a gravação: a base ficaria inconsistente.
**Aviso** grava, mas conta o que vai acontecer — regra que nunca vai casar,
por exemplo, é legítima enquanto está sendo escrita.
"""
from __future__ import annotations

from dataclasses import dataclass

from .modelo import BaseDeRegras, Regra

ERRO, AVISO = "erro", "aviso"

#: Operadores aceitos em cada campo de condição. Ver `predicados.py`.
OPERADORES = {
    "cond_produto": ("INICIA:", "NAOINICIA:", "TABELA:", "TABELAEXCETO:"),
    "cond_par_uf": ("INTRA", "INTER", "UFORIG:", "NAOUFORIG:", "NAOPARUF:"),
    "cond_parceiro": ("INICIA:", "NAOINICIA:"),
    "esp_cst": ("EM:", "NAOEM:"),
    "esp_icms": ("CARGA", ">0"),
    "esp_aliq": ("TABELAUF",),
    "esp_outros": ("PARCEIRO<20", "PARCEIROINICIA:", "SEMPRE:", "SECST:"),
}


@dataclass(frozen=True)
class Problema:
    gravidade: str
    onde: str
    mensagem: str

    def __str__(self) -> str:
        return f"{self.onde}: {self.mensagem}"


def _operador_conhecido(campo: str, valor: str) -> bool:
    """Um valor literal é sempre aceito; o que se recusa é `PREFIXO:` inventado."""
    v = valor.strip()
    if not v:
        return True
    if ":" not in v:
        # Sem dois-pontos é valor literal (um CFOP, um CST, uma lista de UFs).
        return True
    prefixo = v.split(":", 1)[0].upper() + ":"
    return prefixo in [o.upper() for o in OPERADORES.get(campo, ()) if o.endswith(":")]


def _identidade(regra: Regra) -> tuple:
    """O que faz duas regras casarem exatamente com os mesmos registros."""
    return (
        regra.es.upper()[:1], regra.especie.upper(),
        tuple(sorted(regra.cfops_conferidos)),
        regra.cond_produto.upper(), regra.cond_par_uf.upper(),
        regra.cond_parceiro.upper(),
    )


def conferir(base: BaseDeRegras) -> list[Problema]:
    """Todos os problemas da base, erros primeiro."""
    problemas: list[Problema] = []

    if base.parametros.tolerancia_carga < 0:
        problemas.append(Problema(
            ERRO, "Parâmetros",
            "a tolerância da carga efetiva não pode ser negativa."))

    vistos: dict[str, Regra] = {}
    identidades: dict[tuple, str] = {}

    for regra in base.regras:
        onde = f"Regra {regra.id or '(sem ID)'}"

        if not regra.id.strip():
            problemas.append(Problema(ERRO, onde, "toda regra precisa de um ID."))
        elif regra.id in vistos:
            problemas.append(Problema(
                ERRO, onde, "há outra regra com este mesmo ID."))
        else:
            vistos[regra.id] = regra

        if not regra.operacao.strip():
            problemas.append(Problema(
                AVISO, onde,
                "sem nome de operação — é o texto que aparece na planilha."))

        preenchidos = [c for c in regra.cfop if c.strip()]
        if regra.ativa and not preenchidos:
            problemas.append(Problema(
                AVISO, onde,
                "está ativa e não tem CFOP: nunca vai casar com registro nenhum."))
        for campo in OPERADORES:
            valor = getattr(regra, campo)
            if not _operador_conhecido(campo, valor):
                aceitos = ", ".join(OPERADORES[campo]) or "nenhum"
                problemas.append(Problema(
                    ERRO, onde,
                    f"o campo {campo} usa um operador que o motor não conhece "
                    f"({valor.split(':', 1)[0]}:). Aceitos: {aceitos}."))

        for campo in ("cond_produto",):
            valor = getattr(regra, campo).strip()
            for marcador in ("TABELA:", "TABELAEXCETO:"):
                if not valor.upper().startswith(marcador):
                    continue
                nome = valor[len(marcador):].split(":", 1)[0].strip().upper()
                if nome not in base.parametros.tabelas:
                    problemas.append(Problema(
                        ERRO, onde,
                        f"cita a tabela de produtos {nome!r}, que não existe."))

        if regra.esp_aliq.strip().upper() == "TABELAUF" and not base.aliquotas:
            problemas.append(Problema(
                ERRO, onde,
                "usa TABELAUF, mas a matriz de alíquotas está vazia."))

        if regra.esp_cst.strip() and ":" not in regra.esp_cst:
            cst = regra.esp_cst.strip().lstrip("=")
            if len(cst) != 2 or not cst.isdigit():
                problemas.append(Problema(
                    AVISO, onde,
                    f"o CST esperado {cst!r} não tem dois dígitos — o motor "
                    f"compara com os dois primeiros caracteres da coluna."))

        if regra.ativa:
            identidade = _identidade(regra)
            if identidade in identidades:
                problemas.append(Problema(
                    ERRO, onde,
                    f"identifica exatamente os mesmos registros que a regra "
                    f"{identidades[identidade]}. Duas regras casando com o "
                    f"mesmo documento fazem a auditoria virar AMBIGUA."))
            else:
                identidades[identidade] = regra.id

    if not base.ativas:
        problemas.append(Problema(
            ERRO, "Base", "nenhuma regra ativa: o Fiscalbot não roda assim."))

    if not base.parceiros_simples_nacional:
        problemas.append(Problema(
            AVISO, "Parceiros",
            "a lista do Simples Nacional está vazia — a camada de frete SN "
            "não vai rodar. Ela não vem no repositório por conter dado da "
            "empresa; precisa ser cadastrada aqui."))

    return sorted(problemas, key=lambda p: 0 if p.gravidade == ERRO else 1)


def tem_erro(problemas: list[Problema]) -> bool:
    return any(p.gravidade == ERRO for p in problemas)
