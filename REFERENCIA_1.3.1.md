# Referência executável da versão 1.3.1

Registro do checkpoint 1 da refatoração, issue #2, em 16/11/2026.
Código de referência: `9acd968b4fc57bf7218f023e22721b36467b2da0`.
A branch `codex/refatoracao-referencia` partiu do mesmo commit de
`codex/refatoracao-integracao`. Nenhum código do aplicativo foi alterado.
A versão foi conferida em `pyproject.toml` e no log do executável existente.

## Ambiente e reprodução

Windows x64, Python 3.13.3, PyQt6 6.10.2, pytest 9.2.0, Ruff 0.17.4,
PyInstaller 6.22.3 e Nuitka 4.3.5 no ambiente utilizado.
Os comandos foram executados na raiz do worktree dedicado, usando o Python
`C:/Projetos/Projeto Golden Apple/.venv/Scripts/python.exe`.
O pytest inclui `src` e a raiz no caminho de importação, portanto testa o código
local do worktree mesmo reutilizando esse ambiente virtual.

Para reproduzir em um checkout independente, prepare `.venv` e `vendor` conforme
`AGENTS.md`, então execute:

```powershell
.\.venv\Scripts\python.exe scripts\verificar.py
.\.venv\Scripts\python.exe -m pytest -q -m externo -x
$env:PYTHONPATH = (Resolve-Path src).Path
.\.venv\Scripts\python.exe -c "from pathlib import Path; from scripts.validar_pacote import validar_pacote; validar_pacote(Path(r'C:/Projetos/Projeto Golden Apple/releases/DLPDownloader-1.3.1'), Path(r'C:/temporario/dlp-referencia-nova'), plataforma='windows')"
```

Use uma pasta de dados inexistente/nova por execução do smoke. O caminho do
pacote deve ser absoluto. O smoke substitui LOCALAPPDATA apenas no subprocesso;
não lê nem altera as preferências pessoais. Não execute o reparador para reproduzir
esta referência: ele baixa ferramentas e altera a distribuição.

Neste worktree, `vendor/deno`, `vendor/ffmpeg` e `vendor/yt-dlp` são junções locais
para o `vendor` original; `installed.json` foi copiado. Os binários grandes não
foram duplicados nem adicionados ao Git. O manifesto versionado continuou intacto.
As junções são preparação local, não parte da distribuição.

## Resultados observados

| Verificação | Resultado |
| --- | --- |
| Ruff | Todos os checks aprovados |
| Formatação | 76 arquivos já formatados |
| Suíte padrão | 174 aprovados, 18 externos excluídos; 5,73 s |
| Mídia local real | 18 aprovados, 174 excluídos; 71,07 s |
| Pacote PyInstaller 1.3.1, plugin Qt Windows | Inicializou em diretório diferente, informou versão 1.3.1 e alcançou PRONTO |
| Mídia no executável congelado | `sucesso: true`; mp4, mkv, original, mp3, m4a, opus, flac, wav |

A integração real gera mídia sintética com FFmpeg, serve somente em `127.0.0.1`
e baixa com yt-dlp real. Verifica os oito perfis, áudio/vídeo via FFprobe,
junção DASH de duas faixas, VP9, H.264, HEVC, AV1, Vorbis, HLS e limpeza dos
arquivos temporários. Fonte: `tests/test_integracao_midia.py` no commit acima.
O smoke congelado também verifica recusa de sobrescrita e cancelamento já
solicitado antes do download (`servicos/autoteste.py`). Isso não comprova todos
os casos de cancelamento em andamento nem substitui a inspeção interativa da UI.

A primeira execução restrita falhou nos 18 externos com `ErroDownload`; o
pacote chegou a PRONTO mas sua mídia falhou igualmente. Repetir ambos fora do
sandbox, com autorização de execução, aprovou tudo sem mudança de código ou
ferramentas. Portanto o sandbox com rede restrita não é um ambiente válido para
essas integrações localhost. A criação das junções também exigiu execução fora
do sandbox. Essas falhas de preparação não foram contabilizadas como regressões.

## Pacote anterior preservado para upgrade

