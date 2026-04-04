# V44 Plan — Work Tracking + Testing + Audio Driver + GM Instruments

## Date: 2026-04-04

## Context
User wants to come back in YOLO mode and work through game bugs + GM
instrument quality systematically. This plan sets up the scaffolding.

## Deliverables for v44 (this cut — scaffolding only)
1. WORKLOG.md — master work-to-be-done file with sections per facet
2. CLAUDE.md — reference WORKLOG.md, add work tracking protocol
3. Session-start hook — inject top work items at session start
4. v44 session log + journal

## Work to tackle in subsequent cuts (v45+)

### Priority 1: Testing Infrastructure
- **Local-first testing**: document the local test commands clearly,
  ensure hooks nudge for local runs before push. Avoid GitHub CI minutes.
- **Audio waveform driver**: set up PulseAudio null sink or similar so
  Playwright can load MP3s and we can capture waveform output. Enables:
  - Playhead seeking in MP3 mode
  - Verifying audio actually produces output
  - Automated regression testing of all sound modes
- **End-to-end visual tests**: Playwright screenshots at key positions
  across all modes (game, grid, player) × all sound modes (MP3, MIDI,
  Synth, WASM). Currently partial — works for grid screenshots but can't
  seek without audio loaded.

### Priority 2: General MIDI Instrument Quality
- Proper GM instrument mapping for MIDI mode
- Same quality instruments in WASM mode
- Evaluate Synth mode instrument quality
- This is the "make it sound good" pass

### Priority 3: Outstanding Game Bugs (5 items)
- MIDI track listing next/prev
- Mobile multi-tap track listing
- Grid final score on non-infinite
- Emoji lane crossing
- Key 3 grid mode switch

### Priority 4: Architecture
- Topical index for future_memories
- Session-start hook injects WORKLOG.md top items
