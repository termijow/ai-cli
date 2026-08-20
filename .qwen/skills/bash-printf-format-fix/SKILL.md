---
name: bash-printf-format-fix
description: Fix printf format specifier issues in shell scripts where $ prefix causes variable interpolation instead of format string
source: auto-skill
extracted_at: '2026-08-20T07:25:00.000Z'
---

# Procedure: Fixing printf Format Specifiers in Shell Scripts

## Overview
This skill captures the approach for fixing printf format specifier issues in bash scripts. The problem occurs when a `$` prefix is used in the format string (e.g., `$%-8s`), causing the shell to interpret it as a variable reference instead of a printf format specifier.

## Problem Identification

### Root Cause
In bash, when using `printf` or `echo -e`, the format string must use standard printf format specifiers. If a `$` is included (e.g., `$%-8s`), the shell attempts to interpolate a variable named `$%-8s` instead of treating `%8s` as a format specifier.

### Symptom
- Numbers are printed without proper alignment
- Format specifiers like `%8s` (right-aligned, width 8) appear literally in output instead of being applied
- Dollar signs `$` in format strings are treated as variable references

## Solution Pattern

### 1. Remove Dollar Prefix from Format String
Change `$%-8s` to `%8s`:
```bash
# WRONG - Shell tries to interpolate variable $%-8s
echo "Value: $%-8s" "$value"

# CORRECT - printf format specifier %8s
echo "Value: %8s" "$value"
```

### 2. Quote printf Arguments
When passing variables to printf, use proper quoting to prevent shell expansion during the `printf` call:
```bash
# WRONG - Shell may expand variables before printf receives them
echo "$(printf '%.2f' $total)"

# CORRECT - Quote the variable so printf receives the value directly
echo "$(printf '%.2f' "$total")"
```

### 3. Handle Multiple Format Specifiers
For multiple lines, apply the same pattern consistently:
```bash
echo -e "\033[0;32m│\033[0m \033[1;33mTokens Input Totales:\033[0m \033[1;33m%8s\033[0m       \033[0;32m│\033[0m" "$total_input_tokens"
echo -e "\033[0;32m│\033[0m \033[1;33mTokens Output Totales:\033[0m \033[1;33m%8s\033[0m       \033[0;32m│\033[0m" "$total_output_tokens"
echo -e "\033[0;32m│\033[0m \033[1;33mGasto Input Total:\033[0m \033[1;33m%.2f USD\033[0m      \033[0;32m│\033[0m" "$(printf '%.2f' "$total_input_cost")"
echo -e "\033[0;32m│\033[0m \033[1;33mAhorro Output Total:\033[0m \033[1;33m%.2f USD\033[0m      \033[0;32m│\033[0m" "$(printf '%.2f' "$total_output_savings")"
echo -e "\033[0;32m│\033[0m \033[1;32m💰 TOTAL AHORRADO:\033[0m \033[1;32m%.2f USD\033[0m       \033[0;32m│\033[0m" "$(printf '%.2f' "$total_savings")"
```

## Related Pattern: seq Command Syntax

### Problem
`seq -r 6 1` is not supported on all systems (the `-r` flag for "reverse" is non-standard).

### Solution
Use `seq -g 6 1` instead:
```bash
# WRONG - -r flag not universally supported
for month in $(seq -r 6 1); do

# CORRECT - -g flag for decimal range, works on most systems
for month in $(seq -g 6 1); do
```

## Tooling
- **bash**: For printf format specifiers and file I/O
- **sqlite3**: For querying usage data

## Configuration Points
- Format specifiers: `%8s` for right-aligned width 8, `%.2f` for 2 decimal places
- seq range: `seq -g start stop` for decimal range generation

## Error Handling
- Quote all variables in printf calls
- Use `2>/dev/null` for commands that may fail (e.g., date parsing)
- Use `COALESCE(SUM(...), 0)` in SQL to handle empty tables

## Verification
After applying fixes, test with actual data to verify:
- Numbers are properly formatted and aligned
- No literal `%` characters appear in output
- Dollar amounts show 2 decimal places correctly
