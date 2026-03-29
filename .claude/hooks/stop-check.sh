#!/usr/bin/env bash
# ============================================================================
# Stop hook: Verify housekeeping before ending a turn
# ============================================================================
# Checks for uncommitted changes and missing session logs. If critical items
# are found, outputs a reason for Claude to continue working (exit 2 blocks
# the stop). Lightweight checks only — no test runs here.
# ============================================================================

set -uo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ISSUES=""

# 1. Check for uncommitted changes (staged or unstaged, excluding untracked)
UNCOMMITTED=$(git -C "$PROJECT_ROOT" diff --stat HEAD 2>/dev/null)
STAGED=$(git -C "$PROJECT_ROOT" diff --cached --stat 2>/dev/null)

if [ -n "$UNCOMMITTED" ] || [ -n "$STAGED" ]; then
    ISSUES="${ISSUES}[STOP-CHECK] Uncommitted changes detected. Commit and push before ending.\n"
fi

# 2. Check for unpushed commits (warning only — push may require auth setup)
UPSTREAM=$(git -C "$PROJECT_ROOT" rev-parse --abbrev-ref '@{upstream}' 2>/dev/null)
if [ -n "$UPSTREAM" ]; then
    UNPUSHED=$(git -C "$PROJECT_ROOT" log "$UPSTREAM"..HEAD --oneline 2>/dev/null)
    if [ -n "$UNPUSHED" ]; then
        echo "[STOP-CHECK] Warning: unpushed commits detected. Push when auth is available."
    fi
fi

# 3. Check that a session log exists for this session
LATEST_SESSION=$(ls -t "$PROJECT_ROOT/session_logs/"*.md 2>/dev/null | head -1)
if [ -z "$LATEST_SESSION" ]; then
    ISSUES="${ISSUES}[STOP-CHECK] No session log found. Generate session_logs/v{VERSION}-session.md.\n"
fi

if [ -n "$ISSUES" ]; then
    echo -e "$ISSUES" >&2
    echo "Complete the items above before finishing." >&2
    exit 2
fi

exit 0
