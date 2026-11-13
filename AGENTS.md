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

A versão atual indicada em `pyproject.toml` e `MEMORY.md` é **1.3.0**; o projeto saiu
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
  localmente. Executáveis, DLLs e `installed.json` são ignorados pelo Git.

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
em PRs, execução manual e tags também prepara ferramentas e publica o pacote desktop
como artefato, após testes externos.

`scripts/compilar.py` chama PyInstaller diretamente em modo `onedir`, sem arquivo `.spec`
do repositório. Após verificar pré-requisitos, solicita uma versão de três componentes
numéricos, como `1.2.0`, repetindo a pergunta até obter formato válido. Publica em
`releases/DLPDownloader-<versão>/` ou no `--destino` informado, executando antes um smoke
test. Não mantém histórico próprio de versões nem substitui intencionalmente uma pasta
de release existente. Distribua a pasta inteira. A versão digitada nomeia o pacote e é incorporada ao executável; não altera
automaticamente a versão em `pyproject.toml`.

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

## Distribuição otimizada

FFmpeg/FFprobe usam build Windows x64 LGPL compartilhada fixada no manifesto, com sete
DLLs junto dos executáveis. A preparação valida o staging e troca diretórios gerenciados
com backup; falhas de recuperação preservam `.recuperacao-*`. Todos os binários declarados
são verificados por SHA-256, com leitura cancelável. Deno permanece como runtime JavaScript.
O PyInstaller usa `--contents-directory lib`; `vendor` permanece externo. O build copia
somente binários declarados, metadados e licenças, testa mídia local no executável congelado
e gera relatório `<pacote>.tamanho.json`. Aceita `--versao X.Y.Z` e `--zip` opcionais.
Não aplica cortes de bibliotecas Qt, otimização de bytecode, UPX ou strip.

`scripts/compilar_beta.py` reutiliza a configuração e a validação do build de produção,
mas gera pacotes de desenvolvimento local em `releases/beta/`, sem relatório ou histórico.
Aceita nome livre válido para arquivo Windows; a convenção é `1.3.0_beta1`. Não integra
o fluxo do GitHub. Os metadados de integridade de `vendor` continuam necessários ao app.
Ao implementar planos, corrigir problemas ou realizar testes locais que exijam uma
distribuição compilada, use `scripts/compilar_beta.py` por padrão. Use `scripts/compilar.py`
para distribuição de produção ou quando a tarefa exigir explicitamente validar o próprio
compilador ou processo de produção. Instruções explícitas do usuário têm prioridade.

Os compiladores incluem `vendor/repair.exe`, programa de console portátil com manifesto
e aviso de licenças incorporados. Ele exige o aplicativo fechado, baixa novamente todas as
ferramentas declaradas, verifica hashes, restaura manifesto e metadados e troca os conjuntos
sem confirmação. A instalação usa staging com recuperação em falhas. Um bloqueio
compartilhado impede novas instâncias do app durante o reparo; a verificação de processos
também detecta versões antigas do executável. O reparador não substitui a si próprio.
Se a verificação das ferramentas falhar, a interface oferece iniciar o reparo ou informa
como fazê-lo manualmente. Ao aceitar, a janela fecha e `repair.exe` abre em console separado,
aguardando o encerramento do processo antes de verificar e reparar. Em terminal interativo,
o reparador aguarda qualquer tecla ao final, inclusive quando ocorrer erro.

O menu Opções permite consultar releases estáveis; a consulta automática e a manual usam
`servicos/updates.py` em thread de trabalho, sem bloquear downloads ou o fechamento seguro.
As distribuições incorporam a versão base ao executável, sem arquivo `version.json`; nomes
beta numéricos usam essa versão base e outros nomes usam a versão de `pyproject.toml`. Uma
release estável da mesma versão é oferecida para builds beta. O smoke test não acessa a rede.

`scripts/betafull.py` e `scripts/compilarfull.py` reutilizam os compiladores existentes e
geram também 7z e instalador Inno Setup 6, exigindo ambas as ferramentas instaladas.
Os instaladores beta e estável têm identidades e pastas separadas, exigem administrador
e permitem escrita por usuários locais na pasta instalada para o reparador. Atualizações
não removem arquivos obsoletos. Os artefatos já publicados são preservados em falhas.

A interface realça controles sob o cursor e campos com foco. As seleções animam o realce
da borda e o botão Baixar anima sua pintura sem alterar a área de clique; o menu Opções
mantém uma margem direita proporcional à largura da janela.
