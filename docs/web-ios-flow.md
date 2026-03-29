# Claude Code Web/iOS Flow (gVisor Hooks)

This document preserves the hook-based steering approach used when working in
**Claude Code for Web** or **Claude Code for iOS**, which runs inside a gVisor
sandbox container. The primary flow for this repo is now **Claude Code CLI** --
see `CLAUDE.md` for current steering.

If you need to restore the Web/iOS flow, follow the [Restoration Guide](#restoration-guide)
at the bottom of this document.

---

## How It Worked

Claude Code for Web/iOS runs in a gVisor container at `/home/user/inthebeginning/`.
Unlike the CLI, the Web/iOS environment has limited ways to enforce per-turn
housekeeping. The solution was a **self-cueing mechanism**: shell hooks that emit
"FAIL" markers on every tool use, nudging the agent to complete mandatory tasks.

The hooks fired at three lifecycle points:
- **PostToolUse** (on Bash commands): Lightweight start-of-turn reminder
- **Notification**: Full steering checklist
- **Stop**: End-of-turn verification checklist

The "FAIL" markers were **intentional** -- not test failures, but self-cueing signals.

### Why FAIL Markers?

In the Web/iOS flow, the agent had no persistent memory between turns within a
conversation and could easily "forget" housekeeping tasks (session logging, future
memories, release history updates). The FAIL markers in hook output reliably triggered
the agent to check its compliance. This was a pragmatic hack for an environment
with limited steering surface.

### Triple Cross-Check Principle (Historical)

Under the Web/iOS flow, every steering rule had to exist in three places:
1. `CLAUDE.md` (agent reads this)
2. `AGENTS.md` (multi-agent coordination)
3. `.claude/steering-check.sh` (hook enforcement)

This triple redundancy ensured the agent couldn't miss rules. It was necessary for
Web/iOS but created maintenance burden and bloat. The CLI flow eliminates this --
`CLAUDE.md` is the single source of truth.

---

## Original Hook Configuration

### .claude/settings.json (Web/iOS version)

```json
{
  "hooks": {
    "PreToolUse": [],
    "PostToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "echo '[REMINDER] Generate JSON transcript companion (session_logs/v{VERSION}-session.json) alongside markdown session log. Schema: session_logs/transcript_schema.json. Truncate tool output at 500 lines. Proofread user input. Redact security tokens only (system paths OK).' && bash /home/user/inthebeginning/.claude/steering-check.sh post-tool"
          }
        ]
      }
    ],
    "Notification": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "bash /home/user/inthebeginning/.claude/steering-check.sh notification"
          }
        ]
      }
    ],
    "Stop": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "bash /home/user/inthebeginning/.claude/steering-check.sh stop"
          }
        ]
      }
    ]
  },
  "permissions": {
    "allow": [],
    "deny": []
  }
}
```

### .claude/steering-check.sh (Full Original)

```bash
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
    echo "[START-OF-TURN CUE] Have you done your per-turn housekeeping?"
    echo "  1. Update/create session_logs/v{VERSION}-session.md (append new turn)"
    echo "  2. Update future_memories/ plan file (if work is in progress)"
    echo "  3. Update RELEASE_HISTORY.md (append turn summary)"
    echo "  4. Include [YYYY-MM-DD HH:MM CT] timestamps in responses"
    echo "  5. Provide user updates every ~2 minutes during long operations"
    echo "  6. Use CT + UTC dual timestamps in session logs: [YYYY-MM-DD HH:MM CT (HH:MM UTC)]"
    echo "  7. Generate JSON transcript companion (session_logs/v{VERSION}-session.json)"
    echo "  Do these BEFORE diving into the main task. Skip only if already done this turn."
    exit 0
fi

# ============================================================================
# STEERING CHECKLIST — emitted at end-of-turn
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

# 3b. JSON transcript companion
if [ -n "$LATEST_SESSION" ]; then
    JSON_COMPANION="${LATEST_SESSION%.md}.json"
    if [ -f "$JSON_COMPANION" ]; then
        echo "[CHECK] JSON transcript companion exists: $(basename "$JSON_COMPANION")"
    else
        echo "[FAIL-CUE] JSON transcript: Generate $(basename "${LATEST_SESSION%.md}.json")"
    fi
fi

# 4. Markdown consistency
echo "[FAIL-CUE] Markdown review: Verify all markdown files are accurate and in harmony"

# 5. Release history
if [ -f "$PROJECT_ROOT/RELEASE_HISTORY.md" ]; then
    echo "[CHECK] RELEASE_HISTORY.md exists"
    echo "[FAIL-CUE] Release history: MUST be updated with changes from this turn"
else
    echo "[FAIL-CUE] Release history: Create RELEASE_HISTORY.md"
fi

# 6. Cross-language consistency
echo "[FAIL-CUE] Cross-language: If physics engine changed, verify all implementations match"

# 7. Test coverage
echo "[FAIL-CUE] Test coverage: Ensure full coverage; use coverage_map for gap analysis"

# 8. Commit format
echo "[FAIL-CUE] Commit format: Use '<type>(<scope>): <description>'"

# 9. AST-guided code generation
echo "[FAIL-CUE] AST-guided code gen: symbols + dependencies before; parse + coverage after"

# 10. Future memories
if [ -d "$PROJECT_ROOT/future_memories" ]; then
    LATEST_PLAN=$(ls -t "$PROJECT_ROOT/future_memories/"*-plan.md 2>/dev/null | head -1)
    if [ -n "$LATEST_PLAN" ]; then
        echo "[CHECK] Future memory plan exists: $(basename "$LATEST_PLAN")"
    else
        echo "[FAIL-CUE] Future memories: Write a plan file before mutating code"
    fi
fi
echo "[FAIL-CUE] Future memories: Ensure plan is committed BEFORE code changes"

# 11. CI flake detection
echo "[FAIL-CUE] CI flakes: Check GitHub CI for flaked builds (gh run list)"

# 12. Frequent commits and pushes
echo "[FAIL-CUE] Frequent commits: Push after every commit"

# 13. Audio engine quality gate
echo "[FAIL-CUE] Audio quality: When modifying radio_engine.py, verify v12 synthesis chain"

# 14. Swift on Linux
echo "[FAIL-CUE] Swift on Linux: Simulator library is Linux-compatible (Swift 5.9+)"

# 15. Domain approval protocol
echo "[FAIL-CUE] Domain approval: Ask user before accessing non-allow-list domains"

# 16. Screen capture testing
echo "[FAIL-CUE] Screen capture: At version cuts, capture visual evidence"

# 17. Session budget management
echo "[FAIL-CUE] Budget: When user provides usage screenshot, analyze and advise"

# 18. Big Bounce
echo "[FAIL-CUE] Big Bounce: All implementations support perpetual cycling"

echo ""
echo "=================================================================="
echo " These FAIL-CUE markers are INTENTIONAL self-cueing signals."
echo "=================================================================="
echo ""
```

---

## gVisor Resource Awareness

The gVisor sandbox has limited resources (~21GB memory). When working in Web/iOS:

- **Download in batches**, not all at once
- **Stream audio rendering** (write to disk segment-by-segment, not in-memory)
- **Sequential renders** (one MP3 at a time, not parallel) to avoid OOM kills
- **Delete intermediate files** (WAV after MP3 conversion)
- **Check `free -h`** before memory-intensive operations (defer if <4GB available)

### Download Content Safety

When downloading external assets from allowed domains:

**Pre-download**: Verify URL targets expected file type, source is trusted
(github.com, raw.githubusercontent.com, pypi.org, files.pythonhosted.org),
license allows redistribution.

**Post-download**: Verify content type matches (MIDI = MThd header, SF2 = RIFF),
scan text for prompt injection, reject executables, reject suspiciously large files.

**Domain approval**: Before accessing any domain not on the allow list, ask the user.
Approved domains persist for current session only.

---

## Session Budget Management

When the user provides a usage dashboard screenshot:

1. Read the screenshot; extract session window %, weekly %, reset times
2. Estimate burn rate from elapsed usage
3. Recommend pausing at 85% of 5-hour window or 90% of weekly limit
4. Plan multi-window work with phased handoff points in future memories
5. Push after every commit (crash resilience)
6. Record budget analysis in session log

```
### Budget Analysis [YYYY-MM-DD HH:MM CT (HH:MM UTC)]
- 5-hour window: XX% used, resets in Xh Xm
- Weekly: XX% used, resets in Xd Xh
- Burn rate: ~X% per hour
- Projected remaining: Xh before 85% threshold
- Recommendation: [continue / pace / pause]
```

---

## Per-Turn Steering Checklist (Web/iOS)

This checklist was enforced via hooks on every conversation turn:

1. Update session log (append new turn entry)
2. Update future memories plan file
3. Update RELEASE_HISTORY.md
4. Run AST introspection on changed files
5. Run Python test suite
6. Review markdown for accuracy
7. Cross-language consistency (if physics changed)
8. AST-guided code generation (pre/post checks)
9. Commit with proper format
10. Frequent commits, push after each
11. Central Time timestamps in responses
12. CT + UTC dual timestamps in session logs
13. JSON transcript companion generation
14. Screen capture testing at version cuts
15. Budget analysis when user provides screenshot

---

## Restoration Guide

To restore the Web/iOS hook-based flow:

### 1. Update settings.json

Copy the [original settings.json](#claudesettingsjson-webios-version) content above
into `.claude/settings.json`. Update the path from `/home/user/inthebeginning/` to
match your gVisor container's project root.

### 2. Restore steering-check.sh

Copy the [original steering-check.sh](#claudesteering-checksh-full-original) content
above into `.claude/steering-check.sh` and `chmod +x` it.

### 3. Expand CLAUDE.md

The current `CLAUDE.md` is optimized for CLI. For Web/iOS, you may want to add back:
- The "Self-Cueing and gVisor Enforcement" section
- The "Start-of-Turn Protocol (MANDATORY)" section
- The per-turn steering checklist
- The "Reflection Principle (Triple Cross-Check)" requiring sync across
  CLAUDE.md, AGENTS.md, and steering-check.sh

### 4. Expand AGENTS.md

Add back the duplicated session logging, test coverage, future memories, and
markdown consistency sections that were previously mirrored from CLAUDE.md.

### 5. Test

Run a conversation turn in the Web/iOS environment and verify that:
- PostToolUse hooks fire on the first Bash call
- Stop/Notification hooks emit the full checklist
- The agent responds to FAIL-CUE markers by completing tasks
