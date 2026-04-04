# V37 Plan — Turn-by-Turn Journal Protocol

## Date: 2026-04-04

## Goal
Formalize turn-by-turn conversation journaling with full tool call capture.
Replace the ad-hoc JSON transcript companion with a structured, versioned,
compressed journal protocol.

## Deliverables
1. `session_logs/journal_schema.json` — JSON Schema for journal files
2. `CLAUDE.md` — replace JSON Transcript Companion with Journal Protocol section
3. `.claude/hooks/pre-commit-plan-check.sh` — add journal freshness warning
4. `.claude/hooks/stop-check.sh` — add journal existence blocker
5. `session_logs/v37-journal.json` → `v37-journal.json.tar.gz` — this session's journal
6. `session_logs/v37-session.md` — session log referencing the tar.gz
7. `RELEASE_HISTORY.md` — v0.37.0 entry

## Key Decisions
- One cut = one version bump (no sub-cuts)
- Journal uncompressed during work, tar.gz on cut
- Pre-commit hook warns; stop hook blocks
- No assistant_text cap; uniform truncation rules for all tool outputs
- Old transcript_schema.json untouched (clean break)
- Version numbering is solution-level, independent of sub-app versions
