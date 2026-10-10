# ==============================================================================
# AI-CLI WINDOWS INSTALLER & CONFIGURATION SCRIPT
# Hardware: NVIDIA CUDA / AMD Radeon (Vulkan) / Intel / CPU
# ==============================================================================

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "        ASISTENTE DE INSTALACION AI-CLI PARA WINDOWS            " -ForegroundColor Cyan
Write-Host "   Soporte Multi-GPU: NVIDIA CUDA / AMD Radeon / Intel / CPU    " -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""

$ProjectRoot = $PSScriptRoot
$BinDir = Join-Path $ProjectRoot "bin"
$LlamaBinDir = Join-Path $ProjectRoot "llama-bin"

# 1. Configurar directiva de ejecución de scripts para el usuario actual
Write-Host "[1/6] Configurando directiva de ejecucion de PowerShell..." -ForegroundColor Yellow
try {
    Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned -Force -ErrorAction SilentlyContinue
    Write-Host "  * ExecutionPolicy RemoteSigned configurada." -ForegroundColor Green
} catch {
    Write-Host "  * ExecutionPolicy verificada." -ForegroundColor Green
}

# 2. Comprobar e instalar herramientas vía winget si faltan
Write-Host ""
Write-Host "[2/6] Verificando dependencias base (jq, fzf, sqlite3)..." -ForegroundColor Yellow

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

# 3. Detección de Hardware y Selección Interactiva de GPU
Write-Host ""
Write-Host "[3/6] Deteccion y seleccion de aceleracion de hardware..." -ForegroundColor Yellow

$DetectedGpus = @()
$HasNvidia = $false
$HasAmd = $false
$HasIntel = $false

try {
    $VideoControllers = Get-CimInstance Win32_VideoController -ErrorAction SilentlyContinue
    foreach ($vc in $VideoControllers) {
        if ($vc.Name) {
            $DetectedGpus += $vc.Name
            if ($vc.Name -match "NVIDIA|GeForce|RTX|GTX|Quadro|Tesla") { $HasNvidia = $true }
            if ($vc.Name -match "AMD|Radeon") { $HasAmd = $true }
            if ($vc.Name -match "Intel") { $HasIntel = $true }
        }
    }
} catch {}

if (Get-Command nvidia-smi -ErrorAction SilentlyContinue) {
    $HasNvidia = $true
}

$DefaultOption = "4"
if ($HasNvidia) {
    $DefaultOption = "1"
} elseif ($HasAmd) {
    $DefaultOption = "2"
} elseif ($HasIntel) {
    $DefaultOption = "3"
}

if ($DetectedGpus.Count -gt 0) {
    Write-Host "  GPUs detectadas en tu equipo:" -ForegroundColor White
    foreach ($g in $DetectedGpus) {
        Write-Host "    * $g" -ForegroundColor Green
    }
} else {
    Write-Host "  No se pudieron identificar adaptadores graficos dedicados especificos." -ForegroundColor Gray
}

Write-Host ""
Write-Host "  ¿Que aceleracion deseas configurar para la inferencia?" -ForegroundColor White
Write-Host "    1) NVIDIA CUDA (GeForce RTX / GTX / Quadro / Tesla) $(if ($HasNvidia) { '[Recomendado]' })" -ForegroundColor $(if ($HasNvidia) { 'Green' } else { 'White' })
Write-Host "    2) AMD Radeon (Vulkan / RDNA / GCN)                 $(if ($HasAmd) { '[Recomendado]' })" -ForegroundColor $(if ($HasAmd) { 'Green' } else { 'White' })
Write-Host "    3) Intel Arc / Iris Xe (Vulkan)                     $(if ($HasIntel) { '[Recomendado]' })" -ForegroundColor $(if ($HasIntel) { 'Green' } else { 'White' })
Write-Host "    4) Solo CPU (Sin aceleracion de GPU)" -ForegroundColor Yellow
Write-Host ""

