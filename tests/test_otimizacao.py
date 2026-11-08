"""Regressões da troca de ferramentas e da seleção do pacote."""

import json
import shutil
import threading

import pytest

from dlpdownloader.modelos.erros import Cancelado, ErroDependencia
from dlpdownloader.servicos.dependencias import verificar
from dlpdownloader.servicos.manifesto import ler_manifesto, relativo_seguro, sha256
from scripts.instalar_ferramentas import instalar_conjunto
from scripts.pacote import copiar_vendor
from tests.apoio_vendor import criar_vendor


@pytest.mark.parametrize("caminho", ["../a", "/a", "C:/a", "a\\b", "a/../b", "a//b"])
def test_destinos_inseguros_rejeitados(caminho):
    with pytest.raises(ValueError):
        relativo_seguro(caminho)


@pytest.mark.parametrize("mudanca", ["ausente", "adulterada", "omitida"])
def test_dll_exigida_pelo_manifesto(tmp_path, monkeypatch, mudanca):
    vendor = criar_vendor(tmp_path)
    dll = vendor / "ffmpeg/avcodec.dll"
    if mudanca == "ausente":
        dll.unlink()
    elif mudanca == "adulterada":
        dll.write_bytes(b"alterado")
    else:
        meta = vendor / "installed.json"
        dados = json.loads(meta.read_text())
        del dados["arquivos"]["ffmpeg/avcodec.dll"]
        meta.write_text(json.dumps(dados))
    monkeypatch.setattr("dlpdownloader.servicos.dependencias.executar", lambda *a, **k: None)
    with pytest.raises(ErroDependencia):
        verificar(tmp_path, threading.Event())


def test_hash_cancelavel(tmp_path):
    arquivo = tmp_path / "binario"
    arquivo.write_bytes(b"x")
    evento = threading.Event()
    evento.set()
    with pytest.raises(Cancelado):
        sha256(arquivo, evento)


def test_pacote_exclui_residuos(tmp_path):
    vendor = criar_vendor(tmp_path / "projeto")
    (vendor / "ffmpeg/antiga.dll").write_bytes(b"antiga")
    destino = tmp_path / "pacote/vendor"
    copiar_vendor(vendor, destino)
    assert (destino / "ffmpeg/avcodec.dll").exists()
    assert not (destino / "ffmpeg/antiga.dll").exists()


def test_troca_falha_restaura_conjunto_e_metadados(tmp_path, monkeypatch):
    vendor = criar_vendor(tmp_path / "projeto")
    staging = tmp_path / "staging"
    shutil.copytree(vendor, staging)
    (staging / "ffmpeg/avcodec.dll").write_bytes(b"novo")
    antigo = (vendor / "installed.json").read_bytes()
    from scripts import instalar_ferramentas

    substituir = instalar_ferramentas.os.replace

    def falhar(origem, destino):
        if origem == staging / "ffmpeg":
            raise PermissionError("Arquivo em uso")
        substituir(origem, destino)

    monkeypatch.setattr(instalar_ferramentas.os, "replace", falhar)
    with pytest.raises(PermissionError):
        instalar_conjunto(vendor, staging, tmp_path / "backup", ler_manifesto(vendor))
    assert (vendor / "installed.json").read_bytes() == antigo
    assert (vendor / "ffmpeg/avcodec.dll").read_bytes() == b"executavel"


def test_troca_remove_dll_antiga_preserva_aviso_particular(tmp_path):
    vendor = criar_vendor(tmp_path / "projeto")
    staging = tmp_path / "staging"
    shutil.copytree(vendor, staging)
    (vendor / "ffmpeg/antiga.dll").write_bytes(b"antiga")
    (vendor / "licenses/aviso.txt").write_text("particular")
    instalar_conjunto(vendor, staging, tmp_path / "backup", ler_manifesto(vendor))
    assert not (vendor / "ffmpeg/antiga.dll").exists()
    assert (vendor / "licenses/aviso.txt").read_text() == "particular"


def test_falha_diagnostico_retorna_erro_sem_dialogo(tmp_path, monkeypatch):
    from dlpdownloader.aplicacao import main

    def falhar(*args):
        raise RuntimeError("conteúdo que não deve ser registrado")

    monkeypatch.setattr("sys.argv", ["App.exe", "--verificar-midia", str(tmp_path)])
    monkeypatch.setattr("dlpdownloader.servicos.autoteste.testar_midia", falhar)
    assert main() == 1
    assert json.loads((tmp_path / "resultado.json").read_text()) == {
        "sucesso": False,
        "erro": "RuntimeError",
    }
