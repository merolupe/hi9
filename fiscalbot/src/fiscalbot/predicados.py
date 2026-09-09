"""A mini-linguagem das regras: como cada condição é escrita e avaliada.

O time fiscal escreve as condições nesta sintaxe desde a versão em VBA. Ela
foi mantida palavra por palavra — quem já sabe cadastrar uma regra continua
sabendo, e as regras existentes valem sem tradução.

## Identificação (decide *qual* operação é o registro)

| Campo | Sintaxe | Significado |
|---|---|---|
| `es` | `Entrada` / `Saida` | compara só a **primeira letra** |
| `especie` | `NF` / `CT` | igualdade, sem diferenciar maiúscula |
| `cfop` | `1602;2602` | o CFOP tem que estar na lista |
| `cond_produto` | `701000701` | código exato |
| | `INICIA:7010` | começa com (**diferencia maiúscula**) |
| | `NAOINICIA:7010` | não começa com |
| | `TABELA:FRETE` | está na lista nomeada |
| | `TABELAEXCETO:FRETE:700000001,700000002` | está na lista, menos estes |
| `cond_par_uf` | `SPxSP;MTxMT` | par origem×destino na lista |
| | `INTRA` / `INTER` | mesma UF / UF diferente |
| | `UFORIG:BA;PR` | UF de origem na lista, destino livre |
| | `NAOUFORIG:SC` | UF de origem fora da lista |
| | `NAOPARUF:SPxSP` | par fora da lista |
| `cond_parceiro` | `INICIA:econet` | nome do parceiro começa com (ignora caixa) |
| | `NAOINICIA:econet` | não começa com |

## Conferência (decide se o registro está *conforme*)

| Campo | Sintaxe | Significado |
|---|---|---|
| `esp_cst` | `60` | CST tem que ser exatamente este |
| | `EM:00,20` | tem que estar entre estes (separados por **vírgula**) |
| | `NAOEM:41,50` | não pode estar entre estes |
| `esp_icms` | `0` / `>0` | valor exato / tem que ser positivo |
| | `CARGA` | quem confere o ICMS é a carga efetiva |
| `esp_aliq` | `7;12` | alíquota tem que ser uma destas |
| | `TABELAUF` | a esperada vem da matriz origem×destino |
| `esp_carga` | `4` | carga efetiva alvo, em %, dentro da tolerância |
| `esp_outros` | `PARCEIRO<20` | código do parceiro menor que 20 |
| | `PARCEIROINICIA:HINOVE` | nome do parceiro começa com |
| | `SEMPRE:texto` | advertência incondicional, com este texto |
| | `SECST:20:texto` | se o CST observado for 20, manda para validação manual |

Uma observação que vale para a leitura inteira: **`EM:` e `NAOEM:` separam por
vírgula; todo o resto separa por ponto e vírgula.** É assim desde o VBA.
"""
from __future__ import annotations

from .modelo import BaseDeRegras, Parametros, Regra

#: Os textos de ocorrência. São comparados contra a saída da macro, então são
#: exatamente os do VBA — sem acento, como estavam lá.
ADV_CST = "Advertencia de CST"
ADV_ICMS = "Advertencia de Valor ICMS"
ADV_PRODUTO = "Advertencia de Produto"
ADV_ALIQUOTA = "Advertencia de Aliquota"
ADV_CARGA = "Advertencia de Carga Efetiva"
ADV_PARCEIRO = "Advertencia de Parceiro"

CFOP_INDUSTRIALIZACAO_INTRA = ("1124", "1125")
CFOP_INDUSTRIALIZACAO_INTER = ("2124", "2125")


# -- utilitários da linguagem ---------------------------------------------

def _lista_por_virgula(texto: str) -> list[str]:
    """`EM:` e `NAOEM:` separam por vírgula. Só eles."""
    return [p.strip() for p in texto.split(",")]


def _lista_por_ponto_e_virgula(texto: str) -> list[str]:
    return [p.strip() for p in texto.split(";")]


def _prefixo(condicao: str, marcador: str) -> str | None:
    """O que vem depois de `MARCADOR:`, ou `None` se não for esse operador."""
    if condicao.upper().startswith(marcador.upper()):
        return condicao[len(marcador):].strip()
    return None


def _numero(texto: str) -> float | None:
    """O `Val` do VBA, no que importa aqui: número ou nada."""
    try:
        return float(texto.strip().replace(",", "."))
    except (TypeError, ValueError):
        return None


def em_tabela(parametros: Parametros, nome: str, produto: str) -> bool:
    return produto in parametros.tabelas.get(nome.strip().upper(), ())


# -- identificação ---------------------------------------------------------

