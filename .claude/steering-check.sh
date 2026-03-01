#!/usr/bin/env bash
# ============================================================================
# gVisor Self-Cueing Mechanism — Steering Enforcement Script
# ============================================================================
#
# PURPOSE: This script is invoked by Claude Code hooks (PostToolUse, Stop,
# Notification) to emit reminders that enforce the steering rules defined
# in CLAUDE.md and AGENTS.md. The "FAIL" markers are INTENTIONAL. They
# serve as self-cueing signals to the agent. Do NOT delete them.
#
# IMPORTANT: This script is NOT a test suite. The word "FAIL" in the output
# is a cueing mechanism, not an actual test failure. It prompts the agent to
# verify it has completed all required steering tasks for the conversation turn.
#
# ============================================================================

set -euo pipefail

PHASE="${1:-unknown}"
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Only emit the full checklist on "stop" (end of turn) or "notification" events.
# On "post-tool" events, emit a lightweight reminder.
if [ "$PHASE" = "post-tool" ]; then
    # Lightweight: no output unless something is clearly wrong
    exit 0
fi

# ============================================================================
# STEERING CHECKLIST — emitted at end-of-turn
# ============================================================================
# Each item below is a required steering action per CLAUDE.md / AGENTS.md.
# The agent should verify each item before completing the conversation turn.
# ============================================================================

echo ""
echo "=================================================================="
echo " STEERING ENFORCEMENT CHECKLIST (gVisor Self-Cueing)"
echo "=================================================================="
echo ""

# 1. AST Introspection
if [ -d "$PROJECT_ROOT/ast_captures" ]; then
    echo "[CHECK] AST introspection: ast_captures/ exists"
else
    echo "[FAIL-CUE] AST introspection: Run AST introspection on changed files"
fi

# 2. Python test suite
echo "[FAIL-CUE] Python tests: Verify 'python -m pytest tests/ -v --tb=short' passes"

# 3. Session log
LATEST_SESSION=$(ls -t "$PROJECT_ROOT/session_logs/"*.md 2>/dev/null | head -1)
if [ -n "$LATEST_SESSION" ]; then
    echo "[CHECK] Session log exists: $(basename "$LATEST_SESSION")"
else
    echo "[FAIL-CUE] Session log: Generate session + transcript log in session_logs/"
fi

# 4. Markdown consistency
echo "[FAIL-CUE] Markdown review: Verify all markdown files are accurate and in harmony"

# 5. Release history — MUST be updated every conversation turn
if [ -f "$PROJECT_ROOT/RELEASE_HISTORY.md" ]; then
    echo "[CHECK] RELEASE_HISTORY.md exists"
    echo "[FAIL-CUE] Release history: RELEASE_HISTORY.md MUST be updated with changes from this turn"
    echo "           Add a new version entry (or update the current one) with:"
    echo "           - Summary of changes made this turn"
    echo "           - Agent activity (agents spawned, tests run)"
    echo "           - Files created/modified"
else
    echo "[FAIL-CUE] Release history: Create RELEASE_HISTORY.md with version entry for this turn"
fi

# 6. Cross-language consistency (if physics changes were made)
echo "[FAIL-CUE] Cross-language: If physics engine changed, verify all 15 implementations match"

# 7. Test coverage
echo "[FAIL-CUE] Test coverage: Ensure full test coverage; use coverage_map for gap analysis"

# 8. Commit format
echo "[FAIL-CUE] Commit format: Use '<type>(<scope>): <description>' with AST context"

# 9. Reflection principle — TRIPLE CROSS-CHECK
echo "[FAIL-CUE] Reflection (TRIPLE CROSS-CHECK):"
echo "           Every steering rule MUST exist in ALL THREE locations:"
echo "             1. CLAUDE.md  (agent steering for Claude Code)"
echo "             2. AGENTS.md  (multi-agent coordination protocol)"
echo "             3. .claude/steering-check.sh (gVisor self-cueing hooks)"
echo "           When ANY new steering is introduced anywhere in the repo,"
echo "           propagate it to all three. This is the enforcement guarantee."
echo "           Specific items that must be in all three:"
echo "             - Session log generation per turn"
echo "             - Release history update per turn"
echo "             - Markdown consistency review per turn"
echo "             - Test coverage enforcement per turn"
echo "             - AST introspection on changed files"
echo "             - Cross-language consistency for physics changes"
echo "             - Commit format rules"

echo ""
echo "=================================================================="
echo " These FAIL-CUE markers are INTENTIONAL self-cueing signals."
echo " Do NOT delete this script or remove the markers."
echo " Verify each item is satisfied before completing the turn."
echo "=================================================================="
echo ""
