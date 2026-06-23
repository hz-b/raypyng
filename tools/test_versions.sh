#!/usr/bin/env bash
# Run raypyng unit tests and (optionally) cross-version functional regression tests.
#
# Usage:
#   ./tools/test_versions.sh                              # unit tests only
#   ./tools/test_versions.sh --dev /path/to/Ray-UI-dev   # unit + functional (auto-detect stable)
#   ./tools/test_versions.sh --stable P1 --dev P2        # unit + full regression
#   ./tools/test_versions.sh --dev P2 --slow             # also run multi-energy tests
#   ./tools/test_versions.sh --tol 0.02                  # 2 % tolerance (default 1 %)
#
# Environment variables (used when CLI flags are not given):
#   RAYUI_STABLE_PATH   path to the stable RAY-UI installation
#   RAYUI_DEV_PATH      path to the development RAY-UI installation
#   TOLERANCE           relative metric tolerance (e.g. 0.01)
#
# Exit codes: 0 = all ran tests passed, non-zero = failure or usage error.

set -euo pipefail
cd "$(dirname "$0")/.."   # run from repo root

# ── defaults ──────────────────────────────────────────────────────────────────
STABLE="${RAYUI_STABLE_PATH:-}"
DEV="${RAYUI_DEV_PATH:-}"
TOL="${TOLERANCE:-0.01}"
SLOW=""

# ── argument parsing ──────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
    case "$1" in
        --stable)   STABLE="$2"; shift 2 ;;
        --dev)      DEV="$2";    shift 2 ;;
        --tol)      TOL="$2";    shift 2 ;;
        --slow)     SLOW="1";    shift   ;;
        -h|--help)
            sed -n '2,/^$/p' "$0"   # print the header comment
            exit 0 ;;
        *) echo "Unknown option: $1" >&2; exit 1 ;;
    esac
done

# ── auto-detect stable path if not given ─────────────────────────────────────
if [[ -z "$STABLE" ]]; then
    for base in "$HOME" "$HOME/Applications" /opt /Applications; do
        for name in RAY-UI Ray-UI; do
            candidate="$base/$name"
            if [[ -d "$candidate" ]]; then
                STABLE="$candidate"
                break 2
            fi
        done
    done
fi

# ── resolve python interpreter ────────────────────────────────────────────────
PYTHON="${PYTHON:-python3}"
if [[ -f ".venv/bin/python" ]]; then
    PYTHON=".venv/bin/python"
fi

PYTEST="$PYTHON -m pytest"

# ── helpers ───────────────────────────────────────────────────────────────────
print_header() { echo ""; echo "=== $* ==="; }
pass_fail()    { [[ $1 -eq 0 ]] && echo "PASSED" || echo "FAILED"; }

UNIT_RC=0
FUNC_RC=0

# ── unit tests ────────────────────────────────────────────────────────────────
# Run only tests/unit/ here.  The pre-existing integration tests
# (test_analyze.py, test_no_analyze.py, etc.) require a running RAY-UI and
# write output to the current directory; run them separately if needed.
print_header "Unit tests (no RAY-UI required)"
$PYTEST tests/unit/ tests/test_simulation_class.py tests/test_mutable_config_properties.py \
    --tb=short -q || UNIT_RC=$?

# ── functional regression tests ───────────────────────────────────────────────
if [[ -n "$DEV" ]]; then
    print_header "Functional regression tests"
    echo "  Stable : ${STABLE:-<not found — will skip stable-only tests>}"
    echo "  Dev    : $DEV"
    echo "  Tol    : $TOL"
    echo ""

    MARK_EXPR="functional"
    [[ -n "$SLOW" ]] && MARK_EXPR="functional or slow"

    FUNC_ARGS=(
        tests/functional/
        "--dev-ray-path=$DEV"
        "--tolerance=$TOL"
        "-m" "$MARK_EXPR"
        --tb=short -v
    )
    [[ -n "$STABLE" ]] && FUNC_ARGS+=("--stable-ray-path=$STABLE")

    $PYTEST "${FUNC_ARGS[@]}" || FUNC_RC=$?
else
    print_header "Functional regression tests"
    echo "  Skipped — pass --dev <path> (or set RAYUI_DEV_PATH) to enable."
fi

# ── summary ───────────────────────────────────────────────────────────────────
echo ""
echo "┌─────────────────────────────────────┐"
echo "│           Test summary              │"
echo "├─────────────────────────────────────┤"
printf "│  Unit tests       : %-15s │\n" "$(pass_fail $UNIT_RC)"
if [[ -n "$DEV" ]]; then
    printf "│  Functional tests : %-15s │\n" "$(pass_fail $FUNC_RC)"
else
    printf "│  Functional tests : %-15s │\n" "skipped"
fi
echo "└─────────────────────────────────────┘"

[[ $UNIT_RC -eq 0 && $FUNC_RC -eq 0 ]]