def cond_produto_ok(condicao: str, produto: str, parametros: Parametros) -> bool:
    c = condicao.strip()
    if not c:
        return True

    alvo = _prefixo(c, "TABELAEXCETO:")
    if alvo is not None:
        nome, _, excluidos = alvo.partition(":")
        return em_tabela(parametros, nome, produto) and (
            produto not in _lista_por_virgula(excluidos)
        )

    alvo = _prefixo(c, "NAOINICIA:")
    if alvo is not None:
        return not produto.startswith(alvo)     # sensível à caixa, como no VBA

    alvo = _prefixo(c, "INICIA:")
    if alvo is not None:
        return produto.startswith(alvo)

    alvo = _prefixo(c, "TABELA:")
    if alvo is not None:
        return em_tabela(parametros, alvo, produto)

    return produto == (c[1:] if c.startswith("=") else c)


def cond_par_uf_ok(condicao: str, operacao: str, par_uf: str) -> bool:
    c = condicao.strip()
    if not c:
        return True
    if c.upper() == "INTRA":
        return operacao == "INTRA"
    if c.upper() == "INTER":
        return operacao == "INTER"

    # O separador é um "x" minúsculo: separa-se antes de subir a caixa,
    # senão "PRxSP" vira "PRXSP" e a UF de origem se perde.
    origem = par_uf.partition("x")[0].upper()

    alvo = _prefixo(c, "NAOUFORIG:")
    if alvo is not None:
        return origem not in [u.upper() for u in _lista_por_ponto_e_virgula(alvo)]

    alvo = _prefixo(c, "UFORIG:")
    if alvo is not None:
        return origem in [u.upper() for u in _lista_por_ponto_e_virgula(alvo)]

    alvo = _prefixo(c, "NAOPARUF:")
    if alvo is not None:
        return par_uf.upper() not in [p.upper() for p in _lista_por_ponto_e_virgula(alvo)]

    return par_uf.upper() in [p.upper() for p in _lista_por_ponto_e_virgula(c)]


def cond_parceiro_ok(condicao: str, nome: str) -> bool:
    c = condicao.strip()
    if not c:
        return True
    alvo = _prefixo(c, "NAOINICIA:")
    if alvo is not None:
        return not nome.strip().upper().startswith(alvo.upper())
    alvo = _prefixo(c, "INICIA:")
    if alvo is not None:
        return nome.strip().upper().startswith(alvo.upper())
    return nome.strip().upper() == c.upper()


def casa_identificacao(regra: Regra, *, es: str, especie: str, cfop: str,
                       produto: str, operacao: str, par_uf: str,
                       parceiro_nome: str, parametros: Parametros) -> bool:
    """Todas as condições de identificação, em `AND`."""
    if not regra.ativa:
        return False
    if regra.es and regra.es[:1].upper() != es[:1].upper():
        return False
    if regra.especie and regra.especie.upper() != especie.upper():
        return False
    if cfop not in regra.cfops_conferidos:
        return False
    if not cond_produto_ok(regra.cond_produto, produto, parametros):
        return False
    if not cond_par_uf_ok(regra.cond_par_uf, operacao, par_uf):
        return False
    if not cond_parceiro_ok(regra.cond_parceiro, parceiro_nome):
        return False
    return True


# -- conferência por dimensão ---------------------------------------------
# Cada função devolve "" quando conforme, ou o texto da ocorrência.

def testar_cst(regra: Regra, cst: str) -> str:
    p = regra.esp_cst.strip()
    if not p:
        return ""
    alvo = _prefixo(p, "NAOEM:")
    if alvo is not None:
        return ADV_CST if cst in _lista_por_virgula(alvo) else ""
    alvo = _prefixo(p, "EM:")
    if alvo is not None:
        return "" if cst in _lista_por_virgula(alvo) else ADV_CST
    if p.startswith("="):
        p = p[1:]
    return "" if cst == p else ADV_CST


def testar_icms(regra: Regra, icms: float) -> str:
    p = regra.esp_icms.strip()
    if not p:
        return ""
    if p.upper() == "CARGA":
        return ""                       # quem confere o ICMS é a carga
    if p == ">0":
        return "" if icms > 0 else ADV_ICMS
    if p.startswith("="):
        p = p[1:]
    esperado = _numero(p)
    if esperado is None:
        # Texto que não é número nesta coluna não faz nada — é o que o VBA
        # faz, e é o caso do `TABELAUF` que ficou em `EspICMS` na regra E11.
        return ""
    return "" if icms == esperado else ADV_ICMS


def testar_produto(regra: Regra, produto: str, parametros: Parametros) -> str:
    if not regra.cond_produto.strip():
        return ""
    return "" if cond_produto_ok(regra.cond_produto, produto, parametros) else ADV_PRODUTO


def testar_aliquota(regra: Regra, aliquota: float, par_uf: str,
                    base: BaseDeRegras) -> str:
    p = regra.esp_aliq.strip()
    if not p:
        return ""
    if p.upper() == "TABELAUF":
        esperada = base.aliquota_de(par_uf)
        if esperada is None:
            return ADV_ALIQUOTA
        return "" if abs(aliquota - esperada) <= 0.01 else ADV_ALIQUOTA
    for parte in _lista_por_ponto_e_virgula(p):
        valor = _numero(parte)
        if valor is not None and valor == aliquota:
            return ""
    return ADV_ALIQUOTA


