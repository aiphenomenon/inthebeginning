# V39 Plan — Journal Compression Logic Finalization

## Date: 2026-04-04

## Goal
Finalize the journal cut/compression lifecycle so it handles version
increments correctly. On each cut, compress ALL prior uncompressed journals
(not just the immediately previous one), update their session log links,
and leave only the current cut's journal uncompressed.

## Deliverables
1. Retroactive v38 cut (session log + cut metadata)
2. CLAUDE.md clarification: compress all prior, not just previous
3. v39 journal capturing this session
4. Compress v37 + v38 journals, update their session log links
5. v39 session log + RELEASE_HISTORY entries for v38 and v39
