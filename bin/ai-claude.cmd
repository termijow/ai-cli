@echo off
setlocal enabledelayedexpansion

set "SCRIPT_DIR=%~dp0"
for %%I in ("%~dp0..") do set "PROJECT_ROOT=%%~fI"

rem Cargar variables desde .env si existe
if exist "%PROJECT_ROOT%\.env" (
    for /f "usebackq tokens=1,* delims==" %%A in ("%PROJECT_ROOT%\.env") do (
        set "line=%%A"
        if not "!line:~0,1!"=="#" (
            if not "%%B"=="" set "%%A=%%B"
        )
    )
)

if not defined PORT set "PORT=1234"
if not defined MODEL_FILE set "MODEL_FILE=local-model"

set "ANTHROPIC_BASE_URL=http://127.0.0.1:%PORT%"
set "ANTHROPIC_AUTH_TOKEN=local"
set "ANTHROPIC_API_KEY=sk-ant-local-no-key-required"
set "ANTHROPIC_MODEL=%MODEL_FILE%"
set "ANTHROPIC_DEFAULT_SONNET_MODEL=%MODEL_FILE%"
set "ANTHROPIC_DEFAULT_HAIKU_MODEL=%MODEL_FILE%"
set "ANTHROPIC_DEFAULT_OPUS_MODEL=%MODEL_FILE%"

rem Optimizaciones locales para Claude Code con llama-server (65,536 tokens)
set "CLAUDE_CODE_ATTRIBUTION_HEADER=0"
set "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1"
set "CLAUDE_CODE_MAX_CONTEXT_TOKENS=65536"
set "CLAUDE_CODE_AUTO_COMPACT_WINDOW=54000"

rem Timeouts generosos para modelos locales (evita falsos desconexiones durante prefill largo)
set "API_TIMEOUT_MS=600000"
set "CLAUDE_STREAM_FIRST_BYTE_TIMEOUT_MS=600000"
set "CLAUDE_STREAM_IDLE_TIMEOUT_MS=300000"
set "CLAUDE_BYTE_STREAM_IDLE_TIMEOUT_MS=300000"
set "CLAUDE_CODE_CONNECT_TIMEOUT_MS=60000"

rem Sincronizar presupuesto de razonamiento (thinking) con llama-server (1024 tokens)
if not defined MAX_THINKING_TOKENS set "MAX_THINKING_TOKENS=1024"

echo [AI-CLAUDE] Conectando Claude Code al servidor local (http://127.0.0.1:%PORT%)...
echo [AI-CLAUDE] Modelo configurado: %MODEL_FILE%
echo.

claude %*