Artefatos existentes em `C:/Projetos/Projeto Golden Apple/releases/`, sem
recompilação ou modificação nesta etapa. A pasta validada é
`DLPDownloader-1.3.1/`; contém executável na raiz, `lib/` e `vendor/` externo.
O instalador e o arquivo 7z permanecem disponíveis para a etapa de upgrade.
Não se afirma que foram produzidos pelo commit de referência: a proveniência
do build antigo não está registrada; sua identidade é fixada pelos hashes.

| Artefato relativo a releases | SHA-256 |
| --- | --- |
| `DLPDownloader-1.3.1-setup.exe` | `3DA6574723DA74F34C9AFB0D1996E3EC2F8ADB8377D9D5BB47DCA9022EC04B2E` |
| `DLPDownloader-1.3.1.7z` | `B1D617F48088927008C817ED80904EEFA11D080137137B7DB9B0123A239FD753` |
| `DLPDownloader-1.3.1/DLPDownloader.exe` | `AA23CD767EDAF7B8356DB63F1987A096A962EAED0F0144B3AA7BBA3A6FB6801D` |
| `DLPDownloader-1.3.1/vendor/repair.exe` | `33F77257E583B3A6DB6D630454FEE7C23CD9C20AC5715CF0A973AFF7A37C80BD` |

O SHA-256 de `vendor/manifest.json`, igual no checkout e no pacote, é
`8967285B3D064DE769DEEB7E585D2ECBE8ED908057C2CDE58E8A62AEC3E85178`.
Fixa yt-dlp 2026.10.26, FFmpeg autobuild-2026-11-08-12-35 e Deno v2.9.8.
O smoke executa verificação de integridade das ferramentas.

## Contratos a preservar durante o porte

- `main.py`, `python -m dlpdownloader` e o entry point instalado
  `dlpdownloader = dlpdownloader.aplicacao:main` convergem na composição atual.
  O atalho Inno aponta para `{app}/DLPDownloader.exe`.
- A raiz externa em distribuição deriva de `sys.executable`, independentemente
  do diretório atual; em fonte deriva de `config/caminhos.py`. O ícone deriva
  do módulo: `recursos/flet.png`, observado no pacote em
  `lib/dlpdownloader/recursos/flet.png`. O PNG da raiz é entrada do compilador.
- Preferências: `%LOCALAPPDATA%/DLPDownloader/config.json`, esquema
  `{"versao": 1, "diretorio": "caminho absoluto"}`. Logs ficam no mesmo diretório,
  com rotação de 1.000.000 bytes e três backups. Não transportar saída bruta do
  yt-dlp para os logs.
- `scripts/validar_pacote.py` limpa variáveis Python/Qt externas, restringe PATH
  ao System32, isola LOCALAPPDATA e espera PRONTO por até 40 segundos. Define
  `DLP_SMOKE_TEST=1`, que impede consulta automática de releases e exige ícone
  carregável e verificação de ferramentas fora da thread de interface.
- Após PRONTO, chama o executável com `--verificar-midia <dados>` (limite de
  180 segundos). Esse contrato deve sobreviver à troca do compilador e produz
  `resultado.json`; o subprocesso deve retornar zero. O validador encerra a
  árvore da GUI ao final, portanto não comprova fechamento normal do usuário.
- O Inno estável tem AppId `330DC7E6-C8B5-44AA-A38A-14D2DF57B4E1` e pasta
  `{autopf64}/DLP Downloader`; beta usa `2AFCE230-A591-4A7F-9829-10D3CFE58D03`
  e `DLP Downloader Beta`. Exige administrador e concede `users-modify` à pasta.
  O script atual copia arquivos sem remover obsoletos.

A instalação sobre a versão antiga, preservação efetiva das preferências pelo
upgrade e abertura do reparador permanecem verificações da etapa de distribuição
nova. Não foram executadas aqui. Use o instalador identificado acima em uma pasta
de teste dedicada, registre preferências isoladas, instale a release Nuitka sobre
a mesma pasta e confirme o atalho, inicialização, ferramentas e reparador. Os
artefatos locais não estão no Git; outro ambiente precisará obter cópias e conferir
os hashes antes de afirmar que reproduziu o mesmo upgrade.
