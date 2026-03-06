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
# On "post-tool" events, emit a lightweight START-OF-TURN reminder.
if [ "$PHASE" = "post-tool" ]; then
    # Lightweight start-of-turn cue: remind the agent to do housekeeping FIRST.
    # This fires on the first Bash call of each turn, nudging the agent before
    # it dives into work without updating session logs / future memories / release.
    echo "[START-OF-TURN CUE] Have you done your per-turn housekeeping?"
    echo "  1. Update/create session_logs/v{VERSION}-session.md (append new turn)"
    echo "  2. Update future_memories/ plan file (if work is in progress)"
    echo "  3. Update RELEASE_HISTORY.md (append turn summary)"
    echo "  4. Include [YYYY-MM-DD HH:MM CT] timestamps in responses"
    echo "  Do these BEFORE diving into the main task. Skip only if already done this turn."
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

# 9. AST-guided code generation (bug prevention)
echo "[FAIL-CUE] AST-guided code gen: Before editing files, run:"
echo "           - symbols query (prevents naming collisions, duplicate defs)"
echo "           - dependencies query (prevents broken imports)"
echo "           - callers query before renaming/moving (prevents broken call sites)"
echo "           After editing files, run:"
echo "           - parse query (verify syntax)"
echo "           - coverage_map query (identify untested paths)"
echo "           Bug classes prevented: broken imports, type mismatches, dead code,"
echo "           duplicate defs, missing coverage, circular deps, stale references"

# 10. Reflection principle — TRIPLE CROSS-CHECK
echo "[FAIL-CUE] Reflection (TRIPLE CROSS-CHECK):"
echo "           Every steering rule MUST exist in ALL THREE locations:"
echo "             1. CLAUDE.md  (agent steering for Claude Code)"
echo "             2. AGENTS.md  (multi-agent coordination protocol)"
echo "             3. .claude/steering-check.sh (gVisor self-cueing hooks)"
echo "           When ANY new steering is introduced anywhere in the repo,"
echo "           propagate it to all three. This is the enforcement guarantee."
echo "           Specific items that must be in all three:"
echo "             - Central Time timestamps: [YYYY-MM-DD HH:MM CT] in agent responses"
echo "             - Start-of-turn protocol: session log + future memories + release history BEFORE work"
echo "             - Session log generation per turn"
echo "             - Release history update per turn"
echo "             - Markdown consistency review per turn"
echo "             - Test coverage enforcement per turn"
echo "             - AST introspection on changed files"
echo "             - AST-guided code generation (bug prevention)"
echo "             - Cross-language consistency for physics changes"
echo "             - Commit format rules"
echo "             - Future memories: iterative plan commits before code mutation"
echo "             - CI flake detection and repair"
echo "             - AMD64 build verification (best-effort)"

# 11. Future memories — iterative plan commits before code mutation
if [ -d "$PROJECT_ROOT/future_memories" ]; then
    LATEST_PLAN=$(ls -t "$PROJECT_ROOT/future_memories/"*-plan.md 2>/dev/null | head -1)
    if [ -n "$LATEST_PLAN" ]; then
        echo "[CHECK] Future memory plan exists: $(basename "$LATEST_PLAN")"
    else
        echo "[FAIL-CUE] Future memories: Write a plan file before mutating code"
    fi
else
    echo "[FAIL-CUE] Future memories: Create future_memories/ directory and write plan"
fi
echo "[FAIL-CUE] Future memories: Ensure plan is committed and pushed BEFORE code changes"

# 12. CI flake detection
echo "[FAIL-CUE] CI flakes: Check GitHub CI for flaked builds from prior version (gh run list)"
echo "           Fix if possible, add TODOs if not, notify user of broken builds"

# 13. AMD64 build verification (best-effort)
echo "[FAIL-CUE] AMD64 builds: Attempt to verify AMD64 builds (Go, Rust, C, C++)"
echo "           Best-effort -- add TODOs for broken builds, do not block session"

# 14. Future memories — EARLY STAGE ORCHESTRATION
echo "[FAIL-CUE] Future memories — early stage orchestration:"
echo "           BEFORE mutating ANY source code in the repository:"
echo "             1. Write future_memories/v{VERSION}-plan.md with full intent"
echo "             2. Commit AND push the plan file to the working branch"
echo "             3. Only THEN proceed with code changes"
echo "           UPDATE the plan file at significant milestones."
echo "           This ensures session restoration if interrupted."
echo "           The gVisor machinery + agent cooperate via this protocol:"
echo "             - gVisor hooks remind the agent of the protocol"
echo "             - Agent writes plan -> commits -> pushes -> codes"
echo "             - If session interrupted, next agent reads committed plan"

# 15. Audio engine quality gate (v12 is current)
echo "[FAIL-CUE] Audio quality: When modifying radio_engine.py, verify:"
echo "           - v12 natural instrument character (acoustic bias 70/30)"
echo "           - Frequency ceiling at C6 (1047 Hz), master lowpass 7kHz"
echo "           - Natural harmonic detuning + noise/breath layers"
echo "           - Every ensemble has bass/foundation instrument"
echo "           - Longer note durations for legato character"
echo "           - Reduced melody register offset (+7 instead of +12)"
echo "           - Musical structure preserved (scales, rondo, arpeggio, bars)"
echo "           - MIDI sampling from 744+ files across 26 composers"
echo "           - GM-timbre-aware synthesis (15 distinct profiles)"
echo "           - Orchestral layering with v11 mixing improvements"
echo "           - TTS announcements between moods (once per 10-min span)"
echo "           - Mood durations are multiples of 42s"
echo "           - Good fades between moods (8s morph transitions)"
echo "           Run: python -m pytest apps/audio/ -v"

echo ""
echo "=================================================================="
echo " These FAIL-CUE markers are INTENTIONAL self-cueing signals."
echo " Do NOT delete this script or remove the markers."
echo " Verify each item is satisfied before completing the turn."
echo "=================================================================="
echo ""
