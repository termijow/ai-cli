---
name: python-deps-virtual-env
description: Install Python dependencies using virtual environment when pip fails on externally-managed-systems
source: auto-skill
extracted_at: '2026-08-20T08:45:00.000Z'
---

## Problem
When attempting to install Python packages on a system with PEP 668 externally-managed-environment restrictions (e.g., Arch Linux with pacman-managed Python), direct `pip install` commands fail with:
```
error: externally-managed-environment
This environment is externally managed
```

## Solution
Create a virtual environment first, then install packages:

```bash
# 1. Create virtual environment
python3 -m venv ~/.venv

# 2. Upgrade pip inside venv
~/.venv/bin/pip install --upgrade pip

# 3. Install all required packages
~/.venv/bin/pip install <package1> <package2> ...

# 4. Verify no broken dependencies
~/.venv/bin/pip check

# 5. Use venv for Python
export PATH="$HOME/.venv/bin:$PATH"
```

## Why
- PEP 668 prevents system-wide pip installs to avoid breaking system Python packages
- Virtual environments isolate dependencies and provide a clean installation method
- The approach works on any OS (Linux, macOS, Windows)

## How to apply
- Use this pattern whenever pip install fails with externally-managed-environment error
- Store venv in a consistent location (`~/.venv`) for easy access
- Verify installations with `pip check` before proceeding