def testar_carga(regra: Regra, icms: float, valor_contabil: float,
                 tem_valor_contabil: bool, tolerancia: float) -> str:
    p = regra.esp_carga.strip()
    if not p:
        return ""
    if not tem_valor_contabil or valor_contabil == 0:
        return ADV_CARGA                        # divisão por zero
    alvo = _numero(p)
    if alvo is None:
        return ""
    carga = icms / valor_contabil * 100.0
    return "" if (alvo - tolerancia) <= carga <= (alvo + tolerancia) else ADV_CARGA


def testar_outros(regra: Regra, parceiro: object, parceiro_nome: str) -> str:
    bruto = regra.esp_outros.strip()
    p = bruto.upper()
    if not p:
        return ""
    if p == "PARCEIRO<20":
        try:
            return "" if float(str(parceiro).replace(",", ".")) < 20 else ADV_PARCEIRO
        except (TypeError, ValueError):
            return ADV_PARCEIRO
    if p.startswith("PARCEIROINICIA"):
        alvo = bruto.partition(":")[2].strip()
        conforme = parceiro_nome[:len(alvo)].upper() == alvo.upper()
        return "" if conforme else ADV_PARCEIRO
    alvo = _prefixo(bruto, "SEMPRE:")
    if alvo is not None:
        return alvo
    if p.startswith("SECST:"):
        return ""                       # tratado na auditoria, por CST observado
    return ""


def mensagem_secst(regra: Regra, cst: str) -> str:
    """`SECST:20:texto` — o texto só aparece quando o CST observado casa."""
    alvo = _prefixo(regra.esp_outros.strip(), "SECST:")
    if alvo is None:
        return ""
    cst_alvo, sep, mensagem = alvo.partition(":")
    if not sep:
        return ""
    return mensagem.strip() if cst == cst_alvo.strip() else ""


# -- Camada 0: a rede que vale para todo registro -------------------------

def cst_exige_icms_positivo(cst: str, parametros: Parametros) -> bool:
    return cst in parametros.cst_exigem_icms_positivo


def coerencia_cst_icms(cst: str, icms: float, parametros: Parametros) -> str:
    """Regra A: CST que exige ICMS positivo tem que ter; os demais, zero."""
    if cst_exige_icms_positivo(cst, parametros):
        return "" if icms > 0 else ADV_ICMS
    return "" if icms == 0 else ADV_ICMS


def coerencia_cfop_operacao(cfop: str, operacao: str) -> str:
    """Regra B: o primeiro dígito do CFOP tem que combinar com INTRA/INTER.

    CFOP 3 e 7 (exterior) estão fora de escopo e não são conferidos.
    """
    if not cfop:
        return ""
    digito = cfop[0]
    if digito == "0":
        return ADV_PARCEIRO             # CFOP 0 não deveria existir
    if digito in ("1", "5"):
        return ADV_PARCEIRO if operacao not in ("INTRA", "INDEFINIDO") else ""
    if digito in ("2", "6"):
        return ADV_PARCEIRO if operacao not in ("INTER", "INDEFINIDO") else ""
    return ""


def cfop_de_industrializacao(operacao: str, cfop: str) -> str:
    """Produto cuja descrição começa com `Ind.` só circula em CFOP próprio."""
    if operacao == "INTRA" and cfop not in CFOP_INDUSTRIALIZACAO_INTRA:
        return "CFOP incorreto p/ produto de industrializacao"
    if operacao == "INTER" and cfop not in CFOP_INDUSTRIALIZACAO_INTER:
        return "CFOP incorreto p/ produto de industrializacao"
    return ""


# -- o texto da coluna "Auditoria" ----------------------------------------

def _descrever_predicado(p: str) -> str:
    alvo = _prefixo(p, "NAOEM:")
    if alvo is not None:
        return "diferente de {" + alvo + "}"
    alvo = _prefixo(p, "EM:")
    if alvo is not None:
        return "em {" + alvo + "}"
    return p[1:] if p.startswith("=") else p


def montar_auditoria(regra: Regra) -> str:
    """A frase que explica o que a regra esperava daquele registro."""
    s = f"{regra.operacao} - esperado"
    if regra.esp_cst:
        s += " CST " + _descrever_predicado(regra.esp_cst)
    if regra.esp_icms:
        if regra.esp_icms.upper() == "CARGA":
            s += ", ICMS conforme carga"
        else:
            s += ", ICMS " + regra.esp_icms
    if regra.esp_aliq:
        s += ", Aliquota " + regra.esp_aliq.replace(";", " ou ")
    if regra.esp_carga:
        s += f", Carga efetiva {regra.esp_carga}% (ICMS/Vlr contabil)"
    if regra.esp_outros:
        bruto = regra.esp_outros.strip()
        alvo = _prefixo(bruto, "SEMPRE:")
        if alvo is not None:
            return f"{regra.operacao} - {alvo}"
        if bruto.upper().startswith("SECST:"):
            return s                    # a mensagem entra só se o CST casar
        s += ", " + regra.esp_outros
    return s
