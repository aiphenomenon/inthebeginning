# V40 Plan — Journal Verbatim Content Clarification

## Date: 2026-04-04

## Goal
Clarify that assistant_text must be full verbatim screen output (not bracketed
summaries), and that reasoning/process commands go in tool_calls verbatim while
raw code patch diffs are excluded (diff stat is sufficient).

## Deliverables
1. CLAUDE.md: clarify assistant_text and tool_calls content rules
2. v40 journal demonstrating correct verbatim capture
3. Compress v39 journal, update v39-session.md link
