#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

PUBLISH_VENV="${PROJECT_ROOT}/.venv_publish"
TOKEN_FILE="${PROJECT_ROOT}/.token"

get_named_token() {
    local token_file="$1"
    local header="$2"

    awk -v header="$header" '
        $0 ~ "^# " header " token[[:space:]]*$" {in_block=1; next}
        in_block && $0 ~ "^#" {in_block=0}
        in_block && $0 !~ "^[[:space:]]*$" {print; exit}
    ' "$token_file"
}

cd "${PROJECT_ROOT}"

echo "============================================================"
echo "Preparing publish environment"
echo "============================================================"

if ! command -v uv >/dev/null 2>&1; then
    echo
    echo "Error: uv is not installed."
    echo
    echo "Install from:"
    echo "https://docs.astral.sh/uv/getting-started/installation/"
    exit 1
fi

if [[ ! -d "${PUBLISH_VENV}" ]]; then
    echo "Creating publish virtual environment..."
    uv venv "${PUBLISH_VENV}"
fi

PYTHON_BIN="${PUBLISH_VENV}/bin/python"

if ! "${PYTHON_BIN}" -m pip --version >/dev/null 2>&1; then
    echo "Bootstrapping pip..."
    "${PYTHON_BIN}" -m ensurepip --upgrade
fi

echo "Installing publish dependencies..."

"${PYTHON_BIN}" -m pip install --upgrade \
    pip \
    build \
    twine

echo
echo "============================================================"
echo "Cleaning old builds"
echo "============================================================"

rm -rf build dist *.egg-info

echo
echo "============================================================"
echo "Building package"
echo "============================================================"

"${PYTHON_BIN}" -m build

echo
echo "============================================================"
echo "Checking distributions"
echo "============================================================"

"${PYTHON_BIN}" -m twine check dist/*

echo
echo "============================================================"
echo "Uploading to PyPI"
echo "============================================================"

if [[ -f "${TOKEN_FILE}" ]]; then
    TOKEN_VALUE="$(get_named_token "${TOKEN_FILE}" "PyPI")"

    if [[ -z "${TOKEN_VALUE}" ]]; then
        echo "Error: could not find '# PyPI token' in ${TOKEN_FILE}"
        exit 1
    fi

    export TWINE_USERNAME="__token__"
    export TWINE_PASSWORD="${TOKEN_VALUE}"

    "${PYTHON_BIN}" -m twine upload --non-interactive dist/*
else
    "${PYTHON_BIN}" -m twine upload dist/*
fi

echo
echo "============================================================"
echo "PyPI upload completed"
echo "============================================================"