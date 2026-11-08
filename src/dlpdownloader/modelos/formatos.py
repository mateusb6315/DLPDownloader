"""Traduz o perfil de saída em opções declarativas do yt-dlp."""

from dlpdownloader.modelos.download import SolicitacaoDownload


def argumentos_formato(pedido: SolicitacaoDownload) -> list[str]:
    """Escolhe faixas dinamicamente; nunca depende de IDs fixos do YouTube."""
    if pedido.perfil == "mp4":
        return [
            "-f",
            "bv[ext=mp4]+ba[ext=m4a]/b[ext=mp4]",
            "--merge-output-format",
            "mp4",
            "--remux-video",
            "mp4",
        ]
    if pedido.perfil == "mkv":
        return ["-f", "bv+ba/b", "--merge-output-format", "mkv", "--remux-video", "mkv"]
    argumentos = ["-f", "ba/b"]
    if pedido.perfil == "original":
        return argumentos + ["-x", "--audio-format", "best"]
    return argumentos + ["-x", "--audio-format", pedido.perfil]
