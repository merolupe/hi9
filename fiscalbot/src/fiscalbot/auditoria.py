"""O motor: como cada registro do Livro Fiscal é auditado.

A ordem importa, e é ela que define o resultado. Três camadas têm precedência
sobre a base de regras inteira, porque valem independentemente do CFOP:

1. **Cancelada** — nota cancelada não se audita. Conforme, e encerra.
2. **Frete Simples Nacional** — CT-e de parceiro na lista do SN espera CST 90,
   sobrepondo qualquer regra.
3. **Cavaco** — compra de matéria-prima (CFOP 1101/2101) desses parceiros tem
   enquadramento próprio: intra CST 51 com ICMS zero, inter CST 00 com
   alíquota 7 ou 12.

Passadas as três, o registro é confrontado com as regras ativas. O casamento é
**MECE**: espera-se que exatamente uma regra case.

* **nenhuma casou** — CT-e vira advertência de frete não mapeado; nota fiscal
  vai para validação manual, e ainda assim leva a Camada 0;
* **mais de uma casou** — a base está ambígua. Vira advertência apontando para
  a tela de regras, porque o defeito é do cadastro, não do documento;
* **uma casou** — conferem-se as seis dimensões.

A **Camada 0** é a rede embaixo de tudo. Ela vale mesmo para registro sem
regra, e tem duas partes: a coerência entre CST e valor de ICMS (regra A) e a
coerência entre o primeiro dígito do CFOP e a operação ser INTRA ou INTER
(regra B). Onde a regra já se pronunciou, a Camada 0 não fala de novo — é o
que evita contar a mesma divergência duas vezes.

Por cima de tudo há a **camada Ind**: produto cuja descrição começa com `Ind.`
só circula em CFOP de industrialização.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from . import predicados as p
from .leitura import (MapaDeColunas, extrair_cfop, extrair_cst, extrair_produto,
                      parse_numero)
from .modelo import BaseDeRegras

CONFORME = "Conforme"
ADVERTENCIA = "Advertencia"
VALIDACAO_MANUAL = "Validação manual"

INTRA, INTER, INDEFINIDO = "INTRA", "INTER", "INDEFINIDO"


@dataclass(frozen=True)
class Ocorrencias:
    """As seis dimensões conferidas. Vazio quer dizer conforme."""

    cst: str = ""
    icms: str = ""
    produto: str = ""
    aliquota: str = ""
    carga: str = ""
    outros: str = ""

    @property
    def alguma(self) -> bool:
        return any((self.cst, self.icms, self.produto,
                    self.aliquota, self.carga, self.outros))

    def como_lista(self) -> list[str]:
        return [self.cst, self.icms, self.produto,
                self.aliquota, self.carga, self.outros]


@dataclass(frozen=True)
class Achado:
    """O veredito de um registro."""

    status: str
    operacao: str
    tipo_operacao: str
    auditoria: str
    ocorrencias: Ocorrencias = Ocorrencias()


def _normalizar_codigo(valor: Any) -> str:
    if valor is None or str(valor).strip() == "":
        return ""
    if isinstance(valor, (int, float)) and not isinstance(valor, bool):
        return f"{int(valor)}" if float(valor) == int(valor) else str(valor)
    return str(valor).strip()


def _tipo_de_operacao(uf_origem: str, uf_destino: str) -> str:
    if not uf_origem or not uf_destino:
        return INDEFINIDO
    return INTRA if uf_origem == uf_destino else INTER


def auditar_linha(valores: list[Any], mapa: MapaDeColunas,
                  base: BaseDeRegras) -> Achado:
    """Audita um registro. É aqui que a ordem das camadas se resolve."""
    def celula(campo: str) -> Any:
        i = mapa.posicoes.get(campo, -1)
        return valores[i] if 0 <= i < len(valores) else ""

    cst = extrair_cst(str(celula("CST")))
    icms, _ = parse_numero(celula("ICMS"))
    cfop = extrair_cfop(celula("CFOP"))
    produto = extrair_produto(celula("PROD"))
    aliquota, _ = parse_numero(celula("ALIQ"))
    valor_contabil, tem_valor_contabil = parse_numero(celula("VCONT"))
    especie = str(celula("ESP")).strip()
    es = str(celula("ES")).strip()
    uf_origem = str(celula("UFO")).strip().upper()
    uf_destino = str(celula("UFD")).strip().upper()
    parceiro = celula("PARC")
    parceiro_nome = str(celula("PARCNOME")).strip()
    origem = str(celula("ORIGEM")).strip()
    desc_tipo = str(celula("DESCTIPO")).strip()

    tipo = _tipo_de_operacao(uf_origem, uf_destino)
    par_uf = f"{uf_origem}x{uf_destino}"

    # --- camada Ind: só para nota fiscal, e só onde a tabela CFOP_IND manda
    ocorrencia_ind = ""
    if especie.upper() != "CT" and mapa.tem("DESCPROD"):
        descricao = str(celula("DESCPROD")).strip().upper()
        if descricao.startswith("IND.") and p.em_tabela(
            base.parametros, "CFOP_IND", cfop
        ):
            ocorrencia_ind = p.cfop_de_industrializacao(tipo, cfop)

    # --- 1. cancelada: precedência máxima
    if origem.upper() == "CANCELADA":
        return Achado(CONFORME, "Cancelada", tipo,
                      "Nota cancelada (Origem = Cancelada)")

    # --- 2. frete de parceiro do Simples Nacional
    codigo = _normalizar_codigo(parceiro)
    if especie.upper() == "CT" and codigo in base.codigos_simples_nacional():
        ocorrencia = "" if cst == "90" else p.ADV_CST
        return Achado(
            CONFORME if not ocorrencia else ADVERTENCIA,
            "Frete SN (Simples Nacional)", tipo,
            "Parceiro Simples Nacional: CST esperado 90",
            Ocorrencias(cst=ocorrencia),
        )

    # --- 3. compra de matéria-prima de parceiro de cavaco
    if cfop in ("1101", "2101") and codigo in base.codigos_cavaco():
        if tipo == INTRA:
            explicacao = "intra: CST 51, ICMS 0"
            ocorrencias = Ocorrencias(
                cst="" if cst == "51" else p.ADV_CST,
                icms="" if icms == 0 else p.ADV_ICMS,
            )
        else:
            explicacao = "inter: CST 00, aliquota 7 ou 12"
            ocorrencias = Ocorrencias(
                cst="" if cst == "00" else p.ADV_CST,
                aliquota="" if aliquota in (7, 12) else p.ADV_ALIQUOTA,
            )
        return Achado(
            ADVERTENCIA if ocorrencias.alguma else CONFORME,
            "Compra MP Cavaco", tipo,
            f"Compra MP Cavaco ({explicacao})", ocorrencias,
        )

    # --- 4. identificar a operação contra as regras ativas
    casadas = [
        regra for regra in base.regras
        if p.casa_identificacao(
            regra, es=es, especie=especie, cfop=cfop, produto=produto,
            operacao=tipo, par_uf=par_uf, parceiro_nome=parceiro_nome,
            parametros=base.parametros,
        )
    ]

    if not casadas:
        if especie.upper() == "CT":
            recado = ("Circulacao nao mapeada" if tipo == INTRA
                      else "Operacao de frete nao mapeada")
            return Achado(ADVERTENCIA, "Frete nao mapeado", tipo, recado,
                          Ocorrencias(outros=recado))
        # Nota fiscal sem regra: validação manual, mas a Camada 0 ainda vale.
        return Achado(
            VALIDACAO_MANUAL,
            f"{cfop} - {desc_tipo}" if desc_tipo else cfop,
            tipo, "Validar manualmente",
            Ocorrencias(
                cst="",
                icms=p.coerencia_cst_icms(cst, icms, base.parametros),
                produto=ocorrencia_ind,
                outros=p.coerencia_cfop_operacao(cfop, tipo),
            ),
        )

    if len(casadas) > 1:
        # A base ficou ambígua: o defeito é do cadastro, não do documento.
        return Achado(ADVERTENCIA, "AMBIGUA (verificar REGRAS)", tipo,
                      "Registro casou com mais de uma regra")

    # --- 5. regra única: as seis dimensões
    regra = casadas[0]
    cst_oc = p.testar_cst(regra, cst)
    icms_oc = p.testar_icms(regra, icms)
    produto_oc = p.testar_produto(regra, produto, base.parametros)
    aliquota_oc = p.testar_aliquota(regra, aliquota, par_uf, base)
    carga_oc = p.testar_carga(regra, icms, valor_contabil, tem_valor_contabil,
                              base.parametros.tolerancia_carga)
    outros_oc = p.testar_outros(regra, parceiro, parceiro_nome)

    # --- Camada 0 como rede, só onde a regra não se pronunciou
    if not outros_oc:
        outros_oc = p.coerencia_cfop_operacao(cfop, tipo)
    if not icms_oc:
        icms_oc = p.coerencia_cst_icms(cst, icms, base.parametros)

    if ocorrencia_ind:
        produto_oc = f"{produto_oc} | {ocorrencia_ind}" if produto_oc else ocorrencia_ind

    auditoria = p.montar_auditoria(regra)
    recado_secst = p.mensagem_secst(regra, cst)
    if recado_secst:
        auditoria = f"{auditoria} | {recado_secst}"

    ocorrencias = Ocorrencias(cst_oc, icms_oc, produto_oc,
                              aliquota_oc, carga_oc, outros_oc)
    if recado_secst:
        status = VALIDACAO_MANUAL      # o CST casou com o alerta condicional
    elif ocorrencias.alguma:
        status = ADVERTENCIA
    else:
        status = CONFORME
    return Achado(status, regra.operacao, tipo, auditoria, ocorrencias)
