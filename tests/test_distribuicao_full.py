"""Verifica a coordenação dos artefatos sem depender dos compiladores externos."""

from pathlib import Path

import pytest

from scripts import distribuicao_full as full


def preparar(monkeypatch, tmp_path, falhar=None):
    monkeypatch.setattr(full.os, "name", "nt")
    monkeypatch.setattr(full, "localizar_ferramenta", lambda nome, candidatos: Path(nome))
    chamadas = []

    def compilar(destino, versao):
        pacote = destino / f"DLPDownloader-{versao}"
        pacote.mkdir(parents=True)
        (pacote / "DLPDownloader.exe").write_bytes(b"exe")
        chamadas.append("beta")
        return pacote

    def executar(comando, **kwargs):
        chamadas.append(comando[0])
        if comando[0] == falhar:
            raise RuntimeError("falha simulada")
        if comando[0] == "7z":
            Path(comando[3]).write_bytes(b"7z")
        else:
            (Path(kwargs["env"]["DLP_SAIDA"]) / "instalador.exe").write_bytes(b"setup")

    monkeypatch.setattr(full, "compilar_beta", compilar)
    monkeypatch.setattr(full, "compilar", compilar)
    monkeypatch.setattr(full, "executar_etapa", executar)
    return chamadas


@pytest.mark.parametrize("beta", [True, False])
def test_fluxo_completo(tmp_path, monkeypatch, beta):
    chamadas = preparar(monkeypatch, tmp_path)
    destino = tmp_path / "pasta com espaços"
    pacote = full.gerar_full(beta, "1.3.0", destino)
    assert pacote.is_dir()
    assert (destino / "DLPDownloader-1.3.0.7z").read_bytes() == b"7z"
    assert (destino / "DLPDownloader-1.3.0-setup.exe").read_bytes() == b"setup"
    assert chamadas == ["beta", "7z", "ISCC"]


def test_falha_no_instalador_preserva_pacote_e_arquivo(tmp_path, monkeypatch):
    preparar(monkeypatch, tmp_path, falhar="ISCC")
    with pytest.raises(RuntimeError, match="simulada"):
        full.gerar_full(True, "1.3.0_beta1", tmp_path)
    assert (tmp_path / "DLPDownloader-1.3.0_beta1").is_dir()
    assert (tmp_path / "DLPDownloader-1.3.0_beta1.7z").exists()
    assert not list(tmp_path.glob(".full-*"))


def test_publicacao_nao_sobrescreve(tmp_path):
    origem = tmp_path / "origem"
    destino = tmp_path / "destino"
    origem.write_bytes(b"novo")
    destino.write_bytes(b"original")
    with pytest.raises(FileExistsError):
        full.publicar(origem, destino)
    assert destino.read_bytes() == b"original"


def test_publicacao_recusa_arquivo_vazio(tmp_path):
    origem = tmp_path / "vazio"
    origem.touch()
    with pytest.raises(RuntimeError, match="válido"):
        full.publicar(origem, tmp_path / "destino")


def test_ferramenta_ausente_interrompe_antes_do_build(tmp_path, monkeypatch):
    monkeypatch.setattr(full.shutil, "which", lambda _: None)
    with pytest.raises(FileNotFoundError, match="não encontrada"):
        full.localizar_ferramenta("ferramenta-inexistente", [tmp_path / "ausente.exe"])


def test_falha_na_compactacao_preserva_pacote(tmp_path, monkeypatch):
    preparar(monkeypatch, tmp_path, falhar="7z")
    with pytest.raises(RuntimeError, match="simulada"):
        full.gerar_full(True, "1.3.0_beta1", tmp_path)
    assert (tmp_path / "DLPDownloader-1.3.0_beta1").is_dir()
    assert not list(tmp_path.glob("*.7z"))
