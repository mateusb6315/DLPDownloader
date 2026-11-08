# DLP Downloader

Aplicativo desktop para baixar um vídeo ou áudio por vez, escolher o formato de saída
e salvar em uma pasta de sua preferência. Usa **PyQt6** na interface e **yt-dlp,
FFmpeg/FFprobe e Deno portáteis** no processamento, organizados em arquitetura MVC.

## Recursos

- Vídeo MP4 e MKV com seleção dinâmica de vídeo e áudio.
- Áudio original, MP3, M4A/AAC, Opus, FLAC e WAV PCM.
- Bitrate selecionável nos perfis de conversão correspondentes.
- Diretório escolhido pelo usuário e restaurado ao reabrir o aplicativo.
- Popup de progresso por faixa, com bytes, velocidade e ETA quando disponíveis.
- Interface responsiva e cancelamento dos processos da operação.
- Preservação de arquivos existentes e publicação somente após processamento.
- Ícone baseado em `flet.png`, independente do framework Flet.

O programa processa um item por operação e desativa playlists. Não implementa fila,
login, cookies ou atualização automática das ferramentas.

## Requisitos

O alvo de distribuição é **Windows x86-64**. O pacote desktop completo dispensa
Python, Qt, yt-dlp, FFmpeg e Deno instalados separadamente no computador de destino.

| Ferramenta | Para desenvolver ou compilar |
| --- | --- |
| Python | 3.13 ou 3.14, 64 bits; validação local com 3.13.3 |
| Poetry | 2.x, usando `poetry.lock` |
| Git | Obter o código e contribuir |
| GitHub CLI (`gh`) | Opcional, para PR e merge remoto pelos scripts |
| Internet | Preparação das ferramentas e download dos conteúdos |

PyQt6 é a dependência de execução Python. PyInstaller, Pillow, pytest, pytest-qt,
Ruff e build ficam no grupo de desenvolvimento. Flet e a biblioteca Python `yt-dlp`
não são dependências do aplicativo refatorado.

## Instalação e execução

Em PowerShell, com o launcher `py` e Python 3.13 instalado:

```powershell
git clone https://github.com/mateusb6315/DLPDownloader.git
cd DLPDownloader
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install poetry
.\.venv\Scripts\python.exe scripts\preparar_ambiente.py
.\.venv\Scripts\python.exe scripts\preparar_ferramentas.py
.\.venv\Scripts\python.exe -m dlpdownloader
```

Não é necessário ativar a `.venv`. Se usar Python 3.14, ajuste a criação do ambiente.
O script de ambiente executa `poetry install`, instalando o pacote local e o grupo dev.
Após instalar, também pode executar `.\.venv\Scripts\python.exe main.py`.

Se `python` ou `poetry` passar por um pyenv sem versão selecionada, use o caminho
explícito da `.venv` acima. Reserve espaço para download, extração e empacotamento:
FFmpeg e Deno ocupam uma parte relevante da distribuição.

### Ferramentas portáteis

[vendor/manifest.json](vendor/manifest.json) fixa versões, URLs oficiais e SHA-256.
`preparar_ferramentas.py` verifica os downloads e extrai somente arquivos esperados.
Executáveis e `installed.json` são gerados localmente e ignorados pelo Git.

```text
vendor/
├── manifest.json
├── installed.json           # hashes dos executáveis preparados
├── yt-dlp/yt-dlp.exe
├── ffmpeg/ffmpeg.exe
├── ffmpeg/ffprobe.exe
├── deno/deno.exe
└── licenses/
```

