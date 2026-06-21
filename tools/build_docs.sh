#!/usr/bin/env bash
# Build raypyng documentation using Sphinx.
#
# Usage:
#   ./tools/build_docs.sh            # build HTML + PDF (default)
#   ./tools/build_docs.sh --html     # HTML only
#   ./tools/build_docs.sh --pdf      # PDF only
#   ./tools/build_docs.sh --open     # build HTML and open in browser
#   ./tools/build_docs.sh --html --open
#   ./tools/build_docs.sh --skip-image-sync   # skip copying example images

set -euo pipefail

LAUNCH_HTML=false
SKIP_IMAGE_SYNC=false
BUILD_HTML=false
BUILD_LATEX=false
BUILD_PDF=false
EXPLICIT_BUILD_SELECTION=false

for arg in "$@"; do
    case "$arg" in
        --html)
            BUILD_HTML=true
            EXPLICIT_BUILD_SELECTION=true
            ;;
        --pdf)
            BUILD_LATEX=true
            BUILD_PDF=true
            EXPLICIT_BUILD_SELECTION=true
            ;;
        --open)
            LAUNCH_HTML=true
            ;;
        --skip-image-sync)
            SKIP_IMAGE_SYNC=true
            ;;
        *)
            echo "Unknown option: $arg"
            echo "Usage: $0 [--html] [--pdf] [--open] [--skip-image-sync]"
            exit 1
            ;;
    esac
done

if [[ "${EXPLICIT_BUILD_SELECTION}" == false ]]; then
    if [[ "${LAUNCH_HTML}" == true ]]; then
        BUILD_HTML=true
    else
        BUILD_HTML=true
        BUILD_LATEX=true
        BUILD_PDF=true
    fi
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
DOCS_DIR="${PROJECT_ROOT}/docs"
DOCS_VENV_DIR="${PROJECT_ROOT}/venv_docs"
UV_BIN="${UV_BIN:-uv}"

if ! command -v "${UV_BIN}" >/dev/null 2>&1; then
    echo "Error: 'uv' is required to bootstrap the docs environment."
    echo "Install uv first: https://docs.astral.sh/uv/getting-started/installation/"
    exit 1
fi

if [[ ! -x "${DOCS_VENV_DIR}/bin/python" ]]; then
    echo "============================================================"
    echo "Creating docs virtual environment: ${DOCS_VENV_DIR}"
    echo "============================================================"
    "${UV_BIN}" venv --python 3.12 "${DOCS_VENV_DIR}"
fi

echo "============================================================"
echo "Installing docs dependencies into ${DOCS_VENV_DIR}"
echo "============================================================"
"${UV_BIN}" pip install --python "${DOCS_VENV_DIR}/bin/python" -e "${PROJECT_ROOT}[docs]"

PYTHON_BIN="${DOCS_VENV_DIR}/bin/python"

HTML_BUILD_DIR="${DOCS_DIR}/_build/html"
LATEX_BUILD_DIR="${DOCS_DIR}/_build/latex"

if [[ "${SKIP_IMAGE_SYNC}" == false ]]; then
    echo "============================================================"
    echo "Syncing images from examples/"
    echo "============================================================"
    DOCS_IMAGES_DIR="${DOCS_DIR}/images"
    mkdir -p "${DOCS_IMAGES_DIR}"

    # Copy any plots that examples produce into docs/images/ so RST files can reference them.
    # Add cp lines here as new example plots are introduced.
    for png in "${PROJECT_ROOT}"/examples/*.png "${PROJECT_ROOT}"/examples/**/*.png; do
        [[ -f "${png}" ]] && cp "${png}" "${DOCS_IMAGES_DIR}/" || true
    done
    echo "Images synced to ${DOCS_IMAGES_DIR}"
    echo
fi

rm -rf "${DOCS_DIR}/_build"

if [[ "${BUILD_HTML}" == true ]]; then
    echo "============================================================"
    echo "Building HTML documentation"
    echo "============================================================"
    "${PYTHON_BIN}" -m sphinx -b html "${DOCS_DIR}" "${HTML_BUILD_DIR}"
