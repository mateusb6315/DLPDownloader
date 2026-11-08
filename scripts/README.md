# Scripts do projeto

Scripts implementados para desenvolvimento e distribuição. Execute a partir de um
clone com o pacote instalado; cada script possui `--help`.

| Arquivo | Responsabilidade |
| --- | --- |
| `preparar_ambiente.py` | Validar Python e executar `poetry install` |
| `preparar_ferramentas.py` | Obter e verificar yt-dlp, FFmpeg/FFprobe e Deno do manifesto |
| `verificar.py` | Executar lint, testes e verificações de arquitetura |
| `compilar.py` | Publicar distribuição Windows completa, sem `.spec` como entrada |
| `validar_pacote.py` | Confirmar inicialização do executável com PATH e dados isolados |
| `git_workflow.py` | Comandos explícitos de status, branch, sincronização, commit, push, PR e merge |

Cada script possui mensagens claras e retorno diferente de zero em falha.
Comandos Git/GitHub devem indicar arquivos e ações explicitamente, interromper em
conflitos e respeitar proteções do repositório.

`comum.py` contém auxiliares compartilhadas. Os testes usam diretórios temporários e
executores falsos; build real e integração de mídia são verificações separadas.
Instalação, exemplos e detalhes estão no [README do projeto](../README.md).
