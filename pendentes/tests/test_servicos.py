"""O motor de serviços: as chaves, a cascata por passos, o vínculo e a inversa.

Todo teste aqui exercita **comportamento**, não implementação: o que muda na
planilha, o que entra em cada aba, o que bloqueia o encerramento da semana.

O teste que dá nome ao arquivo é
`test_a_cascata_por_passos_nao_e_a_cascata_por_linha`: ele monta o caso em que
as duas ordens de laço dão resultados diferentes, roda a cascata ingênua ali
mesmo para mostrar o resultado errado, e trava o certo. É a armadilha nº 1 do
porte, e é a única que não se percebe olhando a saída.
"""
from __future__ import annotations

import pytest

from pendentes.servicos import (
    chaves, colunas, confronto, enriquecimento, fontes, inversa, vinculo,
)
from pendentes.cabecalho import Exigencia, mapear
from conftest import COLUNAS_ASIS, COLUNAS_PORTAL, linha_asis, linha_portal


# -- montagem em memória, sem passar por planilha ---------------------------

def _mapa(colunas_do_relatorio):
    return mapear(colunas_do_relatorio,
                  [Exigencia(nome) for nome in colunas_do_relatorio], "teste")


def notas(*linhas):
    return fontes.ler_notas(list(linhas), _mapa(COLUNAS_ASIS))


def registros(*linhas):
    return fontes.ler_registros(list(linhas), _mapa(COLUNAS_PORTAL))


TOPS = ("2020", "2111")


def confrontar(as_notas, os_registros):
    lancamentos = enriquecimento.lancamentos_de(os_registros, TOPS)
    indices = chaves.indexar(lancamentos)
    return confronto.confrontar(as_notas, lancamentos, indices), lancamentos


# =========================================================================
# A cascata
# =========================================================================

def test_a_cascata_por_passos_nao_e_a_cascata_por_linha():
    """A armadilha nº 1 do porte, montada para falhar se alguém inverter.

    Duas notas do mesmo prestador e do mesmo valor. A **segunda** casa com o
    lançamento por chave forte (nota + CNPJ); a primeira só casaria por chave
    fraca (CNPJ + valor).

    Por passos, o procedimento 1 roda antes e entrega o lançamento a quem tem
    direito a ele. Por linha, a primeira nota tentaria os quatro
    procedimentos, o 3 consumiria o lançamento, e a nota certa ficaria
    pendente — com o resultado dependendo da ordem das linhas no relatório.
    """
    cnpj = "99888777000166"
    as_notas = notas(
        linha_asis("501", cnpj, "1000.00"),      # só casa por CNPJ+valor
        linha_asis("777", cnpj, "1000.00"),      # casa por nota+CNPJ
    )
    os_registros = registros(linha_portal(1, "777", cnpj, 1000.00))

    resultado, lancamentos = confrontar(as_notas, os_registros)

    assert resultado.procedimento == [confronto.PENDENTE, 1]
    assert resultado.lancadas == 1
    assert resultado.pendentes == 1

    # E o contraste: a mesma entrada, com os laços invertidos.
    assert _cascata_por_linha(as_notas, lancamentos) == [3, confronto.PENDENTE]


def _cascata_por_linha(as_notas, lancamentos):
    """A cascata errada — a nota por fora, o procedimento por dentro.

    Existe só para este teste: é o desenho que o comentário do VBA diz ter
    sido o inicial, e que foi corrigido. Se alguém inverter os laços no
    `confronto.py`, o teste acima passa a ver este resultado.
    """
    indices = chaves.indexar(lancamentos)
    consumidos = [False] * len(lancamentos)
    saida = []
    for nota in as_notas:
        decidido = confronto.PENDENTE
        for passo in confronto.PROCEDIMENTOS:
            chave = confronto._chave(passo, nota)
            if chave is None:
                continue
            if confronto._indice(passo, indices).consumir(chave, consumidos) >= 0:
                decidido = passo
                break
        saida.append(decidido)
    return saida


def test_a_ordem_das_linhas_do_relatorio_nao_muda_o_resultado():
    """É a consequência prática de rodar por passos: determinismo."""
    cnpj = "99888777000166"
    linhas = [
        linha_asis("501", cnpj, "1000.00"),
        linha_asis("777", cnpj, "1000.00"),
        linha_asis("999", cnpj, "2000.00"),
    ]
    os_registros = registros(
        linha_portal(1, "777", cnpj, 1000.00),
        linha_portal(2, "999", cnpj, 2000.00),
    )

    direto, _ = confrontar(notas(*linhas), os_registros)
    invertido, _ = confrontar(notas(*reversed(linhas)), os_registros)

    assert sorted(direto.procedimento) == sorted(invertido.procedimento)
    assert direto.lancadas == invertido.lancadas == 2


