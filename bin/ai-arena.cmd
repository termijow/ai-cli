@echo off
setlocal
set "PROJECT_ROOT=%~dp0.."
set "PYTHON_EXE=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
if not exist "%PYTHON_EXE%" set "PYTHON_EXE=python"
"%PYTHON_EXE%" "%~dp0ai-arena.py" %*
endlocal
