# Memória do projeto

- A versão atual do DLP Downloader, configurada em `pyproject.toml`, é **1.3.1**.
  O projeto saiu da fase beta; as notas estão em `changelog/1.3.1.md`.
- O repositório está em `C:\Projetos\Projeto Golden Apple`; DLP Downloader continua
  sendo o nome do aplicativo.
- A interface possui realces de cursor e foco, transição nas bordas das seleções e
  animação do botão Baixar. O menu Opções tem margem direita proporcional à janela.
- Os scripts `betafull.py` e `compilarfull.py` geram também 7z e instalador. A busca
  automática do Inno Setup usa `ISCC` no PATH ou caminhos padrão do Inno Setup 7;
  os instaladores beta e de produção têm identidades e pastas separadas.
- Mensagens de commits/releases devem explicar a mudança em palavras que façam sentido
  para quem usa o aplicativo, evitando descrições internas ou técnicas demais. Exemplo:
  `1.0.0: reformulação na interface e arquitetura`.
- Para testes locais de distribuições, use `scripts/compilar_beta.py`; o compilador de
  produção é destinado a releases e testes explícitos do processo de produção.
- As notas de versão devem seguir a formatação mais recente do projeto e ser compreensíveis
  para usuários; a verificação de atualizações e o reparo são recursos do aplicativo.