def test_um_lancamento_paga_uma_nota_so():
    """Sem consumo, um lançamento casaria com todas as notas de mesmo valor."""
    cnpj = "99888777000166"
    as_notas = notas(
        linha_asis("100", cnpj, "500.00"),
        linha_asis("200", cnpj, "500.00"),
    )
    resultado, _ = confrontar(
        as_notas, registros(linha_portal(1, "300", cnpj, 500.00)))

    assert resultado.lancadas == 1
    assert resultado.pendentes == 1


def test_a_nota_com_prefixo_de_ano_do_portal_nacional_casa_com_o_lancamento():
    """`202600000001234` do Portal Nacional é o `1234` do Sankhya."""
    cnpj = "99888777000166"
    resultado, _ = confrontar(
        notas(linha_asis("202600000001234", cnpj, "1500.00")),
        registros(linha_portal(1, "1234", cnpj, 1500.00)),
    )
    assert resultado.procedimento == [1]


def test_a_nota_cujo_numero_e_o_da_rps_casa_pelo_procedimento_2():
    """Há prefeituras que informam o número da RPS como número da nota."""
    cnpj = "99888777000166"
    resultado, _ = confrontar(
        notas(linha_asis("88888", cnpj, "320.50", rps="555")),
        registros(linha_portal(1, "555", cnpj, 320.50)),
    )
    assert resultado.procedimento == [2]


def test_rps_vazia_ou_zero_nao_vira_chave():
    """A chave `0|cnpj` casaria notas sem nenhuma relação entre si."""
    cnpj = "99888777000166"
    resultado, _ = confrontar(
        notas(linha_asis("88888", cnpj, "77.77", rps="000")),
        registros(linha_portal(1, "0", cnpj, 999.99)),
    )
    assert resultado.pendentes == 1


def test_a_cancelada_sai_antes_da_cascata_e_nao_consome_lancamento():
    """Uma cancelada que casasse por CNPJ+valor roubaria a nota de outra."""
    cnpj = "99888777000166"
    as_notas = notas(
        linha_asis("100", cnpj, "500.00", cancelamento="06/08/2026"),
        linha_asis("700", cnpj, "500.00"),
    )
    resultado, _ = confrontar(
        as_notas, registros(linha_portal(1, "999", cnpj, 500.00)))

    assert resultado.procedimento[0] == confronto.CANCELADA
    assert resultado.procedimento[1] == 3
    assert resultado.canceladas == 1
    assert resultado.lancadas == 1


def test_qualquer_conteudo_em_data_de_cancelamento_cancela_a_nota():
    """A condição do VBA é generosa de propósito: adivinhar seria pior."""
    as_notas = notas(linha_asis("1", "99888777000166", "10.00",
                                cancelamento="nao interpretavel"))
    assert as_notas[0].cancelada


# =========================================================================
# As identidades aritméticas — o que a execução real vai confirmar
# =========================================================================

def test_lancadas_mais_pendentes_mais_canceladas_dao_as_notas_do_asis():
    cnpj = "99888777000166"
    as_notas = notas(
        linha_asis("1", cnpj, "10.00"),
        linha_asis("2", cnpj, "20.00"),
        linha_asis("3", cnpj, "30.00", cancelamento="07/08/2026"),
        linha_asis("4", cnpj, "40.00"),
    )
    resultado, _ = confrontar(as_notas, registros(
        linha_portal(1, "1", cnpj, 10.00),
        linha_portal(2, "2", cnpj, 20.00),
    ))
    assert resultado.lancadas + resultado.pendentes + resultado.canceladas == 4


def test_lancadas_mais_sem_correspondencia_dao_os_lancamentos_indexados():
    """Cada lançamento é consumido no máximo uma vez: a inversa é o complemento."""
    cnpj = "99888777000166"
    as_notas = notas(linha_asis("1", cnpj, "10.00"), linha_asis("2", cnpj, "20.00"))
    os_registros = registros(
        linha_portal(1, "1", cnpj, 10.00),
        linha_portal(2, "9", cnpj, 90.00),
        linha_portal(3, "8", cnpj, 80.00),
    )
    resultado, lancamentos = confrontar(as_notas, os_registros)
    assert resultado.lancadas + resultado.sem_correspondencia == len(lancamentos)


