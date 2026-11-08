"""Conjunto portátil mínimo consistente para testes sem downloads."""

import json
from pathlib import Path

from dlpdownloader.servicos.manifesto import sha256


def criar_vendor(raiz: Path) -> Path:
    vendor = raiz / "vendor"
    vendor.mkdir(parents=True, exist_ok=True)
    ferramentas, hashes = [], {}
    for nome, arquivos in [
        ("yt-dlp", ["yt-dlp.exe"]),
        ("ffmpeg", ["ffmpeg.exe", "ffprobe.exe", "avcodec.dll"]),
        ("deno", ["deno.exe"]),
    ]:
        destinos = {a: f"{nome}/{a}" for a in arquivos}
        ferramentas.append(
            {"nome": nome, "versao": "teste", "sha256": "0" * 64, "arquivos": destinos}
        )
        for relativo in destinos.values():
            arquivo = vendor / relativo
            arquivo.parent.mkdir(exist_ok=True)
            arquivo.write_bytes(b"executavel")
            hashes[relativo] = sha256(arquivo)
    manifesto = vendor / "manifest.json"
    manifesto.write_text(json.dumps({"ferramentas": ferramentas}), encoding="utf-8")
    (vendor / "installed.json").write_text(
        json.dumps({"manifesto_sha256": sha256(manifesto), "arquivos": hashes}), encoding="utf-8"
    )
    (vendor / "licenses").mkdir(exist_ok=True)
    (vendor / "licenses/README.md").write_text("Licenças", encoding="utf-8")
    return vendor
