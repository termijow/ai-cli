# Script de descarga secuencial en segundo plano (0% GPU)
$ErrorActionPreference = "Continue"

$ProjectRoot = Resolve-Path "$PSScriptRoot\.."
$ModelsDir = Join-Path $ProjectRoot "models"

$tasks = @(
    @{
        Url = "https://huggingface.co/unsloth/gemma-4-E4B-it-GGUF/resolve/main/gemma-4-E4B-it-UD-Q8_K_XL.gguf"
        Dest = Join-Path $ModelsDir "gemma-4-E4B-it-GGUF\gemma-4-E4B-it-UD-Q8_K_XL.gguf"
        Name = "Gemma 4 E4B UD-Q8_K_XL (8.11 GB)"
    },
    @{
        Url = "https://huggingface.co/bartowski/Ling-3.0-tiny-GGUF/resolve/main/Ling-3.0-tiny-Q8_0.gguf"
        Dest = Join-Path $ModelsDir "Ling-3.0-tiny-GGUF\Ling-3.0-tiny-Q8_0.gguf"
        Name = "Ling 3.0 Tiny Q8_0 (7.83 GB)"
    }
)

foreach ($t in $tasks) {
    $parent = Split-Path $t.Dest
    if (-not (Test-Path $parent)) { New-Item -ItemType Directory -Path $parent -Force | Out-Null }

    Write-Host "`n>>> [DESCARGANDO]: $($t.Name)..."
    & curl.exe -L -C - "$($t.Url)" -o "$($t.Dest)"
    Write-Host ">>> [COMPLETADO]: $($t.Name) guardado en $($t.Dest)`n"
}
