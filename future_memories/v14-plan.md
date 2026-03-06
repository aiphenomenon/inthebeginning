# v0.14.0 Plan — Radio Engine V14: Full Palette Serial Render

## Date: 2026-03-06 16:37 CT

## Context

User found that V13 (V8 core + V12 tempo) eliminated the bitcrusher noise by removing
the double limiting. Now wants V14 to bring back the full instrument palette and MIDI
library from V12, but rendered **serially** (not with multiprocessing) to completely
avoid the bitcrusher artifacts.

Key insight from user: rendering tracks serially (not in parallel) eliminates the
bitcrusher noise. V12 used multiprocessing which contributed to artifacts.

## Plan

### RadioEngineV14 Design
- Inherit from RadioEngineV8 (same base as V12/V13)
- Use V12's `_choose_gm_instruments` — 15 family pools, variety enforcement
- Use V12's `_compute_tempo_multiplier` — 1.1x-1.7x density-aware
- Do NOT override `_render_segment` — use V8's clean version (no GainStage.master_limit)
- Use V8's serial `render_streaming` — inherited, no multiprocessing
- Include V12's family tracking (`_used_family_groups`, `_family_groups`)

### Key Differences from V12
- No `GainStage.master_limit` per segment (V8's clean render path)
- No multiprocessing — serial rendering only
- Still has all 15 instrument families + 744 MIDI files

### Key Differences from V13
- All 15 instrument families (V13 only had V8's 5 pools)
- All 744 MIDI files active
- Same serial render approach

### Deliverables
- RadioEngineV14 class in radio_engine.py
- generate_radio_v14_mp3() function
- CLI --version v14 support
- V14 unit tests
- Two 30-min MP3s: seed 42 + random seed
- Raw GitHub download URLs

## Milestones
- [ ] Housekeeping complete (plan, session log, release history)
- [ ] V14 engine implemented
- [ ] Tests pass
- [ ] MP3s rendered (serial)
- [ ] Committed, pushed, URLs provided
