"""Reparo sem downloads reais e coordenação entre processos."""

import csv
import hashlib
import io
import json
import subprocess
import zipfile

import pytest

from services import repair, repair_console
from services._infra.bloqueios import bloquear_uso
from tests.apoio_vendor import criar_vendor


def test_pausa_terminal_aceita_qualquer_tecla(monkeypatch, capsys):
    import msvcrt

    class Entrada:
        def isatty(self):
            return True

    teclas = []
    monkeypatch.setattr(repair_console.sys, "argv", ["repair.exe"])
    monkeypatch.setattr(repair_console.sys, "stdin", Entrada())
    monkeypatch.setattr(msvcrt, "getwch", lambda: teclas.append("x") or "x")
    assert repair_console.main() == 1
    assert teclas == ["x"] and "Pressiona qualquer tecla para sair" in capsys.readouterr().out


def test_verificacao_do_pacote_nao_espera_tecla_em_console(tmp_path, monkeypatch):
    import msvcrt
    from types import SimpleNamespace

    class Entrada:
        def isatty(self):
            return True

    vendor = criar_vendor(tmp_path / "incorporado")
    (tmp_path / "pacote/DLPDownloader.exe").parent.mkdir()
    (tmp_path / "pacote/DLPDownloader.exe").touch()
    compilado = SimpleNamespace(onefile=True, containing_dir=tmp_path / "pacote/vendor")
    monkeypatch.setattr(repair_console, "__file__", str(vendor / "repair_console.py"))
    monkeypatch.setattr(repair_console.sys, "argv", ["repair.exe", "--verificar-empacotamento"])
    monkeypatch.setattr(repair_console.sys, "stdin", Entrada())
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: pytest.fail("Smoke test sem processos"))
    monkeypatch.setattr(msvcrt, "getwch", lambda: pytest.fail("A verificação não deve pausar"))
    assert repair_console.main(compilado) == 0


def test_aguarda_encerramento_real_do_processo():
    import sys
    import time

    processo = subprocess.Popen(
        [sys.executable, "-c", "import time; time.sleep(1)"],
        creationflags=subprocess.CREATE_NO_WINDOW,
    )
    try:
        inicio = time.monotonic()
        repair_console.aguardar_processo(processo.pid)
        assert processo.poll() is not None
        assert time.monotonic() - inicio >= 0.5
    finally:
        if processo.poll() is None:
            processo.kill()
        processo.wait()


def test_inicia_reparador_com_novo_console_e_pid(tmp_path, monkeypatch):
    import os

    from services.repair import iniciar_reparo

    chamadas = []
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **k: chamadas.append((a, k)))
    iniciar_reparo(tmp_path)
    args, opcoes = chamadas[0]
    assert args[0] == [str(tmp_path / "vendor/repair.exe"), "--aguardar-pid", str(os.getpid())]
    assert opcoes["creationflags"] == subprocess.CREATE_NEW_CONSOLE
    assert opcoes["cwd"] == tmp_path / "vendor"


def test_aplicativo_aberto_impede_download(tmp_path, monkeypatch):
    saida = io.StringIO()
    csv.writer(saida).writerow(["DLPDownloader.exe", "123", "Console", "1", "20 K"])
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *a, **k: subprocess.CompletedProcess(a[0], 0, stdout=saida.getvalue()),
    )
    with pytest.raises(RuntimeError, match="Feche"):
        repair.reparar(
            tmp_path / "app",
            tmp_path / "manifest.json",
            dados=tmp_path / "dados",
            obter=lambda *a: pytest.fail("Aplicativo aberto impede downloads"),
        )


def test_falha_ao_consultar_processos_interrompe_com_mensagem_clara(monkeypatch):
    def falhar(*args, **kwargs):
        raise subprocess.TimeoutExpired("tasklist", 15)

    monkeypatch.setattr(subprocess, "run", falhar)
    with pytest.raises(RuntimeError, match="Não foi possível verificar"):
        repair.verificar_fechado()


def test_bloqueio_compartilhado_impede_reparo_e_vice_versa(tmp_path):
    with bloquear_uso(tmp_path, exclusivo=False), bloquear_uso(tmp_path, exclusivo=False):
        with pytest.raises(RuntimeError, match="Feche"):
            with bloquear_uso(tmp_path, exclusivo=True):
                pass
    with bloquear_uso(tmp_path, exclusivo=True):
        with pytest.raises(RuntimeError, match="Feche"):
            with bloquear_uso(tmp_path, exclusivo=False):
                pass


def test_reparo_restaura_manifesto_dll_e_metadados(tmp_path, monkeypatch):
    from services.repair import reparar

    raiz = tmp_path / "app"
    vendor = criar_vendor(raiz)
    fonte = tmp_path / "incorporado"
    fonte.mkdir()
    manifesto = json.loads((vendor / "manifest.json").read_text())
    downloads = {}
    for ferramenta in manifesto["ferramentas"]:
        nome = ferramenta["nome"]
        if nome == "ffmpeg":
            buffer = io.BytesIO()
            with zipfile.ZipFile(buffer, "w") as arquivo:
                for entrada in ferramenta["arquivos"]:
                    arquivo.writestr("bin/" + entrada, b"novo")
            dados = buffer.getvalue()
            ferramenta["url"] = "https://example.com/ffmpeg.zip"
        else:
            dados = b"novo"
            ferramenta["url"] = f"https://example.com/{nome}.exe"
        ferramenta["sha256"] = hashlib.sha256(dados).hexdigest()
        downloads[ferramenta["url"]] = dados
    confiavel = fonte / "manifest.json"
    confiavel.write_text(json.dumps(manifesto), encoding="utf-8")
    (fonte / "licenses").mkdir()
    (fonte / "licenses/README.md").write_text("Aviso incorporado", encoding="utf-8")
    (vendor / "repair.exe").write_bytes(b"reparador")
    (vendor / "manifest.json").write_text("corrompido")
    (vendor / "ffmpeg/avcodec.dll").unlink()
    (vendor / "installed.json").unlink()

    def obter(url, destino):
        destino.write_bytes(downloads.get(url, b"licenca"))

    monkeypatch.setattr(
        subprocess, "run", lambda comando, **k: subprocess.CompletedProcess(comando, 0, stdout="")
    )
    monkeypatch.setattr("services._infra.dependencias.executar", lambda *a, **k: None)
    reparar(raiz, confiavel, dados=tmp_path / "dados", obter=obter)
    assert (vendor / "manifest.json").read_bytes() == confiavel.read_bytes()
    assert (vendor / "ffmpeg/avcodec.dll").read_bytes() == b"novo"
    assert "ffmpeg/avcodec.dll" in json.loads((vendor / "installed.json").read_text())["arquivos"]
    assert (vendor / "licenses/README.md").read_text(encoding="utf-8") == "Aviso incorporado"
    assert (vendor / "repair.exe").read_bytes() == b"reparador"
