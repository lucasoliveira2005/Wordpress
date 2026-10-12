#!/usr/bin/env bash
set -e

# Install MiniZinc, in case it is not already in the system
if ! command -v minizinc >/dev/null 2>&1; then
    sudo apt-get install -y minizinc
fi

# Create virtual environment if necessary
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi

# Install the minizinc Python library
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install minizinc

echo "Setup complete."
