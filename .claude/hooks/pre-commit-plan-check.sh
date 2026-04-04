#!/usr/bin/env bash
# ============================================================================
# PreToolUse hook: Ensure future_memories plan exists before committing code
# ============================================================================
# Fires on Bash tool calls that look like git commits. If there are staged
# changes to source files (not just docs/session_logs), verifies that a
# future_memories plan file exists. Blocks (exit 2) if not.
# ============================================================================

set -uo pipefail

INPUT=$(cat)
COMMAND=$(echo "$INPUT" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(data.get('tool_input', {}).get('command', ''))
" 2>/dev/null)

# Only intercept git commit commands
if ! echo "$COMMAND" | grep -qE 'git\s+commit'; then
    exit 0
fi

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

# Check if there's a future_memories plan file
PLAN_EXISTS=$(ls "$PROJECT_ROOT/future_memories/"*-plan.md 2>/dev/null | head -1)

if [ -z "$PLAN_EXISTS" ]; then
    # Check if the commit includes source code changes (not just docs/logs)
    STAGED=$(git -C "$PROJECT_ROOT" diff --cached --name-only 2>/dev/null || true)
    HAS_CODE_CHANGES=false

    for file in $STAGED; do
        case "$file" in
            session_logs/*|future_memories/*|*.md|RELEASE_HISTORY.md)
                # These are docs/logs, not code — OK to commit without plan
                ;;
            *)
                HAS_CODE_CHANGES=true
                break
                ;;
        esac
    done

    if [ "$HAS_CODE_CHANGES" = true ]; then
        echo "Blocked: No future_memories plan file found." >&2
        echo "Before committing code changes, write a plan to future_memories/v{VERSION}-plan.md" >&2
        echo "and commit it first. This ensures session restoration if interrupted." >&2
        exit 2
    fi
fi

# --- Journal freshness check ---
# Warn (not block) if the journal file is missing or stale during code commits
LATEST_JOURNAL=$(ls -t "$PROJECT_ROOT/session_logs/"*-journal.json 2>/dev/null | head -1)
if [ -n "$LATEST_JOURNAL" ]; then
    JOURNAL_AGE=$(( $(date +%s) - $(stat -c %Y "$LATEST_JOURNAL" 2>/dev/null || echo 0) ))
    if [ "$JOURNAL_AGE" -gt 1800 ]; then
        echo "[PRE-COMMIT] Warning: Journal file $(basename "$LATEST_JOURNAL") is $(( JOURNAL_AGE / 60 )) minutes old." >&2
        echo "Update the journal before committing." >&2
    fi
elif [ "${HAS_CODE_CHANGES:-false}" = true ]; then
    echo "[PRE-COMMIT] Warning: No journal file found. Write session_logs/v{VERSION}-journal.json." >&2
fi

exit 0
