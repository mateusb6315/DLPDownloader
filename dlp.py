import yt_dlp
import os

diretorio_padrao = r"J:\Biblioteca"


class Downloader:
    def __init__(self, url):
        self.url = url
        self.diretorio = os.path.join(diretorio_padrao, "%(title)s.%(ext)s")
        self.ydl_opts = {
            "format": "best",
            "outtmpl": self.diretorio,
            "noplaylist": True,
        }

    def downloadMP4(self):
        mp4_opts = self.ydl_opts.copy()
        mp4_opts.update(
            {
                "format": "bestvideo+bestaudio/best",
                "merge_output_format": "mp4",
            }
        )
        with yt_dlp.YoutubeDL(mp4_opts) as ydl:
            ydl.download([self.url])

    def downloadM4A(self):
        m4a_opts = self.ydl_opts.copy()
        m4a_opts.update(
            {
                "format": "bestaudio/best",
                "postprocessors": [
                    {
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "m4a",
                        "preferredquality": "192",
                    }
                ],
            }
        )
        with yt_dlp.YoutubeDL(m4a_opts) as ydl:
            ydl.download([self.url])
