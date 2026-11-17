# DLP Downloader

Aplicativo desktop para baixar um vídeo ou áudio por vez, escolher o formato de saída
e salvar em uma pasta de sua preferência. A versão **1.3.1** é destinada a
**Windows de 64 bits** e inclui as ferramentas necessárias para funcionar.

## Novidades recentes

- Pacote menor: a pasta do aplicativo passou de aproximadamente **530 MB para 360 MB**,
  uma redução de cerca de **170 MB (32%)**. O arquivo compactado para download tem cerca
  de **133 MB**. Esses valores são os registrados nas [notas da versão](changelog/1.3.0.md)
  e podem variar entre compilações; reserve espaço também para extração e downloads.
- Reparo das ferramentas: se arquivos necessários estiverem ausentes ou alterados,
  o aplicativo oferece abrir o reparador em um terminal.
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
Para mover o aplicativo, mova a pasta extraída inteira, incluindo `vendor` e os
arquivos internos. A versão 1.3.1 disponível nas releases organiza esses arquivos
na pasta `lib`. A conexão com a internet é necessária para baixar conteúdo,
consultar atualizações e reparar ferramentas.

```text
DLPDownloader-1.3.1/
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

O reparo cobre as ferramentas de `vendor`. Se arquivos internos, o aplicativo ou
o próprio `repair.exe` estiverem ausentes ou corrompidos, extraia novamente o
pacote completo. Se o reparo falhar, leia a mensagem
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

PyQt6 é a dependência de execução Python. Nuitka e as ferramentas de verificação
ficam no grupo de desenvolvimento. O processamento usa os executáveis portáteis,
sem depender da biblioteca Python `yt-dlp`.

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
Após instalar, também pode executar `.\.venv\Scripts\python.exe main.py` ou abrir
`.venv\Scripts\dlpdownloader.exe`.

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

### Executar a partir do pacote Python

Execute `poetry build` no checkout para gerar o wheel e o sdist. Em um ambiente
virtual separado, instale o wheel com `python -m pip install <caminho-do-wheel>`.
O wheel inclui a interface e seu ícone. Copie a pasta `vendor` preparada para
`Lib/site-packages/vendor` do ambiente, ao lado dos pacotes `config`, `services`
e `ui`. Você pode localizar essa pasta com
`python -c "import sysconfig; print(sysconfig.get_path('purelib'))"` usando o Python
do mesmo ambiente.

Com as ferramentas no lugar, execute `python -m dlpdownloader` ou abra
`Scripts/dlpdownloader.exe` no ambiente virtual. Os dois funcionam de qualquer
diretório de trabalho.

## Arquitetura

| Caminho | Responsabilidade |
| --- | --- |
| `main.py`, `dlpdownloader.py` e `config/bootstrap.py` | Entradas e composição da aplicação, resolução de recursos e configuração de logs |
| `config/controller.py` | Coordenação da interface, dos serviços injetados e das tarefas em segundo plano |
| `config/preferences.py` | Preferência de diretório |
| `ui/` | Janela, diálogos, controles, textos e ícone |
| `services/downloader.py` | Coordenação, staging e publicação do download |
| `services/yt_dlp.py` e `services/ffmpeg.py` | Adaptadores de mídia independentes |
| `services/updater.py`, `services/repair.py` e `services/repair_console.py` | Consulta de releases, reparo e entrada do reparador |
| `services/_models/` e `services/_infra/` | Contratos puros e infraestrutura compartilhada |
| `tests/` | Regras, serviços, interface, scripts e integrações |
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
.\.venv\Scripts\python.exe -m pytest tests\test_controller.py -v
```

`verificar.py` executa Ruff, conferência de formatação e
`pytest -m "not externo and not interface_windows"`.

Os testes da janela em primeiro plano exigem uma sessão interativa do Windows
e as ferramentas portáteis instaladas em `vendor`. Execute em um PowerShell separado:

```powershell
$env:QT_QPA_PLATFORM = "windows"
.\.venv\Scripts\python.exe -m pytest -q -m interface_windows
```
Os testes focados do mediador usam Qt offscreen na suíte padrão.

Depois de preparar `vendor/`, execute a integração real:

```powershell
.\.venv\Scripts\python.exe -m pytest -q -m externo
```

Ela gera mídia sintética com FFmpeg, serve somente em `127.0.0.1`, executa yt-dlp e
verifica streams com FFprobe. Não baixa conteúdo do YouTube. Ambientes que bloqueiam
sockets locais precisam permitir esse tráfego para executar esses testes.

A CI Windows valida instalação, qualidade e pacote Python. Em pull requests, execução
manual e tags, um job separado prepara ferramentas, executa testes externos e gera a
distribuição desktop com Nuitka e publica o ZIP como artefato.

## Compilação

Com as ferramentas portáteis preparadas, execute `poetry run python scripts/nuitka.py`
e escolha **1 — Beta** ou **2 — Release**. Os dois canais geram a pasta portátil,
o arquivo 7z e o instalador. Para executar os canais diretamente:

```powershell
poetry run python scripts/beta.py --versao 1.3.2-beta3
poetry run python scripts/release.py --versao 1.3.2 --zip
```

A pasta portátil reúne `DLPDownloader.exe`, os arquivos de execução do Nuitka e do Qt
e o diretório `vendor` com os binários de mídia e o reparador. Distribua a pasta inteira.
Consulte os pré-requisitos, destinos e validações no [catálogo de scripts](scripts/README.md#compilação-com-nuitka).

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
| Arquivos internos ou reparador ausentes | Extraia novamente o pacote completo |
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
