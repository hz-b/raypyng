#!/usr/bin/env bash
# Creates .venv with Python 3.12 using uv, installs raypyng[dev], and wires up pre-commit.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
VENV_DIR="${PROJECT_ROOT}/.venv"
UV_BIN="${UV_BIN:-uv}"

if ! command -v "${UV_BIN}" >/dev/null 2>&1; then
    echo "Error: 'uv' is required."
    echo "Install it: https://docs.astral.sh/uv/getting-started/installation/"
    exit 1
fi

echo "============================================================"
echo "Creating .venv with Python 3.12"
echo "============================================================"
"${UV_BIN}" venv --python 3.12 "${VENV_DIR}"

PYTHON_BIN="${VENV_DIR}/bin/python"

echo
echo "============================================================"
echo "Installing raypyng[dev]"
echo "============================================================"
"${UV_BIN}" pip install --python "${PYTHON_BIN}" -e "${PROJECT_ROOT}[dev]"

echo
echo "============================================================"
echo "Installing pre-commit hooks"
echo "============================================================"
"${VENV_DIR}/bin/pre-commit" install --install-hooks

echo
echo "============================================================"
echo "Done"
echo "============================================================"
echo "Activate with:  source .venv/bin/activate"
echo "Run linters:    pre-commit run --all-files"
