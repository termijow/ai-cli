@echo off
setlocal
for %%I in ("%~dp0..") do set "AI_CLI_ROOT=%%~fI"
set "PY_BIN=python"
if exist "%AI_CLI_ROOT%\venv\Scripts\python.exe" set "PY_BIN=%AI_CLI_ROOT%\venv\Scripts\python.exe"
"%PY_BIN%" "%AI_CLI_ROOT%\master.py" %*
exit /b %ERRORLEVEL%
