"""Eventos reais do protocolo, ausência de totais e ruído externo."""

import json

import pytest

from dlpdownloader.modelos.progresso import interpretar_progresso, numero


def linha(progresso, faixa="299", etapa="baixando"):
    return "DLP_PROGRESS:" + json.dumps({"etapa": etapa, "faixa": faixa, "progresso": progresso})


def test_progresso_por_faixa_nao_confunde_video_com_audio():
    video = interpretar_progresso(linha({"downloaded_bytes": 100, "total_bytes": 100}))
    audio = interpretar_progresso(linha({"downloaded_bytes": 1, "total_bytes": 100}, "140"))
    assert video.percentual == 100
    assert audio.percentual == 1
    assert video.faixa != audio.faixa


def test_total_estimado_e_identificado():
    evento = interpretar_progresso(linha({"downloaded_bytes": 5, "total_bytes_estimate": 10}))
    assert evento.estimado and evento.percentual == 50


def test_total_ausente_e_finalizacao_indeterminados():
    assert interpretar_progresso(linha({"downloaded_bytes": 50})).percentual is None
    assert interpretar_progresso(linha({}, etapa="finalizando")).percentual is None


@pytest.mark.parametrize(
    "entrada",
    ["[download] 10%", "DLP_PROGRESS:{", "DLP_PROGRESS:[]", 'DLP_PROGRESS:{"progresso":null}', ""],
)
def test_ruido_ou_evento_invalido_nao_quebra(entrada):
    assert interpretar_progresso(entrada) is None


@pytest.mark.parametrize("valor", [None, "NA", float("nan"), float("inf"), -1, True, {}])
def test_numeros_invalidos_nao_produzem_percentual(valor):
    assert numero(valor) is None


def test_percentual_limitado_a_cem():
    assert (
        interpretar_progresso(linha({"downloaded_bytes": 200, "total_bytes": 100})).percentual
        == 100
    )
