$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$python = Join-Path $root ".venv\\Scripts\\python.exe"
$voiceDir = Join-Path $root "config\\models\\piper"

if (-not (Test-Path $python)) {
    throw "Lokale .venv niet gevonden. Maak eerst de virtuele omgeving aan."
}

New-Item -ItemType Directory -Force -Path $voiceDir | Out-Null

& $python -m piper.download_voices --download-dir $voiceDir nl_NL-ronnie-medium
