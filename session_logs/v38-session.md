# V38 Session Log — Journal Compression Strategy Fix

## Date: 2026-04-04

---

### Summary

Updated the journal protocol so the latest cut's journal stays prettified and
uncompressed (browsable on GitHub), while all prior cuts get compressed to
`.tar.gz` on the next cut.

### What Was Done

1. **CLAUDE.md**: Revised "Cuts and Version Bumps" — latest journal stays
   uncompressed, previous cut's journal compressed on next cut, session log
   links updated to point to `.tar.gz`.

2. **v37-journal.json**: Decompressed from `.tar.gz` back to prettified JSON
   (it was the latest cut at the time).

3. **v37-session.md**: Updated link from `.tar.gz` to `.json`.

### Files Modified

| File | Action |
|------|--------|
| `CLAUDE.md` | Edited (compression strategy) |
| `session_logs/v37-journal.json` | Restored from tar.gz |
| `session_logs/v37-session.md` | Updated link |
| `session_logs/v38-journal.json` | Created (1 turn) |
| `session_logs/v38-session.md` | Created (this file) |

### Journal

Full turn-by-turn transcript: [v38-journal.json.tar.gz](v38-journal.json.tar.gz)
