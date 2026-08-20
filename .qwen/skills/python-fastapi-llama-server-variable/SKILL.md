---
name: python-fastapi-llama-server-variable
description: Fix FastAPI server undefined variable error when referencing llama.cpp server path
source: auto-skill
extracted_at: '2026-08-20T18:13:55.110Z'
---

## Problem

The FastAPI backend server failed to start with an `AttributeError` or `NameError` when trying to use a variable `LLAMA_SERVER` that was undefined in the code. The code referenced `LLAMA_SERVER` but this variable was never defined.

Example error:
```
AttributeError: 'NoneType' object has no attribute 'parent'
```

This occurred because the code was using `LLAMA_SERVER` instead of `LLAMA_CPP_SERVER`.

## Root Cause

In Python/FastAPI code, the variable `LLAMA_SERVER` was referenced but never defined. The correct variable name is `LLAMA_CPP_SERVER`, which is set from the project root path:

```python
# WRONG - undefined variable
LLAMA_SERVER = PROJECT_ROOT / "llama-server"

# CORRECT - properly defined
LLAMA_CPP_SERVER = PROJECT_ROOT / "llama-server"
```

The code had inconsistent naming: the constant was defined as `LLAMA_CPP_SERVER` but referenced as `LLAMA_SERVER` elsewhere in the file.

## Solution

1. **Identify the undefined variable** by examining the error traceback
2. **Find all references** to the undefined variable (e.g., lines 52 and 65 in `server.py`)
3. **Replace the variable name** to match the defined constant:

```python
# Fix in server.py line 52:
logger.info(f"LLAMA_CPP_SERVER: {LLAMA_CPP_SERVER}")

# Fix in server.py line 65:
test_url = f"http://localhost:{LLAMA_PORT}/v1/chat/completions"
```

## When to Apply

When a FastAPI server fails to start with an undefined variable error:
1. Check the error message for the undefined variable name
2. Search for all references to that variable in the codebase
3. Verify if a similar-named variable exists (e.g., `LLAMA_CPP_SERVER` vs `LLAMA_SERVER`)
4. Replace the undefined references with the correct variable names

## Debugging Tips

- Use `grep -n "undefined_variable"` to find all references
- Check the beginning of the file for variable definitions
- Look for typos in variable names that are very similar (e.g., `SERVER` vs `CPP_SERVER`)
- Run the server with `python server.py` and observe the error output

## Related Skills

- `python-deps-virtual-env`: For managing Python dependencies in virtual environments
- `ai-cli-services-startup`: For starting the backend server using startup scripts
