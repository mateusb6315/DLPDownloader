param (
    [Parameter(Mandatory)] [string] $Versao,
    [Parameter(Mandatory)] [string] $Pacote
)

$ErrorActionPreference = 'Stop'
if ($env:RUNNER_ENVIRONMENT -ne 'github-hosted' -or $env:RUNNER_OS -ne 'Windows') {
    throw 'Este teste requer uma VM Windows descartavel hospedada pelo GitHub.'
}
if ($Versao -notmatch '^[0-9]+\.[0-9]+\.[0-9]+$' -or [version]$Versao -le [version]'1.3.1') {
    throw 'Informe uma versao X.Y.Z posterior a 1.3.1.'
}

$portable = (Resolve-Path -LiteralPath $Pacote).Path
$candidate = (Resolve-Path -LiteralPath "$portable-setup.exe").Path
$root = Join-Path $env:RUNNER_TEMP 'dlp-upgrade'
$app = Join-Path $root 'DLP Installed'
$data = Join-Path $root 'localappdata'
$destination = Join-Path $root 'saved downloads'
$evidence = Join-Path $env:RUNNER_TEMP 'dlp-upgrade-evidencias'
$config = Join-Path $data 'DLPDownloader\config.json'
New-Item -ItemType Directory -Path $root, $destination, $evidence, (Split-Path -Parent $config) |
    Out-Null
$hashes = Join-Path $evidence 'sha256.txt'
"Run $env:GITHUB_RUN_ID, commit $env:GITHUB_SHA" |
    Set-Content -LiteralPath (Join-Path $evidence 'execucao.txt')

function Invoke-Setup($setup, $label, $installationDirectory) {
    $log = Join-Path $evidence "$label-inno.log"
    $arguments = @('/VERYSILENT', '/SUPPRESSMSGBOXES', '/SP-', '/NORESTART',
        '/RESTARTEXITCODE=3010', '/NORESTARTAPPLICATIONS', ('/LOG="{0}"' -f $log))
    if ($installationDirectory) {
        $arguments += '/DIR="{0}"' -f $installationDirectory
    }
    $process = Start-Process -FilePath $setup -ArgumentList $arguments -WindowStyle Hidden -PassThru
    if (-not $process.WaitForExit(180000)) {
        taskkill /PID $process.Id /T /F
        throw "Setup $label excedeu o prazo."
    }
    if ($process.ExitCode -ne 0) { throw "Setup $label retornou $($process.ExitCode)." }
}

