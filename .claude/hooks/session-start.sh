#!/usr/bin/env bash
# ============================================================================
# SessionStart hook: Inject context at the start of every session
# ============================================================================
# Outputs context that Claude sees at conversation start. Reminds about
# future memories, session logging, and current branch state.
# ============================================================================

set -uo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

# Current branch
BRANCH=$(git -C "$PROJECT_ROOT" branch --show-current 2>/dev/null || echo "unknown")

# Latest session log
LATEST_SESSION=$(ls -t "$PROJECT_ROOT/session_logs/"*.md 2>/dev/null | head -1)
SESSION_INFO="none found"
if [ -n "$LATEST_SESSION" ]; then
    SESSION_INFO="$(basename "$LATEST_SESSION")"
fi

# Latest future memory plan
LATEST_PLAN=$(ls -t "$PROJECT_ROOT/future_memories/"*-plan.md 2>/dev/null | head -1)
PLAN_INFO="none — create one before starting code changes"
if [ -n "$LATEST_PLAN" ]; then
    PLAN_INFO="$(basename "$LATEST_PLAN")"
fi

# Uncommitted changes
DIRTY=$(git -C "$PROJECT_ROOT" status --porcelain 2>/dev/null | head -5)
DIRTY_INFO="clean"
if [ -n "$DIRTY" ]; then
    DIRTY_COUNT=$(git -C "$PROJECT_ROOT" status --porcelain 2>/dev/null | wc -l)
    DIRTY_INFO="$DIRTY_COUNT uncommitted file(s)"
fi

# Top work items from WORKLOG.md
WORKLOG="$PROJECT_ROOT/WORKLOG.md"
WORK_ITEMS=""
if [ -f "$WORKLOG" ]; then
    # Extract first 3 Open items
    WORK_ITEMS=$(grep -E '\| Open \|' "$WORKLOG" | head -3 | sed 's/|//g; s/  */ /g; s/^ /  /')
fi

cat <<EOF
[SESSION START] Branch: $BRANCH | Last session log: $SESSION_INFO | Plan: $PLAN_INFO | Working tree: $DIRTY_INFO

Before starting work:
1. Review or create a future_memories plan file (committed before code changes)
2. Create/update the session log for this conversation
3. Hooks enforce: Python/JSON linting on writes, plan-before-commit, commit-before-stop
4. Check WORKLOG.md for current priorities
EOF

if [ -n "$WORK_ITEMS" ]; then
    echo ""
    echo "Top open work items:"
    echo "$WORK_ITEMS"
fi