def test_a_soma_dos_procedimentos_da_as_lancadas():
    """A identidade que a tela mostra, e que dispensa abrir teste para conferir."""
    cnpj = "99888777000166"
    as_notas = notas(
        linha_asis("1", cnpj, "10.00"),
        linha_asis("2", cnpj, "20.00", rps="777"),
        linha_asis("3", cnpj, "30.00"),
    )
    resultado, _ = confrontar(as_notas, registros(
        linha_portal(1, "1", cnpj, 10.00),
        linha_portal(2, "777", cnpj, 20.00),
        linha_portal(3, "555", cnpj, 30.00),
    ))
    assert sum(resultado.por_procedimento().values()) == resultado.lancadas
    assert resultado.por_procedimento() == {1: 1, 2: 1, 3: 1, 4: 0}


# =========================================================================
# O enriquecimento
# =========================================================================

def _cadastro(*linhas):
    return enriquecimento.cadastrar(registros(*linhas), tops=TOPS,
                                    prefixo_de_pedido="PC")


def test_lancamento_com_cnpj_zerado_nao_indexa_e_e_contado():
    """Hoje ele some da análise sem contagem e sem aviso."""
    linhas = [
        linha_portal(1, "1", "00000000000000", 10.00),
        linha_portal(2, "2", "", 20.00),
        linha_portal(3, "3", "99888777000166", 30.00),
    ]
    assert _cadastro(*linhas).descartados_por_cnpj == 2
    assert len(enriquecimento.lancamentos_de(registros(*linhas), TOPS)) == 1


def test_parceiro_sem_cadastro_fica_com_o_nome_que_o_asis_trouxe():
    cadastro = _cadastro(linha_portal(1, "1", "99888777000166", 10.00))
    assert cadastro.codigo_do_parceiro("11111111111111") == "Sem cadastro"
    assert cadastro.nome_do_parceiro("11111111111111", "OFICINA DO ZE") == (
        "OFICINA DO ZE")


def test_o_de_para_de_filiais_vem_do_proprio_export_e_o_que_falta_fica_visivel():
    """A filial sem movimento no período desaparece — é o caso conhecido."""
    cadastro = _cadastro(linha_portal(1, "1", "99888777000166", 10.00))
    assert cadastro.filial_mapeada("11222333000144")
    assert cadastro.filial_de("11222333000144") == "HINOVE MATRIZ"
    assert not cadastro.filial_mapeada("55555555000155")
    assert cadastro.filial_de("55555555000155") == (
        "CNPJ nao mapeado: 55555555000155")


def test_o_complemento_estatico_so_preenche_o_que_o_export_nao_trouxe():
    """O mapa dinâmico é o que está atual; um cadastro esquecido não o sobrepõe."""
    cadastro = enriquecimento.cadastrar(
        registros(linha_portal(1, "1", "99888777000166", 10.00)),
        tops=TOPS, prefixo_de_pedido="PC",
        complemento_de_filiais=[
            {"cnpj": "11.222.333/0001-44", "codigo": "9", "nome": "OUTRO NOME"},
            {"cnpj": "55555555000155", "codigo": "7", "nome": "HINOVE MICROBIO"},
        ],
    )
    assert cadastro.filial_de("11222333000144") == "HINOVE MATRIZ"
    assert cadastro.filial_de("55555555000155") == "HINOVE MICROBIO"


def test_o_pedido_mais_recente_e_o_de_maior_numero_unico():
    cnpj = "99888777000166"
    cadastro = _cadastro(
        linha_portal(10, "", cnpj, 0, top="1102", descricao_do_top="PC COMPRA",
                     comprador="ANTIGO"),
        linha_portal(90, "", cnpj, 0, top="1102", descricao_do_top="PC COMPRA",
                     comprador="RECENTE"),
        linha_portal(50, "", cnpj, 0, top="1102", descricao_do_top="PC COMPRA",
                     comprador="MEIO"),
    )
    assert cadastro.pedido_de(cnpj).numero_unico == 90
    assert cadastro.pedido_de(cnpj).comprador == "RECENTE"


def test_so_a_descricao_de_top_que_comeca_em_pc_e_pedido():
    cnpj = "99888777000166"
    cadastro = _cadastro(
        linha_portal(10, "", cnpj, 0, top="1102",
                     descricao_do_top="VENDA COM PC NO MEIO"))
    assert cadastro.pedido_de(cnpj) is None


# =========================================================================
# O vínculo com a Conferência de Serviços
# =========================================================================

