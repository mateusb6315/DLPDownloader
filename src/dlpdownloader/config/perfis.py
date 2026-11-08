"""Catálogo de saídas; adicione novos perfis aqui e regras em modelos/formatos."""

# id, rótulo, extensão, bitrates permitidos, ajuda
PERFIS = (
    ("mp4", "Vídeo MP4", "mp4", (), "Melhor vídeo MP4 com áudio M4A disponível."),
    ("mkv", "Vídeo MKV — melhor disponível", "mkv", (), "Melhor vídeo e áudio disponíveis."),
    ("original", "Áudio original", None, (), "Preserva a faixa e a extensão de origem."),
    ("mp3", "Áudio MP3", "mp3", (128, 192, 256, 320), "Conversão com bitrate selecionado."),
    ("m4a", "Áudio M4A / AAC", "m4a", (None, 128, 192, 256), "Original ou conversão AAC."),
    ("opus", "Áudio Opus", "opus", (96, 128, 160, 192), "Conversão com bitrate selecionado."),
    (
        "flac",
        "Áudio FLAC (lossless)",
        "flac",
        (),
        "Não recupera qualidade perdida na origem. Preserva o áudio decodificado.",
    ),
    (
        "wav",
        "Áudio WAV PCM",
        "wav",
        (),
        "Áudio sem compressão perceptual. Não recupera qualidade perdida na origem.",
    ),
)
