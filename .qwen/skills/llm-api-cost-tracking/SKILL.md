---
name: llm-api-cost-tracking
description: Track LLM API usage costs using token counts from chat sessions and simulated pricing
source: auto-skill
extracted_at: '2026-08-20T06:12:50.852Z'
---

# Procedure: Implementing LLM API Cost Tracking Script

## Overview
This skill captures the approach for building a bash script that tracks LLM API usage costs by reading token counts from chat session JSON files and calculating simulated savings.

## Key Components

### 1. Session Data Extraction
- Read from `$HOME/.qwen/history.json` containing session arrays with `prompt_tokens`, `completion_tokens`, and `timestamp` fields
- Navigate to the last session: `.sessions | -1 | . + 1` to get the index of the most recent session
- Extract token counts with fallback defaults: `.sessions[$LAST_SESSION].prompt_tokens // 0`

### 2. Cost Calculation
- Use awk for floating-point arithmetic to compute costs:
  - Prompt cost: `prompt_tokens * 0.0000050` ($0.000005 per token)
  - Completion cost: `completion_tokens * 0.0000100` ($0.000010 per token)
  - Total: `prompt_cost + completion_cost`
- Format output to 6 decimal places for individual costs, 4 for total

### 3. Savings Tracking
- Maintain a cumulative savings file (`$HOME/.ai_cli_savings`)
- Load current total, add new session savings, save back with 2 decimal places
- Handle missing file by initializing with "0.00"

### 4. History Logging
- Append new entries to a JSONL file (`$HOME/.ai_cli_history/queries.jsonl`)
- Each entry includes: timestamp, query_type, prompt_tokens, completion_tokens, savings, total_savings
- Use jq to construct JSON without shell escaping issues

### 5. Rotation Policy
- Keep only last 20 entries maximum
- Use `head -n $KEEP_COUNT` + `mv` to rotate old entries
- Prevents unbounded growth of history file

## Tooling

- **jq**: For JSON parsing and construction
- **awk**: For floating-point arithmetic
- **bash**: For file I/O, conditionals, and orchestration

## Configuration Points

- Token pricing: `$0.000005` per prompt token, `$0.000010` per completion token
- History limit: 20 entries
- Session file location: `$HOME/.qwen/history.json`
- Savings file: `$HOME/.ai_cli_savings`
- History directory: `$HOME/.ai_cli_history/`

## Dependencies

- Bash 4+ (for `[[ ]]` syntax)
- jq
- awk

## Error Handling

- Gracefully handle missing session files (exit 0)
- Handle missing sessions in JSON (exit 0)
- Handle empty token values (treat as 0)
- Use `2>/dev/null` to suppress warnings