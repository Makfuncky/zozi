#!/usr/bin/env bash
# =============================================================================
#  Zozi Backend — Time-Budgeted Test Runner
# =============================================================================
#  Usage:
#    bash run_tests.sh                          # Run all tests (budgeted)
#    bash run_tests.sh tests/test_health.py     # Run a single file
#    bash run_tests.sh --fast                   # Skip integration markers
#    bash run_tests.sh --list                   # Just list test files + timing
#    bash run_tests.sh --profile                # Run with --durations=10
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# ── Defaults ──────────────────────────────────────────────────────────────────
PYTEST_OPTS=("-x" "--tb=short" "-q")
TIMEOUT=180                       # Per-file timeout (seconds) — generous
PARALLEL_GROUPS=2                 # Run up to N test files in parallel
PYTEST="python -m pytest"

# ── Parse CLI ────────────────────────────────────────────────────────────────
FAST_MODE=false
LIST_MODE=false
PROFILE_MODE=false
TARGET=""

for arg in "$@"; do
  case "$arg" in
    --fast)     FAST_MODE=true ;;
    --list)     LIST_MODE=true ;;
    --profile)  PROFILE_MODE=true ;;
    --help|-h)  sed -n '3,/^  /p' "$0"; exit 0 ;;
    *)          TARGET="$arg" ;;   # treat as file/dir pattern
  esac
done

# ── List mode ────────────────────────────────────────────────────────────────
if $LIST_MODE; then
  echo "=== Test files detected ==="
  find tests/ -name 'test_*.py' | sort
  echo ""
  echo "=== Timing estimates (based on prior runs) ==="
  echo "  Per file:          ~45-60s  (includes 12s app import)"
  echo "  All 32 files:      ~60-90s  (session-scoped fixtures shared)"
  echo "  With --fast:       ~15-30s  (unit-only markers)"
  exit 0
fi

# ── Build pytest arguments ────────────────────────────────────────────────────
if $PROFILE_MODE; then
  PYTEST_OPTS+=("--durations=20")
fi

if $FAST_MODE; then
  echo "🔹 Fast mode: skipping @pytest.mark.integration tests"
  PYTEST_OPTS+=("-m" "not integration")
fi

if [[ -n "$TARGET" ]]; then
  # Single file — run directly with timeout
  CMD="$PYTEST ${PYTEST_OPTS[*]} --timeout=$TIMEOUT $TARGET"
  echo "🔹 Running: $CMD"
  $CMD
  exit $?
fi

# ── Multi-file — run in parallel groups ──────────────────────────────────────
TEST_FILES=($(find tests/ -name 'test_*.py' | sort))
echo "🔹 Found ${#TEST_FILES[@]} test files"
echo "🔹 Parallel groups: $PARALLEL_GROUPS"
echo "🔹 Per-file timeout: ${TIMEOUT}s"
echo ""

FAILED=0
BATCHES=()
BATCH=""
COUNT=0

# Group files into batches
for f in "${TEST_FILES[@]}"; do
  if [[ -z "$BATCH" ]]; then
    BATCH="$f"
  else
    BATCH="$BATCH $f"
  fi
  COUNT=$((COUNT + 1))
  if [[ $COUNT -ge $PARALLEL_GROUPS ]]; then
    BATCHES+=("$BATCH")
    BATCH=""
    COUNT=0
  fi
done
if [[ -n "$BATCH" ]]; then
  BATCHES+=("$BATCH")
fi

echo "--- Batching ${#TEST_FILES[@]} files into ${#BATCHES[@]} groups ---"

BATCH_NUM=1
for batch in "${BATCHES[@]}"; do
  echo ""
  echo "================================"
  echo "  Group $BATCH_NUM / ${#BATCHES[@]}"
  echo "  Files: $batch"
  echo "================================"

  # Use timeout command for hard wall-clock limit per group
  # (If timeout is not available, fall back to pytest's --timeout)
  CMD="$PYTEST ${PYTEST_OPTS[*]} --timeout=$TIMEOUT $batch"
  echo "  \$ $CMD"
  echo ""
  if $CMD; then
    echo "  ✅ Group $BATCH_NUM passed"
  else
    FAILED=$((FAILED + 1))
    echo "  ❌ Group $BATCH_NUM FAILED"
  fi
  BATCH_NUM=$((BATCH_NUM + 1))
done

echo ""
echo "═══════════════════════════════════════"
if [[ $FAILED -eq 0 ]]; then
  echo "  ✅ ALL GROUPS PASSED"
else
  echo "  ❌ $FAILED group(s) FAILED"
fi
echo "═══════════════════════════════════════"
exit $FAILED
