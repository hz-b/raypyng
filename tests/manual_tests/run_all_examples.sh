#!/bin/bash
# Run the raypyng examples. Each example lives in its own folder. Scripts are
# classified by filename:
#   simulation_*.py  -> a simulation (writes RAYPy_Simulation_* output)
#   eval_*.py        -> an analysis/plot of a simulation's output
#   anything else    -> a standalone demo (diodes, dipole, rml, runner, rayx, ...)
#
# Usage:
#   ./run_all_examples.sh                 # run EVERYTHING (sims + evals + demos)
#   ./run_all_examples.sh --simulation    # only simulation_*.py
#   ./run_all_examples.sh --eval          # only eval_*.py (needs existing output)
#   ./run_all_examples.sh --demo          # only the standalone demo scripts
#   ./run_all_examples.sh --simulation --eval   # any combination composes
#   ./run_all_examples.sh -v|--verbose    # stream script output to the terminal
#
# No timeout: examples run to completion.

set -uo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

VERBOSE=false
RUN_SIM=false
RUN_EVAL=false
RUN_DEMO=false
RUN_RAYUI_ANALYSIS=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -v|--verbose) VERBOSE=true; shift ;;
        --simulation|--simulations|--sim) RUN_SIM=true; shift ;;
        --eval|--evals) RUN_EVAL=true; shift ;;
        --demo|--demos|--other|--misc) RUN_DEMO=true; shift ;;
        --rayui_analysis|--rayui-analysis) RUN_RAYUI_ANALYSIS=true; shift ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  (no flag)        Run EVERYTHING: simulations, evals and demos"
            echo "  --simulation     Run only simulation_*.py scripts"
            echo "  --eval           Run only eval_*.py scripts (assumes output exists)"
            echo "  --demo           Run only standalone demo scripts (not sim/eval)"
            echo "  --simulation --eval --demo   Any combination composes"
            echo "  --rayui_analysis Also run simulation_analysis_by_RAY-UI.py (skipped by default)"
            echo "  -v, --verbose    Stream script output to the terminal"
            echo "  -h, --help       Show this help message"
            exit 0 ;;
        *) echo "Unknown option: $1"; echo "Use -h for help"; exit 1 ;;
    esac
done

# Default: run all three categories.
if [[ "$RUN_SIM" == false && "$RUN_EVAL" == false && "$RUN_DEMO" == false ]]; then
    RUN_SIM=true
    RUN_EVAL=true
    RUN_DEMO=true
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EXAMPLES_DIR="$SCRIPT_DIR"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# shellcheck disable=SC1091
source "$PROJECT_ROOT/.venv/bin/activate"

PASSED=0
FAILED=0
PASSED_LIST=""
FAILED_LIST=""
TIMING_LIST=""

echo -e "${BLUE}========== RUNNING EXAMPLES ==========${NC}"
echo -e "${BLUE}Started at:   $(date)${NC}"
echo -e "${BLUE}Examples dir: $EXAMPLES_DIR${NC}"
echo -e "${BLUE}Simulations: $RUN_SIM   Evals: $RUN_EVAL   Demos: $RUN_DEMO   RAY-UI analysis: $RUN_RAYUI_ANALYSIS   Verbose: $VERBOSE${NC}"
echo -e "${BLUE}No timeout - examples run to completion${NC}"
echo ""

