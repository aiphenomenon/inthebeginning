# V41 Plan — Journal Content Validation Hook

## Date: 2026-04-04

## Goal
Add structural and content validation to the stop hook so it catches
mechanical journal shortcuts: invalid JSON, missing required fields,
bracketed summaries in assistant_text, empty tool_calls when tools were used.

## Deliverables
1. Python validator script: `.claude/hooks/validate-journal.py`
2. Stop hook update: call validator, block on failure
3. Demonstrate hook catches a deliberate mistake
4. Compress v40 journal on cut