$SelectedOption = $DefaultOption
if ([Environment]::UserInteractive -and -not [Console]::IsInputRedirected) {
    try {
        $rawInput = Read-Host "  Elige una opcion [1-4] (Presiona Enter para [$DefaultOption])"
        if ($rawInput -and $rawInput.Trim()) {
            $SelectedOption = $rawInput.Trim()
        }
    } catch {}
} else {
    Write-Host "  Modo no interactivo detectado, usando opcion sugerida: $DefaultOption" -ForegroundColor Gray
}

$HwMode = "CPU"
$HwDisplayName = "Solo CPU"
$RequiresCuda = $false
$LlamaReleaseBase = "https://github.com/ggml-org/llama.cpp/releases/download/b11552"

switch ($SelectedOption) {
    "1" {
        $HwMode = "CUDA"
        $HwDisplayName = "NVIDIA CUDA"
        $RequiresCuda = $true
    }
    "2" {
        $HwMode = "VULKAN"
        $HwDisplayName = "AMD Radeon (Vulkan)"
    }
    "3" {
        $HwMode = "INTEL"
        $HwDisplayName = "Intel Arc / Iris (Vulkan)"
    }
    default {
        $HwMode = "CPU"
        $HwDisplayName = "Solo CPU"
    }
}

Write-Host "  -> Motor seleccionado: $HwDisplayName" -ForegroundColor Green

# 4. Descargar y desplegar runtime llama.cpp para el hardware elegido
Write-Host ""
Write-Host "[4/6] Desplegando runtime llama.cpp ($HwDisplayName)..." -ForegroundColor Yellow

New-Item -ItemType Directory -Force -Path $LlamaBinDir | Out-Null
$HwStampFile = Join-Path $LlamaBinDir ".hw_mode"
$CurrentInstalledMode = if (Test-Path $HwStampFile) { (Get-Content -Raw $HwStampFile).Trim() } else { "" }
$LlamaServerExe = Join-Path $LlamaBinDir "llama-server.exe"

# Si cambió el modo de hardware o no existe el ejecutable, descargar binarios correspondientes
if ((-not (Test-Path $LlamaServerExe)) -or ($CurrentInstalledMode -ne $HwMode)) {
    Write-Host "  * Preparando binarios limpios para $HwDisplayName en $LlamaBinDir..." -ForegroundColor Gray
    Get-ChildItem -Path $LlamaBinDir -Exclude "*.gguf", "models" -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

    $TempDir = [System.IO.Path]::GetTempPath()

    if ($HwMode -eq "CUDA") {
        Write-Host "  -> Descargando runtime NVIDIA CUDA (b11552)..." -ForegroundColor Cyan
        $CudaZip = Join-Path $TempDir "llama-cuda.zip"
        $CudaUrl = "$LlamaReleaseBase/llama-b11552-bin-win-cuda-12.4-x64.zip"
        curl.exe -L -o $CudaZip $CudaUrl
        tar.exe -xf $CudaZip -C $LlamaBinDir
        Remove-Item -Path $CudaZip -Force -ErrorAction SilentlyContinue

        Write-Host "  -> Descargando librerias de runtime CUDA (cuBLAS DLLs para Windows)..." -ForegroundColor Cyan
        $CudartZip = Join-Path $TempDir "cudart-cuda.zip"
        $CudartUrl = "$LlamaReleaseBase/cudart-llama-bin-win-cuda-12.4-x64.zip"
        curl.exe -L -o $CudartZip $CudartUrl
        tar.exe -xf $CudartZip -C $LlamaBinDir
        Remove-Item -Path $CudartZip -Force -ErrorAction SilentlyContinue
    } elseif ($HwMode -eq "VULKAN" -or $HwMode -eq "INTEL") {
        Write-Host "  -> Descargando runtime Vulkan (b11552)..." -ForegroundColor Cyan
        $VkZip = Join-Path $TempDir "llama-vulkan.zip"
        $VkUrl = "$LlamaReleaseBase/llama-b11552-bin-win-vulkan-x64.zip"
        curl.exe -L -o $VkZip $VkUrl
        tar.exe -xf $VkZip -C $LlamaBinDir
        Remove-Item -Path $VkZip -Force -ErrorAction SilentlyContinue
    } else {
        Write-Host "  -> Descargando runtime CPU (b11552)..." -ForegroundColor Cyan
        $CpuZip = Join-Path $TempDir "llama-cpu.zip"
        $CpuUrl = "$LlamaReleaseBase/llama-b11552-bin-win-cpu-x64.zip"
        curl.exe -L -o $CpuZip $CpuUrl
        tar.exe -xf $CpuZip -C $LlamaBinDir
        Remove-Item -Path $CpuZip -Force -ErrorAction SilentlyContinue
    }

    Set-Content -Path $HwStampFile -Value $HwMode -NoNewline
    Get-ChildItem -Path $LlamaBinDir | Unblock-File -ErrorAction SilentlyContinue
    Write-Host "  * Binarios instalados correctamente." -ForegroundColor Green
} else {
    Write-Host "  * Runtime $HwDisplayName ya instalado y listo." -ForegroundColor Green
}

