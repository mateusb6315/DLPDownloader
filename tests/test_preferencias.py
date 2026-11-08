"""Persistência, corrupção e falhas de destino usando tmp_path."""

import json

import pytest

from dlpdownloader.modelos.erros import ErroDestino
from dlpdownloader.servicos.arquivos import gravar_json, validar_destino
from dlpdownloader.servicos.preferencias import Preferencias


def test_pasta_e_restaurada_apos_reabrir(tmp_path):
    arquivo = tmp_path / "dados/config.json"
    Preferencias(arquivo, tmp_path).salvar(tmp_path)
    destino, aviso = Preferencias(arquivo, tmp_path / "outro").carregar()
    assert destino == tmp_path and not aviso


@pytest.mark.parametrize(
    "conteudo", ["{", "[]", "null", '{"versao":2}', '{"versao":1,"diretorio":3}']
)
def test_configuracao_invalida_preservada(tmp_path, conteudo):
    arquivo = tmp_path / "config.json"
    arquivo.write_text(conteudo, encoding="utf-8")
    destino, aviso = Preferencias(arquivo, tmp_path).carregar()
    assert destino == tmp_path and aviso
    assert arquivo.read_text(encoding="utf-8") == conteudo


def test_pasta_removida_nao_muda_silenciosamente(tmp_path):
    arquivo = tmp_path / "config.json"
    removida = tmp_path / "removida"
    Preferencias(arquivo, tmp_path).salvar(removida)
    destino, aviso = Preferencias(arquivo, tmp_path).carregar()
    assert destino == removida and aviso
    with pytest.raises(ErroDestino):
        validar_destino(destino)


def test_gravacao_atomica_preserva_original_em_falha(tmp_path, monkeypatch):
    arquivo = tmp_path / "config.json"
    gravar_json(arquivo, {"valor": 1})

    def falhar(*args):
        raise PermissionError("sem permissão")

    monkeypatch.setattr("dlpdownloader.servicos.arquivos.os.replace", falhar)
    with pytest.raises(PermissionError):
        gravar_json(arquivo, {"valor": 2})
    assert json.loads(arquivo.read_text()) == {"valor": 1}
    assert list(tmp_path.iterdir()) == [arquivo]
