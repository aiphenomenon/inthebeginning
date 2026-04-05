#!/usr/bin/env bash
# ============================================================================
# PostToolUse hook: Capture tool calls for journal logging
# ============================================================================
# Appends every tool call's parameters and output to a JSONL capture file.
# This runs automatically after every tool use, providing verbatim data
# that the journal protocol requires. Claude reads this file when writing
# the turn-by-turn journal, avoiding reconstructed/summarized entries.
#
# Output: session_logs/.tool_capture.jsonl (one JSON object per line)
# Non-blocking (exit 0 always) — journal capture must never block work.
# ============================================================================

set -uo pipefail

PROJECT_ROOT="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
CAPTURE_FILE="$PROJECT_ROOT/session_logs/.tool_capture.jsonl"

# Save stdin to temp file for reliable JSON handling
TMPFILE=$(mktemp)
cat > "$TMPFILE"

python3 - "$TMPFILE" "$CAPTURE_FILE" << 'PYEOF'
import json, sys, os
from datetime import datetime, timezone

tmpfile = sys.argv[1]
capture_file = sys.argv[2]

try:
    with open(tmpfile) as f:
        data = json.load(f)
except Exception:
    sys.exit(0)
finally:
    os.unlink(tmpfile)

tool_name = data.get("tool_name", "unknown")
tool_input = data.get("tool_input", {})
tool_response = data.get("tool_response", {})
tool_use_id = data.get("tool_use_id", "")

# Truncation: cap large string fields at 12000 chars / 100 lines
# to match journal protocol limits.
def truncate_str(v, max_chars=12000, max_lines=100):
    if not isinstance(v, str):
        return v, False
    lines = v.split("\n")
    truncated = False
    if len(lines) > max_lines:
        v = "\n".join(lines[:max_lines])
        truncated = True
    if len(v) > max_chars:
        v = v[:max_chars]
        truncated = True
    return v, truncated

def truncate_dict(d):
    """Truncate large string values in a dict. Returns (dict, was_truncated)."""
    if not isinstance(d, dict):
        return d, False
    any_truncated = False
    for key in list(d.keys()):
        val = d[key]
        if isinstance(val, str) and len(val) > 500:
            d[key], was_t = truncate_str(val)
            if was_t:
                any_truncated = True
    return d, any_truncated

response_copy = dict(tool_response) if isinstance(tool_response, dict) else {}
input_copy = dict(tool_input) if isinstance(tool_input, dict) else {}

_, resp_truncated = truncate_dict(response_copy)
_, inp_truncated = truncate_dict(input_copy)

# Build capture entry
now = datetime.now(timezone.utc)
entry = {
    "ts": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
    "tool": tool_name,
    "id": tool_use_id,
    "input": input_copy,
    "response": response_copy,
    "input_truncated": inp_truncated,
    "response_truncated": resp_truncated,
}

# Append to JSONL (atomic-ish: write line then flush)
try:
    os.makedirs(os.path.dirname(capture_file), exist_ok=True)
    with open(capture_file, "a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
except Exception:
    pass  # Never fail — journal capture is best-effort

PYEOF

exit 0