if (Test-Path $LlamaServerExe) {
    Write-Host "  * Consultando dispositivos reconocidos:" -ForegroundColor Gray
    try {
        & $LlamaServerExe --list-devices | Out-String | Write-Host -ForegroundColor DarkCyan
    } catch {}
} else {
    Write-Warning "No se encontro llama-server.exe despues del despliegue."
}

# 5. Configurar Python y librería requests
Write-Host ""
Write-Host "[5/6] Verificando entorno Python..." -ForegroundColor Yellow
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

# 6. Configurar archivo .env
Write-Host ""
Write-Host "[6/6] Configurando archivo .env para $HwDisplayName..." -ForegroundColor Yellow
$EnvPath = Join-Path $ProjectRoot ".env"

$CleanLlamaPath = $LlamaServerExe.Replace('\', '/')

# Leer configuraciones previas si existen para no sobreescribir el modelo activo del usuario
$ExistingModelRepo = "local/gemma-4-E4B-it-Q4_K_M.gguf"
$ExistingModelFile = "gemma-4-E4B-it-Q4_K_M.gguf"
$ExistingPort = "1234"

if (Test-Path $EnvPath) {
    $currentEnv = Get-Content $EnvPath
    foreach ($line in $currentEnv) {
        if ($line -match "^MODEL_REPO=(.*)$") { $ExistingModelRepo = $matches[1] }
        if ($line -match "^MODEL_FILE=(.*)$") { $ExistingModelFile = $matches[1] }
        if ($line -match "^PORT=(.*)$") { $ExistingPort = $matches[1] }
    }
}

$EnvLines = @(
    "# AI-CLI Server Configuration (Hardware: $HwMode)",
    "MODEL_REPO=$ExistingModelRepo",
    "MODEL_FILE=$ExistingModelFile",
    "PORT=$ExistingPort",
    "",
    "LLAMA_PATH=$CleanLlamaPath",
    "",
    "AI_API_URL=http://localhost:$ExistingPort/v1/chat/completions",
    "AI_BACKUP_DIR=.ai_backups",
    "AI_VERBOSE=false",
    "",
    "# --- TUNING DE HARDWARE: $HwDisplayName ---",
    "AI_HARDWARE_MODE=$HwMode",
    "AI_GPU_LAYERS=$(if ($HwMode -eq 'CPU') { '0' } else { '99' })",
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
Write-Host "  * Archivo .env guardado con aceleracion $HwMode." -ForegroundColor Green

# 7. Agregar bin al PATH de Usuario
Write-Host ""
Write-Host "Configurando PATH de Windows..." -ForegroundColor Yellow
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
Write-Host "       Aceleracion Activa: $HwDisplayName                       " -ForegroundColor Green
Write-Host "================================================================" -ForegroundColor Green
Write-Host "Comandos disponibles desde cualquier terminal (PowerShell / CMD):" -ForegroundColor White
Write-Host "  * ai                 - Asistente de codigo y chat" -ForegroundColor Cyan
Write-Host "  * ai models          - Seleccionar o descargar modelos GGUF" -ForegroundColor Cyan
Write-Host "  * ai serve           - Iniciar servidor llama.cpp con aceleracion $HwDisplayName" -ForegroundColor Cyan
Write-Host "  * ai menu            - Dashboard interactivo TUI" -ForegroundColor Cyan
Write-Host "  * ai help            - Manual interactivo y ayuda" -ForegroundColor Cyan
Write-Host ""
