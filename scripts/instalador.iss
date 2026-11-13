; Compilado com ISCC. Caminhos e versão são fornecidos pelo coordenador.
#define Beta GetEnv("DLP_BETA") == "1"
#if Beta
#define NomeAplicativo "DLP Downloader Beta"
#else
#define NomeAplicativo "DLP Downloader"
#endif
[Setup]
#if Beta
AppId={{2AFCE230-A591-4A7F-9829-10D3CFE58D03}
AppName={#NomeAplicativo}
DefaultDirName={autopf64}\DLP Downloader Beta
DefaultGroupName=DLP Downloader Beta
#else
AppId={{330DC7E6-C8B5-44AA-A38A-14D2DF57B4E1}
AppName={#NomeAplicativo}
DefaultDirName={autopf64}\DLP Downloader
DefaultGroupName=DLP Downloader
#endif
AppVersion={#GetEnv("DLP_VERSAO")}
AppPublisher=mateusb6315
AppPublisherURL=https://github.com/mateusb6315/DLPDownloader
AppSupportURL=https://github.com/mateusb6315/DLPDownloader
AppUpdatesURL=https://github.com/mateusb6315/DLPDownloader
PrivilegesRequired=admin
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir={#GetEnv("DLP_SAIDA")}
OutputBaseFilename=instalador
Compression=lzma2
SolidCompression=yes
UninstallDisplayIcon={app}\DLPDownloader.exe

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Dirs]
Name: "{app}"; Permissions: users-modify

[Files]
Source: "{#GetEnv('DLP_PACOTE')}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#NomeAplicativo}"; Filename: "{app}\DLPDownloader.exe"
Name: "{autodesktop}\{#NomeAplicativo}"; Filename: "{app}\DLPDownloader.exe"; Tasks: desktopicon
