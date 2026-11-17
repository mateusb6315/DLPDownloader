"""Regressões da troca de ferramentas e da seleção do pacote."""

import json
import shutil
import threading
from contextlib import nullcontext
from pathlib import Path
from types import SimpleNamespace

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


@pytest.mark.parametrize("falha_na_restauracao", [False, True])
def test_troca_falha_preserva_conjunto_e_metadados(tmp_path, monkeypatch, falha_na_restauracao):
    vendor = criar_vendor(tmp_path / "projeto")
    staging = tmp_path / "staging"
    backup = tmp_path / "backup"
    shutil.copytree(vendor, staging)
    (staging / "ffmpeg/avcodec.dll").write_bytes(b"novo")
    antigo = (vendor / "installed.json").read_bytes()
    from services._infra import instalacao

    substituir = instalacao.os.replace

    def falhar(origem, destino):
        if origem == staging / "ffmpeg" or (falha_na_restauracao and origem == backup / "ffmpeg"):
            raise PermissionError("Arquivo em uso")
        substituir(origem, destino)

    monkeypatch.setattr(instalacao.os, "replace", falhar)
    if falha_na_restauracao:
        with pytest.raises(RuntimeError, match="Recuperação manual necessária"):
            instalar_conjunto(vendor, staging, backup, ler_manifesto(vendor))
        (preservado,) = vendor.parent.glob(".recuperacao-*")
        assert not (vendor / "installed.json").exists()
    else:
        with pytest.raises(PermissionError):
            instalar_conjunto(vendor, staging, backup, ler_manifesto(vendor))
        preservado = vendor
    assert (preservado / "installed.json").read_bytes() == antigo
    assert (preservado / "ffmpeg/avcodec.dll").read_bytes() == b"executavel"


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


@pytest.mark.parametrize(
    "assinado,falha,comprimido", [(True, False, False), (False, True, False), (False, False, True)]
)
def test_upx_preserva_extensao_assinada_ou_incompativel(
    tmp_path, monkeypatch, assinado, falha, comprimido
):
    pefile = pytest.importorskip("pefile")
    from scripts import nuitka_beta

    pasta = tmp_path / "pacote/PyQt6"
    pasta.mkdir(parents=True)
    extensao = pasta / "QtGui.pyd"
    extensao.write_bytes(b"original")
    diretorios = [None] * 4 + [SimpleNamespace(Size=int(assinado))]
    pe = SimpleNamespace(OPTIONAL_HEADER=SimpleNamespace(DATA_DIRECTORY=diretorios))
    monkeypatch.setattr(pefile, "PE", lambda *args, **kwargs: nullcontext(pe))
    chamadas = []

    def executar(comando, _):
        chamadas.append(comando)
        if "-o" in comando:
            Path(comando[comando.index("-o") + 1]).write_bytes(b"menor")
        elif falha:
            raise RuntimeError("Compressão incompatível")

    monkeypatch.setattr(nuitka_beta, "executar_build", executar)
    nuitka_beta.comprimir_extensoes_qt("upx", pasta.parent)
    assert len(chamadas) == (0 if assinado else 2)
    assert extensao.read_bytes() == (b"menor" if comprimido else b"original")
