#!/usr/bin/env python3
"""Lightweight jq emulator for Windows environments where jq.exe is blocked or missing."""

import sys
import json
import re

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stdin, "reconfigure"):
    sys.stdin.reconfigure(encoding="utf-8", errors="replace")

def parse_path(obj, path_str):
    """Simple jq path accessor like .choices[0].message.content or .usage.prompt_tokens // 0"""
    default_val = ""
    if " // " in path_str:
        path_str, default_part = path_str.split(" // ", 1)
        default_part = default_part.strip()
        if default_part == "empty":
            default_val = ""
        elif default_part.isdigit():
            default_val = int(default_part)
        elif default_part.startswith('"') and default_part.endswith('"'):
            default_val = default_part[1:-1]
        else:
            default_val = default_part

    # Handle additions like .prompt_tokens + .completion_tokens
    if " + " in path_str:
        parts = path_str.split(" + ")
        total = 0
        for p in parts:
            v = parse_path(obj, p.strip())
            try:
                total += float(v)
            except (ValueError, TypeError):
                pass
        return total

    tokens = [t for t in re.split(r'\.|\b(?=\[)', path_str) if t]
    curr = obj
    for token in tokens:
        if not token:
            continue
        if token.startswith('['):
            idx_match = re.match(r'\[(\d+)\]', token)
            if idx_match and isinstance(curr, list):
                idx = int(idx_match.group(1))
                if idx < len(curr):
                    curr = curr[idx]
                else:
                    return default_val
            else:
                return default_val
        else:
            if isinstance(curr, dict) and token in curr:
                curr = curr[token]
            else:
                return default_val

    return curr if curr is not None else default_val

def main():
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print("pyjq emulator")
        return 0
    if args[0] in ("--version", "-V", "-v"):
        print("pyjq-1.7-compat")
        return 0

    raw_output = False
    compact = False
    slurp = False
    null_input = False
    var_args = {}

    idx = 0
    while idx < len(args):
        arg = args[idx]
        if arg.startswith("-") and not arg.startswith("--"):
            for ch in arg[1:]:
                if ch == "r": raw_output = True
                elif ch == "c": compact = True
                elif ch == "s": slurp = True
                elif ch == "n": null_input = True
            idx += 1
        elif arg == "--arg":
            var_args[args[idx+1]] = args[idx+2]
            idx += 3
        elif arg == "--argjson":
            try:
                var_args[args[idx+1]] = json.loads(args[idx+2])
            except Exception:
                var_args[args[idx+1]] = args[idx+2]
            idx += 3
        else:
            break

    filter_expr = args[idx] if idx < len(args) else "."
    files = args[idx+1:] if idx < len(args) else []

    # Read input data
    input_text = ""
    if null_input:
        input_data = None
    elif files:
        with open(files[0], "r", encoding="utf-8", errors="replace") as f:
            input_text = f.read()
    else:
        input_text = sys.stdin.read()

    # Handle null input construction
    if null_input:
        # Construct object from template with vars
        res = {}
        if "messages" in filter_expr and "system" in filter_expr:
            res = {
                "messages": [
                    {"role": "system", "content": var_args.get("sys", "")},
                    {"role": "user", "content": var_args.get("user", "")}
                ],
                "temperature": float(var_args.get("t", 0.2)),
                "max_tokens": int(var_args.get("max", 2048))
            }
        elif "timestamp" in filter_expr:
            res = {
                "timestamp": var_args.get("ts", ""),
                "query_type": var_args.get("qt", "code"),
                "prompt_tokens": int(var_args.get("pt", 0)),
                "completion_tokens": int(var_args.get("ct", 0)),
                "savings": float(var_args.get("sv", 0.0)),
                "total_savings": float(var_args.get("tsv", 0.0))
            }
        else:
            res = var_args

        if compact:
            print(json.dumps(res, separators=(',', ':'), ensure_ascii=False))
        else:
            print(json.dumps(res, indent=2, ensure_ascii=False))
        return 0

    # Parse input data
    if slurp:
        items = []
        for line in input_text.splitlines():
            line = line.strip()
            if line:
                try:
                    items.append(json.loads(line))
                except Exception:
                    pass
        if "add" in filter_expr:
            total = 0
            key_match = re.search(r'\.([a-zA-Z0-9_]+)', filter_expr)
            key = key_match.group(1) if key_match else None
            for item in items:
                if key and isinstance(item, dict):
                    v = item.get(key, 0)
                    try: total += float(v)
                    except Exception: pass
            if raw_output:
                print(f"{total:.2f}" if isinstance(total, float) and total != int(total) else f"{int(total)}")
            else:
                print(total)
            return 0
        elif filter_expr.strip() == ".":
            print(json.dumps(items, indent=2, ensure_ascii=False))
            return 0

    try:
        data = json.loads(input_text.strip()) if input_text.strip() else {}
    except Exception:
        data = {}

    val = parse_path(data, filter_expr.strip())
    if raw_output:
        if val is None:
            pass
        elif isinstance(val, (dict, list)):
            print(json.dumps(val, ensure_ascii=False))
        else:
            print(str(val))
    else:
        print(json.dumps(val, ensure_ascii=False))

    return 0

if __name__ == "__main__":
    sys.exit(main())
