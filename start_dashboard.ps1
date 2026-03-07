$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Push-Location (Join-Path $root "dashboard")

try {
    npm run dev -- --host 127.0.0.1 --port 5173
}
finally {
    Pop-Location
}
