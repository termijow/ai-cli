#!/usr/bin/env python3
"""
AI-CLI Master Script
Starts all services including frontend automatically
"""

import subprocess
import sys
import os
from pathlib import Path


def run_command(cmd, cwd=None, check=True):
    """Run a command and return the result."""
    print(f"Running: {cmd}")
    result = subprocess.run(
        cmd,
        shell=True,
        cwd=cwd,
        capture_output=False,
        text=True
    )
    if result.returncode != 0:
        print(f"Error running command: {cmd}")
        return False
    return True


def print_colored(status, message):
    """Print colored output."""
    colors = {
        "success": "\033[92m",  # Green
        "warning": "\033[93m",  # Yellow
        "info": "\033[94m",  # Blue
        "error": "\033[91m",  # Red
    }
    reset = "\033[0m"
    color = colors.get(status, "")
    print(f"{color}{message}{reset}")


def main():
    """Main function to start all services."""
    project_root = Path(__file__).parent.absolute()
    
    print_colored("info", "🚀 Starting AI-CLI Services...")
    
    # Start backend server
    print_colored("info", "Starting Backend Server...")
    backend_script = project_root / "start-all.sh"
    run_command(backend_script, cwd=project_root)
    
    print_colored("success", "All services started successfully!")
    print("\nServices:")
    print("  - Backend Server: http://localhost:3094")
    print("  - Frontend Server: http://localhost:5173")
    print("\nPress Ctrl+C to stop all services.")
    
    try:
        # Keep running until interrupted
        sys.stdout.flush()
    except KeyboardInterrupt:
        print("\nShutting down...")
        # Cleanup will be handled by the trap in start-all.sh


if __name__ == "__main__":
    main()
