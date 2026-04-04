# V37 Session Log — Turn-by-Turn Journal Protocol

## Date: 2026-04-04

---

### Summary

Designed and implemented a turn-by-turn conversation journaling protocol that
captures full conversation text and all tool calls verbatim. Replaces the ad-hoc
JSON transcript companion (format v1) with a structured, versioned, compressed
journal system (format v2).

### What Was Done

1. **Journal Schema** (`session_logs/journal_schema.json`): JSON Schema 2020-12
   defining the rolling journal format with per-turn writes, tool call capture,
   truncation rules (500 lines/60K chars → 100 lines/12K chars), and cut metadata.

2. **CLAUDE.md**: Replaced "JSON Transcript Companion" subsection with
   "Turn-by-Turn Journal Protocol" (~50 lines). Covers per-turn writes, truncation,
   redaction, cuts, version bumps, and compression.

3. **Pre-commit hook** (`.claude/hooks/pre-commit-plan-check.sh`): Added journal
   freshness warning — warns if journal is missing or >30 minutes stale during
   code commits. Non-blocking (warning only).

4. **Stop hook** (`.claude/hooks/stop-check.sh`): Added journal existence check —
   blocks session stop if no journal file (`.json` or `.tar.gz`) exists.

5. **First journal** (`session_logs/v37-journal.json.tar.gz`): 6-turn journal
   capturing this entire session including the design discussion and implementation.

### Key Design Decisions

- One cut = one version bump (no sub-cuts within a version)
- Journal uncompressed during work (crash recovery), tar.gz on cut
- No assistant_text cap; uniform truncation rules for all tool outputs
- Pre-commit warns; stop hook blocks
- Old transcript_schema.json untouched (clean break, new schema forward)
- Version numbering is solution-level, independent of sub-app versions

### Files Created/Modified

| File | Action |
|------|--------|
| `session_logs/journal_schema.json` | Created (211 lines) |
| `session_logs/v37-journal.json.tar.gz` | Created (6-turn journal, compressed) |
| `session_logs/v37-session.md` | Created (this file) |
| `CLAUDE.md` | Edited (+52 lines, -10 lines) |
| `.claude/hooks/pre-commit-plan-check.sh` | Edited (+13 lines) |
| `.claude/hooks/stop-check.sh` | Edited (+7 lines) |
| `future_memories/v37-plan.md` | Created |
| `RELEASE_HISTORY.md` | Updated (v0.37.0 entry) |

### Journal

Full turn-by-turn transcript: [v37-journal.json.tar.gz](v37-journal.json.tar.gz)
