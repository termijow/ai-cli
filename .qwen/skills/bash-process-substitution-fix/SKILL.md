---
name: bash-process-substitution-fix
description: Fix bash syntax error with process substitution in for loops using find + read loop
source: auto-skill
extracted_at: '2026-08-20T06:35:41.388Z'
---

## Problem

Bash process substitution `< <(...)` inside a `for` loop causes a syntax error: "unexpected token '<'"

Example failing code:
```bash
for log in < <(ls -tr "$HOME/.ai_cli_history" 2>/dev/null | head -n "$max_show"); do
    # ...
done
```

## Solution

Replace the `for` loop with a `while IFS= read -r var` loop reading from process substitution:

```bash
while IFS= read -r log; do
    # ...
done < <(find "$HOME/.ai_cli_history" -maxdepth 1 -type f -printf "%T@ %p\n" 2>/dev/null | sort -rn | cut -d' ' -f2- | head -n "$max_show")
```

## Why This Works

- `for` loops cannot use process substitution directly as the iteration variable
- `while read` loops can read from process substitution piped into the command
- Using `find` with `-printf "%T@ %p"` gives timestamp and path, allowing sorting by modification time
- `sort -rn` sorts numerically in reverse (newest first)
- `cut -d' ' -f2-` extracts just the paths (removes timestamp prefix)

## When to Apply

When you need to iterate over files from process substitution with process substitution output:
- List files sorted by timestamp: `while read -r file; do ... done < <(find ...)`
- Process file contents: `while read -r line; do ... done < <(cat file)`
- Any case where direct process substitution in `for` doesn't work

## Alternative Approaches

1. Use a temporary file:
   ```bash
   find ... -printf "%T@ %p\n" | sort -rn | cut -d' ' -f2- > "$tmpfile"
   while IFS= read -r log; do ... done < "$tmpfile"
   ```

2. Use a different loop construct:
   ```bash
   mapfile -t logs < <(find ... -printf "%T@ %p\n" | sort -rn | cut -d' ' -f2- | head -n "$max_show")
   for log in "${logs[@]}"; do ... done
   ```
