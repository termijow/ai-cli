# ==============================================================================
# AI-CLI WINDOWS INSTALLER & CONFIGURATION SCRIPT
# Hardware: AMD Radeon RX 6600 (Vulkan Acceleration)
# ==============================================================================

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "        ASISTENTE DE INSTALACION AI-CLI PARA WINDOWS            " -ForegroundColor Cyan
Write-Host "        Soporte GPU Nativo: AMD Radeon RX 6600 (Vulkan)         " -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""

$ProjectRoot = $PSScriptRoot
$BinDir = Join-Path $ProjectRoot "bin"
$LlamaBinDir = Join-Path $ProjectRoot "llama-bin"

# 1. Comprobar e instalar herramientas vía winget si faltan
Write-Host "[1/5] Verificando dependencias base (jq, fzf, sqlite3)..." -ForegroundColor Yellow

function Install-WingetPkg {
    param(
        [string]$PackageId,
        [string]$CmdName
    )
    if (-not (Get-Command $CmdName -ErrorAction SilentlyContinue)) {
        Write-Host "  -> Instalando $PackageId..." -ForegroundColor Gray
        try {
            winget install --id $PackageId -e --source winget --accept-source-agreements --accept-package-agreements | Out-Null
        } catch {
            Write-Host "  Aviso al instalar $PackageId, verificando..." -ForegroundColor DarkYellow
        }
    } else {
        Write-Host "  * $CmdName disponible." -ForegroundColor Green
    }
}

Install-WingetPkg -PackageId "jqlang.jq" -CmdName "jq"
Install-WingetPkg -PackageId "junegunn.fzf" -CmdName "fzf"
Install-WingetPkg -PackageId "SQLite.SQLite" -CmdName "sqlite3"

# 2. Verificar o desplegar llama.cpp con Vulkan
Write-Host ""
Write-Host "[2/5] Verificando motor de inferencia llama.cpp con aceleracion Vulkan..." -ForegroundColor Yellow

$LlamaServerExe = Join-Path $LlamaBinDir "llama-server.exe"
if (-not (Test-Path $LlamaServerExe)) {
    $UserLlama = "$HOME\llama.cpp\llama-server.exe"
    if (Test-Path $UserLlama) {
        Write-Host "  * Binarios encontrados en $HOME\llama.cpp, copiando a $LlamaBinDir..." -ForegroundColor Green
        New-Item -ItemType Directory -Force -Path $LlamaBinDir | Out-Null
        Copy-Item -Path "$HOME\llama.cpp\*" -Destination $LlamaBinDir -Recurse -Force
    } else {
        Write-Host "  -> Descargando runtime Vulkan precompilado de llama.cpp..." -ForegroundColor Gray
        New-Item -ItemType Directory -Force -Path $LlamaBinDir | Out-Null
        $VulkanZip = "$env:TEMP\llama-vulkan.zip"
        $VulkanUrl = "https://github.com/ggml-org/llama.cpp/releases/download/b11552/llama-b11552-bin-win-vulkan-x64.zip"
        Invoke-WebRequest -Uri $VulkanUrl -OutFile $VulkanZip
        Expand-Archive -Path $VulkanZip -DestinationPath $LlamaBinDir -Force
        Remove-Item -Path $VulkanZip -Force -ErrorAction SilentlyContinue
    }
}

if (Test-Path $LlamaServerExe) {
    Write-Host "  * llama-server.exe verificado." -ForegroundColor Green
    Write-Host "  * Consultando soporte GPU..." -ForegroundColor Gray
    & $LlamaServerExe --list-devices | Out-String | Write-Host -ForegroundColor DarkCyan
} else {
    Write-Warning "No se pudo preparar llama-server.exe automaticamente."
}

# 3. Configurar Python y librería requests
Write-Host ""
Write-Host "[3/5] Verificando entorno Python..." -ForegroundColor Yellow
$PyExe = (Get-Command python.exe -ErrorAction SilentlyContinue).Source
if (-not $PyExe -or $PyExe -like "*WindowsApps*") {
    $LocalPy = "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe"
    if (Test-Path $LocalPy) {
        $PyExe = $LocalPy
    }
}

