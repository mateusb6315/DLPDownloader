"""Smoke test isolado de uma distribuição Windows antes de publicá-la."""

import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services._infra.processos import encerrar_arvore
from services._models.atualizacoes import VersaoDistribuicao


def _validar_midia(pacote: Path, dados: Path, ambiente: dict, erros) -> None:
    pasta_midia = dados / "midia"
    resultado = subprocess.run(
        [str(pacote / "DLPDownloader.exe"), "--verificar-midia", str(pasta_midia)],
        cwd=dados,
        env=ambiente,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=erros,
        timeout=180,
        check=False,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )
    arquivo_resultado = pasta_midia / "resultado.json"
    relatorio = (
        json.loads(arquivo_resultado.read_text(encoding="utf-8"))
        if arquivo_resultado.is_file()
        else {}
    )
    perfis = ["mp4", "mkv", "original", "mp3", "m4a", "opus", "flac", "wav"]
    if (
        resultado.returncode
        or relatorio.get("sucesso") is not True
        or relatorio.get("perfis") != perfis
    ):
        raise RuntimeError(
            f"O diagnóstico de mídia do executável falhou ({resultado.returncode}, "
            f"{relatorio.get('erro', 'resultado incompleto')})."
        )


def validar_pacote(
    pacote: Path,
    dados: Path,
    limite: float = 40,
    *,
    plataforma: str = "offscreen",
    versao_beta: str | None = None,
    versao: VersaoDistribuicao | None = None,
) -> None:
    """Exige estado PRONTO sem Python/ferramentas de terceiros no PATH."""
    if versao_beta is not None:
        versao = VersaoDistribuicao(versao_beta, beta=True)
    dados.mkdir(parents=True, exist_ok=True)
    ambiente = {
        **os.environ,
        "QT_QPA_PLATFORM": plataforma,
        "LOCALAPPDATA": str(dados),
        "DLP_SMOKE_TEST": "1",
    }
    for nome in ("QT_PLUGIN_PATH", "QT_QPA_PLATFORM_PLUGIN_PATH", "PYTHONPATH", "PYTHONHOME"):
        ambiente.pop(nome, None)
    ambiente["PATH"] = str(Path(ambiente.get("SystemRoot", r"C:\Windows")) / "System32")
    log = dados / "DLPDownloader/aplicacao.log"
    arquivo_erros = dados / "inicializacao.stderr"
    with arquivo_erros.open("wb") as erros:
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
                    if versao is not None and not any(
                        linha.endswith(f"Versão da aplicação: {versao}")
                        for linha in conteudo.splitlines()
                    ):
                        raise RuntimeError(f"A distribuição não informou a versão {versao}.")
                    _validar_midia(pacote, dados, ambiente, erros)
                    return
                if processo.poll() is not None or "INDISPONIVEL" in conteudo:
                    break
                time.sleep(0.1)
            ultimas_linhas = (
                conteudo.splitlines()[-10:]
                + arquivo_erros.read_text(encoding="utf-8", errors="replace").splitlines()[-10:]
            )
            detalhes = "\n".join(ultimas_linhas)
            codigo = processo.poll()
            raise RuntimeError(
                f"O pacote não alcançou PRONTO no smoke test (saída: {codigo}).\n{detalhes}"
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
    except (OSError, RuntimeError, ValueError, subprocess.SubprocessError) as erro:
        print(f"ERRO: {erro}", file=sys.stderr)
        return 1
    print("Pacote alcançou PRONTO em ambiente isolado.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
