# Orientações para agentes

## Manutenção deste arquivo

Leia este arquivo e confira o código relevante antes de alterar o projeto. Atualize o
`AGENTS.md` na mesma tarefa quando houver mudanças relevantes de arquitetura, comportamento,
dependências, comandos, compilação, testes ou convenções. Registre fatos verificáveis e evite
informações temporárias. Instruções explícitas do usuário têm prioridade sobre este arquivo.

## Panorama

O DLP Downloader é um aplicativo desktop Windows x86-64, em português, para baixar um
vídeo ou áudio por operação. A interface usa PyQt6; o processamento usa executáveis
portáteis de yt-dlp, FFmpeg/FFprobe e Deno. Preserve a arquitetura MVC e a organização em
módulos pequenos, legíveis e com responsabilidade principal clara, acessíveis também a
colaboradores iniciantes.

A versão atual indicada em `pyproject.toml` e `MEMORY.md` é **1.1.0**; o projeto saiu
da fase beta. Consulte esses arquivos e o código antes de assumir a versão em tarefas
futuras. Mensagens de commit, releases e changelogs devem ser compreensíveis para o
usuário comum, dando preferência aos efeitos percebidos por quem usa o aplicativo.
As notas de versão ficam em `changelog/<versão>.md`; use as existentes como referência.

## Estrutura e limites

- `main.py` e `src/dlpdownloader/__main__.py`: pontos de entrada; `aplicacao.py` compõe
  dependências e configura a aplicação.
- `src/dlpdownloader/modelos/`: dados, estados, validações, perfis e progresso; mantenha
  regras puras e independentes de Qt e de I/O.
- `src/dlpdownloader/servicos/`: execução dos programas portáteis, arquivos,
  preferências, processos e verificação de dependências.
- `src/dlpdownloader/controladores/`: coordenação da interface, estados e trabalho em
  segundo plano; `visoes/` concentra widgets, diálogos, sinais e apresentação.
- `src/dlpdownloader/config/`: caminhos, perfis e textos de interface. Os recursos da
  interface incluem `src/dlpdownloader/recursos/flet.png`; `flet.png` na raiz é usado na
  compilação. O nome do ícone não indica dependência do framework Flet.
- `tests/`: testes de modelos, serviços, interface, scripts e integração; `scripts/`:
  preparação, verificação, compilação e operações Git. Consulte `scripts/README.md`.
- `vendor/`: manifesto com versões, origens e hashes, licenças e ferramentas preparadas
  localmente. Executáveis e `installed.json` são ignorados pelo Git.

Mantenha a View independente de modelos, serviços e controladores; injete dependências
no controlador. Operações demoradas rodam em `QThread` por meio de `Trabalhador` e
sinais; atualizações de widgets pertencem à thread da interface. Preserve o cancelamento,
as transições de estado e o encerramento seguro dos processos.

## Comportamento a preservar

- Uma operação por vez, sem playlists. Vídeo MP4/MKV usa seleção dinâmica de faixas;
  não fixe IDs de formato do YouTube. Áudio original, MP3, M4A/AAC, Opus, FLAC e WAV
  estão disponíveis, com bitrate nas opções aplicáveis.
- O destino escolhido persiste em `%LOCALAPPDATA%/DLPDownloader/config.json`; logs com
  rotação ficam no mesmo diretório. Não registre saída bruta do yt-dlp, que pode conter
  links assinados ou dados sensíveis.
- O progresso deriva dos eventos do yt-dlp, por faixa; quando não há total conhecido
  ou durante o processamento, use indicação indeterminada, sem simular porcentagem.
- O arquivo é processado em pasta temporária no destino e publicado ao concluir. Se já
  existir, peça confirmação antes de substituir; recusar preserva o original. Preserve
  limpeza de temporários e segurança em erro ou cancelamento.
- Os processos usam argumentos separados, sem shell, e ferramentas portáteis por caminho
  explícito. Não desative a verificação de integridade de `vendor/manifest.json`.

## Ambiente, verificações e distribuição

Python suportado: 3.13 ou 3.14, com Poetry 2.x. Em PowerShell, com a `.venv` preparada:

```powershell
.\.venv\Scripts\python.exe scripts\preparar_ambiente.py
.\.venv\Scripts\python.exe scripts\preparar_ferramentas.py
.\.venv\Scripts\python.exe -m dlpdownloader
.\.venv\Scripts\python.exe scripts\verificar.py
.\.venv\Scripts\python.exe -m pytest tests\test_interface_controlador.py -v
```

`verificar.py` executa Ruff, verificação de formatação e testes sem o marcador `externo`.
Escolha verificações proporcionais à alteração; acrescente testes de regressão relevantes
em `tests/`. Para alterações de comandos de mídia ou codecs, considere também
`.\.venv\Scripts\python.exe -m pytest -q -m externo`: exige ferramentas preparadas e
pode exigir sockets locais. A CI Windows executa as verificações padrão e build Python;
em tags também prepara ferramentas e publica o pacote desktop como artefato.

`scripts/compilar.py` chama PyInstaller diretamente em modo `onedir`, sem arquivo `.spec`
do repositório. Após verificar pré-requisitos, solicita uma versão de três componentes
numéricos, como `1.2.0`, repetindo a pergunta até obter formato válido. Publica em
`releases/DLPDownloader-<versão>/` ou no `--destino` informado, executando antes um smoke
test. Não mantém histórico próprio de versões nem substitui intencionalmente uma pasta
de release existente. Distribua a pasta inteira. A versão digitada nomeia o pacote e não
altera automaticamente a versão em `pyproject.toml`.

## Git e documentação

Confira `git status` antes de editar e preserve mudanças existentes do usuário. A branch
local de trabalho pode ser `codex/main`; não presuma que ela corresponda à `main` local
ou remota. `git push origin codex/main` publica uma branch remota de mesmo nome;
`git push origin codex/main:main` direciona a branch local à `main` remota. Faça commit,
merge, push ou operações destrutivas apenas conforme as instruções aplicáveis do usuário.
`scripts/git_workflow.py` fornece comandos explícitos para tarefas Git/GitHub.

Atualize documentação afetada ao mudar o comportamento. `docs/` é ignorada pelo Git e
não deve conter a única cópia de documentação necessária ao projeto. Confira o código
ao atualizar a documentação. Não presuma que a licença
do código do aplicativo exista; preserve as licenças de terceiros em `vendor/licenses/`.
