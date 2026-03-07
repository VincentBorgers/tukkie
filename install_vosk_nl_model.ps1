$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$modelsDir = Join-Path $root "config\\models"
$zipPath = Join-Path $modelsDir "vosk-model-small-nl-0.22.zip"
$extractDir = Join-Path $modelsDir "vosk-model-small-nl-0.22"
$downloadUrl = "https://alphacephei.com/vosk/models/vosk-model-small-nl-0.22.zip"

New-Item -ItemType Directory -Force -Path $modelsDir | Out-Null

if (Test-Path $extractDir) {
    Write-Host "Vosk-model bestaat al op $extractDir"
    exit 0
}

Write-Host "Download Nederlands Vosk-model..."
Invoke-WebRequest -Uri $downloadUrl -OutFile $zipPath

Write-Host "Pak model uit..."
Expand-Archive -Path $zipPath -DestinationPath $modelsDir -Force

Write-Host "Klaar: $extractDir"
