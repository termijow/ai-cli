$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$BashCandidates = @(
    "$env:LOCALAPPDATA\Programs\Git\bin\bash.exe",
    "C:\Program Files\Git\bin\bash.exe"
)
$BashExe = $BashCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1

if (-not $BashExe) {
    $BashExe = (Get-Command bash.exe -ErrorAction SilentlyContinue).Source
}

if (-not $BashExe) {
    Write-Error "No se encontro Git Bash en el sistema."
    exit 1
}

& $BashExe "$ScriptDir\ai-menu" @args
