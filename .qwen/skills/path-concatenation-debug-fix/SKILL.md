---
name: path-concatenation-debug-fix
description: Fix double path prefixing bug when using find output in while read loops
source: auto-skill
extracted_at: '2026-08-20T06:55:08.548Z'
---

## Problem

When iterating over file paths from `find` command output, the code was prepending `$HOME/.ai_cli_history/` to a variable `$log` that already contained the full path returned by `find`.

Example failing code:
```bash
while IFS= read -r log; do
    # $log already contains: /home/termihoe/.ai_cli_history/2026-07-27_12-00-opus.json
    # But code did: $HOME/.ai_cli_history/$log
    # Result: $HOME/.ai_cli_history/$HOME/.ai_cli_history/2026-07-27_12-00-opus.json
    cat "$HOME/.ai_cli_history/$log"  # 404: file not found
done < <(find "$HOME/.ai_cli_history" -maxdepth 1 -type f ...)
```

## Solution

Use the `$log` variable directly instead of prepending the directory path:

```bash
while IFS= read -r log; do
    # $log already contains the full path from find
    cat "$log"  # Works correctly
done < <(find "$HOME/.ai_cli_history" -maxdepth 1 -type f ...)
```

## Why This Works

- `find` with an explicit path like `find "$HOME/.ai_cli_history" ...` returns full paths (e.g., `/home/termihoe/.ai_cli_history/2026-07-27_12-00-opus.json`)
- The loop variable `$log` already contains the complete path
- Prepending `$HOME/.ai_cli_history/` again creates a double prefix, resulting in a non-existent path
- When `$log` contains a `$` followed by non-alphanumeric characters (like `.ai_cli_history/...`), bash treats it as a variable reference, causing unexpected behavior

## When to Apply

When working with `find` command output in while loops:
1. Check what path `find` actually returns for the given arguments
2. Avoid double-prefixing directory paths when the output already contains full paths
3. Test with actual file paths to verify the resulting path is valid

## Debugging Tips

- Use `echo "$log"` to inspect the actual value of the loop variable
- Check if the path contains unexpected `$` characters being interpreted as variable references
- Verify the resulting file path exists: `[[ -f "$resulting_path" ]]`

## Related Skills

- `bash-process-substitution-fix`: For using process substitution with while loops
