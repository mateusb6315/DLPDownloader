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

Para testes locais, execute `python scripts/compilar_beta.py --versao 1.3.0_beta1`.
O nome é livre, observadas as regras de nomes de arquivos do Windows; a convenção é
`<próxima versão>_beta<número>`. A saída padrão é `releases/beta/`, separada da produção.
O script aceita `--destino` e `--zip`, valida o pacote e não gera relatório nem histórico.
É destinado a desenvolvimento local e não é executado pelo fluxo do GitHub.