fi

if [[ "${BUILD_LATEX}" == true ]]; then
    if [[ "${BUILD_HTML}" == true ]]; then
        echo
    fi
    echo "============================================================"
    echo "Building LaTeX documentation"
    echo "============================================================"
    "${PYTHON_BIN}" -m sphinx -b latex "${DOCS_DIR}" "${LATEX_BUILD_DIR}"
fi

if [[ "${BUILD_PDF}" == true ]]; then
    if [[ "${BUILD_HTML}" == true || "${BUILD_LATEX}" == true ]]; then
        echo
    fi
    echo "============================================================"
    echo "Building PDF"
    echo "============================================================"
    make -C "${LATEX_BUILD_DIR}"
fi

PDF_FILE=""
if [[ "${BUILD_PDF}" == true && -d "${LATEX_BUILD_DIR}" ]]; then
    PDF_FILE="$(find "${LATEX_BUILD_DIR}" -maxdepth 1 -name '*.pdf' | head -n 1)"
fi

echo
echo "============================================================"
echo "Build completed"
echo "============================================================"
if [[ "${BUILD_HTML}" == true ]]; then
    echo "HTML:"
    echo "  ${HTML_BUILD_DIR}/index.html"
fi

if [[ "${BUILD_PDF}" == true && -n "${PDF_FILE}" ]]; then
    echo
    echo "PDF:"
    echo "  ${PDF_FILE}"
fi

if [[ "${LAUNCH_HTML}" == true ]]; then
    echo
    echo "Opening HTML documentation..."
    HTML_INDEX="${HTML_BUILD_DIR}/index.html"
    DOCS_BROWSER="${DOCS_BROWSER:-google-chrome}"
    if command -v "${DOCS_BROWSER}" >/dev/null 2>&1; then
        if "${DOCS_BROWSER}" "file://${HTML_INDEX}" >/dev/null 2>&1; then
            :
        elif "${DOCS_BROWSER}" "${HTML_INDEX}" >/dev/null 2>&1; then
            :
        elif command -v xdg-open >/dev/null 2>&1 && xdg-open "${HTML_INDEX}" >/dev/null 2>&1; then
            :
        elif command -v gio >/dev/null 2>&1 && gio open "${HTML_INDEX}" >/dev/null 2>&1; then
            :
        elif command -v python3 >/dev/null 2>&1 && python3 -m webbrowser "file://${HTML_INDEX}" >/dev/null 2>&1; then
            :
        else
            echo "Could not auto-open browser."
            echo "Open manually: ${HTML_INDEX}"
        fi
    elif command -v xdg-open >/dev/null 2>&1; then
        if xdg-open "${HTML_INDEX}" >/dev/null 2>&1; then
            :
        elif command -v gio >/dev/null 2>&1 && gio open "${HTML_INDEX}" >/dev/null 2>&1; then
            :
        elif command -v python3 >/dev/null 2>&1 && python3 -m webbrowser "file://${HTML_INDEX}" >/dev/null 2>&1; then
            :
        else
            echo "Could not auto-open browser."
            echo "Open manually: ${HTML_INDEX}"
        fi
    elif command -v gio >/dev/null 2>&1; then
        if gio open "${HTML_INDEX}" >/dev/null 2>&1; then
            :
        elif command -v python3 >/dev/null 2>&1 && python3 -m webbrowser "file://${HTML_INDEX}" >/dev/null 2>&1; then
            :
        else
            echo "Could not auto-open browser."
            echo "Open manually: ${HTML_INDEX}"
        fi
    elif command -v python3 >/dev/null 2>&1; then
        if ! python3 -m webbrowser "file://${HTML_INDEX}" >/dev/null 2>&1; then
            echo "Could not auto-open browser."
            echo "Open manually: ${HTML_INDEX}"
        fi
    else
        echo "Could not auto-open browser."
        echo "Open manually: ${HTML_INDEX}"
    fi
fi