function Assert-Installation($expectedVersion) {
    $entry = Get-ItemProperty -LiteralPath $stableKey
    $stableEntries = @(Get-ItemProperty -Path "$uninstall\*", "$uninstall32\*" -ErrorAction SilentlyContinue |
        Where-Object DisplayName -match '^DLP Downloader(?: [0-9]+\.[0-9]+\.[0-9]+)?$')
    if ($stableEntries.Count -ne 1 -or $entry.DisplayVersion -ne $expectedVersion -or
        $entry.InstallLocation.TrimEnd('\') -ne $app -or $betaKeys.Where({ Test-Path -LiteralPath $_ })) {
        throw "Identidade ou pasta inesperada para $expectedVersion."
    }
    if (-not (Test-Path -LiteralPath $link -PathType Leaf)) { throw 'Atalho ausente.' }
    $shell = New-Object -ComObject WScript.Shell
    $target = $shell.CreateShortcut($link).TargetPath
    if ($target -ne (Join-Path $app 'DLPDownloader.exe')) { throw "Destino inesperado $target." }
    $entry | Select-Object DisplayName, DisplayVersion, InstallLocation, UninstallString |
        ConvertTo-Json | Set-Content -LiteralPath (Join-Path $evidence "$expectedVersion-registro.json")
    $target | Set-Content -LiteralPath (Join-Path $evidence "$expectedVersion-atalho.txt")
    return $entry.UninstallString
}

function Invoke-Smoke($label, $expectedVersion) {
    $record = Join-Path $evidence $label
    New-Item -ItemType Directory -Path $record | Out-Null
    $applicationLog = Join-Path $data 'DLPDownloader\aplicacao.log'
    $media = Join-Path $data 'midia'
    $result = Join-Path $media 'resultado.json'
    $stderr = Join-Path $data 'inicializacao.stderr'
    try {
        @'
import sys
from pathlib import Path

from scripts.validar_pacote import validar_pacote
from services._models.atualizacoes import VersaoDistribuicao

pacote, dados, versao = sys.argv[1:]
validar_pacote(Path(pacote), Path(dados), plataforma="windows", versao=VersaoDistribuicao(versao, False))
'@ | python -m poetry run python - $app $data $expectedVersion
        if ($LASTEXITCODE -ne 0) { throw "Smoke $label falhou." }
        if ((Get-Content -Raw -LiteralPath $result | ConvertFrom-Json).sucesso -ne $true) {
            throw "Midia local falhou no smoke $label."
        }
    } finally {
        foreach ($file in $applicationLog, $stderr, $media) {
            if (Test-Path -LiteralPath $file) { Move-Item -LiteralPath $file -Destination $record }
        }
    }
}

function Assert-SavedDestination($label) {
    $existingLocalAppData = $env:LOCALAPPDATA
    $env:LOCALAPPDATA = $data
    $env:DLP_SMOKE_TEST = '1'
    $env:QT_QPA_PLATFORM = 'windows'
    $process = $null
    try {
        $process = Start-Process -FilePath (Join-Path $app 'DLPDownloader.exe') -WorkingDirectory $data -PassThru
        $byPid = New-Object Windows.Automation.PropertyCondition (
            [Windows.Automation.AutomationElement]::ProcessIdProperty, $process.Id)
        $byEdit = New-Object Windows.Automation.PropertyCondition (
            [Windows.Automation.AutomationElement]::ControlTypeProperty,
            [Windows.Automation.ControlType]::Edit)
        $desktop = [Windows.Automation.AutomationElement]::RootElement
        $timeout = [Diagnostics.Stopwatch]::StartNew()
        do {
            $window = $desktop.FindFirst([Windows.Automation.TreeScope]::Children, $byPid)
            if ($window) {
                foreach ($field in $window.FindAll([Windows.Automation.TreeScope]::Descendants, $byEdit)) {
                    $pattern = $null
                    if ($field.TryGetCurrentPattern([Windows.Automation.ValuePattern]::Pattern, [ref]$pattern) -and
                        $pattern.Current.Value -eq $destination) {
                        $pattern.Current.Value | Set-Content -LiteralPath (Join-Path $evidence "$label-destino.txt")
                        return
                    }
                }
            }
            Start-Sleep -Milliseconds 250
        } while ($timeout.Elapsed.TotalSeconds -lt 45 -and -not $process.HasExited)
        throw "Destino salvo ausente na janela $label."
    } finally {
        if ($process -and -not $process.HasExited) {
            Stop-Process -Id $process.Id -Force
            $process.WaitForExit()
        }
        $env:LOCALAPPDATA = $existingLocalAppData
        $env:DLP_SMOKE_TEST = $null
        $env:QT_QPA_PLATFORM = $null
    }
}

$uninstall = 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall'
$uninstall32 = 'HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall'
$stableKey = Join-Path $uninstall '{330DC7E6-C8B5-44AA-A38A-14D2DF57B4E1}_is1'
$betaId = '{2AFCE230-A591-4A7F-9829-10D3CFE58D03}_is1'
$betaKeys = @((Join-Path $uninstall $betaId), (Join-Path $uninstall32 $betaId))
$link = Join-Path ([Environment]::GetFolderPath('CommonPrograms')) 'DLP Downloader\DLP Downloader.lnk'
if (Test-Path -LiteralPath $stableKey) { throw 'A VM ja tem uma instalacao estavel.' }

$legacy = Join-Path $root 'DLPDownloader-1.3.1-setup.exe'
$uri = 'https://github.com/mateusb6315/DLPDownloader/releases/download/1.3.1/DLPDownloader-1.3.1-setup.exe'
Invoke-WebRequest -Uri $uri -OutFile $legacy -UseBasicParsing
$legacyHash = (Get-FileHash -LiteralPath $legacy).Hash
"Setup 1.3.1: $legacyHash" | Set-Content -LiteralPath $hashes
if ($legacyHash -ne '3DA6574723DA74F34C9AFB0D1996E3EC2F8ADB8377D9D5BB47DCA9022EC04B2E') {
    throw 'O setup 1.3.1 diverge do artefato de referencia.'
}

Invoke-Setup $legacy 'pyinstaller' $app
$uninstallBefore = Assert-Installation '1.3.1'
$preferences = @{ versao = 1; diretorio = $destination } | ConvertTo-Json
[IO.File]::WriteAllText($config, $preferences)
$preferenceHash = (Get-FileHash -LiteralPath $config).Hash
"Preferencia antes: $preferenceHash" | Add-Content -LiteralPath $hashes
Invoke-Smoke 'pyinstaller' '1.3.1'
if ((Get-FileHash -LiteralPath $config).Hash -ne $preferenceHash) {
    throw 'Preferencia anterior mudou no smoke.'
}

Invoke-Setup $candidate 'nuitka'
if ((Assert-Installation $Versao) -ne $uninstallBefore) {
    throw 'O upgrade divergiu do desinstalador registrado pela 1.3.1.'
}
foreach ($relative in 'DLPDownloader.exe', 'vendor\repair.exe') {
    $installedHash = (Get-FileHash -LiteralPath (Join-Path $app $relative)).Hash
    $portableHash = (Get-FileHash -LiteralPath (Join-Path $portable $relative)).Hash
    "$relative instalado=$installedHash portatil=$portableHash" | Add-Content -LiteralPath $hashes
    if ($installedHash -ne $portableHash) { throw "Binario instalado difere do portatil $relative." }
}
Invoke-Smoke 'nuitka' $Versao
Add-Type -AssemblyName UIAutomationClient, UIAutomationTypes
Assert-SavedDestination 'nuitka'
$preferenceAfter = (Get-FileHash -LiteralPath $config).Hash
"Preferencia depois: $preferenceAfter" | Add-Content -LiteralPath $hashes
if ($preferenceAfter -ne $preferenceHash) { throw 'Preferencia mudou apos o upgrade.' }

$repair = Join-Path $app 'vendor\repair.exe'
@'
import os
import subprocess
import sys
from pathlib import Path

repair, data, record = sys.argv[1:]
result = subprocess.run(
    [repair, "--verificar-empacotamento"],
    cwd=data,
    env={**os.environ, "LOCALAPPDATA": data},
    stdin=subprocess.DEVNULL,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    timeout=60,
    creationflags=subprocess.CREATE_NO_WINDOW,
)
Path(record).write_bytes(result.stdout + f"\nExit code: {result.returncode}\n".encode())
sys.exit(result.returncode)
'@ | python - $repair $data (Join-Path $evidence 'reparador.txt')
if ($LASTEXITCODE -ne 0) { throw 'A verificacao do reparador falhou.' }
