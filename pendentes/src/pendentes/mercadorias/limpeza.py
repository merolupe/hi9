"""A limpeza — A1, A2 e A3 — e a aba `Descartados`, que é a única aba nova.

As três regras rodam num laço só, **antes do roteamento**, e nessa ordem. Cada
uma dessas afirmações carrega uma decisão do VBA que o comentário do próprio
código justifica:

| Regra | O que faz | Por que a ordem importa |
|---|---|---|
| **A1** | `Nome Fantasia` vazio → a linha sai | se rodasse depois do roteamento, um XML de terceiro com `Entrada/Saida NF-e = "Entrada"` já teria ido para `Entradas 3os` e sobreviveria lá |
| **A3** | `Tipo NF-e` = `NF-e Destinada a Transporte` → a linha sai | o comentário da v8.0 é literal: "aplicado antes do roteamento, para que não vazem para as sheets CTe / Manifestados / Entradas 3os" |
| **A2** | `Nome Parceiro` vazio → recebe o CNPJ, e `Cód. Parceiro` recebe `Sem cadastro` | roda só no ramo `Else` da exclusão: não se conserta o cadastro de uma linha que vai sair |

**A1 é avaliada antes de A3**, e isso também é ordem com consequência: quando
a fantasia está vazia a linha já sai, e `Tipo NF-e` nem chega a ser consultado.

### O que muda em relação ao VBA

Uma coisa, e é acréscimo: **as linhas descartadas passam a ir para a aba
`Descartados`, com o motivo**. `[FATO]` Hoje elas somem — a exclusão é física,
não há contador, não há aba e a mensagem final não reporta volume descartado.
O próprio dossiê registra a limitação nestes termos: *não há como medir volume
descartado por semana*. Nenhuma aba existente muda; a nova nasce oculta, como
as outras auxiliares, e é reexibível por clique direito.

### O que **não** muda, de propósito

A comparação de A3 é tolerante a caixa e a espaço — porque `vbTextCompare` e
`NormalizarTexto` são o que o VBA usa — e **não** é tolerante a acento. Quem
comparasse por `chave_de_texto` estaria uniformizando por conta própria uma
comparação que o time nunca mediu. É o defeito 10 do porte, e ele espera
medição sobre arquivo real antes de mexer.

A degradação silenciosa da A2 — gravar o CNPJ **sem** a marca `Sem cadastro`
quando `Cód. Parceiro` não existe na saída — não é reproduzível aqui, e não
por escolha: as 27 colunas do XML são igualmente obrigatórias, e a execução
aborta antes se alguma faltar. O caminho degradado não ocorre hoje nem lá.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from ..chaves import SEM_CADASTRO
from ..texto import aparar, texto_de
from . import colunas as col
from .fontes import Documento

#: O motivo que vai para a aba `Descartados`, um por regra.
MOTIVO_XML_DE_TERCEIRO = "XML de terceiro (sem Nome Fantasia)"
MOTIVO_NFE_DE_TRANSPORTE = "NF-e destinada a transporte"


@dataclass
class Limpeza:
    """O que a limpeza tirou, o que ela consertou e o que sobrou."""

    mantidos: list[Documento] = field(default_factory=list)
    descartados: list[Documento] = field(default_factory=list)
    por_xml_de_terceiro: int = 0
    por_nfe_de_transporte: int = 0
    parceiros_sem_cadastro: int = 0

    @property
    def total_descartado(self) -> int:
        return len(self.descartados)


def _igual_ignorando_caixa(valor, alvo: str) -> bool:
    """`StrComp(NormalizarTexto(v), alvo, vbTextCompare) = 0`, sem mais nada.

    Espaço múltiplo e ponta somem, caixa não importa — e **acento importa**.
    É a comparação do VBA, com o alcance que ela tem hoje.
    """
    return aparar(valor).casefold() == aparar(alvo).casefold()


def limpar(documentos: list[Documento], *,
           tipo_nfe_de_transporte: str) -> Limpeza:
    """Roda A1, A3 e A2 num laço só, nessa ordem, antes do roteamento."""
    relato = Limpeza()

    for documento in documentos:
        # A1 — XML emitido para um CNPJ que não é o da Hinove, importado
        # manualmente por engano. `Nome Fantasia` é quem identifica a empresa
        # destinatária; sem ela, o documento não é nosso.
        if not texto_de(documento.de(col.X_NOME_FANTASIA)).strip():
            documento.motivo_do_descarte = MOTIVO_XML_DE_TERCEIRO
            relato.descartados.append(documento)
            relato.por_xml_de_terceiro += 1
            continue

        # A3 — NF-e emitida por terceiro que informa o CNPJ da Hinove no grupo
        # <transporta>. A captura DF-e recolhe o documento por CNPJ vinculado,
        # mas a Hinove não é destinatária: não é entrada de mercadoria.
        if _igual_ignorando_caixa(documento.de(col.X_TIPO_NFE),
                                  tipo_nfe_de_transporte):
            documento.motivo_do_descarte = MOTIVO_NFE_DE_TRANSPORTE
            relato.descartados.append(documento)
            relato.por_nfe_de_transporte += 1
            continue

        # A2 — fornecedor sem cadastro no ERP. O nome vazio recebe o CNPJ, e o
        # código recebe o literal que torna a ausência explícita: sem ele o
        # registro pareceria íntegro, que é o que a regra quer evitar.
        if not texto_de(documento.de(col.X_NOME_PARCEIRO)).strip():
            documento.definir(col.X_NOME_PARCEIRO,
                              texto_de(documento.de(col.X_CNPJ_PARCEIRO)))
            documento.definir(col.X_COD_PARCEIRO, SEM_CADASTRO)
            relato.parceiros_sem_cadastro += 1

        relato.mantidos.append(documento)

    return relato