Na abertura, a verificação roda em segundo plano. A aplicação usa caminhos absolutos
e não procura essas ferramentas no `PATH`. O Deno atende aos desafios JavaScript do
YouTube; o executável oficial do yt-dlp inclui os scripts EJS correspondentes.
[Configuração oficial de EJS](https://github.com/yt-dlp/yt-dlp/wiki/EJS).

Para atualizar, revise versões, URLs e checksums no manifesto, prepare novamente e
rode a integração real. Falha de checksum interrompe a preparação; não desative essa
verificação. Nenhum download de atualização ocorre ao abrir a GUI.

## Como usar

1. Abra o aplicativo e aguarde a verificação das ferramentas.
2. Cole um link HTTP ou HTTPS.
3. Escolha o formato e, quando disponível, o bitrate.
4. Use **Escolher pasta** para alterar o destino.
5. Clique em **Baixar** e acompanhe o popup até a confirmação do caminho final.
6. Para interromper, use **Cancelar**.

A pasta é salva imediatamente após uma seleção válida. Cancelar o seletor preserva
o valor anterior. Se a pasta salva estiver indisponível, escolha outra: não há mudança
silenciosa do destino.

Os arquivos são preparados em uma subpasta `.dlp-*` dentro do destino e publicados
quando o processamento termina. Os nomes incluem título e ID; conversões com bitrate
explícito incluem também o bitrate. Arquivos existentes são preservados. As pastas
temporárias são removidas após sucesso, erro ou cancelamento tratado; quedas de energia
ou término forçado pelo sistema podem deixar temporários para remoção manual.

### Perfis de saída

| Perfil | Seleção/processamento | Bitrate |
| --- | --- | --- |
| MP4 | Melhor vídeo MP4 + áudio M4A; fallback para MP4 combinado | Da origem |
| MKV | Melhor vídeo + melhor áudio disponíveis, remuxados para MKV | Da origem |
| Áudio original | Melhor faixa, extraída sem conversão quando possível | Da origem |
| MP3 | Conversão com `libmp3lame` | 128, 192, 256 ou 320 kb/s |
| M4A/AAC | Original ou conversão AAC | Original, 128, 192 ou 256 kb/s |
| Opus | Conversão com `libopus` | 96, 128, 160 ou 192 kb/s |
| FLAC | Codec lossless | Não selecionável |
| WAV PCM | Sem compressão perceptual | Não selecionável |

FLAC/WAV não recuperam detalhes perdidos em uma fonte AAC/Opus. Bitrate maior também
não aumenta a fidelidade da origem. O bitrate escolhido é um parâmetro de codificação;
o valor medido pode variar conforme codec, duração e modo de codificação.

MP4 é um contêiner, não uma promessa de compatibilidade com todos os players. Se não
existir uma combinação adequada ao perfil, o download falha sem trocar o formato.
A seleção é dinâmica: IDs como `299+140` não são fixados no código.
[Seleção de formatos do yt-dlp](https://github.com/yt-dlp/yt-dlp#format-selection).

### Progresso e encerramento

O popup usa eventos JSON do yt-dlp. A barra representa a faixa atual e pode reiniciar
quando o áudio começa após o vídeo; o rótulo identifica a faixa. Total estimado é
sinalizado. Sem total conhecido, ou durante junção/conversão, a barra é indeterminada.
Não há simulação de percentual de processamento do FFmpeg.

Cancelar pode levar alguns segundos para encerrar processos e liberar os arquivos.
Fechar o popup ou pressionar Escape também solicita cancelamento. Fechar a janela
principal durante o trabalho pede confirmação e aguarda a liberação antes de sair.

## Preferências e logs

Os dados por usuário ficam fora da pasta de instalação:

```text
%LOCALAPPDATA%/DLPDownloader/
├── config.json
├── aplicacao.log
└── aplicacao.log.1 …
```

As preferências têm esquema versionado e gravação atômica. JSON inválido é preservado
até uma nova pasta ser salva. Os logs têm rotação; a saída bruta do yt-dlp não é
registrada porque pode conter links assinados ou outros dados sensíveis.

## Arquitetura

```text
main.py / python -m dlpdownloader
└── aplicacao.py                       composição e logging
    └── ControladorDownload
        ├── modelos/                  dados e regras puras
        ├── servicos/                 arquivos e processos
        ├── Trabalhador + QThread     execução fora da GUI
        └── visoes/                   widgets e sinais
```

| Pasta | Responsabilidade |
| --- | --- |
| `src/dlpdownloader/config/` | Textos, tema, perfis e caminhos |
| `src/dlpdownloader/modelos/` | Solicitação, estados, erros, seleção e progresso |
| `src/dlpdownloader/servicos/` | Executáveis, persistência e publicação do resultado |
| `src/dlpdownloader/controladores/` | Intenções, tarefas e ciclo de vida |
| `src/dlpdownloader/visoes/` | Janela principal, popup e tema |
| `src/dlpdownloader/recursos/` | PNG usado em execução |
| `tests/` | Regras, serviços, GUI, scripts e integrações |
| `scripts/` | Preparação, qualidade, compilação e rotina Git/GitHub |
| `vendor/` | Manifesto, ferramentas preparadas e licenças |

Model e serviços não importam Qt; a View não importa Model, serviço ou Controller.
O Controller recebe dependências por injeção. O trabalhador traduz callbacks em sinais;
somente a GUI atualiza widgets. Processos usam argumentos separados, `shell=False`,
leitura contínua limitada e cancelamento por evento seguro entre threads.

## Testes e qualidade

O ciclo padrão não baixa mídia nem depende dos executáveis portáteis:

```powershell
.\.venv\Scripts\python.exe scripts\verificar.py
.\.venv\Scripts\python.exe -m pytest tests\test_interface_controlador.py -v
```

`verificar.py` executa Ruff, conferência de formatação e `pytest -m "not externo"`.
Os testes de GUI usam Qt offscreen; os testes de build usam um compilador falso.

Depois de preparar `vendor/`, execute a integração real:

```powershell
.\.venv\Scripts\python.exe -m pytest -q -m externo
```

Ela gera mídia sintética com FFmpeg, serve somente em `127.0.0.1`, executa yt-dlp e
verifica streams com FFprobe. Não baixa conteúdo do YouTube. Ambientes que bloqueiam
sockets locais precisam permitir esse tráfego para executar esses testes.

A CI Windows valida instalação, qualidade e pacote Python. Em tags, um job separado
prepara ferramentas e gera a distribuição desktop como artefato.

## Compilação

Com dependências e ferramentas preparadas:

```powershell
.\.venv\Scripts\python.exe scripts\compilar.py
# Opcional: escolher onde publicar a distribuição local
.\.venv\Scripts\python.exe scripts\compilar.py --destino C:\Pacotes\DLPDownloader
```

O script chama PyInstaller diretamente e não lê um `.spec` do repositório. O `.spec`
intermediário gerado pelo próprio PyInstaller fica no staging temporário e é descartado.
Todos os parâmetros ficam em `scripts/compilar.py`: `onedir`, sem console, strip ou UPX.
O processo usa um `PATH` limitado ao Python, Qt e Windows, evitando capturar DLLs
incompatíveis de outros programas instalados na máquina.

```text
releases/
├── historico.json
└── DLPDownloader-1.0.0-build.1/
    ├── DLPDownloader.exe
    ├── _internal/
    ├── vendor/
    ├── README.md
    └── build.json
```

A versão vem do `pyproject.toml`; o número do build cresce a partir do histórico e
das publicações recuperadas. Builds simultâneos são bloqueados e falhas não publicam
pacotes incompletos. A saída é resumida, com diagnóstico final quando PyInstaller falha.

O build já exige um smoke test de inicialização em modo offscreen, com PATH e dados
isolados, antes de publicar a pasta. Esse teste verifica o estado PRONTO e não baixa mídia.
Para repetir em um pacote existente, use `scripts/validar_pacote.py` com o caminho da pasta.

Distribua **a pasta inteira**. Valide em Windows sem Python ou ferramentas globais,
incluindo download, junção, cancelamento, destino com espaços e persistência.

Para wheel/sdist: `.\.venv\Scripts\python.exe -m poetry build`. Esses artefatos Python
não substituem o pacote desktop com `vendor/`.

## Rotina Git/GitHub

[scripts/git_workflow.py](scripts/git_workflow.py) oferece ações explícitas:

```powershell
.\.venv\Scripts\python.exe scripts\git_workflow.py status
.\.venv\Scripts\python.exe scripts\git_workflow.py iniciar melhorar-progresso
.\.venv\Scripts\python.exe scripts\git_workflow.py commit -m "Melhora documentação" --arquivos README.md
.\.venv\Scripts\python.exe scripts\git_workflow.py publicar
.\.venv\Scripts\python.exe scripts\git_workflow.py sincronizar
.\.venv\Scripts\python.exe scripts\git_workflow.py pr --help
.\.venv\Scripts\python.exe scripts\git_workflow.py merge-local --help
.\.venv\Scripts\python.exe scripts\git_workflow.py merge-pr --help
```

`iniciar` cria `codex/<nome>`. `commit` aceita arquivos individuais e recusa stage
preexistente. `publicar` envia a branch atual para uma branch remota de mesmo nome.
`sincronizar` exige árvore limpa/upstream e permite somente fast-forward.
PR usa `gh` autenticado e descrição em arquivo. Conflitos interrompem os comandos;
não há force-push ou resolução automática de conflitos.

## Problemas conhecidos e investigação

| Situação | Ação |
| --- | --- |
| Baixar indisponível na abertura | Prepare as ferramentas e reinicie; confira hashes e manifesto |
| Falha de extração | Verifique link, conexão, acesso e compatibilidade do yt-dlp fixado |
| MP4 indisponível | Experimente MKV se atender à necessidade; o perfil não muda sozinho |
| Falha ao gravar | Verifique pasta existente, permissão e espaço livre |
| Arquivo já existe | O original foi preservado; use outra pasta ou mova o anterior |
| Preferências inválidas | Escolha a pasta novamente para gravar uma configuração válida |
| Erro inesperado | Consulte o log em `%LOCALAPPDATA%/DLPDownloader/` e relate o cenário |

Fontes externas podem mudar. A integração local comprova HTTP, protocolo e conversões,
mas não garante disponibilidade contínua do YouTube, conteúdo privado, restrições
regionais, transmissões ao vivo ou DRM. Baixe apenas conteúdos cujo download você pode realizar.

## Colaboração

Abra uma issue neste repositório com reprodução, perfil escolhido, versão e resultado
esperado. Não publique credenciais, URLs privadas ou logs sem revisar dados sensíveis.

1. Crie uma branch com propósito claro.
2. Use nomes em português e uma responsabilidade principal por módulo.
3. Coloque regras no Model e I/O nos serviços; não faça downloads na View.
4. Injete dependências e use arquivos temporários nos testes.
5. Inclua teste de regressão e execute `scripts/verificar.py`.
6. Rode integração real se mudar comandos, codecs ou protocolo.
7. Atualize a documentação afetada e abra um PR.

`docs/` é ignorada pelo Git por decisão do projeto. A documentação necessária para
um clone fica neste README e no [catálogo de scripts](scripts/README.md).

## Licenças

Não existe um arquivo de licença para o código do aplicativo neste repositório.
Nenhuma licença foi presumida ou criada na refatoração.

Terceiros têm termos próprios. Preserve [vendor/licenses/](vendor/licenses/), incluindo
os avisos obtidos na preparação, e confira obrigações de redistribuição dos executáveis
e disponibilização das fontes correspondentes.
