# DLP Downloader

Aplicativo desktop para baixar um vídeo ou áudio por vez, escolher o formato de saída
e salvar em uma pasta de sua preferência. A versão **1.3.0** é destinada a
**Windows de 64 bits** e inclui as ferramentas necessárias para funcionar.

## Novidades recentes

- Pacote menor: a pasta do aplicativo passou de aproximadamente **530 MB para 360 MB**,
  uma redução de cerca de **170 MB (32%)**. O arquivo compactado para download tem cerca
  de **133 MB**. Esses valores são os registrados nas [notas da versão](changelog/1.3.0.md)
  e podem variar entre compilações; reserve espaço também para extração e downloads.
- Reparo das ferramentas: se arquivos necessários estiverem ausentes ou alterados,
  o aplicativo oferece abrir o reparador em um terminal.
- Organização dos arquivos internos na pasta `lib`, com as ferramentas em `vendor`.
- Mensagens revisadas e novas janelas de aviso e orientação.

Os oito formatos de saída continuam disponíveis. A versão usa uma variante menor do
FFmpeg, que pode não reconhecer alguns formatos de origem menos comuns.

## Baixar e abrir o aplicativo

1. Acesse a [página de releases](https://github.com/mateusb6315/DLPDownloader/releases)
   e escolha o pacote Windows da versão desejada.
2. Extraia **todo o conteúdo** do arquivo compactado para uma pasta em que você possa
   gravar arquivos. Não execute o programa de dentro do ZIP.
3. Abra `DLPDownloader.exe` e aguarde a verificação das ferramentas.

Não é necessário instalar Python, Qt ou as ferramentas de mídia separadamente.
Mantenha `DLPDownloader.exe`, `lib` e `vendor` juntos. Para mover o aplicativo, mova
sua pasta inteira. A conexão com a internet é necessária para baixar conteúdo,
consultar atualizações e reparar ferramentas.

```text
DLPDownloader-1.3.0/
├── DLPDownloader.exe        # abra este arquivo
├── lib/                    # arquivos internos; mantenha a pasta completa
├── vendor/                 # ferramentas de mídia e repair.exe
└── README.md
```

## Recursos

- Vídeo MP4 e MKV com seleção dinâmica de vídeo e áudio.
- Áudio original, MP3, M4A/AAC, Opus, FLAC e WAV PCM.
- Bitrate selecionável nos perfis de conversão correspondentes.
- Diretório escolhido pelo usuário e restaurado ao reabrir o aplicativo.
- Janela de progresso por faixa, com tamanho baixado, velocidade e tempo restante quando disponíveis.
- Interface responsiva e cancelamento dos processos da operação.
- Arquivo final salvo após o processamento, com confirmação antes de substituir outro de mesmo nome.
- Consulta de novas versões pelo menu **Opções → Procurar atualizações**.
- Verificação das ferramentas e opção de reparo quando houver arquivos ausentes ou alterados.

O programa baixa um item por vez, sem fila ou playlists. A interface não oferece
login nem importação de cookies para conteúdo que exija autenticação.

## Como usar

1. Abra o aplicativo e aguarde a verificação das ferramentas.
2. Cole um link HTTP ou HTTPS.
3. Escolha o formato e, quando disponível, o bitrate.
4. Use **Escolher pasta** para alterar o destino.
5. Clique em **Baixar** e acompanhe a janela de progresso até a mensagem de conclusão e o caminho final.
6. Para interromper, use **Cancelar**.

A pasta é salva imediatamente após uma seleção válida. Cancelar o seletor preserva
o valor anterior. Se a pasta salva estiver indisponível, escolha outra: não há mudança
silenciosa do destino.

Os arquivos são preparados em uma subpasta `.dlp-*` dentro do destino e publicados
quando o processamento termina. Os nomes incluem título e ID; conversões com bitrate
explícito incluem também o bitrate. Se já existir um arquivo com o mesmo nome, ao fim
do processamento o aplicativo pergunta se deseja substituí-lo. Escolha **Sim** para
substituir o arquivo ou **Não** para manter o original e encerrar a operação. As pastas
temporárias são removidas após sucesso, erro ou cancelamento tratado; quedas de energia
ou término forçado pelo sistema podem deixar temporários para remoção manual.

### Reparar ferramentas portáteis

Ao detectar ferramentas ausentes ou danificadas, o aplicativo pergunta:

> Algumas ferramentas foram danificadas ou estão ausentes. Deseja iniciar o script de reparo dos arquivos?

- **Sim:** o DLP Downloader fecha e abre o reparador em um terminal separado.
  Aguarde a mensagem de conclusão, pressione qualquer tecla para fechar o terminal
  e abra o DLP Downloader novamente.
- **Não:** aparece uma orientação para fechar o aplicativo e executar `repair.exe`
  na pasta `vendor`. Os downloads ficam indisponíveis até resolver o problema.

Para iniciar o reparo manualmente, feche todas as janelas do DLP Downloader e abra
`vendor/repair.exe` pelo Explorador de Arquivos. Também é possível usar o PowerShell,
na pasta do aplicativo:

```powershell
.\vendor\repair.exe
```

O reparador exige internet e permissão de escrita na pasta do aplicativo. Ele baixa
novamente todas as ferramentas declaradas, verifica sua integridade e substitui os
arquivos de ferramentas e seus metadados sem pedir confirmação individual. Mantenha
o aplicativo fechado até o fim; o reparador impede a abertura durante a operação.

O reparo cobre as ferramentas de `vendor`; ele não restaura `lib`, o executável
principal nem o próprio `repair.exe`. Se esses arquivos estiverem ausentes ou
corrompidos, extraia novamente o pacote completo. Se o reparo falhar, leia a mensagem
no terminal e confira a conexão e a permissão de escrita antes de tentar novamente.

### Procurar atualizações

Abra **Opções → Procurar atualizações**, no canto superior direito. Se houver uma
release estável mais recente, **Baixar agora** abre a página da versão no navegador;
**Deixar para depois** fecha o aviso. O aplicativo também faz essa consulta ao iniciar.
A consulta exige internet e não instala nem substitui arquivos automaticamente.

Para atualizar, baixe o novo pacote, feche o aplicativo e extraia a pasta completa da
nova versão. Sua pasta de destino salva fica fora da instalação e continua disponível.
Em uma beta, a release estável da mesma versão também é oferecida. A execução pelo
código-fonte não tem versão de distribuição para essa consulta.

### Perfis de saída

| Perfil | Seleção/processamento | Bitrate |
| --- | --- | --- |
| MP4 | Melhor vídeo MP4 + áudio M4A; se necessário, usa MP4 com áudio integrado | Da origem |
| MKV | Melhor vídeo + melhor áudio disponíveis, remuxados para MKV | Da origem |
| Áudio original | Melhor faixa, extraída sem conversão quando possível | Da origem |
| MP3 | Conversão com `libmp3lame` | 128, 192, 256 ou 320 kb/s |
| M4A/AAC | Original ou conversão AAC | Original, 128, 192 ou 256 kb/s |
| Opus | Conversão com `libopus` | 96, 128, 160 ou 192 kb/s |
| FLAC | Compressão de áudio sem perdas | Não selecionável |
| WAV PCM | Áudio sem compressão | Não selecionável |

FLAC/WAV não recuperam detalhes perdidos em uma fonte AAC/Opus. Bitrate maior também
não aumenta a fidelidade da origem. O bitrate escolhido é um parâmetro de codificação;
o valor medido pode variar conforme codec, duração e modo de codificação.

MP4 é um contêiner, não uma promessa de compatibilidade com todos os players. Se não
existir uma combinação adequada ao perfil, o download falha sem trocar o formato.
A seleção é dinâmica: IDs como `299+140` não são fixados no código.
[Seleção de formatos do yt-dlp](https://github.com/yt-dlp/yt-dlp#format-selection).

### Progresso e encerramento

A janela de progresso acompanha os dados enviados pela ferramenta de download.
A barra representa a faixa atual e pode reiniciar
quando o áudio começa após o vídeo; o rótulo identifica a faixa. Total estimado é
sinalizado. Sem total conhecido, ou durante junção/conversão, a barra indica atividade sem mostrar uma porcentagem.
Não há simulação de percentual de processamento do FFmpeg.

Cancelar pode levar alguns segundos para encerrar processos e liberar os arquivos.
Fechar a janela de progresso ou pressionar Escape também solicita cancelamento. Fechar a janela
principal durante o trabalho pede confirmação e aguarda a liberação antes de sair.

## Preferências e logs

O aplicativo lembra a pasta escolhida para salvar seus downloads. Essa preferência e
os registros usados para investigar erros ficam fora da pasta do aplicativo. Para
encontrá-los, cole `%LOCALAPPDATA%\DLPDownloader` na barra do Explorador de Arquivos:

```text
%LOCALAPPDATA%/DLPDownloader/
├── config.json
├── aplicacao.log
└── aplicacao.log.1 …
```

O arquivo `config.json` guarda a pasta escolhida. Se essa configuração estiver inválida,
escolha a pasta novamente no aplicativo para salvá-la. Os arquivos `aplicacao.log`
registram informações para diagnóstico e são renovados automaticamente para limitar
o espaço ocupado. A saída completa do yt-dlp não é gravada, pois pode conter links
assinados ou outros dados sensíveis.

## Desenvolvimento

As seções a seguir explicam como preparar e manter o código-fonte. Para usar o
aplicativo pronto, siga [Baixar e abrir o aplicativo](#baixar-e-abrir-o-aplicativo).

### Requisitos

O alvo de distribuição é **Windows x86-64**. O pacote desktop completo dispensa
Python, Qt, yt-dlp, FFmpeg e Deno instalados separadamente no computador de destino.

| Ferramenta | Para desenvolver ou compilar |
| --- | --- |
| Python | 3.13 ou 3.14, 64 bits; validação local com 3.13.3 |
| Poetry | 2.x, usando `poetry.lock` |
| Git | Obter o código e contribuir |
| GitHub CLI (`gh`) | Opcional, para PR e merge remoto pelos scripts |
| Internet | Preparação das ferramentas e download dos conteúdos |

PyQt6 e PyYAML são as dependências de execução Python. PyInstaller, Pillow, pytest, pytest-qt,
Ruff e build ficam no grupo de desenvolvimento. O processamento usa os executáveis portáteis, sem depender da biblioteca Python `yt-dlp`.

### Preparar e executar o código-fonte

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
Executáveis, DLLs e `installed.json` são gerados localmente e ignorados pelo Git.

```text
vendor/
├── manifest.json
├── installed.json           # hashes dos executáveis e DLLs preparados
├── yt-dlp/yt-dlp.exe
├── ffmpeg/ffmpeg.exe
├── ffmpeg/ffprobe.exe
├── ffmpeg/*.dll             # bibliotecas compartilhadas declaradas no manifesto
├── repair.exe               # incluído nas distribuições compiladas
├── deno/deno.exe
└── licenses/
```

Na abertura, a verificação roda em segundo plano. A aplicação usa caminhos absolutos
e não procura essas ferramentas no `PATH`. O Deno atende aos desafios JavaScript do
YouTube; o executável oficial do yt-dlp inclui os scripts EJS correspondentes.
[Configuração oficial de EJS](https://github.com/yt-dlp/yt-dlp/wiki/EJS).

Para atualizar, revise versões, URLs e checksums no manifesto, prepare novamente e
rode a integração real. Falha de checksum interrompe a preparação; não desative essa
verificação. A abertura da interface consulta releases, mas não baixa atualizações das ferramentas.

## Arquitetura

```text
main.py / python -m dlpdownloader
└── aplicacao.py                       composição e logging
    ├── ControladorAtualizacoes       consulta de releases em segundo plano
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

A CI Windows valida instalação, qualidade e pacote Python. Em pull requests, execução
manual e tags, um job separado prepara ferramentas, executa testes externos e gera a
distribuição desktop como artefato.

## Compilação

Para desenvolvimento e testes locais, com dependências e ferramentas preparadas:

```powershell
.\.venv\Scripts\python.exe scripts\compilar_beta.py --versao 1.3.1_beta1
```

O nome acima é um exemplo da convenção `<próxima versão>_beta<número>`. O script aceita
nomes livres válidos no Windows e publica em `releases/beta/`, sem relatório de produção
nem integração com o GitHub. Ele reutiliza as validações do pacote de produção.

Para uma distribuição de produção:

```powershell
.\.venv\Scripts\python.exe scripts\compilar.py
.\.venv\Scripts\python.exe scripts\compilar.py --versao 1.3.0 --zip
# Opcional: escolher onde publicar a distribuição local
.\.venv\Scripts\python.exe scripts\compilar.py --destino C:\Pacotes\DLPDownloader
```

O script chama PyInstaller diretamente e não lê um `.spec` do repositório. O `.spec`
intermediário gerado pelo próprio PyInstaller fica no staging temporário e é descartado.
A configuração do aplicativo principal fica em `scripts/compilar.py`: `onedir`, sem console, strip ou UPX.
O processo usa um `PATH` limitado ao Python, Qt e Windows, evitando capturar DLLs
incompatíveis de outros programas instalados na máquina.

```text
releases/
└── DLPDownloader-1.3.0/
    ├── DLPDownloader.exe
    ├── lib/
    ├── vendor/
    └── README.md
```

Após verificar os pré-requisitos, o script solicita a versão no formato `1.3.0`.
A versão é incorporada ao executável e nomeia a pasta de saída; o script não altera
`pyproject.toml`. Ao lado da pasta é gerado um relatório `<pacote>.tamanho.json`, com
tamanhos em bytes e versões do ambiente. `--zip` gera também o arquivo compactado.
Escolha outra versão ou outro destino se já existir uma pasta com o mesmo nome. Compilações simultâneas são bloqueadas e
falhas não publicam pacotes incompletos. A saída inclui diagnóstico se o PyInstaller falhar.

O build já exige um smoke test de inicialização em modo offscreen, com PATH e dados
isolados, antes de publicar a pasta. Esse teste verifica o estado PRONTO e os oito perfis com mídia sintética servida
localmente, incluindo cancelamento e recusa de substituição. Não acessa a internet nem
depende de ferramentas globais.
Para repetir em um pacote existente:

```powershell
.\.venv\Scripts\python.exe scripts\validar_pacote.py releases\DLPDownloader-1.3.0
```

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
| Ferramentas ausentes ou danificadas | Aceite o reparo oferecido ou feche o aplicativo e execute `vendor/repair.exe` |
| Arquivos de `lib` ou reparador ausentes | Extraia novamente o pacote completo |
| Consulta de atualização falhou | Confira a conexão e tente novamente pelo menu Opções |
| Formato de origem pouco comum | A variante menor do FFmpeg pode não reconhecê-lo; tente uma origem compatível |
| Falha de extração | Verifique link, conexão, acesso e compatibilidade do yt-dlp fixado |
| MP4 indisponível | Experimente MKV se atender à necessidade; o perfil não muda sozinho |
| Falha ao gravar | Verifique pasta existente, permissão e espaço livre |
| Arquivo já existe | Escolha **Sim** para substituí-lo ou **Não** para manter o original |
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

Esse projeto existe sob licença MIT. Você pode baixar, usar, modificar, aprimorar e distribuir o código, creditando ao DLP Downloader e seus autores.
