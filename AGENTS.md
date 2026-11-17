# Orientações para agentes

Leia este arquivo e confira o código relevante antes de editar. Confira `git status`
e preserve as alterações já existentes. Atualize as orientações afetadas na mesma tarefa
quando mudarem arquitetura, comportamento, dependências, compilação, testes ou convenções.
Registre fatos verificáveis. Instruções explícitas do usuário têm prioridade.

## Arquitetura

O DLP Downloader é um aplicativo desktop Windows x86-64 em português. Ele usa PyQt6,
Python 3.13 ou 3.14 e executáveis portáteis de yt-dlp, FFmpeg/FFprobe e Deno. A versão
declarada fica em `pyproject.toml`. Preserve o MVC e módulos pequenos com responsabilidade
clara, acessíveis também a colaboradores iniciantes.

- `main.py`, `dlpdownloader.py` e a entrada gráfica do pacote chamam `config/bootstrap.py:main`.
  A composição monta e injeta as operações. `criar_aplicacao` recebe uma `QApplication`
  e pode receber a raiz de ferramentas, a pasta de dados e o destino padrão.
- `ui/` contém widgets, diálogos, tema, sinais e textos. Mantenha a View independente
  de serviços, modelos e mediador. O ícone único é `ui/resources/flet.png`. Seu nome
  vem do histórico do projeto.
- `config/controller.py` coordena estados, preferências e trabalho em `QThread` com
  `Trabalhador` e sinais. Apenas a thread da interface atualiza widgets. A consulta de
  releases em `config/update_tasks.py` tem trabalhador próprio, funciona durante o
  download e aguarda o fim do download e dos diálogos modais para apresentar a oferta
  automática. O fechamento espera as tarefas ativas, inclusive `QThread.finished`.
- `services/downloader.py` recebe pedido imutável, evento de cancelamento e callbacks
  de progresso e confirmação. Os adaptadores `services/yt_dlp.py` e `services/ffmpeg.py`
  são independentes. Use FFmpeg diretamente nos pedidos com bitrate explícito.
  Contratos puros ficam em `services/_models`. Processos, arquivos, instalação e
  verificação ficam em `services/_infra`. Mantenha toda a camada `services` sem Qt.
- `vendor/` reúne o manifesto e as licenças de terceiros. O Git ignora executáveis,
  DLLs e `installed.json`. O checkout e a wheel buscam `vendor` ao lado de `config`,
  `services` e `ui`. A distribuição standalone busca `vendor` ao lado do executável.

## Comportamento a preservar

- Uma operação por vez, sem playlists. MP4/MKV usam seleção dinâmica de faixas.
  Preserve áudio original, MP3, M4A/AAC, Opus, FLAC e WAV e os bitrates aplicáveis.
- O progresso vem dos eventos por faixa. Total desconhecido ou processamento usam
  indicação indeterminada. Preserve a área de clique, as animações, o foco e o
  redimensionamento quando alterar controles em `ui/controles_animados.py`.
- Processe em pasta temporária no destino e publique somente ao concluir. Confirme
  antes de substituir um arquivo. Recusa, erro e cancelamento preservam originais
  e limpam temporários.
- Preserve o destino salvo em `%LOCALAPPDATA%/DLPDownloader/config.json` e a rotação
  dos logs no mesmo diretório. A saída bruta do yt-dlp pode conter links assinados.
  Registre mensagens de erro tratadas.
- Execute ferramentas por caminho explícito, com argumentos separados e sem shell.
  Preserve verificação por SHA-256, cancelamento da árvore de processos e licenças.
  A preparação valida o staging, mantém backup na troca e conserva `.recuperacao-*`
  quando a restauração falha.
- O menu Opções consulta releases estáveis pelo GitHub. Uma beta recebe oferta da
  estável de mesma versão base. Consulte `config/version.py` para versão incorporada
  e compatibilidade com metadados de versões antigas.
- O bootstrap mantém `uso.lock` compartilhado durante a sessão. Ao aceitar o reparo,
  a janela encerra as tarefas e o bootstrap libera o bloqueio antes de iniciar
  `vendor/repair.exe` em console separado, com o PID do aplicativo. O reparador
  aguarda o PID, detecta instâncias antigas, obtém bloqueio exclusivo, baixa e valida
  os conjuntos e restaura ferramentas, manifesto e metadados. Em terminal interativo,
  aguarda uma tecla ao final.

## Verificações

Use Python x64 e Poetry 2.x. Com a `.venv` preparada, execute no PowerShell:

```powershell
.\.venv\Scripts\python.exe scripts\preparar_ambiente.py
.\.venv\Scripts\python.exe scripts\preparar_ferramentas.py
.\.venv\Scripts\python.exe -m dlpdownloader
.\.venv\Scripts\python.exe scripts\verificar.py
```

`verificar.py` executa Ruff, verificação de formatação e testes com Qt offscreen,
excluindo `externo` e `interface_windows`. Acrescente testes de regressão relevantes.
Use os testes focados do mediador, da consulta e do reparador para simular falhas
e encerramento. Quando mudar comandos de mídia, codecs ou protocolo, rode
`python -m pytest -q -m externo` com as ferramentas preparadas. Para alterar janela
ou mediador, rode também `python -m pytest -q -m interface_windows` em sessão interativa,
com `QT_QPA_PLATFORM=windows`. Os testes reais preservam as preferências pessoais e
podem exigir acesso a sockets locais.

## Compilação e distribuição

Consulte [scripts/README.md](scripts/README.md#compilação-com-nuitka) para compilar.
Use `scripts/beta.py` quando testes locais exigirem distribuição compilada.
Use `scripts/release.py` para o canal estável, para a CI e para validar o fluxo de produção.
O seletor `scripts/nuitka.py` também oferece ambos. Em PRs, execução manual e tags, a
CI Windows prepara as ferramentas, executa testes externos e publica o ZIP da release.

O Nuitka compila `main.py` em standalone e `services/repair_console.py` em onefile.
A invocação ocorre no staging para evitar importar o seletor
`scripts/nuitka.py` como compilador. Preserve `__compiled__.containing_dir` no
reparador e mantenha o manifesto e o aviso de licenças incorporados. A beta usa UPX
nos executáveis gerados e nas extensões elegíveis do PyQt6. Preserve binários assinados
e a seleção explícita dos plugins Qt.

Antes de publicar os artefatos, confirme o ícone, o estado PRONTO e a versão com
plugin Windows, PATH restrito e dados isolados. O smoke desativa consulta de releases
e usa `--verificar-midia <dados>` para validar oito perfis de mídia em localhost.
`vendor/repair.exe --verificar-empacotamento` valida os recursos incorporados.
Preserve identidades distintas para instaladores beta e estável e o AppId e a pasta
da release instalada. Preferências ficam fora da pasta da instalação.

## Git e documentação

Confirme qual é a branch de trabalho e o destino antes de operações Git.
`git push origin codex/main` atualiza a remota `codex/main`.
`git push origin codex/main:main` direciona a branch local à remota `main`.
Faça commit, merge, push ou operações destrutivas conforme as instruções do usuário.
`scripts/git_workflow.py` oferece comandos explícitos para tarefas Git/GitHub.

Atualize a documentação afetada. `docs/` é ignorada pelo Git. Mantenha registros
necessários ao projeto em arquivos versionados. Redija mensagens de commit, releases
e changelogs com foco no efeito percebido pelo usuário. Use as notas existentes em
`changelog/<versão>.md` como referência. Preserve as licenças de terceiros em
`vendor/licenses/`.
