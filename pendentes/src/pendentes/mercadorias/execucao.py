"""O pipeline de ponta a ponta, e o que a tela mostra quando ele termina.

Dos arquivos arrastados até a planilha gravada, o livro atualizado e o
snapshot da semana. A ordem das etapas é a do VBA, porque a ordem **é** parte
da regra:

```
reconhecer os arquivos pelo cabeçalho de cada um
   ↓
ler o XML e a Conferência de Entradas; mapear as colunas por nome
   ↓
limpeza A1 → A3 → A2        ← antes do roteamento, e por um motivo
   ↓                          o que saiu vai para a aba `Descartados`
roteamento das 4 condições  ← a primeira verdadeira consome a linha
   ↓                          CTe · Manifestados · Entradas 3os
lookup do CE: 6 colunas     ← só sobre o que sobrou
   ↓
`Conf fiscal = Sim` sai para `Lançados`
   ↓
herança pelo livro → B1 (Fiscal) → B2 (split FIS-FAT)
   ↓
gravar a planilha, o livro e o snapshot imutável da semana
```

### O que este módulo devolve para a Central

Uma `Execucao`: título, fichas e listas, já em texto. A ferramenta não conhece
a Central — quem monta `Ficha` e `Lista` é o catálogo, do outro lado. É o
mesmo contrato que o DiXML, o Fiscalbot e o motor de serviços já cumprem.

### O que bloqueia o encerramento da semana

Nota que sobra depois das quatro condições **não** bloqueia: ela é o produto.
O que bloqueia é a ferramenta não conseguir dizer o que uma coisa é —
unidade não reconhecida, categoria fora da lista, guardião fora da lista
cadastrada e chave duplicada no CE cujas linhas divergem. Nesses casos a
planilha **é gravada**, a lista vermelha abre a tela e o snapshot registra
`encerravel: false`.

### O defeito 1 do porte fecha aqui

`[FATO]` No VBA, `ConstruirResumoExecutivo` aborta sem criar a aba e a etapa
seguinte executa `Sheets("Resumo Executivo").Activate` — erro 9 não tratado, o
`SaveAs` nunca acontece e **a execução inteira é perdida**, depois de uma
mensagem que fala só do resumo. Aqui a planilha é gravada antes de qualquer
coisa opcional, e nenhuma etapa posterior pode desfazê-la. O painel que
causava o problema, aliás, não existe mais neste porte.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

from .. import cabecalho as cab
from .. import escrita, estado, papeis, parametros, snapshot
from ..chaves import chave_de_acesso
from ..valores import numero_br
from . import classificacao, conferencia, limpeza, roteamento, vocabulario
from . import colunas as col
from . import fontes

#: O domínio, para o livro e para a pasta de snapshots.
DOMINIO = "mercadorias"

#: A aba da planilha da semana anterior que traz Fiscal e Faturamento. A outra
#: é a `Pendentes`, que é a que o papel do arquivo já exige.
ABA_FIS_FAT_ANTERIOR = "PENDENTES FIS-FAT"


class SemRegistros(Exception):
    """O relatório veio sem nenhuma linha de dado."""


@dataclass
class Execucao:
    """O que uma execução produziu — os números, as listas e os arquivos."""

    ano: int = 0
    semana: int = 0
    documentos: int = 0
    pendentes: int = 0
    fis_fat: int = 0
    lancados: int = 0
    descartados: int = 0
    valor_pendente: float = 0.0

    por_destino: dict[str, int] = field(default_factory=dict)
    farol: dict[str, int] = field(default_factory=dict)
    no_ce: int = 0

    # limpeza
    xml_de_terceiro: int = 0
    nfe_de_transporte: int = 0
    parceiros_sem_cadastro: int = 0

    # classificação
    herdadas: int = 0
    sem_classificacao: int = 0
    com_retorno: int = 0
    reclassificadas_para_fiscal: int = 0
    ingestao: estado.Ingestao | None = None

    # o que bloqueia
    nao_reconhecidos: vocabulario.NaoReconhecidos = field(
        default_factory=vocabulario.NaoReconhecidos)
    chaves_divergentes: list[str] = field(default_factory=list)

    # o que informa
    chaves_duplicadas: int = 0
    linhas_do_ce: int = 0
    avisos: list[str] = field(default_factory=list)

    planilha: Path | None = None
    pasta_do_snapshot: Path | None = None
    executada_em: str = ""

    @property
    def encerravel(self) -> bool:
        return not self.bloqueios()

    def bloqueios(self) -> list[str]:
        """O que impede encerrar a semana, em ordem de gravidade."""
        itens = list(self.nao_reconhecidos.bloqueios())
        if self.chaves_divergentes:
            mostradas = ", ".join(self.chaves_divergentes[:3])
            resto = len(self.chaves_divergentes) - 3
            itens.append(
                f"{len(self.chaves_divergentes)} chave(s) com mais de uma linha "
                f"na Conferência de Entradas, e as linhas divergem em pedido ou "
                f"farol — valeu a primeira: {mostradas}"
                + (f" e mais {resto}" if resto > 0 else "")
            )
        return itens

    def atencoes(self) -> list[str]:
        """O que degradou ou ficou de fora — sem bloquear."""
        itens = []
        if self.chaves_duplicadas:
            itens.append(
                f"{self.chaves_duplicadas} chave(s) com mais de uma linha na "
                f"Conferência de Entradas; a primeira valeu — divergência de "
                f"pedido ou farol entre elas: {len(self.chaves_divergentes)}"
            )
        if self.parceiros_sem_cadastro:
            itens.append(
                f"{self.parceiros_sem_cadastro} nota(s) de fornecedor sem "
                f"cadastro no ERP: o nome recebeu o CNPJ e o código recebeu "
                f"\"Sem cadastro\" (regra A2)"
            )
        return itens + list(self.avisos)

    def descarte(self) -> list[str]:
        """O que a limpeza tirou antes do roteamento. Hoje isto some sem rastro."""
        return [
            f"XML de terceiro (sem Nome Fantasia): {self.xml_de_terceiro}",
            f"NF-e destinada a transporte: {self.nfe_de_transporte}",
            "os dois grupos estão na aba \"Descartados\", com o motivo",
        ]

    def roteamento(self) -> list[str]:
        """Para onde as notas foram, na ordem em que as condições são avaliadas.

        É o teste de regressão visível deste domínio: quem roda confere o
        porte sem abrir teste nenhum, como a lista dos quatro procedimentos
        faz do lado de serviços.
        """
        itens = [f"{aba}: {self.por_destino.get(aba, 0)}"
                 for aba in col.ABAS_DO_ROTEAMENTO]
        itens.append(f"Lançados (Conf fiscal = Sim): {self.lancados}")
        itens.append(
            f"pendentes: {self.pendentes} nas áreas + {self.fis_fat} em "
            f"Fiscal/Faturamento"
        )
        return itens

    def conferencia(self) -> list[str]:
        """O casamento com o CE e os três estados do farol de pedido."""
        total = self.pendentes + self.fis_fat + self.lancados
        return [
            f"{self.no_ce} de {total} notas encontradas na Conferência de "
            f"Entradas ({self.linhas_do_ce} linhas lidas)",
            f"pedido confirmado: {self.farol.get('Sim', 0)} · não confirmado: "
            f"{self.farol.get('Não', 0)} · sem pedido vinculado: "
            f"{self.farol.get('sem pedido', 0)}",
        ]

    def heranca(self) -> list[str]:
        itens = [
            f"{self.herdadas} classificação(ões) vieram do livro · "
            f"{self.sem_classificacao} nota(s) sem classificação",
            f"{self.com_retorno} nota(s) trouxeram o retorno da semana anterior",
            f"{self.reclassificadas_para_fiscal} reclassificada(s) para Fiscal "
            f"pela regra B1",
        ]
        if self.ingestao is not None:
            relato = self.ingestao
            itens.append(
                f"a planilha da semana anterior devolveu {relato.lidas} linha(s): "
                f"{relato.novas} nova(s), {relato.alteradas} alterada(s), "
                f"{relato.preservadas} preservada(s) pelo livro"
            )
        return itens

    def titulo(self) -> str:
        total = self.pendentes + self.fis_fat
        return (f"Semana {self.semana} — "
                f"{_milhar(total)} nota{'s' if total != 1 else ''} pendente"
                f"{'s' if total != 1 else ''}, {_reais(self.valor_pendente)}")

    def fichas(self) -> list[tuple[str, str]]:
        return [
            ("Pendentes (áreas)", _milhar(self.pendentes)),
            ("Pendentes Fiscal/Fat.", _milhar(self.fis_fat)),
            ("Lançados na semana", _milhar(self.lancados)),
            ("Sem classificação", _milhar(self.sem_classificacao)),
        ]

    def listas(self) -> list[tuple[str, list[str], str]]:
        """Título, itens e tom — o vermelho primeiro, porque é o que trava."""
        saida = []
        bloqueios = self.bloqueios()
        if bloqueios:
            saida.append(("Bloqueiam o encerramento da semana", bloqueios, "erro"))
        atencoes = self.atencoes()
        if atencoes:
            saida.append(("Degradaram ou ficaram de fora", atencoes, "atencao"))
        saida.append(("Para onde as notas foram", self.roteamento(), "neutro"))
        saida.append(("Conferência de Entradas", self.conferencia(), "neutro"))
        saida.append(("Herança da classificação", self.heranca(), "neutro"))
        saida.append(("Descartados antes do roteamento", self.descarte(), "neutro"))
        return saida


def _milhar(n: int) -> str:
    return f"{n:,}".replace(",", ".")


def _reais(valor: float) -> str:
    inteiro = f"{valor:,.2f}"
    return "R$ " + inteiro.replace(",", "·").replace(".", ",").replace("·", ".")


def nome_sugerido(semana: int) -> str:
    """`Pendentes31.xlsx` — o nome que a macro dá, com a extensão que muda.

    `[FATO]` O VBA grava `.xls` 97-2003 (`FileFormat:=56`). O openpyxl não
    escreve `.xls`, `xlwt` está abandonado e ninguém consome o arquivo como
    `.xls` — o consumo é humano, por e-mail. A leitura de entrada continua
    aceitando `.xls`, que é o que o Sankhya entrega.
    """
    return f"Pendentes{semana}.xlsx"


# -- leitura das fontes -----------------------------------------------------

def _ler(reconhecido: papeis.Reconhecido, dados: dict, fonte: str,
         rotulo: str, ancora: str) -> tuple[list[list[Any]], cab.Mapa]:
    """Relê o arquivo inteiro, mapeia as colunas por nome e corta o rodapé."""
    inteiro = papeis.ler_inteiro(reconhecido)
    mapa = cab.mapear(inteiro.cabecalho, parametros.colunas_de(dados, fonte),
                      rotulo)
    return cab.ate_a_ultima(inteiro.dados, mapa, ancora), mapa


def _chave_de_heranca(valores: list[Any]) -> str:
    """A identidade de um documento entre semanas: a chave de acesso.

    Aqui, ao contrário de serviços, a chave é natural e não colide: são os 44
    dígitos do próprio documento. Ela é gravada **normalizada** no livro, que
    é nosso — o confronto com a Conferência de Entradas é que continua
    comparando o texto cru, porque lá há macro com que divergir.
    """
    return chave_de_acesso(valores[0])


def _ingerir_semana_anterior(reconhecido: papeis.Reconhecido,
                             livro: estado.Livro, semana: int,
                             responsavel: str | None,
                             avisos: list[str]) -> estado.Ingestao | None:
    """A planilha da semana passada volta para o livro, antes de tudo.

    As **duas** abas são lidas, e nesta ordem: primeiro a `PENDENTES FIS-FAT`,
    depois a `Pendentes`. A ordem reproduz a precedência do VBA, onde
    `dicAnt` (a `Pendentes`) é consultado antes de `dicAntFF` — aqui, quem
    entra por último no livro é quem vence onde as duas divergem.

    Falha de leitura **não** aborta: degrada com aviso contado, como o VBA já
    fazia com a FIS-FAT ausente — só que sem o silêncio.
    """
    inteiro = papeis.ler_inteiro(reconhecido)
    anterior = max(semana - 1, 0)
    relato: estado.Ingestao | None = None

    fis_fat = inteiro.arquivo.aba(ABA_FIS_FAT_ANTERIOR)
    if fis_fat is not None:
        linha = cab.localizar(fis_fat.linhas, (col.X_CHAVE,))
        if linha >= 0:
            relato = estado.ingerir(
                livro,
                estado.extrair_da_planilha(
                    fis_fat.linha(linha), fis_fat.linhas[linha + 1:],
                    colunas_da_chave=(col.X_CHAVE,),
                    montar_chave=_chave_de_heranca, semana=anterior),
                origem=f"planilha da semana {anterior} (FIS-FAT)",
                responsavel=responsavel)
        else:
            avisos.append(
                f"a aba {ABA_FIS_FAT_ANTERIOR} da planilha da semana anterior "
                f"não trouxe a coluna '{col.X_CHAVE}' — nada foi ingerido dela"
            )

    da_principal = estado.ingerir(
        livro,
        estado.extrair_da_planilha(
            inteiro.cabecalho, inteiro.dados,
            colunas_da_chave=(col.X_CHAVE,),
            montar_chave=_chave_de_heranca, semana=anterior),
        origem=f"planilha da semana {anterior}", responsavel=responsavel)

    if relato is None:
        return da_principal
    for campo in ("lidas", "novas", "alteradas", "preservadas", "inalteradas",
                  "retornos"):
        setattr(relato, campo, getattr(relato, campo) + getattr(da_principal, campo))
    relato.detalhes.extend(da_principal.detalhes)
    return relato


# -- o pipeline -------------------------------------------------------------

def gerar(arquivos: Iterable[Path | str], saida: Path | str, *,
          dados: dict | None = None, livro: estado.Livro | None = None,
          raiz_dos_dados: Path | None = None, responsavel: str | None = None,
          agora: datetime | None = None) -> Execucao:
    """Cruza XML e CE, monta as sete abas, grava a planilha, o livro e a semana."""
    agora = agora or datetime.now()
    dados = dados if dados is not None else parametros.carregar()
    literais = parametros.mercadorias(dados)
    ano, semana = parametros.semana_de(dados, agora.date())

    reconhecimento, _ = papeis.ler_e_reconhecer(
        arquivos, parametros.papeis_de(dados, DOMINIO))
    # Arquivo que não casou com papel nenhum roda com os demais — mas aparece
    # na tela nomeado. Regra nº 4: nada é decidido por semelhança, e nada some
    # em silêncio.
    avisos = [f"não reconheci {nome}; ele não entrou na execução"
              for nome in reconhecimento.nao_reconhecidos]

    linhas_do_xml, mapa_do_xml = _ler(
        reconhecimento["xml"], dados, "xml",
        "de importação de XML", col.X_NRO_NOTA)
    if not linhas_do_xml:
        raise SemRegistros(
            "O relatório de importação de XML não trouxe nenhuma linha de dados.")
    documentos = fontes.ler_documentos(linhas_do_xml, mapa_do_xml)
    if not documentos:
        raise SemRegistros(
            "Nenhuma linha do relatório de importação de XML tem 'Nro Nota'.")

    linhas_do_ce, mapa_do_ce = _ler(
        reconhecimento["conferencia_de_entradas"], dados,
        "conferencia_de_entradas", "de Conferência de Entradas", col.E_CHAVE)
    indice = conferencia.indexar(
        fontes.ler_conferencia(linhas_do_ce, mapa_do_ce),
        parametros.farol_de(dados, "pedido") or None)

    # -- limpeza, antes do roteamento -------------------------------------
    faxina = limpeza.limpar(
        documentos,
        tipo_nfe_de_transporte=literais["tipo_nfe_de_transporte"])

    # -- roteamento: a primeira condição verdadeira consome ---------------
    rotas = roteamento.rotear(
        faxina.mantidos,
        roteamento.condicoes_de(parametros.roteamento(dados)))

    # -- conferência, só sobre o que sobrou -------------------------------
    casaram = conferencia.anotar(
        rotas.pendentes, indice,
        ausente_da_conferencia=literais["ausente_da_conferencia"])
    lancados, restantes = roteamento.segregar_lancados(
        rotas.pendentes, literais["conf_fiscal_lancada"])

    # -- classificação: herança → B1 → B2 ---------------------------------
    livro = livro if livro is not None else estado.carregar(
        DOMINIO, raiz=raiz_dos_dados)
    relato = None
    if reconhecimento.tem("semana_anterior_mercadorias"):
        try:
            relato = _ingerir_semana_anterior(
                reconhecimento["semana_anterior_mercadorias"], livro, semana,
                responsavel, avisos)
        except cab.ColunasFaltando as erro:
            avisos.append(
                f"a planilha da semana anterior não trouxe a coluna de "
                f"identidade — nada foi ingerido. {erro}".replace("\n", " ")
            )
    else:
        avisos.append(
            "não veio planilha da semana anterior; a classificação vem só do "
            "livro da ferramenta"
        )

    heranca = classificacao.herdar(restantes, livro)
    reclassificadas = classificacao.reclassificar_para_fiscal(
        restantes,
        conferencia_fisica_confirmada=literais["conferencia_fisica_confirmada"],
        guardiao=literais["guardiao_da_reclassificacao"])
    para_fis_fat, pendentes = classificacao.dividir_fis_fat(
        restantes, literais["guardioes_da_fis_fat"])

    execucao = Execucao(
        ano=ano, semana=semana, documentos=len(documentos),
        pendentes=len(pendentes), fis_fat=len(para_fis_fat),
        lancados=len(lancados), descartados=faxina.total_descartado,
        por_destino={aba: rotas.quantos_em(aba)
                     for aba in col.ABAS_DO_ROTEAMENTO},
        farol=conferencia.farois(lancados + restantes),
        no_ce=casaram,
        xml_de_terceiro=faxina.por_xml_de_terceiro,
        nfe_de_transporte=faxina.por_nfe_de_transporte,
        parceiros_sem_cadastro=faxina.parceiros_sem_cadastro,
        herdadas=heranca.herdadas, sem_classificacao=heranca.sem_classificacao,
        com_retorno=heranca.com_retorno,
        reclassificadas_para_fiscal=reclassificadas,
        ingestao=relato,
        chaves_duplicadas=len(indice.chaves_duplicadas),
        chaves_divergentes=list(indice.chaves_divergentes),
        linhas_do_ce=indice.linhas,
        avisos=avisos,
        executada_em=agora.strftime("%Y-%m-%d %H:%M:%S"),
    )
    execucao.valor_pendente = sum(
        numero_br(documento.de(col.X_VALOR))
        for documento in pendentes + para_fis_fat)

    # O que a ferramenta não soube dizer o que é — e que trava a semana.
    posicao_do_guardiao = col.indice(col.categorizacao(0), col.C_GUARDIAO)
    posicao_da_categoria = col.indice(col.categorizacao(0), col.C_CATEGORIA)
    execucao.nao_reconhecidos = vocabulario.conferir(
        ((documento.de(col.X_NOME_FANTASIA),
          documento.categorizacao[posicao_da_categoria],
          documento.categorizacao[posicao_do_guardiao])
         for documento in pendentes + para_fis_fat),
        unidades=parametros.unidades(dados),
        categorias=parametros.categorias(dados),
        guardioes=parametros.guardioes(dados),
    )

    # -- a planilha, antes de qualquer coisa opcional ---------------------
    execucao.planilha = _escrever(
        Path(saida) / nome_sugerido(semana), semana,
        pendentes=pendentes, fis_fat=para_fis_fat, lancados=lancados,
        rotas=rotas, descartados=faxina.descartados,
    )

    estado.gravar(livro, responsavel, raiz=raiz_dos_dados)
    execucao.pasta_do_snapshot = snapshot.gravar(
        DOMINIO, ano, semana,
        planilha=execucao.planilha, livro=livro,
        entradas=_impressoes(reconhecimento),
        resumo={
            "titulo": execucao.titulo(),
            "fichas": dict(execucao.fichas()),
            "roteamento": execucao.por_destino,
            "farol": execucao.farol,
            "valor_pendente": round(execucao.valor_pendente, 2),
            "descartados": {
                "xml_de_terceiro": execucao.xml_de_terceiro,
                "nfe_de_transporte": execucao.nfe_de_transporte,
            },
            "bloqueios": execucao.bloqueios(),
            "atencoes": execucao.atencoes(),
        },
        encerravel=execucao.encerravel,
        raiz=raiz_dos_dados,
    )
    return execucao


def _escrever(caminho: Path, semana: int, *,
              pendentes: list[fontes.Documento],
              fis_fat: list[fontes.Documento],
              lancados: list[fontes.Documento],
              rotas: roteamento.Roteamento,
              descartados: list[fontes.Documento]) -> Path:
    """As sete abas, na ordem do VBA, com as larguras de cada uma.

    `Pendentes` e `PENDENTES FIS-FAT` saem centralizadas, com borda pontilhada
    e cabeçalho em negrito — é o `FormatarSheetPendentes`. As auxiliares saem
    como cópia crua, que é o que a etapa 11 do VBA faz, e **ocultas**: elas são
    evidência para auditoria, e ocultar não é apagar.
    """
    principal = escrita.Estilo(centralizar=True, bordas=True)
    caderno = escrita.novo_livro()
    conteudo: dict[str, tuple] = {
        "Pendentes": (col.pendentes(semana),
                      [d.linha_pendente() for d in pendentes], principal),
        "CTe": (col.AUXILIARES,
                [d.linha_auxiliar() for d in rotas.destinos.get("CTe", ())], None),
        "Manifestados": (
            col.AUXILIARES,
            [d.linha_auxiliar() for d in rotas.destinos.get("Manifestados", ())],
            None),
        "Entradas 3os": (
            col.AUXILIARES,
            [d.linha_auxiliar() for d in rotas.destinos.get("Entradas 3os", ())],
            None),
        "Lançados": (col.LANCADOS, [d.linha_lancada() for d in lancados], None),
        "PENDENTES FIS-FAT": (col.fis_fat(semana),
                              [d.linha_fis_fat() for d in fis_fat], principal),
        "Descartados": (col.DESCARTADOS,
                        [d.linha_descartada() for d in descartados], None),
    }
    for nome, visivel in col.ABAS:
        colunas, linhas, estilo = conteudo[nome]
        escrita.escrever_aba(caderno, nome, colunas, linhas,
                             oculta=not visivel, estilo=estilo)
    return escrita.salvar(caderno, caminho)


def _impressoes(reconhecimento: papeis.Reconhecimento
                ) -> list[snapshot.EntradaDaSemana]:
    """Nome, tamanho e SHA-256 de cada entrada, com o papel reconhecido."""
    return [
        snapshot.impressao_de(achado.arquivo.caminho, papel_id)
        for papel_id, achado in reconhecimento.por_papel.items()
    ]
