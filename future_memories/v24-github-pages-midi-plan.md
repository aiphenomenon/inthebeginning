# V24 Plan: GitHub Pages Deployment + MIDI Mode + Enhanced Player

**Created**: 2026-03-22 11:54 CT (16:54 UTC)
**Branch**: claude/resume-v9-document-v8-6yhAe

## Overview

Make Cosmic Runner V3 fully self-contained and deployable to any GitHub Pages repo:
1. Fix audio paths so V3 is self-contained (no cross-directory references)
2. Build a MIDI catalog (1,854 files, 120 composers) with full provenance
3. Implement in-browser MIDI playback via Web Audio API
4. Enhance standalone player with infinite/finite modes, MIDI/MP3 toggle
5. Create build.py to organize all assets for GitHub Pages deployment
6. Write comprehensive deployment guide
7. Full test coverage for all new features

## Key Issues Found

### Audio Path Problem
- V3 currently loads MP3s from `../cosmic-runner-v2/audio/` (cross-directory)
- JSON note files are in V3's own `audio/` dir but MP3s are not
- For GitHub Pages: V3 must be self-contained with all assets in its own tree

### MIDI Mode Gap
- `music-sync.js` has `loadMidiCatalog()`, `getRandomMidi()`, `getMidiDisplayInfo()`
- `config.js` has 16 MIDI_MUTATIONS presets (pitchShift, tempoMult, reverb, filter)
- But NO actual MIDI player/synthesizer exists yet
- Need: Web Audio API MIDI parser + synthesizer module

### MIDI Library (1,854 files, 25MB)
- 120 composer directories
- Sources: MAESTRO (CC BY-NC-SA 4.0), ADL Piano MIDI (CC-BY 4.0), narcisse-dev, Nottingham Folk (public domain)
- All compositions public domain (composers died before 1925)
- Need: midi_catalog.json index with provenance metadata

## Implementation Plan

### Phase 1: Self-Contained Audio
- Copy MP3s into V3's audio directory (or create build.py to symlink/copy)
- Update `_loadMusic()` in app.js to only use local `audio/` paths
- Verify album_notes.json and all 12 per-track JSON files are present

### Phase 2: MIDI Catalog
- Generate `midi_catalog.json` from the library with full provenance
- Include: composer, era, source, license, piece name, file size
- Script: `tools/generate_midi_catalog.py`

### Phase 3: MIDI Player
- `js/midi-player.js` — Web Audio API MIDI parser + synthesizer
- SMF Format 0/1 parsing (VLQ, running status, meta events)
- Multi-channel synthesis (oscillators + envelopes)
- MIDI_MUTATIONS preset support
- Real-time note event emission for grid visualization

### Phase 4: Enhanced Player
- MIDI toggle in UI (switch between album MP3 and MIDI library)
- Infinite mode: shuffle through MIDIs endlessly
- Finite mode: play album tracks in order
- Provenance display: composer, era, source, license
- Mode persistence across page refreshes

### Phase 5: Build & Deploy
- `build.py` for V3: organizes all assets, copies MIDIs, generates dist/
- GitHub Pages deployment guide (DEPLOY.md)
- Instructions for copying to any GitHub Pages repo

### Phase 6: Tests
- MIDI catalog validation tests
- MIDI player unit tests (parser, synthesis, timing)
- V3 integration tests (paths, modes, UI)
- Full codebase sweep

## File Changes

### New Files
- `apps/cosmic-runner-v3/js/midi-player.js`
- `apps/cosmic-runner-v3/audio/midi_catalog.json`
- `apps/cosmic-runner-v3/build.py`
- `apps/cosmic-runner-v3/DEPLOY.md`
- `apps/cosmic-runner-v3/test/test_midi_player.js`
- `tools/generate_midi_catalog.py`
- `tests/test_midi_catalog.py`

### Modified Files
- `apps/cosmic-runner-v3/js/app.js` — fix audio paths, add MIDI mode toggle
- `apps/cosmic-runner-v3/js/player.js` — MIDI playback integration
- `apps/cosmic-runner-v3/js/music-sync.js` — MIDI event emission
- `apps/cosmic-runner-v3/index.html` — MIDI toggle UI, provenance panel
- `apps/cosmic-runner-v3/css/styles.css` — MIDI mode styles
- `RELEASE_HISTORY.md` — V24 entry
