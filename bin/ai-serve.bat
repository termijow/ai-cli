@echo off
setlocal
set "SCRIPT_DIR=%~dp0"
set "BASH_EXE="

if exist "%LOCALAPPDATA%\Programs\Git\bin\bash.exe" set "BASH_EXE=%LOCALAPPDATA%\Programs\Git\bin\bash.exe"
if not defined BASH_EXE if exist "C:\Program Files\Git\bin\bash.exe" set "BASH_EXE=C:\Program Files\Git\bin\bash.exe"
if not defined BASH_EXE for %%X in (bash.exe) do (set "BASH_EXE=%%~$PATH:X")

if not defined BASH_EXE (
    echo [ERROR] No se encontro Git Bash en el sistema.
    exit /b 1
)

"%BASH_EXE%" "%SCRIPT_DIR%ai-serve" %*