def _anexo(numero_unico, valor, **campos):
    from pendentes.servicos.fontes import Anexo
    from pendentes.valores import data_hora

    return Anexo(
        posicao=0, numero_unico=numero_unico,
        data_do_anexo=data_hora(campos.get("anexo", "10/08/26 14:35")),
        valor=valor, parceiro=campos.get("parceiro", "4001"),
        empresa=campos.get("empresa", "1"),
        status_do_lancamento=campos.get("status", "Pendente"),
        pedido_confirmado=campos.get("confirmado", ""),
        motivo_da_incongruencia=campos.get("motivo", ""),
    )


def _vincular(nota, anexos, **extras):
    indice = vinculo.indexar(anexos)
    argumentos = {"codigo_do_parceiro": "4001", "codigo_da_filial": "1",
                  "anexos": anexos, "indice": indice}
    argumentos.update(extras)
    return vinculo.vincular(nota, **argumentos)


def test_o_pedido_de_valor_exato_vence_o_pedido_global():
    """Um pedido global nunca deve roubar o vínculo de um específico."""
    nota = notas(linha_asis("1", "99888777000166", "100.00"))[0]
    ligacao = _vincular(nota, [_anexo(700, 200.00), _anexo(500, 100.00)])
    assert ligacao.fator == "1x"
    assert ligacao.numero_unico == 500
    assert ligacao.confianca == "Exato"


def test_sem_exato_o_multiplo_inteiro_vale_como_pedido_global():
    nota = notas(linha_asis("1", "99888777000166", "100.00"))[0]
    ligacao = _vincular(nota, [_anexo(700, 300.00)])
    assert ligacao.fator == "3x"
    assert ligacao.confianca == "Multiplo (pedido global)"


def test_o_anexo_anterior_a_emissao_nao_serve():
    """Anexo de antes da nota não pode ser o anexo daquela nota."""
    nota = notas(linha_asis("1", "99888777000166", "100.00",
                            emissao="20/08/2026"))[0]
    ligacao = _vincular(nota, [_anexo(700, 100.00, anexo="10/08/26 14:35")])
    assert ligacao.confianca == "Nao encontrado"


def test_o_anexo_do_mesmo_dia_serve_mesmo_com_hora_anterior():
    """A comparação é por dia; a hora fica no valor e sai da comparação."""
    nota = notas(linha_asis("1", "99888777000166", "100.00",
                            emissao="10/08/2026"))[0]
    ligacao = _vincular(nota, [_anexo(700, 100.00, anexo="10/08/26 00:05")])
    assert ligacao.fator == "1x"


def test_pedido_ambiguo_e_marcado_com_a_contagem_de_candidatos():
    """A ferramenta escolheu um, mas não sabe se escolheu o certo."""
    nota = notas(linha_asis("1", "99888777000166", "100.00"))[0]
    ligacao = _vincular(nota, [_anexo(700, 100.00), _anexo(800, 100.00)])
    assert ligacao.ambiguo
    assert ligacao.confianca == "Exato (ambiguo: 2 candidatos)"
    assert ligacao.numero_unico == 800


def test_sem_cadastro_de_parceiro_a_coluna_36_diz_qual_ancora_faltou():
    nota = notas(linha_asis("1", "99888777000166", "100.00"))[0]
    ligacao = _vincular(nota, [_anexo(700, 100.00)],
                        codigo_do_parceiro="Sem cadastro")
    assert ligacao.confianca == "Sem cadastro de parceiro"


def test_conferencia_nao_lida_deixa_a_coluna_36_vazia():
    """Vazio não é "não encontrei": é "não procurei"."""
    nota = notas(linha_asis("1", "99888777000166", "100.00"))[0]
    ligacao = _vincular(nota, [], conferencia_lida=False)
    assert ligacao.confianca == ""
    assert ligacao.como_colunas() == ["", "", "", "", "", "", "", ""]


def test_o_semaforo_da_conferencia_tem_o_estado_parcial():
    nota = notas(linha_asis("1", "99888777000166", "100.00"))[0]
    ligacao = _vincular(nota, [_anexo(
        700, 100.00, confirmado='<div><span>&#128993;</span></div>')])
    assert ligacao.pedido_confirmado == "Parcial"


# =========================================================================
# A população inversa
# =========================================================================

