# Procedure: AI-CLI Code Explanation Background Process

## Overview
This skill captures the approach for using the AI-CLI tool to explain code in a background shell process, extracting the modified code output and presenting it to the user.

## Key Components

### 1. Background Process Setup
- **Worker Process**: Start the AI-CLI local worker at `mcp/local-worker/dist/index.js`
- **Background Shell**: Use `eval "$(ai-cli-background --output /tmp/background-shells/...)"` to create a persistent shell session
- **Session ID**: Each background shell has a unique session identifier (e.g., `847dcc8f-3780-4088-98ca-020b3ad7cbb9`)

### 2. Code Explanation Request
- **Command Format**: `./bin/ai "Explain this code" <file_path>`
- **Input File**: Path to the code file to be explained (e.g., `/tmp/test.js`)
- **Language**: The AI-CLI tool auto-detects or accepts language specification

### 3. Output Extraction
- **Output Location**: Background shell writes output to `background-shells/<session-id>/shell-bg_<hash>.output`
- **Format**: The output contains:
  - Process confirmation: `✦ Procesando <file> con Qwen...`
  - Cost tracking: `💸 Ahorro en esta consulta: $X.XXXX USD | Total acumulado: $Y.YYYY USD`
  - Diff output: `✦ Cambios propuestos para <file>:`
  - Modified code: The complete modified code block
  - Thinking process (optional): Internal reasoning displayed in XML format

### 4. Output Parsing
- Extract the modified code section from the background shell output
- Remove any XML thinking blocks (`<thinking>...</thinking>`)
- Preserve the code format (no markdown code blocks)

### 5. Cost Tracking Integration
- **Savings Display**: Show per-query savings and cumulative total
- **Format**: `💸 Ahorro en esta consulta: $X.XXXX USD | Total acumulado: $Y.YYYY USD`
- **Source**: Extracted from the background shell output

## Tooling

- **ai-cli**: Main CLI tool for code explanation
- **ai-cli-background**: Background process runner with file output
- **Background shell**: Bash subprocess for running AI-CLI in detached mode

## Configuration Points

- **Worker path**: `mcp/local-worker/dist/index.js`
- **Background output dir**: `background-shells/<session-id>/`
- **Output file name**: `shell-bg_<hash>.output`
- **AI-CLI binary**: `./bin/ai`

## Dependencies

- **ai-cli CLI**: Installed at project root or in `~/.local/bin/`
- **Background shell**: Bash subprocess with file redirection
- **jq/awk**: For cost calculations (if tracking is enabled)

## Error Handling

- Check if background shell output file exists
- Handle incomplete processing (missing output file)
- Validate cost tracking values (ensure they're valid numbers)

## Related Skills

- `llm-api-cost-tracking`: Cost calculation logic used in AI-CLI background processes
- `bash-process-substitution-fix`: Background shell setup patterns
