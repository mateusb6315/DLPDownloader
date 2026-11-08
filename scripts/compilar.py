"""Compila uma distribuição Windows onedir sem depender de arquivo .spec."""

import argparse
import importlib.metadata
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import tomllib
from datetime import datetime, timezone
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dlpdownloader.modelos.erros import ErroAplicacao
from scripts.comum import RAIZ, bloqueio, ler_historico, status
from scripts.validar_pacote import validar_pacote


def montar_comando(raiz: Path, temporario: Path) -> list[str]:
    """Todos os parâmetros de empacotamento são definidos aqui."""
    return [
        sys.executable,
        "-u",
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--onedir",
        "--windowed",
        "--noupx",
        "--name",
        "DLPDownloader",
        "--paths",
        str(raiz / "src"),
        "--distpath",
        str(temporario / "dist"),
        "--workpath",
        str(temporario / "work"),
        "--specpath",
        str(temporario),
        "--icon",
        str(raiz / "flet.png"),
        "--add-data",
        f"{raiz / 'src/dlpdownloader/recursos'}:dlpdownloader/recursos",
        str(raiz / "main.py"),
    ]


def executar_compilador(comando: list[str], executar=subprocess.run) -> None:
    """Oculta saída no sucesso e mostra até 30 linhas de diagnóstico na falha."""
    try:
        executar(
            comando,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=True,
            env=ambiente_compilacao(),
        )
    except subprocess.CalledProcessError as erro:
        status("Últimas linhas do PyInstaller:")
        print("\n".join(((erro.stdout or "") + (erro.stderr or "")).splitlines()[-30:]))
        raise


def ambiente_compilacao() -> dict[str, str]:
    """Evita coletar DLLs incompatíveis de Git, Poppler ou outro software no PATH."""
    import PyQt6

    ambiente = dict(os.environ)
    windows = Path(ambiente.get("SystemRoot", r"C:\Windows"))
    caminhos = [
        Path(PyQt6.__file__).parent / "Qt6/bin",
        Path(sys.executable).parent,
        Path(sys.base_prefix),
        windows / "System32",
        windows,
    ]
    ambiente["PATH"] = os.pathsep.join(map(str, caminhos))
    for nome in ("QT_PLUGIN_PATH", "QT_QPA_PLATFORM_PLUGIN_PATH", "PYTHONPATH", "PYTHONHOME"):
        ambiente.pop(nome, None)
    return ambiente


def reconciliar(destino: Path, historico: list[dict]) -> list[dict]:
    """Recupera publicação concluída cuja gravação do histórico foi interrompida."""
    conhecidos = {item["numero"] for item in historico}
    for pasta in destino.glob("DLPDownloader-*"):
        if not (pasta / "DLPDownloader.exe").is_file() or not (pasta / "build.json").is_file():
            continue
        dados = json.loads((pasta / "build.json").read_text(encoding="utf-8"))
        if type(dados.get("numero")) is not int or dados["numero"] < 1:
            raise ValueError(f"Metadados de compilação inválidos: {pasta.name}")
        if dados["numero"] not in conhecidos:
            historico.append(dados)
            conhecidos.add(dados["numero"])
    return sorted(historico, key=lambda item: item["numero"])


def compilar(
    raiz: Path = RAIZ,
    destino: Path | None = None,
    executar=subprocess.run,
    validar_ferramentas=None,
) -> Path:
    """Publica staging completo; versões históricas nunca são sobrescritas."""
    from dlpdownloader.servicos.arquivos import gravar_json
    from dlpdownloader.servicos.dependencias import verificar

    destino = destino or raiz / "releases"
    status("Verificando pré-requisitos…")
    if os.name != "nt":
        raise RuntimeError("A distribuição suportada deve ser compilada no Windows.")
    for nome in ("PyInstaller", "Pillow", "PyQt6"):
        importlib.metadata.version(nome)
    (validar_ferramentas or verificar)(raiz, threading.Event())
    if not (raiz / "vendor/installed.json").is_file():
        raise RuntimeError("Prepare as ferramentas antes de compilar.")
    versao = tomllib.loads((raiz / "pyproject.toml").read_text(encoding="utf-8"))["project"][
        "version"
    ]
    with bloqueio(destino / ".compilacao.lock"):
        status("Verificando histórico e versões existentes…")
        arquivo_historico = destino / "historico.json"
        original = ler_historico(arquivo_historico)
        historico = reconciliar(destino, list(original))
        if historico != original:
            gravar_json(arquivo_historico, historico)
            status(f"Histórico recuperado: {len(historico)} versão(ões).")
        numero = max((item["numero"] for item in historico), default=0) + 1
        final = destino / f"DLPDownloader-{versao}-build.{numero}"
        status(f"Próxima versão: {versao}, compilação {numero}.")
        with tempfile.TemporaryDirectory(prefix=".compilacao-", dir=destino) as pasta:
            temporario = Path(pasta)
            status("Fazendo a compilação…")
            executar_compilador(montar_comando(raiz, temporario), executar)
            pacote = temporario / "dist/DLPDownloader"
            if not (pacote / "DLPDownloader.exe").is_file():
                raise RuntimeError("O compilador não gerou o executável esperado.")
            shutil.copytree(
                raiz / "vendor", pacote / "vendor", ignore=shutil.ignore_patterns(".cache", "*.zip")
            )
            shutil.copy2(raiz / "README.md", pacote / "README.md")
            status("Validando inicialização do pacote sem ferramentas globais…")
            validar_pacote(pacote, temporario / "dados-smoke")
            dados = {
                "numero": numero,
                "versao": versao,
                "data": datetime.now(timezone.utc).isoformat(),
                "pasta": final.name,
                "python": sys.version.split()[0],
                "pyinstaller": importlib.metadata.version("PyInstaller"),
            }
            gravar_json(pacote / "build.json", dados)
            status(f"Publicando {final.name}…")
            pacote.rename(final)
        status("Registrando versão no histórico…")
        gravar_json(arquivo_historico, [*historico, dados])
    status("Compilação concluída.")
    return final


def main() -> int:
    """CLI com retornos 0, 1 ou 130; o .spec temporário não é uma entrada."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destino", type=Path, help="Pasta de releases (padrão: releases/)")
    args = parser.parse_args()
    try:
        compilar(destino=args.destino.resolve() if args.destino else None)
    except KeyboardInterrupt:
        status("Compilação interrompida pelo usuário.")
        return 130
    except (
        OSError,
        ValueError,
        RuntimeError,
        subprocess.CalledProcessError,
        importlib.metadata.PackageNotFoundError,
        ErroAplicacao,
    ) as erro:
        status(f"ERRO: {erro}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
