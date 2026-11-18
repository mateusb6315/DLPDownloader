# Memória do projeto

- A versão declarada é **1.3.1**, conforme `pyproject.toml`. As notas das versões
  publicadas ficam em `changelog/`.
- A execução direta, o módulo Python e a entrada gráfica da wheel convergem em
  `config.bootstrap:main`. A wheel instala o PNG em `ui/resources` e usa a pasta
  `vendor` com as ferramentas preparadas ao lado de `config`, `services` e `ui`.
- Nuitka é o compilador da aplicação standalone e do reparador onefile. O seletor
  `scripts/nuitka.py` oferece Beta e Release. Ambos geram pasta portátil, 7z e instalador.
  A release oferece ZIP para a CI. O UPX é restrito à beta.
- Os instaladores beta e estável têm identidades e pastas distintas. A release Nuitka
  preserva o AppId estável e reaproveita a pasta da versão instalada. O teste de upgrade
  da 1.3.1 confirmou preferência de destino, inicialização, mídia e lançamento do
  reparador. [Evidência de validação](https://github.com/mateusb6315/DLPDownloader/actions/runs/44195134824)
- Para testes locais com distribuição compilada, use `scripts/beta.py`. O fluxo de
  produção e seus testes usam `scripts/release.py`. Os comandos estão no
  [catálogo de scripts](scripts/README.md).
