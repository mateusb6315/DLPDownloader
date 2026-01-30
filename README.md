# DLP Downloader

Um downloader de vídeos e áudios simples, leve e intuitivo, construído com Python e interface gráfica moderna.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Flet](https://img.shields.io/badge/Flet-GUI-purple.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

## 📋 Sobre o Projeto

O **DLP Downloader** é uma aplicação desktop que permite baixar vídeos e áudios de diversas plataformas (YouTube, Vimeo, Twitter, e [muitas outras](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md)) com apenas alguns cliques. 

Desenvolvido para usuários que buscam uma alternativa simples e direta aos conversores online cheios de anúncios e limitações.

## ✨ Funcionalidades

| Formato | Descrição |
|---------|-----------|
| **MP4** | Vídeo em alta qualidade (melhor vídeo + melhor áudio disponível) |
| **M4A** | Áudio em alta qualidade (320kbps) - ideal para dispositivos Apple |
| **MP3** | Áudio universal em alta qualidade (320kbps) |

## 🚀 Por que usar o DLP Downloader?

- **Sem anúncios** - Interface limpa e sem distrações
- **Sem limites** - Baixe quantos vídeos quiser
- **Offline** - Funciona sem depender de serviços externos instáveis
- **Rápido** - Downloads diretos sem filas de espera
- **Simples** - Apenas cole o link e escolha o formato

## 📦 Instalação

### Pré-requisitos

- Python 3.8 ou superior
- FFmpeg instalado e configurado no PATH do sistema

### Passo a passo

1. **Clone o repositório**
   ```bash
   git clone https://github.com/seu-usuario/DLPDownloader.git
   cd DLPDownloader
   ```

2. **Crie um ambiente virtual (recomendado)**
   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   # ou
   source .venv/bin/activate  # Linux/Mac
   ```

3. **Instale as dependências**
   ```bash
   pip install flet yt-dlp
   ```

4. **Execute o aplicativo**
   ```bash
   python app.py
   ```

## 📖 Como Usar

### Tutorial Rápido (3 passos)

```
┌─────────────────────────────────────────┐
│           DLP Downloader                │
├─────────────────────────────────────────┤
│                                         │
│  Link: [_________________________]  ◄── 1. Cole o link aqui
│                                         │
│      [MP4]   [M4A]   [MP3]          ◄── 2. Escolha o formato
│                                         │
│                                     ◄── 3. Aguarde o download!
└─────────────────────────────────────────┘
```

1. **Cole o link** do vídeo no campo "Link:"
2. **Clique no formato** desejado (MP4, M4A ou MP3)
3. **Pronto!** O arquivo será salvo na pasta `Downloads` do seu usuário

### Exemplo Prático

```
1. Copie um link do YouTube: https://youtube.com/watch?v=exemplo
2. Cole no campo de texto do DLP Downloader
3. Clique em [MP3] para extrair apenas o áudio
4. Encontre o arquivo em: C:\Users\SeuUsuario\Downloads\
```

## 📁 Estrutura do Projeto

```
DLPDownloader/
├── app.py          # Ponto de entrada e configuração da janela
├── interface.py    # Componentes visuais e handlers de eventos
├── dlp.py          # Lógica de download (wrapper do yt-dlp)
├── .gitignore      # Arquivos ignorados pelo Git
└── README.md       # Este arquivo
```

## 🔧 Arquitetura

O projeto segue uma estrutura modular simples:

```
┌──────────┐     ┌─────────────┐     ┌─────────┐
│  app.py  │────▶│ interface.py│────▶│  dlp.py │
│  (View)  │     │ (Controller)│     │ (Model) │
└──────────┘     └─────────────┘     └─────────┘
                                          │
                                          ▼
                                    ┌──────────┐
                                    │  yt-dlp  │
                                    └──────────┘
```

## ⚠️ Tratamento de Erros

O aplicativo exibe mensagens claras para os erros mais comuns:

| Erro | Causa | Solução |
|------|-------|---------|
| "Link inválido ou ausente" | URL vazia ou formato não reconhecido | Verifique se o link está correto |
| "Falha no download" | Problema de conexão ou vídeo indisponível | Verifique sua internet ou tente outro vídeo |

## 🛠️ Tecnologias Utilizadas

- **[Python](https://python.org)** - Linguagem de programação
- **[Flet](https://flet.dev)** - Framework para interface gráfica
- **[yt-dlp](https://github.com/yt-dlp/yt-dlp)** - Engine de download
- **[FFmpeg](https://ffmpeg.org)** - Conversão e processamento de mídia

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.

## 🤝 Contribuindo

Contribuições são bem-vindas! Sinta-se à vontade para:

1. Fazer um Fork do projeto
2. Criar uma branch para sua feature (`git checkout -b feature/NovaFeature`)
3. Commit suas mudanças (`git commit -m 'Adiciona NovaFeature'`)
4. Push para a branch (`git push origin feature/NovaFeature`)
5. Abrir um Pull Request

---

<p align="center">
  Feito com ❤️ usando Python
</p>
