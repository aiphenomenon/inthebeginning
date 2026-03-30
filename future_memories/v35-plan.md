# V35 Plan — Comprehensive Markdown Sweep

## Date: 2026-03-30

## Overview
Verify all 115+ markdown files against actual code/config state.
Fix stale paths, outdated commands, wrong versions, dead cross-refs.
Bump solution version to v0.35.0.

## Approach: Map-Reduce in 3 Rounds

### Round 1: MAP (5 parallel agents)
- A1: Top-level MDs + .claude/ + .github/
- A2: docs/ (25 MDs)
- A3: apps/ READMEs + source verification
- A4: deploy/ READMEs + structure
- A5: future_memories/ + session_logs/ (read-only, check cross-refs)

### Round 2: REDUCE (central apply)
- Collect issues, deduplicate, apply fixes in batches

### Round 3: VERIFY (single sweep)
- Confirm no remaining issues

## Steering Note
Markdown cleanup is inherently self-referential (updating CLAUDE.md while
following CLAUDE.md). Rule: apply factual corrections only. Don't rewrite
steering intent. Session logs are append-only (never modified).
This behavior is now enshrined in CLAUDE.md.
