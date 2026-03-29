#!/usr/bin/env bash
# ============================================================================
# PostToolUse hook: Nudge about running tests after build commands
# ============================================================================
# After certain Bash commands (make, cargo build, go build, npm run build),
# emits a lightweight reminder to run the corresponding test suite.
# Non-blocking — just informational output.
# ============================================================================

set -uo pipefail

INPUT=$(cat)
COMMAND=$(echo "$INPUT" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(data.get('tool_input', {}).get('command', ''))
" 2>/dev/null)

# Match build-like commands and suggest corresponding test commands
if echo "$COMMAND" | grep -qE 'cargo\s+build'; then
    echo "[TEST NUDGE] Rust built — run 'cargo test' to verify"
elif echo "$COMMAND" | grep -qE 'go\s+build'; then
    echo "[TEST NUDGE] Go built — run 'go test ./...' to verify"
elif echo "$COMMAND" | grep -qE 'make(\s|$)' && ! echo "$COMMAND" | grep -qE 'make\s+test'; then
    echo "[TEST NUDGE] C/C++ built — run 'make test' or 'ctest' to verify"
elif echo "$COMMAND" | grep -qE 'npm\s+run\s+build'; then
    echo "[TEST NUDGE] TypeScript built — run 'npm test' to verify"
fi

exit 0
