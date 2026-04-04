#!/usr/bin/env python3
"""
Journal content validator for stop-check hook.

Validates the most recent *-journal.json file in session_logs/:
- Valid JSON matching journal_schema structure
- Required fields present in every turn
- assistant_text is non-empty and not a bracketed summary
- tool_calls present when tools were clearly used
- user_input has both raw and proofread fields

Exit codes:
  0 = valid
  1 = validation errors found (prints details to stderr)
  2 = no journal file found (not an error — stop-check handles this)
"""

import glob
import json
import os
import re
import sys


def find_latest_journal(project_root):
    """Find the most recently modified *-journal.json file."""
    pattern = os.path.join(project_root, "session_logs", "*-journal.json")
    files = glob.glob(pattern)
    if not files:
        sys.exit(2)  # No journal found — let stop-check handle it
    return max(files, key=os.path.getmtime)


def validate_journal(path):
    """Validate journal structure and content. Returns list of error strings."""
    errors = []

    # 1. Valid JSON
    try:
        with open(path) as f:
            j = json.load(f)
    except json.JSONDecodeError as e:
        return [f"Invalid JSON: {e}"]

    # 2. Top-level required fields
    for field in ("format_version", "session", "turns"):
        if field not in j:
            errors.append(f"Missing top-level field: {field}")

    if errors:
        return errors  # Can't continue without structure

    # 3. Session fields
    session = j.get("session", {})
    for field in ("session_id", "branch", "started_at", "previous_version"):
        if field not in session:
            errors.append(f"Missing session field: {field}")

    # 4. Per-turn validation
    turns = j.get("turns", [])
    if not turns:
        errors.append("Journal has no turns — write at least one turn before stopping")
        return errors

    for turn in turns:
        tn = turn.get("turn_number", "?")
        prefix = f"Turn {tn}"

        # Required fields
        for field in ("turn_number", "timestamp_ct", "timestamp_utc",
                       "user_input", "assistant_text", "tool_calls",
                       "files_modified", "files_read", "redactions"):
            if field not in turn:
                errors.append(f"{prefix}: missing required field '{field}'")

        # assistant_text checks
        text = turn.get("assistant_text", "")
        if not text or not text.strip():
            errors.append(f"{prefix}: assistant_text is empty")
        else:
            # Detect bracketed summaries: [text that looks like a summary]
            # First, strip out quoted/code-fenced content where brackets are
            # legitimate (backtick-wrapped, double-quoted references, code blocks)
            stripped = re.sub(r'`[^`]*`', '', text)           # inline code
            stripped = re.sub(r'"[^"]*"', '', stripped)        # double-quoted
            stripped = re.sub(r'```[\s\S]*?```', '', stripped) # code blocks
            bracket_pattern = r'\[([^\[\]]{15,200})\]'
            matches = re.findall(bracket_pattern, stripped)
            for match in matches:
                # Heuristic: if it contains action verbs typical of summaries
                summary_words = (
                    "updated", "created", "wrote", "edited", "implemented",
                    "added", "removed", "fixed", "modified", "compressed",
                    "retroactively", "finalized", "presented", "showed"
                )
                lower = match.lower()
                action_count = sum(1 for w in summary_words if w in lower)
                if action_count >= 2:
                    errors.append(
                        f"{prefix}: likely bracketed summary in assistant_text: "
                        f"\"[{match[:60]}{'...' if len(match) > 60 else ''}]\""
                    )

        # user_input checks
        ui = turn.get("user_input", {})
        if not ui.get("raw"):
            errors.append(f"{prefix}: user_input.raw is empty")
        if not ui.get("proofread"):
            errors.append(f"{prefix}: user_input.proofread is empty")

        # tool_calls structure
        for tc in turn.get("tool_calls", []):
            seq = tc.get("sequence", "?")
            tc_prefix = f"{prefix}, tool_call {seq}"
            if "tool" not in tc:
                errors.append(f"{tc_prefix}: missing 'tool' field")
            if "parameters" not in tc:
                errors.append(f"{tc_prefix}: missing 'parameters' field")
            if "result" not in tc:
                errors.append(f"{tc_prefix}: missing 'result' field")
            else:
                result = tc["result"]
                if "output" not in result:
                    errors.append(f"{tc_prefix}: missing 'result.output' field")
                if "truncated" not in result:
                    errors.append(f"{tc_prefix}: missing 'result.truncated' field")

    return errors


def main():
    project_root = os.environ.get(
        "CLAUDE_PROJECT_DIR",
        os.path.join(os.path.dirname(__file__), "..", "..")
    )
    project_root = os.path.abspath(project_root)

    path = find_latest_journal(project_root)
    errors = validate_journal(path)

    if errors:
        print(f"[JOURNAL-VALIDATE] {os.path.basename(path)} has {len(errors)} issue(s):", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
