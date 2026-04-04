# Work To Be Done

Outstanding work items organized by facet. Updated at each solution cut.
Referenced from `CLAUDE.md` — check this file at session start to understand
current priorities.

---

## Cosmic Runner (inthebeginning-bounce)

### Outstanding Bugs (from V36 plan, partially addressed in v0.36.0)

| # | Category | Issue | Status | Notes |
|---|----------|-------|--------|-------|
| 1 | UI | MIDI track listing: show next/prev 12 tracks | Open | V36 #14 |
| 2 | Mobile | Multiple taps spawns track listing unexpectedly | Open | V36 #16 |
| 3 | Gameplay | Grid mode: no final score when non-infinite ends | Open | V36 #7 |
| 4 | Gameplay | Emoji should not cross lanes (stay in their lane) | Open | V36 #11 |
| 5 | Gameplay | Key 3 (grid mode switch) doesn't work in gameplay | Open | V36 #13 |

### Audio / Instruments

| # | Category | Issue | Status | Notes |
|---|----------|-------|--------|-------|
| 6 | MIDI | General MIDI instrument quality — proper GM instrument mapping | Open | Priority |
| 7 | WASM | General MIDI instruments in WASM mode | Open | Priority |
| 8 | Synth | Evaluate GM instrument quality in Synth mode | Open | |
| 9 | Audio | Instrument Soundbank modal text improvements | Open | V36 #21 |

### Known Issues (browser limitations, not fixable from JS)

| # | Issue | Workaround |
|---|-------|------------|
| K1 | Double pause icon (Unicode rendering at certain viewports) | Resize or use P key |
| K2 | Minimize stops MIDI playback (Firefox/Ubuntu Web Audio) | Alt-tab instead; use MP3 mode |

---

## Testing Infrastructure

| # | Item | Status | Notes |
|---|------|--------|-------|
| T1 | Local-first testing — avoid burning GitHub CI minutes | Plan | Run pytest, Playwright, linting locally before push |
| T2 | End-to-end visual testing with Playwright | Partial | Screenshots work; seeking requires audio driver |
| T3 | Audio waveform driver for headless testing | Plan | Virtual audio sink → waveform capture → verify output |
| T4 | Playhead seeking in MP3 mode (requires audio loaded) | Blocked by T3 | Need audio driver to load MP3s in headless |
| T5 | Note data completeness tests | Done | 112 tests, v43 |

---

## Architecture / Infrastructure

| # | Item | Status | Notes |
|---|------|--------|-------|
| A1 | Work-to-be-done tracking (this file) + steering | v44 | WORKLOG.md + CLAUDE.md reference |
| A2 | Turn-by-turn journal protocol | Done | v37-v42 |
| A3 | Journal content validation hook | Done | v41 |
| A4 | Topical index for future_memories | Open | Navigate by topic, not just time |

---

## Steering / Hooks

| # | Item | Status | Notes |
|---|------|--------|-------|
| S1 | CLAUDE.md references WORKLOG.md | v44 | |
| S2 | Session-start hook shows top work items | Open | Inject from WORKLOG.md |
| S3 | Stop hook verifies WORKLOG.md updated on game changes | Open | |

---

## Simulator (Python reference + cross-language)

No outstanding items. Physics engine stable.

---

## Deploy / GitHub Pages

| # | Item | Status | Notes |
|---|------|--------|-------|
| D1 | v4 note data deployed to v10, v11, shared | Done | v43 |
| D2 | Verify deploy works end-to-end on GitHub Pages | Open | Manual check |

---

## Last Updated

v44 — 2026-04-04
