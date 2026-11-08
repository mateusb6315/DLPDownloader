# Ferramentas de terceiros

O código deste repositório não define a licença das ferramentas distribuídas.
Os executáveis são obtidos das releases indicadas em `vendor/manifest.json`.

- [yt-dlp: licença e componentes do executável](https://github.com/yt-dlp/yt-dlp#license).
- [FFmpeg-Builds: receitas e fontes do build](https://github.com/yt-dlp/FFmpeg-Builds).
  A variante selecionada é GPL; consulte também [FFmpeg](https://ffmpeg.org/legal.html).
- [Deno: licença MIT](https://github.com/denoland/deno/blob/main/LICENSE.md).

O script de preparação copia avisos/licenças presentes nos arquivos ZIP e inclui os
textos upstream em `vendor/licenses/`. Ao redistribuir, preserve esta pasta e as
obrigações de disponibilização das fontes correspondentes aos binários e componentes.
