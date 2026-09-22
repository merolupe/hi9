"""O pipeline de ponta a ponta, e o que a tela mostra quando ele termina.

Da pasta de arquivos arrastados até a planilha gravada, o livro atualizado e o
snapshot da semana. A ordem das etapas é a do VBA, porque a ordem **é** parte
da regra:

```
reconhecer os arquivos pelo cabeçalho de cada um
   ↓
ler ASIS e Portal de Compras; mapear as colunas por nome
   ↓
indexar: cadastro de parceiro, de-para de filial, pedido mais recente,
         e os três índices do confronto sobre os lançamentos
   ↓
segregar as canceladas      ← antes da cascata, e por um motivo
   ↓
a cascata dos quatro procedimentos, POR PASSOS
   ↓
montar as quatro abas; herdar a classificação do livro; vincular ao pedido
   ↓
gravar a planilha, o livro e o snapshot imutável da semana
```

### O que este módulo devolve para a Central

Um `Painel`: o título, as fichas e as listas, já em texto. A ferramenta não
conhece a Central — quem monta `Ficha` e `Lista` é o catálogo, do outro lado.
É o mesmo contrato que o DiXML e o Fiscalbot já cumprem.

### O que bloqueia o encerramento da semana

Nota que não casou com nada **não** bloqueia: ela é o produto. O que bloqueia
é a ferramenta não conseguir dizer o que uma coisa é — confronto por chave
fraca, chave duplicada no Sankhya, vínculo de pedido ambíguo e CNPJ de tomador
sem filial. Nesses casos a planilha **é gravada**, a lista vermelha abre a
tela, e o snapshot registra `encerravel: false`.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, Sequence

from .. import cabecalho as cab
from .. import escrita, estado, papeis, parametros, snapshot
from ..texto import aparar
from . import colunas as col
from . import confronto as casc
from . import enriquecimento, exclusao, fontes, inversa, vinculo

#: O domínio, para o livro e para a pasta de snapshots.
DOMINIO = "servicos"


class SemRegistros(Exception):
    """O relatório veio sem nenhuma linha de dado, ou sem o que confrontar."""


@dataclass
class Execucao:
    """O que uma execução produziu — os números, as listas e os arquivos."""

    ano: int = 0
    semana: int = 0
    notas: int = 0
    lancamentos: int = 0
    lancadas: int = 0
    pendentes: int = 0
    canceladas: int = 0
    sem_correspondencia: int = 0
    #: Notas que saíram da `Pendentes` depois da cascata, por motivo.
    fora_do_relatorio: dict[str, int] = field(default_factory=dict)
    por_procedimento: dict[int, int] = field(default_factory=dict)
    herdadas: int = 0
    vinculadas: int = 0
    valor_pendente: float = 0.0

    # o que bloqueia
    por_chave_fraca: int = 0
    chaves_duplicadas: int = 0
    vinculos_ambiguos: int = 0
    filiais_nao_mapeadas: list[str] = field(default_factory=list)

    # o que informa
    cnpj_descartados: int = 0
    datas_ilegiveis: int = 0
    numeros_com_corte_de_ano: int = 0
    pedidos_de_outra_filial: int = 0
    colisoes_de_identidade: int = 0
    avisos: list[str] = field(default_factory=list)
    ingestao: estado.Ingestao | None = None

    planilha: Path | None = None
    pasta_do_snapshot: Path | None = None
    executada_em: str = ""

    @property
    def encerravel(self) -> bool:
        return not self.bloqueios()

    def bloqueios(self) -> list[str]:
        """O que impede encerrar a semana, em ordem de gravidade."""
        itens = []
        if self.por_chave_fraca:
            itens.append(
                f"{self.por_chave_fraca} confronto(s) por nota+valor sem CNPJ "
                f"(procedimento 4) — a chave é fraca e o match exige revisão"
            )
        if self.chaves_duplicadas:
            itens.append(
                f"{self.chaves_duplicadas} lançamento(s) casados por chave "
                f"nota+CNPJ duplicada no Sankhya — pode ter sido o lançamento "
                f"errado entre dois homônimos"
            )
        if self.vinculos_ambiguos:
            itens.append(
                f"{self.vinculos_ambiguos} vínculo(s) de pedido ambíguos — "
                f"mais de um pedido da Conferência serve à mesma nota"
            )
        if self.filiais_nao_mapeadas:
            mostrados = ", ".join(self.filiais_nao_mapeadas[:5])
            resto = len(self.filiais_nao_mapeadas) - 5
            itens.append(
                f"{len(self.filiais_nao_mapeadas)} CNPJ de tomador sem filial "
                f"no de-para: {mostrados}" + (f" e mais {resto}" if resto > 0 else "")
            )
        return itens

    def atencoes(self) -> list[str]:
        """O que ficou de fora da análise, ou degradou — sem bloquear."""
        itens = []
        if self.cnpj_descartados:
            itens.append(
                f"{self.cnpj_descartados} lançamento(s) de serviço com CNPJ "
                f"vazio ou zerado ficaram fora do confronto e da aba inversa"
            )
        if self.datas_ilegiveis:
            itens.append(
                f"{self.datas_ilegiveis} data(s) de emissão não interpretáveis, "
                f"mantidas como texto na célula"
            )
        if self.numeros_com_corte_de_ano:
            itens.append(
                f"{self.numeros_com_corte_de_ano} número(s) de nota tiveram o "
                f"prefixo de ano de 4 dígitos removido para o confronto"
            )
        if self.pedidos_de_outra_filial:
            itens.append(
                f"{self.pedidos_de_outra_filial} nota(s) receberam pedido de "
                f"compra de uma filial diferente da sua"
            )
        if self.colisoes_de_identidade:
            itens.append(
                f"{self.colisoes_de_identidade} registro(s) do livro mudaram de "
                f"CNPJ: dois prestadores distintos compartilham a mesma chave "
                f"nota+código de parceiro"
            )
        return itens + list(self.avisos)

    def confronto_por_procedimento(self) -> list[str]:
        """A soma tem de dar `Lançadas`. É o teste de regressão visível."""
        return [
            f"{numero} ({casc.NOMES[numero]}): {quantas}"
            for numero, quantas in sorted(self.por_procedimento.items())
        ]

    def heranca(self) -> list[str]:
        itens = [f"{self.herdadas} de {self.pendentes} pendentes herdaram "
                 f"Guardião / Gestor / Retorno do livro"]
        if self.ingestao is not None:
            relato = self.ingestao
            itens.append(
                f"a planilha da semana anterior devolveu {relato.lidas} linha(s): "
                f"{relato.novas} nova(s), {relato.alteradas} alterada(s), "
                f"{relato.preservadas} preservada(s) pelo livro"
            )
        return itens

    def titulo(self) -> str:
        return (f"Semana {self.semana} — "
                f"{_contadas(self.notas, 'nota', 'notas')} do ASIS "
                f"{'confrontada' if self.notas == 1 else 'confrontadas'} com "
                f"{_contadas(self.lancamentos, 'lançamento', 'lançamentos')} "
                f"de serviço")

    def fichas(self) -> list[tuple[str, str]]:
        return [
            ("Lançadas", _milhar(self.lancadas)),
            ("Pendentes", _milhar(self.pendentes)),
            ("Canceladas", _milhar(self.canceladas)),
            ("Fora do relatório", _milhar(sum(self.fora_do_relatorio.values()))),
            ("Sem correspondência ASIS", _milhar(self.sem_correspondencia)),
        ]

    def listas(self) -> list[tuple[str, list[str], str]]:
        """Título, itens e tom — o vermelho primeiro, porque é o que trava."""
        saida = []
        bloqueios = self.bloqueios()
        if bloqueios:
            saida.append(("Exigem revisão manual antes de encerrar a semana",
                          bloqueios, "erro"))
        atencoes = self.atencoes()
        if atencoes:
            saida.append(("Ficaram de fora da análise, ou degradaram",
                          atencoes, "atencao"))
        saida.append(("Confronto por procedimento",
                      self.confronto_por_procedimento(), "neutro"))
        if self.fora_do_relatorio:
            saida.append((
                "Fora do relatório, com o motivo",
                [f"{quantas} — {motivo}" for motivo, quantas
                 in sorted(self.fora_do_relatorio.items(), key=lambda t: -t[1])],
                "neutro",
            ))
        saida.append(("Herança da classificação", self.heranca(), "neutro"))
        if self.vinculadas:
            saida.append((
                "Vínculo com a Conferência de Serviços",
                [f"{self.vinculadas} de {self.pendentes} pendentes já estão "
                 f"anexadas a um pedido de compra"],
                "neutro",
            ))
        return saida


def _milhar(n: int) -> str:
    return f"{n:,}".replace(",", ".")


def _contadas(n: int, singular: str, plural: str) -> str:
    """`1 nota` e `2.797 lançamentos` — o título é a primeira coisa que se lê."""
    return f"{_milhar(n)} {singular if n == 1 else plural}"


def nome_sugerido(agora: datetime | None = None) -> str:
    """O nome que a macro dá ao arquivo, e que o time já reconhece."""
    agora = agora or datetime.now()
    return f"Notas_Servico_Pendentes_{agora:%Y%m%d_%H%M}.xlsx"


# -- leitura das fontes -----------------------------------------------------

def _ler(reconhecido: papeis.Reconhecido, dados: dict, fonte: str,
         rotulo: str, ancora: str) -> tuple[list[Any], list[list[Any]], cab.Mapa]:
    """Relê o arquivo inteiro **uma vez**, mapeia as colunas e corta o rodapé.

    Uma vez, e não duas: o Portal de Compras chega a 268 colunas por milhares
    de linhas, e a aba inversa precisa do cabeçalho dele inteiro — devolvê-lo
    junto evita reabrir o arquivo só para lê-lo de novo.
    """
    inteiro = papeis.ler_inteiro(reconhecido)
    mapa = cab.mapear(inteiro.cabecalho, parametros.colunas_de(dados, fonte),
                      rotulo)
    cabecalho = list(inteiro.cabecalho)
    return cabecalho, fontes.ate_a_ultima(inteiro.dados, mapa, ancora), mapa


def _chave_de_heranca(numero: str, codigo_do_parceiro: str) -> str:
    """`número normalizado | código do parceiro` — a identidade entre semanas.

    **Não** é número + CNPJ, por mais natural que pareça: a aba `Pendentes`
    não carrega o CNPJ do prestador, e a chave precisa ser reconstruível a
    partir da planilha que o time devolve editada. O comentário do VBA
    registra a mesma decisão, com as mesmas palavras.
    """
    return f"{numero}|{aparar(codigo_do_parceiro)}"


def _ingerir_semana_anterior(reconhecido: papeis.Reconhecido, dados: dict,
                             livro: estado.Livro, semana: int,
                             responsavel: str | None) -> estado.Ingestao:
    """A planilha da semana passada volta para o livro, antes de tudo.

    É a metade de volta do ciclo: a planilha sai do livro na segunda e volta
    para ele na quarta, com o que o time escreveu. Falha de leitura aqui
    **não** aborta a execução — degrada com aviso, como o VBA já fazia.

    O arquivo só chega aqui se já tiver sido reconhecido como planilha da
    semana anterior, o que exige `Nro Nota` e `Guardiao` no cabeçalho. O que
    ainda pode faltar é o `Cod Parceiro`, que é a outra metade da identidade —
    e sem ele não há chave, então a ingestão não acontece e a tela diz por quê.

    São **duas** abas: a `Pendentes` e a `Fora do relatorio`. A segunda é o
    que faz a nota cancelada na prefeitura continuar fora na semana seguinte
    mesmo se o livro for perdido — e é o que permite alguém marcar uma nota
    como cancelada escrevendo direto nela.
    """
    inteiro = papeis.ler_inteiro(reconhecido)
    anterior = max(semana - 1, 0)
    montar = lambda valores: _chave_de_heranca(                 # noqa: E731
        fontes.analisar_numero_de_nfse(valores[0]).valor, valores[1])

    # A aba de exclusões vem primeiro, como a FIS-FAT em mercadorias: quem
    # entra por último vence onde as duas divergirem. Uma nota que estava
    # fora e voltou para a `Pendentes` já classificada é a pessoa desfazendo
    # a exclusão, e desfazer tem de valer.
    relato: estado.Ingestao | None = None
    fora = inteiro.arquivo.aba(col.ABA_FORA_DO_RELATORIO)
    if fora is not None:
        linha = cab.localizar(fora.linhas, (col.S_NUMERO_NOTA,))
        if linha >= 0:
            relato = estado.ingerir(
                livro,
                estado.extrair_da_planilha(
                    fora.linha(linha), fora.linhas[linha + 1:],
                    colunas_da_chave=col.S_CHAVE, montar_chave=montar,
                    semana=anterior),
                origem=f"aba {col.ABA_FORA_DO_RELATORIO} da semana {anterior}",
                responsavel=responsavel)

    da_principal = estado.ingerir(
        livro,
        estado.extrair_da_planilha(
            inteiro.cabecalho, inteiro.dados,
            colunas_da_chave=col.S_CHAVE, montar_chave=montar, semana=anterior),
        origem=f"planilha da semana {anterior}", responsavel=responsavel)

    if relato is None:
        return da_principal
    for campo in ("lidas", "novas", "alteradas", "preservadas", "inalteradas",
                  "retornos"):
        setattr(relato, campo,
                getattr(relato, campo) + getattr(da_principal, campo))
    relato.detalhes.extend(da_principal.detalhes)
    return relato


# -- montagem das linhas ----------------------------------------------------

def _linha_lancada(nota: fontes.NotaDeServico, lancamento: fontes.Registro,
                   procedimento: int, duplicada: bool) -> list[Any]:
    return [
        lancamento.numero_bruto,
        nota.emissao,
        lancamento.codigo_do_parceiro,
        lancamento.nome_do_parceiro,
        lancamento.valor,
        nota.municipio,
        lancamento.empresa,
        # Literal em 100% das linhas: as canceladas saem antes da cascata e
        # nunca chegam aqui. Preservada porque a largura da aba é invariante.
        "Nao",
        nota.codigo_lei116,
        nota.descricao_do_servico,
        procedimento,
        "Chave nota+CNPJ duplicada no Sankhya" if duplicada else "",
    ]


def _linha_cancelada(nota: fontes.NotaDeServico,
                     cadastro: enriquecimento.Cadastro) -> list[Any]:
    """As 16 colunas da `Canceladas` — **não** são as da `Pendentes` mais duas."""
    pedido = cadastro.pedido_de(nota.cnpj_do_prestador)
    return [
        nota.numero,
        nota.emissao,
        cadastro.codigo_do_parceiro(nota.cnpj_do_prestador),
        cadastro.nome_do_parceiro(nota.cnpj_do_prestador, nota.prestador),
        nota.valor,
        nota.municipio,
        cadastro.filial_de(nota.cnpj_do_tomador),
        pedido.numero_unico if pedido else enriquecimento.SEM_PEDIDO,
        pedido.comprador if pedido else "",
        pedido.requisitante if pedido else "",
        pedido.natureza if pedido else "",
        pedido.centro_de_resultado if pedido else "",
        nota.descricao_do_servico,
        nota.discriminacao,
        nota.data_de_cancelamento,
        nota.motivo_do_cancelamento,
    ]


def _linha_pendente(nota: fontes.NotaDeServico,
                    cadastro: enriquecimento.Cadastro,
                    classificacao: estado.Classificacao,
                    ligacao: vinculo.Vinculo) -> list[Any]:
    pedido = cadastro.pedido_de(nota.cnpj_do_prestador)
    return [
        nota.numero,
        nota.emissao,
        cadastro.codigo_do_parceiro(nota.cnpj_do_prestador),
        cadastro.nome_do_parceiro(nota.cnpj_do_prestador, nota.prestador),
        classificacao.guardiao,
        classificacao.gestor_de_apoio,
        classificacao.ultimo_retorno,
        nota.valor,
        nota.municipio,
        cadastro.filial_de(nota.cnpj_do_tomador),
        pedido.numero_unico if pedido else enriquecimento.SEM_PEDIDO,
        pedido.comprador if pedido else "",
        pedido.requisitante if pedido else "",
        nota.discriminacao,
        pedido.natureza if pedido else "",
        pedido.centro_de_resultado if pedido else "",
        nota.descricao_do_servico,
        *nota.tributos,
        nota.codigo_verificador,
        *ligacao.como_colunas(),
    ]


# -- o pipeline -------------------------------------------------------------

def gerar(arquivos: Iterable[Path | str], saida: Path | str, *,
          dados: dict | None = None, livro: estado.Livro | None = None,
          raiz_dos_dados: Path | None = None, responsavel: str | None = None,
          agora: datetime | None = None) -> Execucao:
    """Confronta, monta as quatro abas, grava a planilha, o livro e a semana."""
    agora = agora or datetime.now()
    dados = dados if dados is not None else parametros.carregar()
    ajuste = parametros.confronto_de_servicos(dados)
    ano, semana = parametros.semana_de(dados, agora.date())

    reconhecimento, _ = papeis.ler_e_reconhecer(
        arquivos, parametros.papeis_de(dados, DOMINIO))
    # Arquivo que não casou com papel nenhum roda com os demais — mas aparece
    # na tela nomeado. Regra nº 4: nada é decidido por semelhança, e nada
    # some em silêncio.
    nao_reconhecidos = [
        f"não reconheci {nome}; ele não entrou na execução"
        for nome in reconhecimento.nao_reconhecidos
    ]

    _, linhas_asis, mapa_asis = _ler(reconhecimento["asis"], dados, "asis",
                                     "ASIS (notas emitidas)", col.ANCORA_ASIS)
    if not linhas_asis:
        raise SemRegistros("O relatório ASIS não trouxe nenhuma linha de dados.")
    notas = fontes.ler_notas(linhas_asis, mapa_asis)

    cabecalho_pc, linhas_pc, mapa_pc = _ler(
        reconhecimento["portal_de_compras"], dados, "portal_de_compras",
        "Portal de Compras", col.ANCORA_PORTAL)
    if not linhas_pc:
        raise SemRegistros(
            "O relatório do Portal de Compras não trouxe nenhuma linha de dados.")
    registros = fontes.ler_registros(linhas_pc, mapa_pc)

    cadastro = enriquecimento.cadastrar(
        registros, tops=ajuste["tops_de_lancamento"],
        prefixo_de_pedido=ajuste["prefixo_de_pedido"],
        cnpj_descartado=ajuste["cnpj_descartado"],
        complemento_de_filiais=parametros.filiais(dados),
    )
    lancamentos = enriquecimento.lancamentos_de(
        registros, ajuste["tops_de_lancamento"], ajuste["cnpj_descartado"])
    if not lancamentos:
        tops = "/".join(ajuste["tops_de_lancamento"])
        raise SemRegistros(
            f"Nenhum lançamento de serviço (TOP {tops}) no Portal de Compras. "
            f"Confira os TOPs cadastrados na tela de configuração."
        )

    from .chaves import chave_de_nota_e_cnpj, indexar

    indices = indexar(lancamentos)
    resultado = casc.confrontar(notas, lancamentos, indices)

    # A Conferência de Serviços é opcional, e a falta de **qualquer** coluna
    # dela desliga só o bloco — o VBA aborta a execução inteira, e é um dos
    # defeitos que este porte corrige.
    anexos: list[fontes.Anexo] = []
    indice_da_conferencia: dict[str, list[int]] = {}
    conferencia_lida = False
    avisos: list[str] = list(nao_reconhecidos)
    if reconhecimento.tem("conferencia_de_servicos"):
        try:
            _, linhas_conf, mapa_conf = _ler(
                reconhecimento["conferencia_de_servicos"], dados,
                "conferencia_de_servicos", "Conferência de Serviços",
                col.ANCORA_CONFERENCIA)
            anexos = fontes.ler_anexos(linhas_conf, mapa_conf)
            indice_da_conferencia = vinculo.indexar(anexos)
            conferencia_lida = bool(anexos)
        except (cab.ColunasFaltando, cab.CabecalhoNaoEncontrado) as erro:
            avisos.append(
                f"não consegui ler a Conferência de Serviços — as colunas de "
                f"vínculo (29 a 36) saíram vazias. {erro}".replace("\n", " ")
            )
    else:
        avisos.append(
            "a Conferência de Serviços não veio — as colunas de vínculo "
            "(29 a 36) saíram vazias"
        )

    livro = livro if livro is not None else estado.carregar(
        DOMINIO, raiz=raiz_dos_dados)
    relato = None
    if reconhecimento.tem("semana_anterior_servicos"):
        try:
            relato = _ingerir_semana_anterior(
                reconhecimento["semana_anterior_servicos"], dados, livro,
                semana, responsavel)
        except cab.ColunasFaltando as erro:
            avisos.append(
                f"a planilha da semana anterior não trouxe as colunas de "
                f"identidade — nada foi ingerido. {erro}".replace("\n", " ")
            )
    else:
        avisos.append(
            "não veio planilha da semana anterior; a classificação vem só do "
            "livro da ferramenta"
        )

    execucao = Execucao(
        ano=ano, semana=semana, notas=len(notas), lancamentos=len(lancamentos),
        lancadas=resultado.lancadas, pendentes=resultado.pendentes,
        canceladas=resultado.canceladas,
        sem_correspondencia=resultado.sem_correspondencia,
        por_procedimento=resultado.por_procedimento(),
        cnpj_descartados=cadastro.descartados_por_cnpj,
        avisos=avisos, ingestao=relato,
        executada_em=agora.strftime("%Y-%m-%d %H:%M:%S"),
    )
    execucao.por_chave_fraca = execucao.por_procedimento.get(
        casc.PROCEDIMENTO_FRACO, 0)
    execucao.numeros_com_corte_de_ano = sum(
        1 for nota in notas if nota.cortou_prefixo_de_ano)
    execucao.datas_ilegiveis = sum(
        1 for nota in notas if nota.emissao and not nota.emissao_e_data)

    fora_do_mapa: list[str] = []
    linhas_lancadas: list[list[Any]] = []
    linhas_pendentes: list[list[Any]] = []
    linhas_canceladas: list[list[Any]] = []
    linhas_fora: list[list[Any]] = []
    excecoes = parametros.excecoes_de_servicos(dados)

    for posicao, nota in enumerate(notas):
        procedimento = resultado.procedimento[posicao]

        if procedimento == casc.CANCELADA:
            linhas_canceladas.append(_linha_cancelada(nota, cadastro))
            continue

        if procedimento > casc.PENDENTE:
            lancamento = lancamentos[resultado.lancamento[posicao]]
            duplicada = indices.nota_e_cnpj.duplicada(chave_de_nota_e_cnpj(
                lancamento.numero, lancamento.cnpj_do_parceiro))
            if duplicada:
                execucao.chaves_duplicadas += 1
            linhas_lancadas.append(
                _linha_lancada(nota, lancamento, procedimento, duplicada))
            continue

        codigo_do_parceiro = cadastro.codigo_do_parceiro(nota.cnpj_do_prestador)
        codigo_da_filial = cadastro.codigo_da_filial(nota.cnpj_do_tomador)
        if not cadastro.filial_mapeada(nota.cnpj_do_tomador):
            if nota.cnpj_do_tomador and nota.cnpj_do_tomador not in fora_do_mapa:
                fora_do_mapa.append(nota.cnpj_do_tomador)

        chave = _chave_de_heranca(nota.numero, codigo_do_parceiro)
        classificacao = livro.de(chave)
        if classificacao.guardiao or classificacao.gestor_de_apoio or (
                classificacao.ultimo_retorno):
            execucao.herdadas += 1

        # A nota que a semana passada declarou cancelada na prefeitura, e a
        # que o cadastro de exceções manda não cobrar, saem aqui — depois da
        # cascata, porque o confronto ainda vale para elas: uma nota marcada
        # que apareceu lançada é notícia, e notícia não se apaga.
        motivo = exclusao.motivo_da_exclusao(
            classificacao, marca=ajuste["marca_de_cancelada"],
            codigo_do_parceiro=codigo_do_parceiro, valor=nota.valor,
            excecoes=excecoes)
        if motivo:
            execucao.fora_do_relatorio[motivo] = (
                execucao.fora_do_relatorio.get(motivo, 0) + 1)
            linhas_fora.append([
                *_linha_pendente(nota, cadastro, classificacao,
                                 vinculo.NAO_PROCURADO),
                motivo,
            ])
            continue
        if estado.registrar_identidade(livro, chave, nota.cnpj_do_prestador):
            execucao.colisoes_de_identidade += 1

        ligacao = vinculo.vincular(
            nota, codigo_do_parceiro=codigo_do_parceiro,
            codigo_da_filial=codigo_da_filial, anexos=anexos,
            indice=indice_da_conferencia, conferencia_lida=conferencia_lida,
            tolerancia=ajuste["tolerancia_da_razao"],
            multiplo_minimo=ajuste["multiplo_minimo"],
            multiplo_maximo=ajuste["multiplo_maximo"],
            tabela_do_semaforo=parametros.farol_de(dados, "semaforo") or None,
        )
        if ligacao.encontrado:
            execucao.vinculadas += 1
        if ligacao.ambiguo:
            execucao.vinculos_ambiguos += 1

        pedido = cadastro.pedido_de(nota.cnpj_do_prestador)
        if pedido and codigo_da_filial and pedido.empresa and (
                pedido.empresa != codigo_da_filial):
            execucao.pedidos_de_outra_filial += 1

        execucao.valor_pendente += nota.valor
        linhas_pendentes.append(
            _linha_pendente(nota, cadastro, classificacao, ligacao))

    execucao.filiais_nao_mapeadas = fora_do_mapa

    presenca = inversa.medir_presenca(notas)
    colunas_da_inversa, linhas_da_inversa = inversa.montar(
        lancamentos, resultado.consumidos, cabecalho_pc, cadastro, presenca,
    )

    caderno = escrita.novo_livro()
    escrita.escrever_aba(caderno, col.ABAS[0], col.LANCADAS, linhas_lancadas)
    escrita.escrever_aba(caderno, col.ABAS[1], col.PENDENTES, linhas_pendentes)
    escrita.escrever_aba(caderno, col.ABAS[2], col.CANCELADAS, linhas_canceladas)
    escrita.escrever_aba(caderno, col.ABAS[3], colunas_da_inversa,
                         linhas_da_inversa)
    escrita.escrever_aba(caderno, col.ABA_FORA_DO_RELATORIO,
                         col.FORA_DO_RELATORIO, linhas_fora)
    execucao.planilha = escrita.salvar(
        caderno, Path(saida) / nome_sugerido(agora))

    estado.gravar(livro, responsavel, raiz=raiz_dos_dados)
    execucao.pasta_do_snapshot = snapshot.gravar(
        DOMINIO, ano, semana,
        planilha=execucao.planilha, livro=livro,
        entradas=_impressoes(reconhecimento),
        resumo={
            "titulo": execucao.titulo(),
            "fichas": dict(execucao.fichas()),
            "confronto_por_procedimento": execucao.por_procedimento,
            # O valor total pendente não vai para a tela — as quatro fichas já
            # são o que se olha primeiro —, mas vai para a evidência: é a
            # resposta a "quanto estava em aberto em 08/09?".
            "valor_pendente": round(execucao.valor_pendente, 2),
            "bloqueios": execucao.bloqueios(),
            "atencoes": execucao.atencoes(),
        },
        encerravel=execucao.encerravel,
        raiz=raiz_dos_dados,
    )
    return execucao


def _impressoes(reconhecimento: papeis.Reconhecimento
                ) -> list[snapshot.EntradaDaSemana]:
    """Nome, tamanho e SHA-256 de cada entrada, com o papel reconhecido."""
    return [
        snapshot.impressao_de(achado.arquivo.caminho, papel_id)
        for papel_id, achado in reconhecimento.por_papel.items()
    ]
