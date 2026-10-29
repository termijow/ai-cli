@echo off
setlocal
set "PY_EXE="
if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" set "PY_EXE=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
if not defined PY_EXE for %%X in (python.exe) do (set "PY_EXE=%%~$PATH:X")

if defined PY_EXE (
    "%PY_EXE%" "%~dp0ai-models.py" %*
    exit /b %ERRORLEVEL%
)

rem Fallback a Git Bash si no hay python
set "SCRIPT_DIR=%~dp0"
set "SCRIPT_DIR=%SCRIPT_DIR:\=/%"
for %%I in ("%~dp0..") do set "AI_CLI_ROOT=%%~fI"
set "AI_CLI_ROOT=%AI_CLI_ROOT:\=/%"
set "BASH_EXE="
if exist "%LOCALAPPDATA%\Programs\Git\bin\bash.exe" set "BASH_EXE=%LOCALAPPDATA%\Programs\Git\bin\bash.exe"
if not defined BASH_EXE if exist "C:\Program Files\Git\bin\bash.exe" set "BASH_EXE=C:\Program Files\Git\bin\bash.exe"
if not defined BASH_EXE for %%X in (bash.exe) do (set "BASH_EXE=%%~$PATH:X")
"%BASH_EXE%" "%SCRIPT_DIR%ai-models" %*
