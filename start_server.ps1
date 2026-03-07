param(
    [switch]$Reload = $true
)

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$venvPython = Join-Path $root ".venv\\Scripts\\python.exe"
$python = if (Test-Path $venvPython) { $venvPython } else { "python" }
$arguments = @("-m", "uvicorn", "server.app.main:app", "--host", "127.0.0.1", "--port", "8000")
if ($Reload) {
    $arguments += "--reload"
}

& $python @arguments
