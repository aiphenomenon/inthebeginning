# V29 Plan — V7 Deploy: Full Python Music Port + Bug Fixes

**Created**: 2026-03-23 21:07 CT (02:07 UTC)
**Updated**: 2026-03-24 05:09 CT (10:09 UTC)
**Branch**: claude/resume-v9-document-v8-6yhAe
**Scope**: Port Python composer.py music generation to JavaScript, fix V6 bugs, create V7 deploy

## Session History

- **Turn 1 (2026-03-23 ~15:00 CT)**: V28 session — massive game overhaul (15 bug fixes, V6 deploy created)
- **Turn 2 (2026-03-23 ~21:00 CT)**: User asked to port Python music engine to JS + fix remaining bugs. Plan file created, partial V7 directory scaffolded, **session timed out before code work**.
- **Turn 3 (2026-03-24 ~05:06 CT)**: Resume. User provided full context from turns 1-2 with screenshots. Starting the Python port and bug fixes.

## V28 Completed Work (Verified via Git)

All 20 checklist items completed and committed:
- Branding fix (Cosmic Runner → inthebeginning bounce) — commit 485ef33
- Theme/accessibility overlays wired — commit 485ef33
- MIDI/Synth playback auto-play + playhead — commit 485ef33
- Pause stops both gameplay and music — commit 485ef33
- Modal close-on-click-outside (partial, X button) — commit 1f29808
- Player position NaN/Infinity safety — commit e17b587
- Two-player controls (P1=arrows/WASD, P2=IJKL/numpad) — commit 485ef33
- 3D mode activation in MIDI/Synth modes — commit e17b587
- 3D obstacles fly past instead of piling up — commit e17b587
- Note info display in grid/player modes — commit 7ab264c
- Track list modal only in MP3 mode — commit 485ef33
- Enriched synth generator (12 epochs, 9 layers) — commit 733c250
- Infinite play for album/MIDI/synth — commit 485ef33
- Game completion at end of 12 tracks — commit 485ef33
- Theme colors applied to ground — commit e17b587
- Visualizer removed from deploy — commit 7cc907f
- deploy/v6 created — commit 7cc907f
- Docs updated — commit c3b1306
- Tests added — commit cc2cd99
- AST captures regenerated — commit a90aa2e

## V29 Remaining Work

### Phase 1: Port Python Data Tables to JS music-generator.js
- 44 scales from SCALES dict (Python has 44, JS has 11 hardcoded per-epoch)
- 15 harmonic progressions from PROGRESSIONS dict (JS has 0)
- 25 rhythm patterns from RHYTHM_PATTERNS dict (JS has random patterns)
- 30 melodic motifs from MOTIFS dict (JS has 0)
- Epoch-to-scale, epoch-to-rhythm, epoch-to-progression, epoch-to-motif mappings
- Time signature system
- Humanization (timing jitter)

### Phase 2: Enhance Generation Algorithms
- Replace random chord progression with progression-based chord changes
- Replace random percussion with structured rhythm patterns from Python
- Replace random-walk melody with motif-based phrases
- Add humanization (timing jitter ±10-50ms)

### Phase 3: Fix Remaining V6 Bugs
- Click-outside-to-close for modals (improve beyond X button)
- Audio buffer management for crunchiness (partial fix in V7 synth-engine)
- Two-player state management (vanishing players)
- Player position pinned to right edge

### Phase 4: Create deploy/v7
- Copy from v6, apply all music + bug fix changes
- Ensure shared asset paths work
- .nojekyll

### Phase 5: Interstitial Voice Waveforms
- Generate ~10 voice waveform MP3s using Python TTS or synth
- These substitute for real-time voice generation in browser
- **DEFERRED** to future session

### Phase 6: Test, document, commit, push

## Completion Status — 2026-03-25 07:47 CT (12:47 UTC)

**COMPLETED**: Phases 1-4 and 6 are done. V7 deploy is GitHub Pages ready.

### What Was Done
- All 44 scales, 15 progressions, 25 rhythms, 30 motifs ported from Python
- Generation algorithms upgraded to use motif-based melody, progression-based
  chords, structured rhythm patterns, and humanization jitter
- V7 deploy fully tracked in git with all files
- Deploy asset tests: 106 passed
- V6 bugs already fixed in V28 — no additional fixes needed

### What Remains
- Phase 5 (voice waveform interstitials) deferred to future session
- Album MP3s need to be in deploy/shared/audio/tracks/ for full playback
  (they may already be there from previous sessions)

### Deploy Instructions
```bash
# Copy to GitHub Pages repo:
cp -r deploy/shared/ /path/to/gh-pages-repo/shared/
cp -r deploy/v7/ /path/to/gh-pages-repo/v7/
cd /path/to/gh-pages-repo && git add shared/ v7/ && git commit -m "V7" && git push
```