if ($PyExe) {
    Write-Host "  * Python detectado: $PyExe" -ForegroundColor Green
    & $PyExe -m pip install requests --quiet --disable-pip-version-check
    Write-Host "  * Paquete requests disponible." -ForegroundColor Green
} else {
    Write-Warning "Python no esta disponible en PATH. Asegurate de tener Python 3.10+ instalado."
}

# 4. Configurar archivo .env
Write-Host ""
Write-Host "[4/5] Configurando archivo .env para aceleracion Vulkan..." -ForegroundColor Yellow
$EnvPath = Join-Path $ProjectRoot ".env"

$CleanLlamaPath = $LlamaServerExe.Replace('\', '/')
$EnvLines = @(
    "# AI-CLI Server Configuration (Windows Vulkan / AMD RX 6600)",
    "MODEL_REPO=unsloth/Qwen3.5-0.8B-GGUF",
    "MODEL_FILE=Qwen3.5-0.8B-Q4_K_M.gguf",
    "PORT=1234",
    "",
    "LLAMA_PATH=$CleanLlamaPath",
    "",
    "AI_API_URL=http://localhost:1234/v1/chat/completions",
    "AI_BACKUP_DIR=.ai_backups",
    "AI_VERBOSE=false",
    "",
    "# --- TUNING: AMD Radeon RX 6600 (GPU Dedicated Offload) ---",
    "AI_HARDWARE_MODE=VULKAN",
    "AI_GPU_LAYERS=99",
    "AI_CTX_SIZE=16384",
    "AI_THREADS=6",
    "AI_REASONING=off",
    "AI_THINKING_LEVEL=off",
    "AI_BATCH_SIZE=2048",
    "AI_UBATCH_SIZE=512",
    "AI_CACHE_TYPE_K=f16",
    "AI_CACHE_TYPE_V=f16",
    "AI_MAX_TOKENS=16384"
)

$Utf8NoBom = [System.Text.UTF8Encoding]::new($false)
[System.IO.File]::WriteAllLines($EnvPath, $EnvLines, $Utf8NoBom)
Write-Host "  * Archivo .env guardado." -ForegroundColor Green

# 5. Agregar bin al PATH de Usuario
Write-Host ""
Write-Host "[5/5] Configurando PATH de Windows..." -ForegroundColor Yellow
$UserPath = [Environment]::GetEnvironmentVariable("Path", "User")
$GitCmd = "$env:LOCALAPPDATA\Programs\Git\cmd"
$GitUsr = "$env:LOCALAPPDATA\Programs\Git\usr\bin"
$PyPath = "$env:LOCALAPPDATA\Programs\Python\Python312"
$PyScripts = "$env:LOCALAPPDATA\Programs\Python\Python312\Scripts"

$PathsToAdd = @($BinDir, $GitCmd, $GitUsr, $PyPath, $PyScripts)
$NewUserPath = $UserPath

foreach ($p in $PathsToAdd) {
    if (Test-Path $p) {
        if ($NewUserPath -notlike "*$p*") {
            $NewUserPath = "$p;$NewUserPath"
            Write-Host "  + Agregado a PATH: $p" -ForegroundColor Gray
        }
    }
}

if ($NewUserPath -ne $UserPath) {
    [Environment]::SetEnvironmentVariable("Path", $NewUserPath, "User")
    $env:Path = "$NewUserPath;$env:Path"
    Write-Host "  * Variable de entorno PATH actualizada." -ForegroundColor Green
} else {
    Write-Host "  * Rutas ya registradas en PATH." -ForegroundColor Green
}

Write-Host ""
Write-Host "================================================================" -ForegroundColor Green
Write-Host "       AI-CLI ESTA LISTO PARA USARSE EN WINDOWS!                " -ForegroundColor Green
Write-Host "================================================================" -ForegroundColor Green
Write-Host "Comandos disponibles desde cualquier terminal (PowerShell / CMD):" -ForegroundColor White
Write-Host "  * ai                 - Abre el menu interactivo o asiste con codigo" -ForegroundColor Cyan
Write-Host "  * ai-menu            - Dashboard interactivo TUI" -ForegroundColor Cyan
Write-Host "  * ai-models          - Seleccionar o descargar modelos GGUF" -ForegroundColor Cyan
Write-Host "  * ai-serve           - Iniciar servidor llama.cpp con aceleracion Vulkan" -ForegroundColor Cyan
Write-Host "  * ai-help            - Manual interactivo y ayuda" -ForegroundColor Cyan
Write-Host ""