# run_script <path> <kind>
run_script() {
    local script="$1" kind="$2"
    local name elapsed
    name="$(basename "$(dirname "$script")")/$(basename "$script")"

    local t_start t_end
    t_start=$(date +%s)

    if [[ "$VERBOSE" == true ]]; then
        echo -e "${BLUE}--- [$kind] $name ---${NC}"
        if python "$script"; then
            t_end=$(date +%s); elapsed=$((t_end - t_start))
            echo -e "${GREEN}✓ $name PASSED (${elapsed}s)${NC}"; echo ""
            PASSED=$((PASSED + 1))
            PASSED_LIST="$PASSED_LIST\n  ✓ [$kind] $name"
            TIMING_LIST="$TIMING_LIST\n  ${elapsed}s  [$kind] $name"
        else
            t_end=$(date +%s); elapsed=$((t_end - t_start))
            echo -e "${RED}✗ $name FAILED (exit $?, ${elapsed}s)${NC}"; echo ""
            FAILED=$((FAILED + 1))
            FAILED_LIST="$FAILED_LIST\n  ✗ [$kind] $name"
            TIMING_LIST="$TIMING_LIST\n  ${elapsed}s  [$kind] $name  FAILED"
        fi
    else
        echo -n "[$kind] $name ... "
        if python "$script" > /tmp/example_output.log 2>&1; then
            t_end=$(date +%s); elapsed=$((t_end - t_start))
            echo -e "${GREEN}PASSED (${elapsed}s)${NC}"
            PASSED=$((PASSED + 1))
            PASSED_LIST="$PASSED_LIST\n  ✓ [$kind] $name"
            TIMING_LIST="$TIMING_LIST\n  ${elapsed}s  [$kind] $name"
        else
            t_end=$(date +%s); elapsed=$((t_end - t_start))
            echo -e "${RED}FAILED (exit $?, ${elapsed}s)${NC}"
            echo -e "${RED}--- last 10 lines ---${NC}"
            tail -10 /tmp/example_output.log | sed 's/^/  /'
            echo ""
            FAILED=$((FAILED + 1))
            FAILED_LIST="$FAILED_LIST\n  ✗ [$kind] $name"
            TIMING_LIST="$TIMING_LIST\n  ${elapsed}s  [$kind] $name  FAILED"
        fi
    fi
}

# Every folder that holds at least one .py (excluding generated output/caches).
# Paths contain no spaces.
FOLDERS=$(find "$EXAMPLES_DIR" -name '*.py' \
    -not -path '*/RAYPy_Simulation_*/*' -not -path '*/__pycache__/*' -print \
    | xargs -n1 dirname | sort -u)

if [[ -z "$FOLDERS" ]]; then
    echo -e "${RED}No example scripts found under $EXAMPLES_DIR${NC}"
    exit 1
fi

for folder in $FOLDERS; do
    # 1) simulations
    if [[ "$RUN_SIM" == true ]]; then
        for s in "$folder"/simulation_*.py; do
            [[ -e "$s" ]] || continue
            if [[ "$(basename "$s")" == "simulation_analysis_by_RAY-UI.py" && "$RUN_RAYUI_ANALYSIS" == false ]]; then
                continue
            fi
            run_script "$s" sim
        done
    fi
    # 2) evals (after their simulation, so they read fresh output)
    if [[ "$RUN_EVAL" == true ]]; then
        for e in "$folder"/eval_*.py; do
            [[ -e "$e" ]] && run_script "$e" eval
        done
    fi
    # 3) demos: every other .py in the folder
    if [[ "$RUN_DEMO" == true ]]; then
        for d in "$folder"/*.py; do
            [[ -e "$d" ]] || continue
            case "$(basename "$d")" in
                simulation_*|eval_*) ;;        # already handled above
                *) run_script "$d" demo ;;
            esac
        done
    fi
done

echo ""
echo -e "${BLUE}========== SUMMARY ==========${NC}"
echo -e "${GREEN}Passed: $PASSED${NC}"
echo -e "${RED}Failed: $FAILED${NC}"
if [[ $PASSED -gt 0 ]]; then echo -e "${GREEN}Passed:${NC}$(echo -e "$PASSED_LIST")"; fi
if [[ $FAILED -gt 0 ]]; then echo -e "${RED}Failed:${NC}$(echo -e "$FAILED_LIST")"; fi
echo ""
echo -e "${BLUE}Timing:${NC}$(echo -e "$TIMING_LIST")"
echo ""
echo -e "${BLUE}Completed at: $(date)${NC}"

[[ $FAILED -gt 0 ]] && exit 1 || exit 0
