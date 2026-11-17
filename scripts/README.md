# Scripts do projeto

| Arquivo | Responsabilidade |
| --- | --- |
| `preparar_ambiente.py` | Validar Python e executar `poetry install` |
| `preparar_ferramentas.py` | Obter e verificar yt-dlp, FFmpeg/FFprobe e Deno |
| `verificar.py` | Executar lint, verificação de formatação e a suíte padrão |
| `nuitka.py` | Selecionar o canal de compilação |
| `beta.py` | Gerar a pasta portátil, o 7z e o instalador beta |
| `release.py` | Gerar a pasta portátil, o 7z e o instalador estável, com ZIP opcional |
| `validar_pacote.py` | Validar a inicialização e processar mídia local pelo executável distribuído |
| `git_workflow.py` | Executar operações explícitas de Git e GitHub |

Os scripts devolvem código diferente de zero em caso de falha. Use `--help` nas
entradas de linha de comando. Para preparar o checkout, siga o
[README do projeto](../README.md#preparar-e-executar-o-código-fonte).

## Compilação com Nuitka

Prepare o grupo de desenvolvimento do Poetry e as ferramentas portáteis. Em Windows
x64, instale o MSVC x64 e o SDK do Windows pela carga de trabalho **Desenvolvimento para
desktop com C++**. Instale também 7-Zip e Inno Setup. A busca usa o PATH e os caminhos
padrão de 7-Zip e Inno Setup 7. A beta também exige UPX no PATH.

Execute `poetry run python scripts/nuitka.py` e escolha **1 — Beta** ou **2 — Release**.
As entradas diretas aceitam argumentos para automação:

```powershell
poetry run python scripts/beta.py --versao 1.3.2-beta3
poetry run python scripts/release.py --versao 1.3.2 --zip
```

A beta aceita nomes válidos para arquivos Windows. Uma beta com base `X.Y.Z`
incorpora essa versão para a consulta de atualizações. Outros nomes usam a versão
de `pyproject.toml`. A release exige `X.Y.Z` e usa o canal estável.
Omitir `--versao` abre a pergunta interativa do canal. O build não edita
`pyproject.toml`.

O destino padrão é `releases/beta/` para beta e `releases/` para release.
`--destino` escolhe outra pasta e `--baixar-compilador` permite usar Zig
com download pelo Nuitka. A CI chama `release.py` com versão explícita e
`--zip` para publicar o ZIP como artefato.

### Pacote e validação

O build usa Nuitka standalone para a aplicação e onefile para o reparador.
Na beta, o UPX comprime os dois executáveis gerados e tenta reduzir as extensões
elegíveis do PyQt6. Extensões assinadas, incompatíveis ou sem ganho de tamanho
são preservadas. O compilador usa `main.py`, inclui o ícone PNG de `ui/resources`
e os plugins Qt de plataforma. O reparador incorpora o manifesto de ferramentas
e o aviso de licenças.

O staging verifica a versão, o ícone, a inicialização com o plugin Qt Windows
e o estado PRONTO em dados isolados. Depois, o executável processa os oito
perfis de mídia sintética em localhost. O reparador valida seus recursos
incorporados com `--verificar-empacotamento`.

A pasta portátil, o 7z e o instalador são publicados como conjunto após validação.
O ZIP da release entra no mesmo conjunto quando solicitado. Os nomes incluem a
versão informada. O script preserva artefatos já existentes. Distribua a pasta
portátil inteira para manter os arquivos Qt, as licenças e o `vendor`.

### Instaladores

O instalador exige administrador, cria atalho no menu Iniciar e oferece atalho na
área de trabalho. Beta e release têm identidades e pastas independentes. O instalador
estável reaproveita a pasta registrada pela instalação anterior. Ambos permitem escrita
por usuários locais na pasta instalada para o reparador. Atualizações substituem
arquivos incluídos e deixam os arquivos obsoletos na pasta. O desinstalador preserva
as preferências em `%LOCALAPPDATA%`.
