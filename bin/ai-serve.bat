@echo off
setlocal enabledelayedexpansion

set "SCRIPT_DIR=%~dp0"
for %%I in ("%~dp0..") do set "PROJECT_ROOT=%%~fI"

rem 1. Cargar variables desde .env si existe
if exist "%PROJECT_ROOT%\.env" (
    for /f "usebackq tokens=1,* delims==" %%A in ("%PROJECT_ROOT%\.env") do (
        set "line=%%A"
        if not "!line:~0,1!"=="#" (
            if not "%%B"=="" set "%%A=%%B"
        )
    )
)

rem 2. Buscar Git Bash
set "BASH_EXE="
if exist "%LOCALAPPDATA%\Programs\Git\bin\bash.exe" set "BASH_EXE=%LOCALAPPDATA%\Programs\Git\bin\bash.exe"
if not defined BASH_EXE if exist "%LOCALAPPDATA%\Programs\Git\usr\bin\bash.exe" set "BASH_EXE=%LOCALAPPDATA%\Programs\Git\usr\bin\bash.exe"
if not defined BASH_EXE if exist "C:\Program Files\Git\bin\bash.exe" set "BASH_EXE=C:\Program Files\Git\bin\bash.exe"
if not defined BASH_EXE if exist "C:\Program Files\Git\usr\bin\bash.exe" set "BASH_EXE=C:\Program Files\Git\usr\bin\bash.exe"
if not defined BASH_EXE for %%X in (bash.exe) do (set "BASH_EXE=%%~$PATH:X")

rem Si hay Git Bash y no se fuerza modo nativo, ejecutar el script bash ai-serve
if defined BASH_EXE if /i not "%~1"=="--native" (
    set "CLEAN_SCRIPT_DIR=%SCRIPT_DIR:\=/%"
    "%BASH_EXE%" "!CLEAN_SCRIPT_DIR!ai-serve" %*
    exit /b !ERRORLEVEL!
)

rem 3. Ejecución Nativa en Windows (cuando no hay bash o se ejecuta con --native)
echo [AI-SERVE] Iniciando servidor llama-server en modo nativo de Windows...

rem Localizar llama-server.exe
set "LLAMA_SERVER="
if defined LLAMA_PATH if exist "%LLAMA_PATH%" set "LLAMA_SERVER=%LLAMA_PATH%"
if not defined LLAMA_SERVER if exist "%PROJECT_ROOT%\llama-bin\llama-server.exe" set "LLAMA_SERVER=%PROJECT_ROOT%\llama-bin\llama-server.exe"
if not defined LLAMA_SERVER if exist "%USERPROFILE%\llama.cpp\llama-server.exe" set "LLAMA_SERVER=%USERPROFILE%\llama.cpp\llama-server.exe"
if not defined LLAMA_SERVER for %%X in (llama-server.exe) do (set "LLAMA_SERVER=%%~$PATH:X")

if not defined LLAMA_SERVER (
    echo [ERROR] No se encontro llama-server.exe en el sistema.
    exit /b 1
)

rem Localizar modelo
set "MODEL_PATH="
if defined MODEL_FILE (
    if exist "%MODEL_FILE%" set "MODEL_PATH=%MODEL_FILE%"
    if not defined MODEL_PATH if exist "%PROJECT_ROOT%\models\%MODEL_FILE%" set "MODEL_PATH=%PROJECT_ROOT%\models\%MODEL_FILE%"
    if not defined MODEL_PATH (
        for /d %%D in ("%PROJECT_ROOT%\models\*") do (
            if not defined MODEL_PATH if exist "%%D\%MODEL_FILE%" set "MODEL_PATH=%%D\%MODEL_FILE%"
        )
    )
    if not defined MODEL_PATH if exist "%USERPROFILE%\models\%MODEL_FILE%" set "MODEL_PATH=%USERPROFILE%\models\%MODEL_FILE%"
)

if not defined MODEL_PATH (
    echo [ERROR] No se encontro el archivo del modelo %MODEL_FILE%
    exit /b 1
)

rem Valores por defecto de configuración
if not defined PORT set "PORT=1234"
if not defined AI_GPU_LAYERS set "AI_GPU_LAYERS=99"
if not defined AI_CTX_SIZE set "AI_CTX_SIZE=8192"
if not defined AI_BATCH_SIZE set "AI_BATCH_SIZE=1024"
if not defined AI_UBATCH_SIZE set "AI_UBATCH_SIZE=256"
if not defined AI_CACHE_TYPE_K set "AI_CACHE_TYPE_K=q4_0"
if not defined AI_CACHE_TYPE_V set "AI_CACHE_TYPE_V=q4_0"
if not defined AI_THREADS set "AI_THREADS=6"
if not defined AI_MAX_TOKENS set "AI_MAX_TOKENS=8192"
if not defined AI_REASONING set "AI_REASONING=off"

