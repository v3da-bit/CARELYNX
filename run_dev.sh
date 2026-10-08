#!/usr/bin/env bash
# CARELYNX — POSIX Development Runner (Linux & macOS)
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if command -v python3 &>/dev/null; then
    PYTHON_CMD="python3"
elif command -v python &>/dev/null; then
    PYTHON_CMD="python"
else
    echo "ERROR: Python 3 is required but neither 'python3' nor 'python' was found on PATH."
    exit 1
fi

exec $PYTHON_CMD run.py "$@"