def test_o_bloco_de_analise_vem_antes_das_colunas_de_origem():
    """Com 268 colunas, análise no fim da linha é análise invisível."""
    cnpj = "99888777000166"
    linha = linha_portal(1, "9", cnpj, 90.00)
    resultado, lancamentos = confrontar(notas(), registros(linha))
    colunas_da_aba, linhas = inversa.montar(
        lancamentos, resultado.consumidos, COLUNAS_PORTAL,
        _cadastro(linha), inversa.medir_presenca(notas()),
    )
    rotulos = [c.rotulo for c in colunas_da_aba]
    assert rotulos[:7] == [c.rotulo for c in colunas.ANALISE_DA_INVERSA]
    assert rotulos[7:12] == ["Nro. Nota", "Parceiro", "Nome Parceiro (Parceiro)",
                             "Vlr. Nota", "Empresa"]
    assert rotulos[12] == "Cidade do Parceiro"
    assert len(linhas) == 1


def test_a_comparacao_antes_e_depois_e_estrita():
    """Emissão na mesma data do `Dt. Neg.` não conta nem como antes nem depois."""
    cnpj = "99888777000166"
    as_notas = notas(linha_asis("1", cnpj, "10.00", emissao="10/08/2026"))
    linha = linha_portal(1, "9", cnpj, 90.00, negociacao="10/08/2026")
    analise = inversa.analisar(registros(linha)[0], _cadastro(linha),
                               inversa.medir_presenca(as_notas))
    assert analise[0] == "Nao" and analise[2] == "Nao"


def test_sem_data_de_negociacao_a_ferramenta_diz_que_nao_sabe():
    """Dizer "Não" onde não há informação seria afirmar o que não se sabe."""
    cnpj = "99888777000166"
    linha = linha_portal(1, "9", cnpj, 90.00, negociacao="")
    analise = inversa.analisar(registros(linha)[0], _cadastro(linha),
                               inversa.medir_presenca(notas()))
    assert analise[0] == analise[2] == inversa.DATA_AUSENTE
    assert analise[1] == analise[3] == ""


def test_a_diferenca_compara_universos_diferentes_e_isso_e_preservado():
    """Entradas conta só TOP de serviço; ASIS conta tudo, cancelada inclusive."""
    cnpj = "99888777000166"
    as_notas = notas(
        linha_asis("1", cnpj, "10.00"),
        linha_asis("2", cnpj, "20.00", cancelamento="07/08/2026"),
    )
    linha = linha_portal(1, "9", cnpj, 90.00)
    analise = inversa.analisar(registros(linha)[0], _cadastro(linha),
                               inversa.medir_presenca(as_notas))
    assert analise[4] == 1        # Entradas: um lançamento de serviço
    assert analise[5] == 2        # ASIS: as duas, cancelada inclusive
    assert analise[6] == -1


# =========================================================================
# Os layouts
# =========================================================================

@pytest.mark.parametrize("layout, quantas", [
    (colunas.LANCADAS, 12),
    (colunas.PENDENTES, 36),
    (colunas.CANCELADAS, 16),
    (colunas.ANALISE_DA_INVERSA, 7),
])
def test_a_largura_de_cada_aba_e_invariante_da_prova(layout, quantas):
    assert len(layout) == quantas


def test_canceladas_nao_e_pendentes_mais_duas_colunas():
    """É a armadilha nº 8: layout próprio, com ordem interna diferente."""
    canceladas = [c.rotulo for c in colunas.CANCELADAS]
    pendentes = [c.rotulo for c in colunas.PENDENTES]
    assert "Guardiao" not in canceladas
    assert "Codigo Verificador" not in canceladas
    assert canceladas[4] == "Valor NFSe (Valor Bruto)"
    assert pendentes[4] == "Guardiao"


def test_o_numero_da_nota_e_o_codigo_verificador_saem_como_texto():
    """44 dígitos em coluna numérica viram notação científica, e o PROCX cai."""
    formatos = {c.rotulo: c.formato for c in colunas.PENDENTES}
    assert formatos["Nro Nota"] == "texto"
    assert formatos["Codigo Verificador"] == "texto"
    assert formatos["Dt. ult. anexo"] == "data"


def test_a_data_de_cancelamento_chega_como_data_e_nao_como_texto():
    """Converter texto que já veio de célula de data perde a data inteira.

    `06/08/2026 10:00:00` aparado vira texto, e o parse explícito por `/` lê
    `2026 10:00:00` como ano — que não é ano nenhum. Guardar o valor cru e
    converter na escrita é o que o VBA faz, e é o que preserva a data.
    """
    from datetime import datetime

    from pendentes.valores import data_br

    nota = notas(linha_asis("1", "99888777000166", "10.00",
                            cancelamento=datetime(2026, 8, 6, 10, 0)))[0]
    assert nota.cancelada
    assert data_br(nota.data_de_cancelamento) == datetime(2026, 8, 6, 10, 0)