rem Extra flags
set "EXTRA_FLAGS=--jinja --flash-attn auto --parallel 1 --cache-ram 4096 --context-shift --alias localmodel --predict !AI_MAX_TOKENS! --reasoning !AI_REASONING!"

rem Fit Memory Management
if defined AI_FIT (
    set "EXTRA_FLAGS=!EXTRA_FLAGS! --fit !AI_FIT!"
)

rem Speculative Decoding / MTP
if defined AI_SPEC_TYPE (
    if not "!AI_SPEC_TYPE!"=="none" (
        set "EXTRA_FLAGS=!EXTRA_FLAGS! --spec-type !AI_SPEC_TYPE!"
        if defined AI_SPEC_DRAFT_N_MAX (
            set "EXTRA_FLAGS=!EXTRA_FLAGS! --spec-draft-n-max !AI_SPEC_DRAFT_N_MAX!"
        ) else (
            set "EXTRA_FLAGS=!EXTRA_FLAGS! --spec-draft-n-max 3"
        )
        if defined AI_MODEL_DRAFT (
            set "DRAFT_PATH="
            if exist "%AI_MODEL_DRAFT%" set "DRAFT_PATH=%AI_MODEL_DRAFT%"
            if not defined DRAFT_PATH if exist "%PROJECT_ROOT%\models\%AI_MODEL_DRAFT%" set "DRAFT_PATH=%PROJECT_ROOT%\models\%AI_MODEL_DRAFT%"
            if not defined DRAFT_PATH (
                for /d %%D in ("%PROJECT_ROOT%\models\*") do (
                    if not defined DRAFT_PATH if exist "%%D\%AI_MODEL_DRAFT%" set "DRAFT_PATH=%%D\%AI_MODEL_DRAFT%"
                )
            )
            if not defined DRAFT_PATH if exist "%USERPROFILE%\models\%AI_MODEL_DRAFT%" set "DRAFT_PATH=%USERPROFILE%\models\%AI_MODEL_DRAFT%"
            if not defined DRAFT_PATH set "DRAFT_PATH=%AI_MODEL_DRAFT%"
            set "EXTRA_FLAGS=!EXTRA_FLAGS! --model-draft "!DRAFT_PATH!""
        )
    )
)

rem Vision / Multimodal Projector
if defined AI_MMPROJ (
    set "MMPROJ_PATH="
    if exist "%AI_MMPROJ%" set "MMPROJ_PATH=%AI_MMPROJ%"
    if not defined MMPROJ_PATH if exist "%PROJECT_ROOT%\models\%AI_MMPROJ%" set "MMPROJ_PATH=%PROJECT_ROOT%\models\%AI_MMPROJ%"
    if not defined MMPROJ_PATH (
        for /d %%D in ("%PROJECT_ROOT%\models\*") do (
            if not defined MMPROJ_PATH if exist "%%D\%AI_MMPROJ%" set "MMPROJ_PATH=%%D\%AI_MMPROJ%"
        )
    )
    if not defined MMPROJ_PATH if exist "%USERPROFILE%\models\%AI_MMPROJ%" set "MMPROJ_PATH=%USERPROFILE%\models\%AI_MMPROJ%"
    if not defined MMPROJ_PATH set "MMPROJ_PATH=%AI_MMPROJ%"
    set "EXTRA_FLAGS=!EXTRA_FLAGS! -mm "!MMPROJ_PATH!""
)

rem Parametros de muestreo
if defined AI_TEMPERATURE (
    set "EXTRA_FLAGS=!EXTRA_FLAGS! --temp !AI_TEMPERATURE!"
)
if defined AI_TOP_P (
    set "EXTRA_FLAGS=!EXTRA_FLAGS! --top-p !AI_TOP_P!"
)
if defined AI_TOP_K (
    set "EXTRA_FLAGS=!EXTRA_FLAGS! --top-k !AI_TOP_K!"
)

rem Ejecutar llama-server
"%LLAMA_SERVER%" --model "%MODEL_PATH%" --host 0.0.0.0 --port %PORT% --threads %AI_THREADS% --threads-batch %AI_THREADS% --n-gpu-layers %AI_GPU_LAYERS% --ctx-size %AI_CTX_SIZE% --batch-size %AI_BATCH_SIZE% --ubatch-size %AI_UBATCH_SIZE% --cache-type-k %AI_CACHE_TYPE_K% --cache-type-v %AI_CACHE_TYPE_V% !EXTRA_FLAGS! %*
