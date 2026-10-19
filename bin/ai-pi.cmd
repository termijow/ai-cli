@echo off
setlocal
set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT=%SCRIPT_DIR%.."

if exist "%PROJECT_ROOT%\.env" (
    for /f "usebackq tokens=1,* delims==" %%A in ("%PROJECT_ROOT%\.env") do (
        if not "%%A"=="" if not "%%A:~0,1%"=="#" set "%%A=%%B"
    )
)
if "%PORT%"=="" set "PORT=1234"
set "LLAMA_BASE_URL=http://127.0.0.1:%PORT%"
set "OPENAI_BASE_URL=http://127.0.0.1:%PORT%/v1"
set "OPENAI_API_KEY=local"
set "PATH=C:\Program Files\nodejs;C:\Users\USUARIO\AppData\Roaming\npm;%PATH%"

pi %*
endlocal
