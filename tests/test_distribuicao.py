import subprocess
from pathlib import Path

import pytest

from scripts import _distribuicao_nuitka as distribuicao
from scripts._nuitka_tools import executar_build
from scripts.comum import ambiente_compilacao, bloqueio


@pytest.mark.parametrize("falha", [None, "compilação", "7z", "instalador"])
def test_publicacao_da_release_entrega_conjunto_validado(tmp_path, monkeypatch, falha):
    monkeypatch.setattr(
        distribuicao, "_localizar_compactador_e_instalador", lambda: (Path("7z"), Path("ISCC"))
    )

    def compilar(staging, versao, *, beta, baixar_compilador):
        if falha == "compilação":
            raise RuntimeError(falha)
        assert not beta
        pacote = staging / f"DLPDownloader-{versao}"
        pacote.mkdir()
        (pacote / "DLPDownloader.exe").write_bytes(b"executavel")
        return pacote

    def executar(comando, *, cwd=None, env=None):
        ferramenta = comando[0]
        if ferramenta == falha or (ferramenta == "ISCC" and falha == "instalador"):
            raise RuntimeError(falha)
        if ferramenta == "ISCC":
            (Path(env["DLP_SAIDA"].replace("{{", "{")) / "instalador.exe").write_bytes(b"setup")
        elif comando[1] == "a":
            assert (cwd / comando[-1] / "DLPDownloader.exe").is_file()
            Path(comando[2]).write_bytes(b"arquivo")
        else:
            assert comando[1] == "t" and Path(comando[2]).is_file()

    monkeypatch.setattr(distribuicao, "compilar_nuitka", compilar)
    monkeypatch.setattr(distribuicao, "executar_etapa", executar)
    anterior = tmp_path / "DLPDownloader-1.3.1.zip"
    anterior.write_bytes(b"publicado")
    artefatos = set(tmp_path.glob("DLPDownloader-*"))
    if falha:
        with pytest.raises(RuntimeError, match=falha):
            distribuicao.gerar_distribuicao("1.3.2", tmp_path, beta=False, criar_zip=True)
    else:
        pacote = distribuicao.gerar_distribuicao("1.3.2", tmp_path, beta=False, criar_zip=True)
        artefatos.update([pacote, tmp_path / f"{pacote.name}.7z", tmp_path / f"{pacote.name}.zip"])
        artefatos.add(tmp_path / f"{pacote.name}-setup.exe")
    assert set(tmp_path.glob("DLPDownloader-*")) == artefatos
    assert anterior.read_bytes() == b"publicado"


def test_bloqueio_da_distribuicao_pode_ser_reutilizado(tmp_path):
    arquivo = tmp_path / ".compilacao.lock"
    with bloqueio(arquivo):
        with pytest.raises(RuntimeError, match="andamento"), bloqueio(arquivo):
            pytest.fail("A segunda tentativa não deve obter o bloqueio.")
    with bloqueio(arquivo):
        assert arquivo.is_file()


def test_diagnostico_do_compilador_preserva_as_ultimas_linhas(tmp_path, monkeypatch):
    def falhar(*args, **kwargs):
        raise subprocess.CalledProcessError(1, args[0], output="\n".join(map(str, range(50))))

    monkeypatch.setattr(subprocess, "run", falhar)
    with pytest.raises(RuntimeError) as erro:
        executar_build(["nuitka"], tmp_path)
    linhas = str(erro.value).splitlines()[1:]
    assert linhas == list(map(str, range(20, 50)))


def test_path_do_compilador_isola_dlls_e_recursos_externos(monkeypatch):
    monkeypatch.setenv("PATH", r"C:\FerramentaExterna\bin")
    monkeypatch.setenv("QT_PLUGIN_PATH", r"C:\FerramentaExterna\plugins")
    ambiente = ambiente_compilacao()
    assert "FerramentaExterna" not in ambiente["PATH"]
    assert "System32" in ambiente["PATH"]
    assert "QT_PLUGIN_PATH" not in ambiente
