# Scripts do projeto

Scripts implementados para desenvolvimento e distribuição. Execute a partir de um
clone com o pacote instalado; cada script possui `--help`.

| Arquivo | Responsabilidade |
| --- | --- |
| `preparar_ambiente.py` | Validar Python e executar `poetry install` |
| `preparar_ferramentas.py` | Obter e verificar yt-dlp, FFmpeg/FFprobe e Deno do manifesto |
| `verificar.py` | Executar lint, testes e verificações de arquitetura |
| `compilar.py` | Publicar distribuição Windows completa, sem `.spec` como entrada |
| `compilar_beta.py` | Compilar pacote local de desenvolvimento sem relatório de produção |
| `compilarfull.py` | Gerar pacote de produção, arquivo 7z e instalador |
| `betafull.py` | Gerar pacote beta com Nuitka, arquivo 7z e instalador local |
| `compilar_repair.py` | Construir o reparador portátil com manifesto incorporado |
| `repair.py` | Reparar as ferramentas do pacote distribuído |
| `validar_pacote.py` | Confirmar inicialização do executável com PATH e dados isolados |
| `git_workflow.py` | Comandos explícitos de status, branch, sincronização, commit, push, PR e merge |

Cada script possui mensagens claras e retorno diferente de zero em falha.
Comandos Git/GitHub devem indicar arquivos e ações explicitamente, interromper em
conflitos e respeitar proteções do repositório.

`comum.py` contém auxiliares compartilhadas. Os testes usam diretórios temporários e
executores falsos; build real e integração de mídia são verificações separadas.
Instalação, exemplos e detalhes estão no [README do projeto](../README.md).

O compilador aceita `--versao X.Y.Z`, `--zip` e `--destino`. Mantém `onedir`, organiza os
arquivos internos em `lib`, seleciona `vendor` pelo manifesto e gera relatório de tamanho.
Valida inicialização e mídia sintética pelo executável congelado. A preparação instala
EXEs/DLLs como conjuntos completos, com rollback e validação em staging antes da troca.

Para testes locais, execute `python scripts/compilar_beta.py --versao 1.3.2_beta1`.
O nome é livre, observadas as regras de nomes de arquivos do Windows; a convenção é
`<próxima versão>_beta<número>`. A saída padrão é `releases/beta/`, separada da produção.
O script aceita `--destino` e `--zip`, valida o pacote e não gera relatório nem histórico.
É destinado a desenvolvimento local e não é executado pelo fluxo do GitHub.

Para criar o 7z e o instalador estáveis, execute
`python scripts/compilarfull.py --versao 1.3.1`. Tanto o fluxo estável quanto o beta
completo aceitam `--destino` e procuram 7-Zip e Inno Setup 7 no PATH ou nos locais
padrão. Os arquivos `.7z` e `-setup.exe` ficam ao lado da pasta; se uma etapa falhar,
os artefatos já publicados são preservados.
O instalador exige administrador, cria atalho no menu Iniciar e oferece atalho na área
de trabalho. Beta e produção têm instalações independentes. A pasta instalada permite
modificação por usuários locais para que o reparador funcione; portanto, outros usuários
locais também podem alterar os executáveis. Atualizações substituem arquivos incluídos,
mas não removem arquivos obsoletos de versões anteriores. Preferências permanecem em
`%LOCALAPPDATA%` e não são removidas pelo desinstalador.

## Beta completa com Nuitka

No Windows x64, tenha UPX no PATH, 7-Zip, Inno Setup 7, as ferramentas de mídia
preparadas e o grupo de desenvolvimento do Poetry instalado. Com MSVC x64 e o SDK
do Windows da carga de trabalho **Desenvolvimento para desktop com C++**, execute:

```powershell
poetry run python scripts/betafull.py --versao 1.3.2-beta2
```

Para usar o Zig, permita que o Nuitka o baixe quando necessário:

```powershell
poetry run python scripts/betafull.py --versao 1.3.2-beta2 --baixar-compilador
```

`--versao` é opcional (`1.3.2-beta2` por padrão). A pasta `releases/beta/DLPDownloader-1.3.2-beta2/`
contém `DLPDownloader.exe`, `vendor/`, `README.md` e os arquivos internos no layout
standalone do Nuitka. Distribua a pasta inteira. O app incorpora `1.3.2 (beta)`;
o nome completo aparece na pasta, no 7z e no instalador. `compilar_beta.py` e
os compiladores de produção continuam com PyInstaller e `lib/`.

Os argumentos do Nuitka ficam em `nuitka_beta.py`; não há `.spec`. O script usa
MSVC por padrão, analisa DLLs localmente com `pefile` e mantém os relatórios XML no staging
temporário. Inclui explicitamente o ícone PNG e a versão gerada. No reparador onefile
só acrescenta o manifesto e o aviso de licenças. Ferramentas e licenças de mídia
continuam externas e verificadas pelo manifesto. O MSVC usa `/O1` para priorizar tamanho,
e o Nuitka descarta as docstrings do aplicativo. O UPX comprime e testa
`DLPDownloader.exe`, `vendor/repair.exe` e as extensões PyQt6 `QtCore`, `QtGui`,
`QtWidgets` e SIP sem assinatura. Extensões incompatíveis, assinadas ou sem ganho de
tamanho são mantidas como recebidas.
Antes de publicar, o script verifica janela com o plugin Windows, ícone, versão,
trabalho fora da thread da interface, mídia local e recursos incorporados do reparador,
sem baixar mídia nem executar reparo.

### Seleção e oportunidades de otimização

| Item | Decisão para a beta |
| --- | --- |
| PyQt6 | O app usa `QtCore`, `QtGui`, `QtWidgets` e SIP. O Nuitka segue os imports; não coleta todo o PyQt6. Mantém os plugins de plataforma (inclusive Windows e offscreen). |
| Imagens, estilos e traduções | O app usa PNG, reconhecido nativamente, e estilo Fusion. Plugins de formatos adicionais, mecanismos de ícone e estilos externos podem ficar de fora. Os textos do app já são em português; traduções do QtWebEngine não são usadas. |
| Rede, mídia e impressão | Sem plugins de TLS, mídia ou impressão do Qt. HTTPS usa `urllib` e TLS do Python; mídia usa `vendor/`. QML, WebEngine, SQL e Designer não são solicitados. |
| Build e testes | `pytest`, `setuptools`, Poetry, Ruff, PyInstaller, Pillow e ferramentas externas de build não são conteúdo de distribuição. Nuitka segue o necessário de cada entrada, e o reparador é compilado sem PyQt6. |

A referência local de produção `1.3.1` (PyInstaller) mede **365,56 MiB** extraídos,
**124,18 MiB** em 7z e **130,45 MiB** no instalador. Cerca de **73%** do pacote
extraído são yt-dlp, Deno e FFmpeg/FFprobe. Os plugins de formatos de imagem,
mecanismos de ícone e estilos somavam **2,08 MiB** nessa referência. Isso indica
onde medir; o tamanho da beta depende do build e da compressão finais.

Após o primeiro build, compare tempo de partida e tamanho de cada EXE, pasta, 7z
e instalador com uma cópia sem UPX. Verifique se a distribuição trouxe `opengl32sw.dll`
(19,68 MiB na referência); qualquer exclusão adicional exige teste em Windows com
driver gráfico limitado. Compare `--lto=auto` com `--lto=no` para medir tempo,
memória e tamanho, antes de alterar o padrão. O Nuitka sinaliza limitações no
suporte a PyQt6; antes de distribuir, teste também download e cancelamento na GUI,
consulta de atualização, seleção de pasta e encerramento com trabalho em andamento.
Use uma instalação beta limpa para medir tamanho; o instalador preserva arquivos
obsoletos deixados por builds anteriores.
