"""Smoke test isolado de uma distribuição Windows antes de publicá-la."""

import argparse
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path


def validar_pacote(pacote: Path, dados: Path, limite: float = 40) -> None:
    """Exige estado PRONTO sem Python/ferramentas de terceiros no PATH."""
    from dlpdownloader.servicos.processos import encerrar_arvore

    dados.mkdir(parents=True, exist_ok=True)
    ambiente = {
        **os.environ,
        "QT_QPA_PLATFORM": "offscreen",
        "LOCALAPPDATA": str(dados),
        "DLP_SMOKE_TEST": "1",
    }
    ambiente["PATH"] = str(Path(ambiente.get("SystemRoot", r"C:\Windows")) / "System32")
    log = dados / "DLPDownloader/aplicacao.log"
    with (dados / "inicializacao.stderr").open("wb") as erros:
        processo = subprocess.Popen(
            [str(pacote / "DLPDownloader.exe")],
            cwd=dados,
            env=ambiente,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=erros,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        try:
            prazo = time.monotonic() + limite
            while time.monotonic() < prazo:
                conteudo = log.read_text(encoding="utf-8") if log.exists() else ""
                if "Estado da aplicação: PRONTO" in conteudo:
                    subprocess.run(
                        [
                            str(pacote / "DLPDownloader.exe"),
                            "--verificar-midia",
                            str(dados / "midia"),
                        ],
                        cwd=dados,
                        env=ambiente,
                        stdin=subprocess.DEVNULL,
                        stdout=subprocess.DEVNULL,
                        stderr=erros,
                        timeout=180,
                        check=True,
                        creationflags=subprocess.CREATE_NO_WINDOW,
                    )
                    return
                if processo.poll() is not None or "INDISPONIVEL" in conteudo:
                    break
                time.sleep(0.1)
            raise RuntimeError(
                "O pacote não alcançou o estado PRONTO no smoke test. "
                "Verifique dependências Qt e ferramentas portáteis."
            )
        finally:
            if processo.poll() is None:
                encerrar_arvore(processo)


def main() -> int:
    """Permite repetir a verificação de uma pasta já compilada."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pacote", type=Path)
    args = parser.parse_args()
    try:
        with tempfile.TemporaryDirectory(prefix="dlp-smoke-") as pasta:
            validar_pacote(args.pacote.resolve(), Path(pasta))
    except (OSError, RuntimeError, subprocess.SubprocessError) as erro:
        print(f"ERRO: {erro}", file=sys.stderr)
        return 1
    print("Pacote alcançou PRONTO em ambiente isolado.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
